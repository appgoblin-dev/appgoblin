import { sequence, type Handle, type ServerInit } from '@sveltejs/kit/hooks';
import type { RequestEvent } from '@sveltejs/kit';
import { building } from '$app/env';

import type { CompanyTypes, AppStore, CollectionRanks, CategoryRanks, Countries } from './types';

import {
	validateSessionToken,
	setSessionTokenCookie,
	deleteSessionTokenCookie
} from '#lib/server/auth/session.js';
import {
	challengeAnonymousSearchQuota,
	checkPreAuthRateLimit,
	checkRateLimit,
	isBlockedDataRequest,
	isNoindexPath,
	isSearchResultsPath,
	isStaticAssetPath,
	isMachineClient,
	rateLimitResponse
} from '#lib/server/request-rate-limit.js';
import {
	machinePagePayment,
	machineSearchPayment,
	isMachinePayablePath
} from '#lib/server/machine-payment.js';
import {
	machineJsonKind,
	machineJsonResponse,
	wantsMachineJson
} from '#lib/server/machine-json.js';

// Static assets, the live-session probe (the header calls /auth/me on every SPA
// navigation, so a 429 would blank it) and the health check.
function isRateLimitExempt(event: RequestEvent): boolean {
	const route = event.url.pathname;
	return building || isStaticAssetPath(route) || route === '/auth/me' || route === '/check';
}

function rateLimitUnavailableResponse(event: RequestEvent): Response {
	const headers = { 'Cache-Control': 'no-store', 'Retry-After': '1' };
	return event.isDataRequest
		? new Response(JSON.stringify({ message: 'Rate limiting unavailable' }), {
				status: 503,
				headers: { ...headers, 'Content-Type': 'application/json' }
			})
		: new Response('Rate limiting unavailable', { status: 503, headers });
}

// Runs before session validation, which costs a database lookup per request.
const preAuthRateLimitHandle: Handle = async ({ event, resolve }) => {
	if (isRateLimitExempt(event)) {
		return resolve(event);
	}

	let result;
	try {
		result = await checkPreAuthRateLimit(event);
	} catch {
		return rateLimitUnavailableResponse(event);
	}
	if (!result.allowed) {
		return rateLimitResponse(event, result);
	}

	return resolve(event);
};

function isMachinePaymentClient(event: RequestEvent): boolean {
	return !event.isDataRequest && machineJsonKind(event.url.pathname) !== null
		? wantsMachineJson(event.request)
		: isMachineClient(event);
}

// Offer payment before auth and rate limiting on eligible pages.
const machinePagePaymentHandle: Handle = async ({ event, resolve }) => {
	if (
		event.locals.user !== null ||
		!isMachinePayablePath(event.url.pathname) ||
		!isMachinePaymentClient(event)
	) {
		return resolve(event);
	}

	const paymentResponse = await machinePagePayment(event.request, () => {
		event.locals.machinePaid = true;
		return resolve(event);
	});
	if (paymentResponse !== null) return paymentResponse;

	return resolve(event);
};

// Runs after authHandle so signed-in users are keyed by user id.
const rateLimitHandle: Handle = async ({ event, resolve }) => {
	if (isRateLimitExempt(event)) {
		return resolve(event);
	}

	// Don't rate-limit a request after charging it.
	if (event.locals.machinePaid) {
		return resolve(event);
	}

	let result;
	try {
		result = await checkRateLimit(event);
	} catch {
		return rateLimitUnavailableResponse(event);
	}
	if (!result.allowed) {
		if (
			result.reason === 'searchQuota' &&
			isSearchResultsPath(event.url.pathname) &&
			!event.request.headers.has('cookie') &&
			isMachinePaymentClient(event)
		) {
			const paymentResponse = await machineSearchPayment(event.request, () => {
				event.locals.machinePaid = true;
				return resolve(event);
			});
			if (paymentResponse !== null) return paymentResponse;
		}

		// Throws a redirect to the login page when the anonymous search quota is
		// exhausted; every other limit still answers with a 429.
		challengeAnonymousSearchQuota(event, result);
		return rateLimitResponse(event, result);
	}

	// This is a heuristic, not an authorization boundary: headers can be spoofed.
	if (isBlockedDataRequest(event)) {
		return new Response(JSON.stringify({ message: 'Not found' }), {
			status: 404,
			headers: {
				'Content-Type': 'application/json',
				'X-Robots-Tag': 'noindex, nofollow',
				'Cache-Control': 'no-store'
			}
		});
	}

	return resolve(event);
};

// Authentication handle
const authHandle: Handle = async ({ event, resolve }) => {
	event.locals.machinePaid = false;
	const token = event.cookies.get('session') ?? null;
	if (token === null) {
		event.locals.user = null;
		event.locals.session = null;
		return resolve(event);
	}

	const { session, user } = await validateSessionToken(token);
	if (session !== null) {
		setSessionTokenCookie(event, token, session.expiresAt);
	} else {
		deleteSessionTokenCookie(event);
	}

	event.locals.session = session;
	event.locals.user = user;
	return resolve(event);
};

// Cache and routing handle
const cacheAndRoutingHandle: Handle = async ({ event, resolve }) => {
	const route = event.url.pathname;

	// --- Handle redirects first (no need to wait for cache) ---
	if (route.startsWith('/networks')) {
		return new Response(undefined, {
			status: 301,
			headers: { Location: '/companies/types/ad-networks' }
		});
	}
	if (route.startsWith('/companies/github.com/')) {
		return new Response(undefined, {
			status: 301,
			headers: { Location: route.replace('github.com/', 'github.com-') }
		});
	}
	if (route.startsWith('/trackers')) {
		return new Response(undefined, {
			status: 301,
			headers: { Location: '/companies/types/ad-attribution' }
		});
	}
	if (route.startsWith('/adtech')) {
		return new Response(undefined, { status: 301, headers: { Location: '/companies' } });
	}
	if (route.startsWith('/companies/types/monetization')) {
		return new Response(undefined, {
			status: 301,
			headers: { Location: '/companies/types/ad-networks' }
		});
	}
	if (route === '/collections/new_weekly') {
		return new Response(undefined, {
			status: 301,
			headers: { Location: '/collections/new_weekly/google/overall' }
		});
	}
	if (route === '/collections/new_monthly') {
		return new Response(undefined, {
			status: 301,
			headers: { Location: '/collections/new_monthly/google/overall' }
		});
	}
	if (route === '/collections/new_yearly') {
		return new Response(undefined, {
			status: 301,
			headers: { Location: '/collections/new_yearly/google/overall' }
		});
	}

	// --- Bounded wait for cache init, only for routes that need it ---
	// The cache is only consumed by a small number of routes. Waiting on it for
	// every request (e.g. /auth/*, which doesn't touch the cache) lets a slow
	// or failing API init hang the whole subtree until the reverse proxy times
	// out — that's the source of the 523s on cold paths. Use a short budget so
	// a stuck init can't exceed typical origin timeouts.
	const cacheDependentPrefixes = [
		'/companies',
		'/apps',
		'/top-mobile-advertisers',
		'/sdks',
		'/ad-creatives',
		'/collections',
		'/categories'
	];
	const needsCache = cacheDependentPrefixes.some((p) => route.startsWith(p));
	if (needsCache && !isInitialized) {
		// Kick off on-demand init if none is in progress (e.g. start-up attempt failed).
		if (!initializationPromise) {
			initializationPromise = initializeCache();
		}
		const CACHE_WAIT_BUDGET_MS = 2000;
		const waitStart = Date.now();
		await Promise.race([
			initializationPromise,
			new Promise<void>((resolve) => setTimeout(resolve, CACHE_WAIT_BUDGET_MS))
		]);
		const waitDuration = Date.now() - waitStart;
		if (waitDuration > 100) {
			console.log(`[Handle] Request to ${route} waited ${waitDuration}ms for cache`);
		}
	}

	const jsonKind =
		!event.isDataRequest && (event.request.method === 'GET' || event.request.method === 'HEAD')
			? machineJsonKind(route)
			: null;
	const response =
		jsonKind && wantsMachineJson(event.request)
			? event.request.method === 'HEAD'
				? new Response(null, {
						headers: { 'Content-Type': 'application/json', 'Cache-Control': 'private, no-store' }
					})
				: await machineJsonResponse(event, jsonKind)
			: await resolve(event);

	const isStaticAssetRequest = route.startsWith('/_app') || route.startsWith('/favicon');

	if (!isStaticAssetRequest) {
		appendVaryHeader(response, 'Cookie');
	}
	if (machineJsonKind(route)) appendVaryHeader(response, 'Accept');

	if (event.isDataRequest && isNoindexPath(route)) {
		response.headers.set('X-Robots-Tag', 'noindex, nofollow');
	}

	// Page HTML and SvelteKit data can depend on the current session.
	const contentType = response.headers.get('content-type') ?? '';
	if (
		!response.ok ||
		event.isDataRequest ||
		contentType.startsWith('text/html') ||
		event.locals.machinePaid ||
		(event.locals.user !== null && !isStaticAssetRequest)
	) {
		response.headers.set('cache-control', 'private, no-store');
	}

	if (route === '/check') {
		response.headers.set('Cache-Control', 'no-store,no-cache,must-revalidate');
		response.headers.set('Pragma', 'no-cache');
		response.headers.set('Expires', '0');
	}

	return response;
};

// Combine all handles in sequence
export const handle = sequence(
	preAuthRateLimitHandle,
	authHandle,
	machinePagePaymentHandle,
	rateLimitHandle,
	cacheAndRoutingHandle
);

interface CachedData {
	appsOverview: any;
	companyTypes: CompanyTypes;
	countries: Countries;
	companyDirectory: Array<{
		name: string;
		company_domain: string;
		parent_company_domain: string | null;
		parent_company_name: string | null;
		company_logo_url: string | null;
		parent_company_logo_url: string | null;
	}>;
	myRankingsMap?: any;
	storeIDLookup: Record<number, AppStore>;
	collectionIDLookup: Record<number, Record<number, CollectionRanks>>;
	categoryIDLookup: Record<number, Record<number, CategoryRanks>>;
}

let cachedData: CachedData = {
	appsOverview: {},
	companyTypes: { types: [] },
	countries: { ['US']: { langen: 'United States', app_ranks: true, app_details: true } },
	companyDirectory: [],
	storeIDLookup: {},
	collectionIDLookup: {},
	categoryIDLookup: {}
};

let isInitialized = false;
let initializationPromise: Promise<void> | null = null;
let initStartTime: number | null = null;

const API_BASE_URL = 'http://localhost:8000/api';

function appendVaryHeader(response: Response, value: string) {
	const existing = response.headers.get('Vary');
	if (existing == null || existing.trim() === '') {
		response.headers.set('Vary', value);
		return;
	}

	const values = existing
		.split(',')
		.map((entry) => entry.trim())
		.filter((entry) => entry.length > 0);

	if (!values.includes(value)) {
		values.push(value);
		response.headers.set('Vary', values.join(', '));
	}
}

async function fetchWithRetry(url: string, retries = 3): Promise<any> {
	for (let i = 0; i < retries; i++) {
		try {
			const response = await fetch(url);
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}
			return await response.json();
		} catch (error) {
			console.error(`Attempt ${i + 1} failed for ${url}:`, error);
			if (i === retries - 1) throw error;
			// Cap each backoff at 1s so total worst-case init stays well under any
			// origin timeout. Previous code used Math.pow(2, i) * 1000 with i up to 9,
			// which could block for ~17 minutes on a single failing endpoint.
			await new Promise((resolve) => setTimeout(resolve, Math.min(1000, 100 * Math.pow(2, i))));
		}
	}
}

function buildRankingsLookups(rankings: { stores_rankings: AppStore[] }) {
	const storeIDLookup: Record<number, AppStore> = {};
	const collectionIDLookup: Record<number, Record<number, CollectionRanks>> = {};
	const categoryIDLookup: Record<number, Record<number, CategoryRanks>> = {};

	rankings.stores_rankings.forEach((store) => {
		storeIDLookup[store.store_id] = store;
		store.collections.forEach((collection) => {
			if (!collectionIDLookup[store.store_id]) collectionIDLookup[store.store_id] = {};
			collectionIDLookup[store.store_id][collection.collection_id] = collection;
			collection.categories.forEach((category) => {
				if (!categoryIDLookup[collection.collection_id])
					categoryIDLookup[collection.collection_id] = {};
				categoryIDLookup[collection.collection_id][category.category_id] = category;
			});
		});
	});

	return { storeIDLookup, collectionIDLookup, categoryIDLookup };
}

async function initializeCache(): Promise<void> {
	if (isInitialized) return;

	initStartTime = Date.now();
	console.log('[Cache] Initializing cache on server start...');

	try {
		const [appsOverview, companyTypes, countries, companyDirectory, myStoreRankingsMap] =
			await Promise.all([
				fetchWithRetry(`${API_BASE_URL}/apps/overview`),
				fetchWithRetry(`${API_BASE_URL}/companies/types`),
				fetchWithRetry(`${API_BASE_URL}/categories/countries`),
				fetchWithRetry(`${API_BASE_URL}/companies/list`),
				fetchWithRetry(`${API_BASE_URL}/rankings`)
			]);

		const { storeIDLookup, collectionIDLookup, categoryIDLookup } =
			buildRankingsLookups(myStoreRankingsMap);

		cachedData = {
			appsOverview,
			companyTypes,
			countries,
			companyDirectory,
			storeIDLookup,
			collectionIDLookup,
			categoryIDLookup
		};

		isInitialized = true;
		const duration = Date.now() - initStartTime!;
		console.log(`[Cache] Cache initialized successfully in ${duration}ms`);
	} catch (error) {
		const duration = initStartTime ? Date.now() - initStartTime : 0;
		console.error(`[Cache] Failed to initialize cache after ${duration}ms:`, error);
		// Reset so the next request can retry initialization (e.g. backend not ready yet).
		initializationPromise = null;
	}
}

export const init: ServerInit = () => {
	// Kick off cache init in the background; do not block server startup on it.
	// Routes that need the cache wait briefly in the handle (with a budget); if
	// init is still pending, the loader can fall back to on-demand fetches.
	initializationPromise = initializeCache();
};

export const getCachedData = async (): Promise<CachedData> => {
	if (!isInitialized) {
		if (initializationPromise) {
			console.log('[Cache] Waiting for cache initialization...');
			const waitStart = Date.now();
			await initializationPromise;
			const waitDuration = Date.now() - waitStart;
			console.log(`[Cache] Cache ready after ${waitDuration}ms wait`);
		} else {
			// No initialization in progress — start one on-demand (e.g. previous start-up attempt failed).
			console.log('[Cache] Cache not initialized, triggering on-demand initialization...');
			initializationPromise = initializeCache();
			await initializationPromise;
		}
	}

	return cachedData;
};
