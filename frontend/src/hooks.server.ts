import type { Handle, ServerInit } from '@sveltejs/kit';
import { sequence } from '@sveltejs/kit/hooks';
import type { CatData, CompanyTypes, AppStore, CollectionRanks, CategoryRanks } from './types';
import { RefillingTokenBucket } from '$lib/server/auth/rate-limit';
import {
	validateSessionToken,
	setSessionTokenCookie,
	deleteSessionTokenCookie
} from '$lib/server/auth/session';

const bucket = new RefillingTokenBucket<string>(100, 1);

// Rate limiting handle
const rateLimitHandle: Handle = async ({ event, resolve }) => {
	const route = event.url.pathname;

	// Skip rate limiting for static assets
	if (route.startsWith('/_app') || route.startsWith('/favicon')) {
		return resolve(event);
	}

	// Optional: Skip rate limiting for specific public routes
	// const publicRoutes = ['/about', '/companies', '/apps'];
	// if (publicRoutes.some(path => route.startsWith(path))) {
	//     return resolve(event);
	// }

	const clientIP = event.request.headers.get('X-Forwarded-For');
	if (clientIP === null) {
		return resolve(event);
	}

	let cost: number;
	if (event.request.method === 'GET' || event.request.method === 'OPTIONS') {
		cost = 1;
	} else {
		cost = 3;
	}

	if (!bucket.consume(clientIP, cost)) {
		return new Response('Too many requests', {
			status: 429
		});
	}

	return resolve(event);
};

// Authentication handle
const authHandle: Handle = async ({ event, resolve }) => {
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

	// --- Block requests until cache is ready (except for static assets) ---
	if (
		!route.startsWith('/_app') &&
		!route.startsWith('/favicon') &&
		!isInitialized &&
		initializationPromise
	) {
		const waitStart = Date.now();
		await initializationPromise;
		const waitDuration = Date.now() - waitStart;
		if (waitDuration > 100) {
			console.log(`[Handle] Request to ${route} waited ${waitDuration}ms for cache`);
		}
	}

	const response = await resolve(event);

	// --- Cache control for specific paths ---
	// Only cache when unauthenticated: layout data includes user, so cached HTML would show
	// "logged out" on direct navigation even when the user has a valid session.
	const cacheablePaths = ['/companies', '/about', '/apps', '/ad-creatives'];
	const pathIsCacheable = cacheablePaths.some((path) => event.url.pathname.startsWith(path));
	const isAuthenticated = event.locals.user !== null;

	if (pathIsCacheable && !isAuthenticated) {
		response.headers.set('cache-control', 'public, max-age=86400, stale-while-revalidate=3600');
		response.headers.set('Vary', 'Cookie');
	}

	return response;
};

// Combine all handles in sequence
export const handle = sequence(rateLimitHandle, authHandle, cacheAndRoutingHandle);

// Cache initialization code
interface Country {
	code: string;
	name: string;
}

interface CachedData {
	appCats: CatData;
	appsOverview: any;
	companyTypes: CompanyTypes;
	countries: Country[];
	myRankingsMap?: any;
	storeIDLookup: Record<number, AppStore>;
	collectionIDLookup: Record<number, Record<number, CollectionRanks>>;
	categoryIDLookup: Record<number, Record<number, CategoryRanks>>;
}

let cachedData: CachedData = {
	appCats: { categories: [] },
	appsOverview: {},
	companyTypes: { types: [] },
	countries: [],
	storeIDLookup: {},
	collectionIDLookup: {},
	categoryIDLookup: {}
};

let isInitialized = false;
let initializationPromise: Promise<void> | null = null;
let initStartTime: number | null = null;

const API_BASE_URL = 'http://localhost:8000/api';

async function fetchWithRetry(url: string, retries = 10): Promise<any> {
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
			await new Promise((resolve) => setTimeout(resolve, Math.pow(2, i) * 1000));
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
		const [appCats, appsOverview, companyTypes, countries, myStoreRankingsMap] = await Promise.all([
			fetchWithRetry(`${API_BASE_URL}/categories`),
			fetchWithRetry(`${API_BASE_URL}/apps/overview`),
			fetchWithRetry(`${API_BASE_URL}/companies/types`),
			fetchWithRetry(`${API_BASE_URL}/categories/countries`),
			fetchWithRetry(`${API_BASE_URL}/rankings`)
		]);

		const { storeIDLookup, collectionIDLookup, categoryIDLookup } =
			buildRankingsLookups(myStoreRankingsMap);

		cachedData = {
			appCats,
			appsOverview,
			companyTypes,
			countries,
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
	}
}

export const init: ServerInit = async () => {
	initializationPromise = initializeCache();
	await initializationPromise;
};

export const getCachedData = async (): Promise<CachedData> => {
	if (!isInitialized && initializationPromise) {
		console.log('[Cache] Waiting for cache initialization...');
		const waitStart = Date.now();
		await initializationPromise;
		const waitDuration = Date.now() - waitStart;
		console.log(`[Cache] Cache ready after ${waitDuration}ms wait`);
	}

	if (!isInitialized) {
		console.warn('[Cache] Cache not initialized, returning empty defaults');
	}

	return cachedData;
};
