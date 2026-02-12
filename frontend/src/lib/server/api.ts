const API_BASE_URL = 'http://localhost:8000/api';
import { error } from '@sveltejs/kit';

export class ApiClient {
	constructor(private fetch: typeof globalThis.fetch) {}

	private async checkStatus(resp: Response, name: string) {
		if (resp.status === 200 || resp.status === 201) {
			return resp.json();
		} else if (resp.status === 404) {
			console.log(`${name} API: ${resp.status}`);
			return { status: 404, error: `${name} Not Found` }; //
		} else if (resp.status === 500) {
			console.log(`${name} API Server error: ${resp.status}`);
			return { status: 500, error: `${name} API Server error` };
		} else {
			console.log(`${name} Unexpected status: ${resp.status}`);
			return { status: resp.status, error: `${name} Unexpected error (${resp.status})` };
		}
	}
	async get(endpoint: string, name: string, timeoutMs: number = 30000, userId?: number | string) {
		console.log(`${API_BASE_URL}${endpoint} fetch ${name}`);

		try {
			const controller = new AbortController();
			const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

			let url = `${API_BASE_URL}${endpoint}`;
			if (userId) {
				const separator = url.includes('?') ? '&' : '?';
				url = `${url}${separator}user_id=${userId}`;
			}

			const resp = await this.fetch(url, {
				signal: controller.signal
			});

			clearTimeout(timeoutId);
			const checkedResp = await this.checkStatus(resp, name);

			if (checkedResp.error) {
				throw error(checkedResp.status, checkedResp.error);
			}

			return checkedResp;
		} catch (err) {
			// Handle abort/timeout - throw SvelteKit error for +error.svelte
			if (err instanceof DOMException && err.name === 'AbortError') {
				console.error(`${name} Request timeout after ${timeoutMs}ms`);
				throw error(504, `${name}: Request timeout - backend may be restarting`);
			}

			// Handle network errors - throw SvelteKit error for +error.svelte
			if (
				err instanceof TypeError &&
				(err.message.includes('fetch') || err.message.includes('terminated'))
			) {
				console.error(`${name} Network error: ${err.message}`);
				throw error(503, `${name}: Service temporarily unavailable - backend may be restarting`);
			}

			// If it's already a SvelteKit error, re-throw it
			throw err;
		}
	}

	async post(
		endpoint: string,
		body: any,
		name: string,
		timeoutMs: number = 30000,
		userId?: number | string
	) {
		console.log(`${API_BASE_URL}${endpoint} fetch (POST) ${name}`);

		try {
			const controller = new AbortController();
			const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

			let url = `${API_BASE_URL}${endpoint}`;
			if (userId) {
				const separator = url.includes('?') ? '&' : '?';
				url = `${url}${separator}user_id=${userId}`;
			}

			const resp = await this.fetch(url, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(body),
				signal: controller.signal
			});

			clearTimeout(timeoutId);
			const checkedResp = await this.checkStatus(resp, name);

			if (checkedResp.error) {
				throw error(checkedResp.status, checkedResp.error);
			}

			return checkedResp;
		} catch (err) {
			if (err instanceof DOMException && err.name === 'AbortError') {
				console.error(`${name} Request timeout after ${timeoutMs}ms`);
				throw error(504, `${name}: Request timeout`);
			}
			if (
				err instanceof TypeError &&
				(err.message.includes('fetch') || err.message.includes('terminated'))
			) {
				console.error(`${name} Network error: ${err.message}`);
				throw error(503, `${name}: Service unavailable`);
			}
			throw err;
		}
	}
}

export function createApiClient(fetch: typeof globalThis.fetch) {
	return new ApiClient(fetch);
}
