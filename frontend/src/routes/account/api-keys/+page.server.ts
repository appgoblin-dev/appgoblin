import { fail } from '@sveltejs/kit';
import { requireAuthOr401 } from '$lib/server/auth/auth';
import { db } from '$lib/server/auth/db';
import { encodeBase32, encodeHexLowerCase, sha256 } from '$lib/server/auth/utils';

import type { Actions, PageServerLoadEvent, RequestEvent } from './$types';

const MAX_ACTIVE_API_KEYS = 5;

interface ApiKeyRow {
	id: number;
	key_prefix: string;
	name: string;
	is_active: boolean;
	last_used_at: Date | null;
	created_at: Date;
}

export async function load(event: PageServerLoadEvent) {
	const { user } = await event.parent();

	const apiKeys = await db.query<ApiKeyRow>(
		`SELECT id, key_prefix, name, is_active, last_used_at, created_at
		 FROM public.api_keys
		 WHERE user_id = $1
		 ORDER BY created_at DESC`,
		[user.id]
	);

	return { apiKeys };
}

function generateApiKey(): string {
	const bytes = new Uint8Array(24);
	crypto.getRandomValues(bytes);
	const encoded = encodeBase32(bytes, false, false);
	return `ag_${encoded}`;
}

export const actions: Actions = {
	create: async (event: RequestEvent) => {
		const { user } = requireAuthOr401(event);
		const data = await event.request.formData();

		const name = data.get('name')?.toString().trim() ?? '';
		if (!name) {
			return fail(400, { section: 'create', message: 'Key name is required' });
		}
		if (name.length > 100) {
			return fail(400, { section: 'create', message: 'Key name must be 100 characters or less' });
		}

		const activeKeyCount = await db.query<{ count: string }>(
			`SELECT COUNT(*)::text AS count
			 FROM public.api_keys
			 WHERE user_id = $1 AND is_active = true`,
			[user.id]
		);
		if (Number(activeKeyCount[0]?.count ?? 0) >= MAX_ACTIVE_API_KEYS) {
			return fail(400, {
				section: 'create',
				message: `You can have at most ${MAX_ACTIVE_API_KEYS} active API keys`
			});
		}

		const rawKey = generateApiKey();
		const keyPrefix = rawKey.slice(0, 11); // "ag_" + 8 chars
		const hashBytes = await sha256(new TextEncoder().encode(rawKey));
		const keyHash = encodeHexLowerCase(hashBytes);

		await db.execute(
			`INSERT INTO public.api_keys (user_id, key_hash, key_prefix, name)
			 VALUES ($1, $2, $3, $4)`,
			[user.id, keyHash, keyPrefix, name]
		);

		return {
			section: 'create',
			success: true,
			message: 'API key created successfully',
			rawKey
		};
	},

	revoke: async (event: RequestEvent) => {
		const { user } = requireAuthOr401(event);
		const data = await event.request.formData();
		const idRaw = data.get('id')?.toString() ?? '';
		const id = Number.parseInt(idRaw, 10);

		if (!Number.isInteger(id) || id <= 0) {
			return fail(400, { section: 'revoke', message: 'Invalid API key ID' });
		}

		const result = await db.execute(
			`UPDATE public.api_keys SET is_active = false
			 WHERE id = $1 AND user_id = $2`,
			[id, user.id]
		);

		if (result.changes === 0) {
			return fail(404, { section: 'revoke', message: 'API key not found' });
		}

		return { section: 'revoke', success: true, message: 'API key revoked' };
	}
};
