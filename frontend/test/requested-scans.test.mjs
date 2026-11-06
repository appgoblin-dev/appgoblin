/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck
import assert from 'node:assert/strict';
import { after, before, test } from 'node:test';
import { createServer } from 'vite';

let server, page, progress, db;
const user = { id: 7 };
const session = { id: 'session' };
const event = (url, locals = { user, session }) => ({ url: new URL(url), locals });

before(async () => {
	server = await createServer({ server: { middlewareMode: true }, appType: 'custom' });
	page = await server.ssrLoadModule('/src/routes/account/requested-scans/+page.server.ts');
	progress = await server.ssrLoadModule(
		'/src/routes/account/requested-scans/[id]/progress/+server.ts'
	);
	({ db } = await server.ssrLoadModule('/src/lib/server/auth/db.ts'));
});
after(async () => {
	await db?.close();
	await server?.close();
});

const statusIs = (status) => (error) => error.status === status;

test('page validates authentication and pagination before querying', async () => {
	let queries = 0;
	db.query = async () => {
		queries++;
		return [];
	};
	await assert.rejects(
		page.load(event('http://localhost/account/requested-scans', { user: null, session: null })),
		statusIs(401)
	);
	for (const query of [
		'page=0',
		'page=1x',
		'page=-1',
		'pageSize=101',
		'pageSize=0',
		'page=999999999999999999'
	]) {
		await assert.rejects(
			page.load(event(`http://localhost/account/requested-scans?${query}`)),
			statusIs(400)
		);
	}
	assert.equal(queries, 0);
});

test('page uses scoped, deterministic pagination and detects next page', async () => {
	const rows = [
		{ id: 4, store_id: 'a', created_at: new Date('2026-01-01T00:00:00Z') },
		{ id: 3, store_id: 'b', created_at: new Date('2026-01-01T00:00:00Z') },
		{ id: 2, store_id: 'c', created_at: null }
	];
	db.query = async (sql, params) => {
		assert.match(sql, /WHERE user_id = \$1/);
		assert.match(sql, /ORDER BY created_at DESC NULLS LAST, id DESC/);
		assert.deepEqual(params, [7, 3, 2]);
		return rows;
	};
	const result = await page.load(
		event('http://localhost/account/requested-scans?page=2&pageSize=2')
	);
	assert.deepEqual(result.pagination, { page: 2, pageSize: 2, hasNext: true });
	assert.deepEqual(
		result.requestedSdkScans.map((row) => row.id),
		[4, 3]
	);
	assert.equal(result.requestedSdkScans[0].app_name, null);
	db.query = async () => [];
	assert.deepEqual(await page.load(event('http://localhost/account/requested-scans')), {
		requestedSdkScans: [],
		pagination: { page: 1, pageSize: 20, hasNext: false }
	});
});

test('progress rejects unauthenticated, invalid and unowned requests', async () => {
	let queries = 0;
	db.query = async (sql, params) => {
		queries++;
		assert.match(sql, /WHERE id = \$1 AND user_id = \$2/);
		assert.deepEqual(params, [3, 7]);
		return [];
	};
	await assert.rejects(
		progress.GET({
			...event('http://localhost', { user: null, session: null }),
			params: { id: '3' }
		}),
		statusIs(401)
	);
	await assert.rejects(
		progress.GET({ ...event('http://localhost'), params: { id: '3x' } }),
		statusIs(400)
	);
	await assert.rejects(
		progress.GET({ ...event('http://localhost'), params: { id: '2147483648' } }),
		statusIs(400)
	);
	assert.equal(queries, 0);
	await assert.rejects(
		progress.GET({ ...event('http://localhost'), params: { id: '3' } }),
		statusIs(404)
	);
});

test('progress calls analytics only for owned requests with a timestamp', async () => {
	const created = new Date('2026-01-01T00:00:00Z');
	db.query = async () => [{ id: 3, store_id: 'app+id', created_at: created }];
	const fetch = async (input) => {
		const url = new URL(input);
		assert.equal(url.pathname, '/analytics/scan-progress');
		assert.equal(url.searchParams.get('store_id'), 'app+id');
		assert.equal(url.searchParams.get('requested_at'), created.toISOString());
		return Response.json({ version_code: '42', stages: { sdk_scan: { status: 'success' } } });
	};
	const response = await progress.GET({ ...event('http://localhost'), params: { id: '3' }, fetch });
	assert.equal(response.headers.get('cache-control'), 'private, no-store');
	const result = await response.json();
	assert.equal(result.id, 3);
	assert.equal(result.version_code, '42');
	assert.equal(result.stages.sdk_scan.status, 'success');
	await assert.rejects(
		progress.GET({
			...event('http://localhost'),
			params: { id: '3' },
			fetch: async () => new Response('', { status: 500 })
		}),
		statusIs(503)
	);
	db.query = async () => [{ id: 3, store_id: 'app', created_at: null }];
	const noTimestamp = await progress.GET({ ...event('http://localhost'), params: { id: '3' } });
	const nullableResult = await noTimestamp.json();
	assert.equal(nullableResult.requested_at, null);
	for (const stage of ['download', 'sdk_scan', 'data_import', 'waydroid']) {
		assert.equal(nullableResult.stages[stage].status, 'unknown');
	}
});

test('submission trims and scopes store IDs, rejecting empty and unauthenticated input', async () => {
	const calls = [];
	db.execute = async (...args) => {
		calls.push(args);
		return { changes: 1 };
	};
	const submit = (storeId, locals = { user, session }) => {
		const form = new FormData();
		form.set('store_id', storeId);
		return {
			...event('http://localhost', locals),
			request: new Request('http://localhost', { method: 'POST', body: form })
		};
	};
	await assert.rejects(
		page.actions.addRequestedSdkScan(submit('app', { user: null, session: null })),
		statusIs(401)
	);
	assert.equal((await page.actions.addRequestedSdkScan(submit('  '))).status, 400);
	const result = await page.actions.addRequestedSdkScan(submit(' app '));
	assert.equal(result.success, true);
	assert.equal(calls.length, 1);
	assert.deepEqual(calls[0][1], ['app', 7]);
});
