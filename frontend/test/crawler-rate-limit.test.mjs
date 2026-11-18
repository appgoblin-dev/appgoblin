/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck
import assert from 'node:assert/strict';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { after, before, test } from 'node:test';
import { createServer } from 'vite';

let server, crawler, limits, requests, directory;
const oldFile = process.env.CRAWLER_IP_FILE;
const oldMultiplier = process.env.CRAWLER_RATE_LIMIT_MULTIPLIER;

before(async () => {
	directory = await mkdtemp(join(tmpdir(), 'crawler-limits-'));
	process.env.CRAWLER_IP_FILE = join(directory, 'crawlers.json');
	await writeFile(
		process.env.CRAWLER_IP_FILE,
		JSON.stringify({ services: { bot: { ipv4: ['192.0.2.0/24'], ipv6: ['2001:db8::/32'] } } })
	);
	await writeFile(join(directory, 'invalid.json'), '{');
	server = await createServer({ server: { middlewareMode: true }, appType: 'custom' });
	crawler = await server.ssrLoadModule('/src/lib/server/crawler-ip.ts');
	limits = await server.ssrLoadModule('/src/lib/server/redis-rate-limit.ts');
	requests = await server.ssrLoadModule('/src/lib/server/request-rate-limit.ts');
});
after(async () => {
	await server?.close();
	if (oldFile === undefined) delete process.env.CRAWLER_IP_FILE;
	else process.env.CRAWLER_IP_FILE = oldFile;
	if (oldMultiplier === undefined) delete process.env.CRAWLER_RATE_LIMIT_MULTIPLIER;
	else process.env.CRAWLER_RATE_LIMIT_MULTIPLIER = oldMultiplier;
	if (directory) await rm(directory, { recursive: true, force: true });
});

test('matches only IP addresses inside IPv4 and IPv6 crawler subnets', () => {
	for (const ip of ['192.0.2.1', '192.0.2.255', '2001:db8::1'])
		assert.equal(crawler.isCrawlerIP(ip), true, ip);
	for (const ip of ['192.0.3.1', '2001:db9::1', 'not-an-ip', '192.0.2.1:80'])
		assert.equal(crawler.isCrawlerIP(ip), false, ip);
	assert.throws(() =>
		crawler.parseCrawlerRanges({ services: { bot: { ipv4: ['192.0.2.0/33'], ipv6: [] } } })
	);
	assert.throws(() =>
		crawler.parseCrawlerRanges({ services: { bot: { ipv4: ['192.0.2.0/24'] } } })
	);
	assert.equal(crawler.loadCrawlerRanges(join(directory, 'missing.json')), null);
	assert.equal(crawler.loadCrawlerRanges(join(directory, 'invalid.json')), null);
});

test('multiplier is configurable and invalid values default to five', () => {
	delete process.env.CRAWLER_RATE_LIMIT_MULTIPLIER;
	assert.equal(crawler.crawlerRateMultiplier('192.0.2.1'), 5);
	process.env.CRAWLER_RATE_LIMIT_MULTIPLIER = '3';
	assert.equal(crawler.crawlerRateMultiplier('192.0.2.1'), 3);
	assert.equal(crawler.crawlerRateMultiplier('192.0.3.1'), 1);
	for (const value of ['0', '2.5', '1001', 'invalid']) {
		process.env.CRAWLER_RATE_LIMIT_MULTIPLIER = value;
		assert.equal(crawler.crawlerRateMultiplier('192.0.2.1'), 5);
	}
});

test('request and pre-auth checks pass scaled limits and expose scaled search quota', async () => {
	process.env.CRAWLER_RATE_LIMIT_MULTIPLIER = '5';
	const original = limits.RedisRateLimiter.prototype.eval;
	const calls = [];
	limits.RedisRateLimiter.prototype.eval = async (script, keys, args) => {
		calls.push(args);
		return args.length === 1 ? [1, 2999, 0] : [1, Number(args[0]), 149, 0, 0, 24];
	};
	try {
		const event = {
			request: new Request('https://example.com/search/foo', {
				headers: { 'CF-Connecting-IP': '192.0.2.1', accept: 'text/html' }
			}),
			getClientAddress: () => '127.0.0.1',
			cookies: { get: () => 'session' },
			url: new URL('https://example.com/search/foo'),
			isDataRequest: false,
			locals: { user: null }
		};
		assert.equal((await requests.checkPreAuthRateLimit(event)).limit, 3000);
		assert.equal((await requests.checkRateLimit(event)).limit, 150);
		assert.deepEqual(calls, [['3000'], ['150', '5000', '1', '25', '86400']]);
		assert.deepEqual(event.locals.anonymousSearchQuota, { remaining: 24, limit: 25 });
		event.request = new Request('https://example.com/search/foo', {
			headers: { 'CF-Connecting-IP': '192.0.3.1' }
		});
		await requests.checkRateLimit(event);
		assert.deepEqual(calls[2], ['30', '1000', '1', '5', '86400']);
	} finally {
		limits.RedisRateLimiter.prototype.eval = original;
	}
});
