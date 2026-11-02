import { redirect, type RequestEvent } from '@sveltejs/kit';

import { ExpiringTokenBucket, RefillingTokenBucket } from './auth/rate-limit.js';
import { getClientIP } from './request.js';

export type RateLimitTier = 'authenticated' | 'anonymous' | 'jsonScraper';

export const isSearchResultsPath = (pathname: string): boolean =>
	pathname.startsWith(`${SEARCH_PAGE_PATH}/`);

export interface RateLimitResult {
	allowed: boolean;
	tier: RateLimitTier;
	limit: number;
	remaining: number;
	retryAfterSeconds: number;
	/** Set when the anonymous search quota, not the token bucket, is the blocker. */
	reason?: 'searchQuota';
}

/**
 * `max` is the burst size and one token refills per second, so it is also the
 * sustained requests-per-minute ceiling. Signed-in users are keyed by user id
 * so they never compete with anonymous traffic sharing their IP.
 */
const BUCKETS: Record<RateLimitTier, RefillingTokenBucket<string>> = {
	authenticated: new RefillingTokenBucket<string>(600, 1),
	anonymous: new RefillingTokenBucket<string>(300, 1),
	// Small bucket plus a large per-request cost, so a scraper is out after a
	// couple of requests.
	jsonScraper: new RefillingTokenBucket<string>(30, 1)
};

/**
 * Runs before session validation, which costs a database lookup per request.
 */
const PRE_AUTH_BUCKET = new RefillingTokenBucket<string>(600, 1);

/**
 * Anonymous search is metered separately and on a much tighter budget than the
 * general token bucket: the search page is the most expensive and most scraped
 * route, so signed-out visitors get three searches per day and are then asked
 * to sign in. Signed-in users keep the `authenticated` bucket above.
 */
export const ANONYMOUS_SEARCHES_PER_DAY = 5;
const DAY_SECONDS = 24 * 60 * 60;
const SEARCH_PAGE_PATH = '/search';

const anonymousSearchBucket = new ExpiringTokenBucket<string>(
	ANONYMOUS_SEARCHES_PER_DAY,
	DAY_SECONDS
);

interface CostProfile {
	read: number;
	write: number;
	dataRequest: number;
	expensiveRoute: number;
}

/**
 * `__data.json` requests are the documented way to read page data without the
 * HTML shell, so they cost extra — heavily for clients that did not come from
 * one of our own pages.
 */
const COSTS: Record<RateLimitTier, CostProfile> = {
	authenticated: { read: 1, write: 3, dataRequest: 1, expensiveRoute: 1 },
	anonymous: { read: 1, write: 3, dataRequest: 2, expensiveRoute: 1 },
	jsonScraper: { read: 3, write: 9, dataRequest: 6, expensiveRoute: 3 }
};

/** Routes that fan out into several backend queries. */
const EXPENSIVE_PREFIXES = [
	'/search',
	'/api/',
	'/companies/',
	'/apps/',
	'/sdks/',
	'/ad-creatives',
	'/collections/',
	'/categories/',
	'/keywords/',
	'/developers/',
	'/app-explorer',
	'/top-mobile-advertisers'
];

/** Routes whose pages are `noindex` or auth-gated. */
const NOINDEX_PREFIXES = ['/search', '/apps/comparison', '/sdks', '/auth', '/account'];

export function isNoindexPath(pathname: string): boolean {
	return NOINDEX_PREFIXES.some((prefix) => pathname.startsWith(prefix));
}

export function isStaticAssetPath(pathname: string): boolean {
	return pathname.startsWith('/_app') || pathname.startsWith('/favicon');
}

/**
 * Browsers attach Fetch Metadata headers to every `fetch()`, including the one
 * SvelteKit's router makes for `__data.json`. A crawler calling the endpoint
 * over plain HTTP sends none. Header check rather than user agent because a
 * user agent is free text that any client can set to anything.
 */
function isBrowserDataFetch(event: RequestEvent): boolean {
	const headers = event.request.headers;
	if (headers.has('sec-fetch-site') && headers.has('sec-fetch-dest')) {
		return true;
	}
	// Browsers predating Fetch Metadata send no `Sec-Fetch-*` headers.
	const referer = headers.get('referer');
	return referer !== null && referer.startsWith(event.url.origin);
}

/** A data request that did not originate from one of our pages. */
export function isJsonScrape(event: RequestEvent): boolean {
	return event.isDataRequest && !isBrowserDataFetch(event);
}

function clientKey(event: Pick<RequestEvent, 'request' | 'getClientAddress'>): string {
	const ip = getClientIP(event.request);
	if (ip !== null) {
		return ip;
	}
	try {
		return event.getClientAddress();
	} catch {
		// Share one bucket rather than letting the request through unmetered.
		return 'unknown';
	}
}

function requestCost(event: RequestEvent, tier: RateLimitTier): number {
	const profile = COSTS[tier];
	const method = event.request.method;
	const isRead = method === 'GET' || method === 'HEAD' || method === 'OPTIONS';

	let cost = isRead ? profile.read : profile.write;
	if (event.isDataRequest) {
		cost += profile.dataRequest;
	}
	if (EXPENSIVE_PREFIXES.some((prefix) => event.url.pathname.startsWith(prefix))) {
		cost += profile.expensiveRoute;
	}
	return cost;
}

function consume(
	bucket: RefillingTokenBucket<string>,
	key: string,
	cost: number
): Omit<RateLimitResult, 'tier'> {
	const allowed = bucket.consume(key, cost);
	const remaining = bucket.getRemaining(key);
	return {
		allowed,
		limit: bucket.max,
		remaining,
		// One token refills per interval, so the wait is the size of the deficit.
		retryAfterSeconds: allowed
			? 0
			: Math.max(1, Math.ceil((cost - remaining) * bucket.refillIntervalSeconds))
	};
}

export function checkPreAuthRateLimit(event: RequestEvent): Omit<RateLimitResult, 'tier'> {
	if (event.cookies.get('session') === undefined) {
		return {
			allowed: true,
			limit: PRE_AUTH_BUCKET.max,
			remaining: PRE_AUTH_BUCKET.max,
			retryAfterSeconds: 0
		};
	}
	return consume(PRE_AUTH_BUCKET, clientKey(event), 1);
}

/**
 * Must run after the auth handle so `locals.user` is populated.
 */
export function checkRateLimit(event: RequestEvent): RateLimitResult {
	const user = event.locals.user;
	const searchQuota = consumeAnonymousSearch(event);
	if (searchQuota !== null && !searchQuota.allowed) {
		// Report the quota rather than the general bucket: it is the tighter of
		// the two limits and the one the caller can act on.
		return { ...searchQuota, tier: 'anonymous', reason: 'searchQuota' };
	}

	const tier: RateLimitTier =
		user !== null ? 'authenticated' : isJsonScrape(event) ? 'jsonScraper' : 'anonymous';

	const key = user !== null ? `user:${user.id}` : `ip:${clientKey(event)}`;
	return { ...consume(BUCKETS[tier], key, requestCost(event, tier)), tier };
}

/**
 * A direct data request for a noindex or auth-gated page. A 404 is cheaper than
 * serving the payload and then rate limiting the follow-up requests. Indexable
 * pages are not blocked; they are charged to the `jsonScraper` bucket and get
 * an `X-Robots-Tag` header instead.
 */
export function isBlockedDataRequest(event: RequestEvent): boolean {
	if (event.locals.user !== null) {
		return false;
	}
	return isJsonScrape(event) && isNoindexPath(event.url.pathname);
}

/**
 * The rendered results route, `/search/<term>`. The bare `/search` route only
 * 303s to it, so charging that too would bill one search twice.
 */
/**
 * Charge a signed-out visit to a search page against the daily quota.
 *
 * Both the rendered page and the `__data.json` twin are charged, because the
 * site's own search box navigates client-side and would otherwise never touch
 * the quota. Crawlers calling `__data.json` directly never get this far:
 * `isBlockedDataRequest` 404s them first, so one charge means one search.
 */
function consumeAnonymousSearch(event: RequestEvent): Omit<RateLimitResult, 'tier'> | null {
	if (event.locals.user !== null || !isSearchResultsPath(event.url.pathname)) {
		return null;
	}
	const key = `ip:${clientKey(event)}`;
	const allowed = anonymousSearchBucket.consume(key, 1);
	return {
		allowed,
		limit: anonymousSearchBucket.max,
		remaining: anonymousSearchBucket.getRemaining(key),
		retryAfterSeconds: allowed ? 0 : DAY_SECONDS
	};
}

/**
 * What is left of the anonymous daily search quota, for the page to warn with.
 * `null` for signed-in users, who are not on this quota.
 */
export function getAnonymousSearchQuota(
	event: Pick<RequestEvent, 'locals' | 'request' | 'getClientAddress'>
): { remaining: number; limit: number } | null {
	if (event.locals.user !== null) {
		return null;
	}
	return {
		remaining: anonymousSearchBucket.getRemaining(`ip:${clientKey(event)}`),
		limit: anonymousSearchBucket.max
	};
}

/**
 * Signed-out visitors who exhausted their daily search quota are sent to the
 * login page rather than shown a 429: the quota is a sign-up prompt, not a
 * punishment, and `redirectTo` brings them back to the results they wanted.
 * SvelteKit turns a hook redirect into a JSON redirect for `__data.json`
 * requests, so client-side navigations follow it too.
 */
export function challengeAnonymousSearchQuota(event: RequestEvent, result: RateLimitResult): void {
	if (result.allowed || result.reason !== 'searchQuota') {
		return;
	}
	const redirectTo = encodeURIComponent(event.url.pathname + event.url.search);
	redirect(303, `/auth/login?redirectTo=${redirectTo}`);
}

export function rateLimitResponse(
	event: RequestEvent,
	result: Omit<RateLimitResult, 'tier'>
): Response {
	const headers = new Headers({
		'Retry-After': String(result.retryAfterSeconds),
		'RateLimit-Limit': String(result.limit),
		'RateLimit-Remaining': String(Math.max(0, result.remaining)),
		'RateLimit-Reset': String(result.retryAfterSeconds),
		'Cache-Control': 'no-store'
	});

	// SvelteKit's client parses data responses as JSON, so a plain-text body
	// would surface as an opaque "Internal Error" instead of the real status.
	if (event.isDataRequest) {
		headers.set('Content-Type', 'application/json');
		return new Response(JSON.stringify({ message: 'Too many requests' }), {
			status: 429,
			headers
		});
	}

	headers.set('Content-Type', 'text/plain; charset=utf-8');
	return new Response('Too many requests', { status: 429, headers });
}

// A fully refilled bucket behaves exactly like a missing one, so dropping it
// keeps the map from growing for the lifetime of the process.
const sweepTimer = setInterval(() => {
	for (const bucket of Object.values(BUCKETS)) {
		bucket.sweep();
	}
	PRE_AUTH_BUCKET.sweep();
	anonymousSearchBucket.sweep();
}, 60_000);
sweepTimer.unref?.();
