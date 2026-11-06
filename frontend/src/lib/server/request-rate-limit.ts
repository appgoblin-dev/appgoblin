import { redirect, type RequestEvent } from '@sveltejs/kit';

import { ANONYMOUS_SEARCHES_PER_DAY, RedisRateLimiter } from './redis-rate-limit.js';

const limiter = new RedisRateLimiter();

export const isSearchResultsPath = (pathname: string): boolean =>
	pathname.startsWith(`${SEARCH_PAGE_PATH}/`);

export interface RateLimitResult {
	allowed: boolean;
	limit: number;
	remaining: number;
	retryAfterSeconds: number;
	/** Set when the anonymous search quota, not the token bucket, is the blocker. */
	reason?: 'searchQuota';
}

const SEARCH_PAGE_PATH = '/search';

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
 * user agent is free text that any client can set to anything. These headers
 * are also spoofable; this is only a heuristic, never access control.
 */
function isBrowserDataFetch(event: RequestEvent): boolean {
	const headers = event.request.headers;
	if (headers.has('sec-fetch-site') && headers.has('sec-fetch-dest')) {
		return true;
	}
	// Browsers predating Fetch Metadata send no `Sec-Fetch-*` headers.
	const referer = headers.get('referer');
	if (referer === null) return false;
	try {
		return new URL(referer).origin === event.url.origin;
	} catch {
		return false;
	}
}

/** A data request that did not originate from one of our pages. */
export function isJsonScrape(event: RequestEvent): boolean {
	return event.isDataRequest && !isBrowserDataFetch(event);
}

/**
 * A non-browser client: an agent, crawler or CLI rather than a human's page
 * load or the SPA's own data fetch. Only these are offered a machine payment
 * challenge; browsers keep the sign-in prompt.
 */
export function isMachineClient(event: RequestEvent): boolean {
	const accept = event.request.headers.get('accept');
	if (accept !== null && accept.includes('text/html')) {
		return false;
	}
	return !isBrowserDataFetch(event);
}

function clientKey(event: Pick<RequestEvent, 'getClientAddress'>): string {
	try {
		return event.getClientAddress() || 'unknown';
	} catch {
		return 'unknown';
	}
}

export async function checkPreAuthRateLimit(event: RequestEvent): Promise<RateLimitResult> {
	if (event.cookies.get('session') === undefined) {
		return { allowed: true, limit: 600, remaining: 600, retryAfterSeconds: 0 };
	}
	return limiter.checkPreAuth(clientKey(event));
}

export async function checkRateLimit(event: RequestEvent): Promise<RateLimitResult> {
	const user = event.locals.user;
	const identity = user !== null ? `user:${user.id}` : `ip:${clientKey(event)}`;
	const search =
		user === null && isSearchResultsPath(event.url.pathname) && !isBlockedDataRequest(event);
	const result = await limiter.check(identity, search);
	if (result.searchRemaining !== undefined) {
		event.locals.anonymousSearchQuota = {
			remaining: result.searchRemaining,
			limit: ANONYMOUS_SEARCHES_PER_DAY
		};
	}
	return result;
}

/**
 * A direct data request for a noindex or auth-gated page. A 404 is cheaper than
 * serving the payload and then rate limiting the follow-up requests. Indexable pages remain subject to the ordinary IP quota.
 */
export function isBlockedDataRequest(event: RequestEvent): boolean {
	if (event.locals.user !== null || event.locals.machinePaid) {
		return false;
	}
	return isJsonScrape(event) && isNoindexPath(event.url.pathname);
}

/**
 * Signed-out visitors who exhausted their daily search quota are sent to the
 * login page rather than shown a 429: the quota is a sign-up prompt, not a
 * punishment, and `redirectTo` brings them back to the results they wanted.
 * SvelteKit turns a hook redirect into a JSON redirect for `__data.json`
 * requests, so client-side navigations follow it too.
 */
export function challengeAnonymousSearchQuota(event: RequestEvent, result: RateLimitResult): void {
	if (result.allowed || result.reason !== 'searchQuota' || isMachineClient(event)) {
		return;
	}
	const redirectTo = encodeURIComponent(event.url.pathname + event.url.search);
	redirect(303, `/auth/login?redirectTo=${redirectTo}`);
}

export function rateLimitResponse(event: RequestEvent, result: RateLimitResult): Response {
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
