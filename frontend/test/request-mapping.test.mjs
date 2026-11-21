/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck
import assert from 'node:assert/strict';
import { after, before, test } from 'node:test';
import { createServer } from 'vite';

let server, endpoint, db;
before(async () => {
	server = await createServer({
		server: { middlewareMode: true },
		appType: 'custom',
		plugins: [
			{
				name: 'mock-mapping-email',
				enforce: 'pre',
				resolveId(source) {
					if (source === '#lib/server/contact.js') return '\0mock-mapping-email';
				},
				load(id) {
					if (id === '\0mock-mapping-email')
						return 'export async function sendMappingRequestEmail() {}';
				}
			}
		]
	});
	endpoint = await server.ssrLoadModule('/src/routes/api/request-mapping/+server.ts');
	({ db } = await server.ssrLoadModule('/src/lib/server/auth/db.ts'));
});
after(async () => {
	await db?.close();
	await server?.close();
});

const user = { id: 7, email: 'test@example.com', username: 'test' };
const event = (body, currentUser = user) => ({
	request: new Request('http://localhost/api/request-mapping', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body)
	}),
	locals: { user: currentUser }
});

test('SDK mapping requests accept a pattern with or without an app store ID', async () => {
	const calls = [];
	db.execute = async (_sql, params) => calls.push(params);
	for (const additionalInfo of [undefined, { store_id: ' app.one ' }]) {
		const response = await endpoint.POST(
			event({ mapType: 'app_sdk', valueToBeMapped: ' com.example ', additionalInfo })
		);
		assert.equal(response.status, 200);
	}
	assert.deepEqual(calls, [
		[7, 'app_sdk', 'com.example', null],
		[7, 'app_sdk', 'com.example', { store_id: 'app.one' }]
	]);
});

test('mapping requests still require authentication and reject invalid app context', async () => {
	let calls = 0;
	db.execute = async () => calls++;
	const body = { mapType: 'app_sdk', valueToBeMapped: 'com.example' };
	assert.equal((await endpoint.POST(event(body, null))).status, 401);
	assert.equal(
		(await endpoint.POST(event({ ...body, additionalInfo: { store_id: ' ' } }))).status,
		400
	);
	assert.equal(calls, 0);
});
