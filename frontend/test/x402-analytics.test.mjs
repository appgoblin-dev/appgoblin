import assert from 'node:assert/strict';
import { after, before, test } from 'node:test';
import { createServer } from 'vite';

let server, createX402Analytics;
before(async () => {
	server = await createServer({ server: { middlewareMode: true }, appType: 'custom' });
	({ createX402Analytics } = await server.ssrLoadModule('/src/lib/server/x402-analytics.ts'));
});
after(async () => {
	await server?.close();
});

const flush = () => new Promise((resolve) => setImmediate(resolve));

test('records signed attempts and outcomes without sending signatures or query strings', async () => {
	const originalFetch = globalThis.fetch;
	const requests = [];
	globalThis.fetch = async (url, options) => {
		requests.push({ url, options, body: JSON.parse(options.body) });
		return new Response(null, { status: 200 });
	};
	try {
		for (const header of ['payment-signature', 'x-payment']) {
			const request = new Request('https://appgoblin.info/apps/com.example/sdks?secret=private', {
				headers: { [header]: 'sensitive-signature' }
			});
			const analytics = createX402Analytics(request, '/apps/{id}/sdks');
			analytics.attempt();
			analytics.settled('failed');
			analytics.failed('stripe_recording');
		}
		await flush();
		assert.equal(requests.length, 6);
		for (let i = 0; i < requests.length; i += 3) {
			const events = requests.slice(i, i + 3);
			assert.deepEqual(
				events.map(({ body }) => body.payload.name),
				['x402-attempt', 'x402-settled', 'x402-failed']
			);
			assert.equal(
				events[0].body.payload.data.signature_header,
				i === 0 ? 'payment-signature' : 'x-payment'
			);
			assert.equal(events[0].body.payload.url, '/apps/com.example/sdks');
			assert.equal(events[0].body.payload.data.resource, '/apps/{id}/sdks');
			assert.equal(events[1].body.payload.data.stripe_recording, 'failed');
			assert.equal(events[2].body.payload.data.stage, 'stripe_recording');
			assert.ok(
				events.every(
					({ body }) => body.payload.data.attempt_id === events[0].body.payload.data.attempt_id
				)
			);
			assert.ok(
				events.every(
					({ options }) =>
						!options.body.includes('sensitive-signature') &&
						!options.body.includes('secret=private')
				)
			);
			assert.ok(events.every(({ url }) => url === 'https://caz.appgoblin.info/api/send'));
		}
		assert.notEqual(
			requests[0].body.payload.data.attempt_id,
			requests[3].body.payload.data.attempt_id
		);
	} finally {
		globalThis.fetch = originalFetch;
	}
});

test('ignores ordinary challenges and non-production requests', () => {
	assert.equal(
		createX402Analytics(new Request('https://appgoblin.info/apps/a/sdks'), '/apps/{id}/sdks'),
		null
	);
	assert.equal(
		createX402Analytics(
			new Request('http://localhost/apps/a/sdks', {
				headers: { 'payment-signature': 'test' }
			}),
			'/apps/{id}/sdks'
		),
		null
	);
});

test('analytics transport failures are best-effort', async () => {
	const originalFetch = globalThis.fetch;
	globalThis.fetch = () => {
		throw new Error('offline');
	};
	try {
		const analytics = createX402Analytics(
			new Request('https://appgoblin.info/search/a', {
				headers: { 'payment-signature': 'test' }
			}),
			'/search/{term}'
		);
		assert.doesNotThrow(() => analytics.attempt());
		assert.doesNotThrow(() => analytics.failed('verification'));
		await flush();
	} finally {
		globalThis.fetch = originalFetch;
	}
});
