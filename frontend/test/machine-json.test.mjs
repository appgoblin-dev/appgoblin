/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck
import assert from 'node:assert/strict';
import { after, before, test } from 'node:test';
import { createServer } from 'vite';
import {
	declareDiscoveryExtension,
	bazaarResourceServerExtension,
	validateAndExtract
} from '@x402/extensions/bazaar';
import { x402HTTPResourceServer, x402ResourceServer } from '@x402/core/server';
import { ExactEvmScheme } from '@x402/evm/exact/server';
import { createCdpFacilitatorClient } from '@coinbase/cdp-sdk/x402';
import { generateKeyPairSync } from 'node:crypto';

let server, machine, openapi, payment, paymentNetwork;
before(async () => {
	server = await createServer({ server: { middlewareMode: true }, appType: 'custom' });
	machine = await server.ssrLoadModule('/src/lib/server/machine-json.ts');
	paymentNetwork = await server.ssrLoadModule('/src/lib/server/machine-payment-network.ts');
	openapi = await server.ssrLoadModule('/src/routes/openapi.json/+server.ts');
	payment = await server.ssrLoadModule('/src/lib/server/machine-payment.ts');
});
after(async () => {
	await server?.close();
});

const request = (accept) =>
	new Request('https://example.com/', { headers: accept === undefined ? {} : { accept } });
test('content negotiation selects JSON for machines and HTML for browsers', () => {
	for (const accept of [undefined, 'application/json', '*/*', 'text/html;q=0, application/json']) {
		assert.equal(machine.wantsMachineJson(request(accept)), true, String(accept));
	}
	for (const accept of ['text/html', 'text/html,*/*', 'TEXT/HTML; charset=utf-8']) {
		assert.equal(machine.wantsMachineJson(request(accept)), false, accept);
	}
});

test('only requested routes get JSON', () => {
	for (const [path, kind] of [
		['/search/music', 'search'],
		['/apps/a/keywords', 'keywords'],
		['/apps/a/keywords/discovery', 'keywords'],
		['/apps/a/keywords/ranking', 'keywords'],
		['/apps/a/sdks', 'sdks'],
		['/apps/a/sdks/permissions', 'sdks'],
		['/apps/a/sdks/queries', 'sdks'],
		['/apps/a/sdks/skadnetwork', 'sdks'],
		['/apps/a/sdks/unknowns', 'sdks'],
		['/sdks/foo', 'pattern'],
		['/sdks/mapped/foo', 'mapped']
	])
		assert.equal(machine.machineJsonKind(path), kind, path);
	for (const path of [
		'/apps/a/keywords/compare',
		'/apps/comparison/a',
		'/developers/a/sdks',
		'/reports/app-ecosystem-report-Q2-2026/download',
		'/apps/a/sdks/history',
		'/apps/a/sdks/__data.json'
	]) {
		assert.equal(machine.machineJsonKind(path), null, path);
	}
});

function event(path, params, values, paid = true) {
	const calls = [];
	return {
		calls,
		url: new URL(path, 'https://example.com'),
		params,
		locals: { user: null, session: null, machinePaid: paid },
		fetch: async (url) => {
			const pathname = new URL(url).pathname;
			calls.push(pathname);
			if (!(pathname in values)) throw new Error(`Unexpected fetch: ${pathname}`);
			return Response.json(values[pathname]);
		}
	};
}

test('search returns app and company data', async () => {
	const e = event(
		'/search/music',
		{ term: 'music' },
		{
			'/api/apps/search/music': { key: 'music', apple: { apps: [] }, google: { apps: [] } },
			'/api/companies/search/music': [{ company_name: 'Music' }]
		},
		false
	);
	const response = await machine.machineJsonResponse(e, 'search');
	assert.match(response.headers.get('content-type'), /^application\/json/);
	assert.match(response.headers.get('cache-control'), /no-store/);
	assert.deepEqual((await response.json()).companies, [{ company_name: 'Music' }]);
});

test('keyword and SDK data require payment or login and use the page data', async () => {
	const values = {
		'/api/apps/com.example': {
			store_id: 'com.example',
			description: 'x'.repeat(101),
			sdk_successful_last_crawled: true
		},
		'/api/apps/com.example/keywords': { keywords: ['music'], keyword_scores: [] },
		'/api/apps/com.example/sdks': { permissions: ['internet'] }
	};
	const denied = event('/apps/com.example/keywords', { id: 'com.example' }, values, false);
	const deniedResponse = await machine.machineJsonResponse(denied, 'keywords');
	assert.equal(deniedResponse.status, 401);
	assert.match(deniedResponse.headers.get('content-type'), /^application\/json/);
	assert.deepEqual(denied.calls, []);
	for (const [kind, path, expected] of [
		['keywords', 'keywords', 'keywords'],
		['sdks', 'sdks', 'sdk']
	]) {
		const e = event(`/apps/com.example/${path}`, { id: 'com.example' }, values);
		const body = await (await machine.machineJsonResponse(e, kind)).json();
		assert.deepEqual(body[expected], values[`/api/apps/com.example/${path}`]);
	}
});

test('subpages return only the relevant keyword or SDK section', async () => {
	const values = {
		'/api/apps/a': {
			store_id: 'a',
			description: 'x'.repeat(101),
			sdk_successful_last_crawled: true
		},
		'/api/apps/a/keywords': {
			keywords: ['ranked', 'suggested'],
			keyword_scores: [
				{ keyword_text: 'ranked', is_keyword_ranking: true },
				{ keyword_text: 'suggested', is_keyword_generated: true },
				{ keyword_text: 'suggested', is_keyword_generated: true }
			]
		},
		'/api/apps/a/sdks': {
			permissions: ['internet'],
			app_queries: ['other'],
			leftovers: { package: ['x'] },
			skadnetwork: ['ad']
		}
	};
	for (const [view, keyword] of [
		['ranking', 'ranked'],
		['discovery', 'suggested']
	]) {
		const e = event(`/apps/a/keywords/${view}`, { id: 'a' }, values);
		const body = await (await machine.machineJsonResponse(e, 'keywords')).json();
		assert.deepEqual(body.keywords.keywords, [keyword]);
	}
	for (const [view, field] of [
		['permissions', 'permissions'],
		['queries', 'app_queries'],
		['unknowns', 'leftovers'],
		['skadnetwork', 'skadnetwork']
	]) {
		const e = event(`/apps/a/sdks/${view}`, { id: 'a' }, values);
		const body = await (await machine.machineJsonResponse(e, 'sdks')).json();
		assert.deepEqual(body.sdk, { [field]: values['/api/apps/a/sdks'][field] });
		assert.deepEqual(Object.keys(machine.machineJsonExample('sdks', e.url.pathname).sdk), [field]);
	}
});

test('SDK pattern and mapped routes return SDK data', async () => {
	const pattern = event(
		'/sdks/foo',
		{ pattern: 'foo' },
		{
			'/api/sdks/foo': { apps: [{ id: 1 }] },
			'/api/sdks/foo/companies': { companies: [] }
		}
	);
	assert.deepEqual(await (await machine.machineJsonResponse(pattern, 'pattern')).json(), {
		apps: { apps: [{ id: 1 }] },
		companies: { companies: [] }
	});
	const mapped = event(
		'/sdks/mapped/foo',
		{ sdkSlug: 'foo' },
		{
			'/api/sdks/appgoblin/foo': { sdk_name: 'Example' }
		}
	);
	assert.deepEqual(await (await machine.machineJsonResponse(mapped, 'mapped')).json(), {
		sdk_name: 'Example'
	});
});

test('network configuration isolates Base Sepolia and validates Stripe mode', () => {
	const mainnet = paymentNetwork.getMachinePaymentNetwork('eip155:8453', 'sk_live_example');
	assert.equal(mainnet.network, 'eip155:8453');
	assert.equal(mainnet.usdcAddress, '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913');
	assert.equal(mainnet.recordInStripe, true);
	for (const key of ['sk_test_example', 'rk_test_example']) {
		const testnet = paymentNetwork.getMachinePaymentNetwork(' eip155:84532 ', key);
		assert.equal(testnet.network, 'eip155:84532');
		assert.equal(testnet.usdcAddress, '0x036CbD53842c5426634e7929541eC2318f3dCF7e');
		assert.equal(testnet.recordInStripe, false);
	}
	assert.throws(
		() => paymentNetwork.getMachinePaymentNetwork('eip155:84532', 'sk_live_example'),
		/requires a Stripe test key/
	);
	assert.throws(
		() => paymentNetwork.getMachinePaymentNetwork('eip155:1', 'sk_test_example'),
		/BLOCKCHAIN_NETWORK/
	);
	assert.throws(
		() => paymentNetwork.getMachinePaymentNetwork(undefined, 'sk_test_example'),
		/BLOCKCHAIN_NETWORK/
	);
});

test('CDP facilitator sends request-bound bearer JWTs', async () => {
	const { privateKey, publicKey } = generateKeyPairSync('ed25519');
	const secret = Buffer.concat([
		Buffer.from(privateKey.export({ format: 'jwk' }).d, 'base64url'),
		Buffer.from(publicKey.export({ format: 'jwk' }).x, 'base64url')
	]).toString('base64');
	const facilitator = createCdpFacilitatorClient({ apiKeyId: 'test-key', apiKeySecret: secret });
	const originalFetch = globalThis.fetch;
	const requests = [];
	globalThis.fetch = async (url, options) => {
		requests.push({ url, method: options.method, headers: new Headers(options.headers) });
		return new Response('mock failure', { status: 401 });
	};
	try {
		await assert.rejects(facilitator.getSupported());
		await assert.rejects(facilitator.verify({ x402Version: 2 }, {}));
		await assert.rejects(facilitator.settle({ x402Version: 2 }, {}));
		assert.equal(requests.length, 3);
		for (const [index, operation] of ['supported', 'verify', 'settle'].entries()) {
			const call = requests[index];
			const method = operation === 'supported' ? 'GET' : 'POST';
			assert.equal(call.url, `https://api.cdp.coinbase.com/platform/v2/x402/${operation}`);
			assert.equal(call.method, method);
			const authorization = call.headers.get('authorization');
			assert.match(authorization, /^Bearer /);
			const claims = JSON.parse(
				Buffer.from(authorization.slice(7).split('.')[1], 'base64url').toString()
			);
			assert.equal(claims.sub, 'test-key');
			assert.deepEqual(claims.uris, [
				`${method} api.cdp.coinbase.com/platform/v2/x402/${operation}`
			]);
		}
	} finally {
		globalThis.fetch = originalFetch;
	}
});

test('unconfigured x402 logs missing variable names and preserves MPP fallback', () => {
	const originalError = console.error;
	const errors = [];
	console.error = (...args) => errors.push(args);
	try {
		const challenge = new Response('MPP payment required', { status: 402 });
		assert.equal(
			payment.unavailableX402Challenge(challenge, ['CDP_API_KEY_ID', 'CDP_API_KEY_SECRET']),
			challenge
		);
		assert.match(errors[0][0], /CDP_API_KEY_ID, CDP_API_KEY_SECRET/);
		assert.match(errors[0][0], /MPP-only challenge/);
		assert.equal(payment.unavailableX402Challenge(null, ['STRIPE_BASE_DEPOSIT_ADDRESS']), null);
		assert.match(errors[1][0], /No MPP challenge is available/);
	} finally {
		console.error = originalError;
	}
});

test('facilitator failure preserves MPP and fails x402 attempts closed', async () => {
	const challenge = new Response('MPP payment required', {
		status: 402,
		headers: { 'WWW-Authenticate': 'Payment method="tempo"' }
	});
	const originalError = console.error;
	const originalWarn = console.warn;
	const errors = [];
	const warnings = [];
	console.error = (...args) => errors.push(args);
	console.warn = (...args) => warnings.push(args);
	try {
		const fail = async () => {
			throw new Error('facilitator 401');
		};
		assert.equal(
			await payment.initializePaymentFacilitator(
				async () => {},
				request('application/json'),
				challenge
			),
			null
		);
		const fallback = await payment.initializePaymentFacilitator(
			fail,
			request('application/json'),
			challenge
		);
		assert.equal(fallback, challenge);
		assert.match(errors[0][0], /x402 facilitator initialization failed/);
		assert.match(warnings[0][0], /MPP-only challenge/);
		for (const header of ['payment-signature', 'x-payment']) {
			const attempted = new Request('https://example.com/', { headers: { [header]: 'test' } });
			const response = await payment.initializePaymentFacilitator(fail, attempted, challenge);
			assert.equal(response.status, 503);
			assert.deepEqual(await response.json(), { error: 'x402_facilitator_unavailable' });
			assert.equal(response.headers.get('cache-control'), 'no-store');
		}
		const unavailable = await payment.initializePaymentFacilitator(
			fail,
			request('application/json'),
			null
		);
		assert.equal(unavailable.status, 503);
	} finally {
		console.error = originalError;
		console.warn = originalWarn;
	}
});

test('x402 challenge advertises the negotiated JSON example', async () => {
	const facilitator = {
		getSupported: async () => ({
			kinds: [{ x402Version: 2, network: 'eip155:8453', scheme: 'exact' }],
			extensions: ['bazaar'],
			signers: {}
		})
	};
	const resourceServer = new x402ResourceServer(facilitator)
		.register('eip155:8453', new ExactEvmScheme())
		.registerExtension(bazaarResourceServerExtension);
	await resourceServer.initialize();
	const req = new Request('https://example.com/apps/a/sdks/permissions', {
		headers: { accept: 'application/json' }
	});
	const route = {
		accepts: {
			scheme: 'exact',
			network: 'eip155:8453',
			price: '$0.10',
			payTo: '0x0000000000000000000000000000000000000001'
		},
		resource: req.url,
		...payment.machinePaymentOutput(req)
	};
	const http = new x402HTTPResourceServer(resourceServer, {
		[payment.machinePaymentRoutePattern('/apps/{id}/sdks/permissions', new URL(req.url).pathname)]:
			route
	});
	const adapter = {
		getHeader: (name) => req.headers.get(name) ?? undefined,
		getMethod: () => 'GET',
		getPath: () => '/apps/a/sdks/permissions',
		getUrl: () => req.url,
		getAcceptHeader: () => 'application/json',
		getUserAgent: () => ''
	};
	const result = await http.processHTTPRequest({ adapter, path: adapter.getPath(), method: 'GET' });
	assert.equal(result.type, 'payment-error');
	const required = JSON.parse(
		Buffer.from(
			result.response.headers['PAYMENT-REQUIRED'] ?? result.response.headers['payment-required'],
			'base64'
		).toString()
	);
	assert.equal(required.resource.mimeType, 'application/json');
	assert.deepEqual(required.extensions.bazaar.info.output, {
		type: 'json',
		example: machine.machineJsonExample('sdks', '/permissions')
	});
	assert.equal(required.extensions.bazaar.info.input.method, 'GET');
	assert.equal(required.extensions.bazaar.routeTemplate, '/apps/:id/sdks/permissions');
	assert.deepEqual(required.extensions.bazaar.info.input.pathParams, { id: 'a' });
	assert.equal(validateAndExtract(required.extensions.bazaar).valid, true);
});

test('payment route patterns match advertised resources, including encoded and data paths', async () => {
	const facilitator = {
		getSupported: async () => ({
			kinds: [{ x402Version: 2, network: 'eip155:8453', scheme: 'exact' }],
			extensions: ['bazaar'],
			signers: {}
		})
	};
	const resourceServer = new x402ResourceServer(facilitator)
		.register('eip155:8453', new ExactEvmScheme())
		.registerExtension(bazaarResourceServerExtension);
	await resourceServer.initialize();
	for (const [resource, path, method, template, params] of [
		['/search/{term}', '/search/space%20game', 'GET', '/search/:term', { term: 'space%20game' }],
		[
			'/apps/{id}/keywords',
			'/apps/com.example/keywords/',
			'GET',
			'/apps/:id/keywords',
			{ id: 'com.example' }
		],
		[
			'/apps/{id}/sdks',
			'/apps/com.example/sdks/__data.json',
			'GET',
			'/apps/:id/sdks/__data.json',
			{ id: 'com.example' }
		],
		['/sdks/{pattern}', '/sdks/com.example', 'HEAD', '/sdks/:pattern', { pattern: 'com.example' }],
		[
			'/sdks/mapped/{sdkSlug}',
			'/sdks/mapped/example',
			'GET',
			'/sdks/mapped/:sdkSlug',
			{ sdkSlug: 'example' }
		]
	]) {
		const req = new Request(`https://example.com${path}`, {
			method,
			headers: { accept: 'application/json' }
		});
		const route = {
			accepts: {
				scheme: 'exact',
				network: 'eip155:8453',
				price: '$0.10',
				payTo: '0x0000000000000000000000000000000000000001'
			},
			resource: req.url,
			...payment.machinePaymentOutput(req)
		};
		const http = new x402HTTPResourceServer(resourceServer, {
			[payment.machinePaymentRoutePattern(resource, path)]: route
		});
		const adapter = {
			getHeader: (name) => req.headers.get(name) ?? undefined,
			getMethod: () => method,
			getPath: () => path.replace(/\/$/, ''),
			getUrl: () => req.url,
			getAcceptHeader: () => 'application/json',
			getUserAgent: () => ''
		};
		const result = await http.processHTTPRequest({ adapter, path, method });
		assert.equal(result.type, 'payment-error', path);
		if (route.extensions) {
			const required = JSON.parse(
				Buffer.from(
					result.response.headers['PAYMENT-REQUIRED'] ??
						result.response.headers['payment-required'],
					'base64'
				).toString()
			);
			assert.equal(required.extensions.bazaar.routeTemplate, template);
			assert.deepEqual(required.extensions.bazaar.info.input.pathParams, params);
		}
	}
});

test('discovery metadata contains examples and current prices', async () => {
	const spec = await (await openapi.GET()).json();
	for (const path of [
		'/search/{term}',
		'/apps/{storeId}/keywords',
		'/apps/{storeId}/sdks',
		'/sdks/{pattern}',
		'/sdks/mapped/{sdkSlug}'
	]) {
		const info = spec.paths[path].get['x-payment-info'];
		assert.equal(info.output.type, 'json');
		assert.ok(info.output.example);
		assert.deepEqual(
			info.output.example,
			spec.paths[path].get.responses['200'].content['application/json'].example
		);
		assert.equal(info.offers[0].amount, '10');
		assert.equal(info.offers[1].amount, '100000');
		const ext = declareDiscoveryExtension({ output: { example: info.output.example } });
		assert.deepEqual(ext.bazaar.info.output, info.output);
	}
	assert.equal(spec.paths['/apps/comparison/{storeId}'].get['x-payment-info'].output, undefined);
});
