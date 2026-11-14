import { isHttpError, isRedirect, json, redirect, type RequestEvent } from '@sveltejs/kit';
import { createApiClient } from './api.js';
import { requireAuthOrMachinePayment } from './auth/auth.js';
import { sanitizeSearchTerm } from '#lib/search.js';

export const machineJsonExamples = {
	search: {
		apps: {
			key: 'music',
			apple: { title: 'Apple', apps: [] },
			google: { title: 'Google', apps: [] }
		},
		companies: []
	},
	keywords: {
		app: { store_id: 'com.example.app', name: 'Example' },
		keywords: { keywords: [], keyword_scores: [] }
	},
	sdks: {
		app: { store_id: 'com.example.app', name: 'Example' },
		sdk: {
			permissions: [],
			company_categories: {},
			leftovers: {},
			app_queries: [],
			skadnetwork: [],
			company_details: {}
		}
	},
	pattern: { apps: { apps: [] }, companies: { companies: [] } },
	mapped: {
		sdk_id: 1,
		sdk_name: 'Example SDK',
		apps: [],
		owner: {},
		patterns: { package_patterns: [], paths: [], mediation_patterns: [] }
	}
} as const;

export type MachineJsonKind = keyof typeof machineJsonExamples;

export function machineJsonExample(kind: MachineJsonKind, path: string): unknown {
	if (kind === 'sdks') {
		const section = path.replace(/\/$/, '').split('/').at(-1);
		const field =
			section === 'queries' ? 'app_queries' : section === 'unknowns' ? 'leftovers' : section;
		if (field && ['permissions', 'app_queries', 'skadnetwork', 'leftovers'].includes(field)) {
			return {
				app: machineJsonExamples.sdks.app,
				sdk: { [field]: field === 'leftovers' ? {} : [] }
			};
		}
	}
	return machineJsonExamples[kind];
}

export function machineJsonKind(path: string): MachineJsonKind | null {
	if (/^\/search\/[^/]+\/?$/.test(path)) return 'search';
	if (/^\/apps\/[^/]+\/keywords(?:\/(?:discovery|ranking))?\/?$/.test(path)) return 'keywords';
	if (/^\/apps\/[^/]+\/sdks(?:\/(?:permissions|queries|skadnetwork|unknowns))?\/?$/.test(path))
		return 'sdks';
	if (/^\/sdks\/mapped\/[^/]+\/?$/.test(path)) return 'mapped';
	if (/^\/sdks\/[^/]+\/?$/.test(path)) return 'pattern';
	return null;
}

export function wantsMachineJson(request: Request): boolean {
	const accept = request.headers.get('accept');
	if (!accept) return true;
	return !accept.split(',').some((part) => {
		const [type, ...params] = part.trim().toLowerCase().split(';');
		const quality = params.find((param) => param.trim().startsWith('q='));
		return type.trim() === 'text/html' && (!quality || Number(quality.trim().slice(2)) > 0);
	});
}

export async function machineJsonResponse(
	event: RequestEvent,
	kind: MachineJsonKind
): Promise<Response> {
	try {
		return await loadMachineJson(event, kind);
	} catch (error) {
		if (isRedirect(error)) throw error;
		if (isHttpError(error)) {
			return json(error.body, {
				status: error.status,
				headers: { Vary: 'Accept, Cookie', 'Cache-Control': 'private, no-store' }
			});
		}
		console.error('Machine JSON response failed:', error);
		return json(
			{ message: 'Internal Error' },
			{ status: 500, headers: { Vary: 'Accept, Cookie', 'Cache-Control': 'private, no-store' } }
		);
	}
}

async function loadMachineJson(event: RequestEvent, kind: MachineJsonKind): Promise<Response> {
	const api = createApiClient(event.fetch);
	let data: unknown;
	if (kind === 'search') {
		const term = sanitizeSearchTerm(event.params.term ?? '');
		if (!term) redirect(303, '/');
		const encoded = encodeURIComponent(term);
		const [apps, companies] = await Promise.all([
			api.get(`/apps/search/${encoded}`, 'Apps Search', 30000, event.locals.user?.id),
			api.get(`/companies/search/${encoded}`, 'Companies Search')
		]);
		data = { apps, companies };
	} else {
		requireAuthOrMachinePayment(event);
		if (kind === 'keywords' || kind === 'sdks') {
			const id = encodeURIComponent(event.params.id ?? '');
			const app = await api.get(`/apps/${id}`, 'App Details');
			if (kind === 'keywords') {
				const keywords =
					app.description && app.description.length > 100
						? await api.get(`/apps/${id}/keywords`, 'App Keywords')
						: 'No Keywords Result';
				const view = event.url.pathname.replace(/\/$/, '').split('/').at(-1);
				if (
					typeof keywords === 'object' &&
					Array.isArray(keywords.keyword_scores) &&
					(view === 'discovery' || view === 'ranking')
				) {
					const seen = new Set<string>();
					keywords.keyword_scores = keywords.keyword_scores.filter(
						(score: {
							keyword_text: string;
							is_keyword_ranking: boolean;
							is_keyword_generated: boolean;
						}) => {
							const matches =
								view === 'ranking'
									? score.is_keyword_ranking === true
									: score.is_keyword_ranking !== true && score.is_keyword_generated === true;
							const text = score.keyword_text?.trim().toLowerCase();
							if (!matches || !text || seen.has(text)) return false;
							seen.add(text);
							return true;
						}
					);
					keywords.keywords = keywords.keyword_scores.map(
						(score: { keyword_text: string }) => score.keyword_text
					);
				}
				data = { app, keywords };
			} else {
				const sdk = app.sdk_successful_last_crawled
					? await api.get(`/apps/${id}/sdks`, 'App Package Info')
					: {};
				const section = event.url.pathname.replace(/\/$/, '').split('/').at(-1);
				const field =
					section === 'queries' ? 'app_queries' : section === 'unknowns' ? 'leftovers' : section;
				data = {
					app,
					sdk:
						field && field !== 'sdks'
							? { [field]: sdk[field] ?? (field === 'leftovers' ? {} : []) }
							: sdk
				};
			}
		} else if (kind === 'pattern') {
			const pattern = encodeURIComponent(event.params.pattern ?? '');
			const [apps, companies] = await Promise.all([
				api.get(`/sdks/${pattern}`, 'Sdks Pattern'),
				api.get(`/sdks/${pattern}/companies`, 'Sdks Pattern Companies')
			]);
			data = { apps, companies };
		} else {
			data = await api.get(
				`/sdks/appgoblin/${encodeURIComponent(event.params.sdkSlug ?? '')}`,
				'SDK Details'
			);
		}
	}
	return json(data, { headers: { Vary: 'Accept, Cookie', 'Cache-Control': 'private, no-store' } });
}
