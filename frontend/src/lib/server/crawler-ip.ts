import { readFileSync } from 'node:fs';
import { BlockList, isIP } from 'node:net';
import { resolve } from 'node:path';

export function parseCrawlerRanges(data: unknown): BlockList {
	if (!data || typeof data !== 'object' || !('services' in data))
		throw new Error('Invalid crawler feed');
	const services = data.services;
	if (!services || typeof services !== 'object' || Array.isArray(services))
		throw new Error('Invalid crawler services');
	const ranges = new BlockList();
	for (const service of Object.values(services)) {
		if (!service || typeof service !== 'object') throw new Error('Invalid crawler service');
		for (const [family, bits] of [
			['ipv4', 32],
			['ipv6', 128]
		] as const) {
			const entries = (service as Record<string, unknown>)[family];
			if (!Array.isArray(entries)) throw new Error('Invalid crawler IP list');
			for (const entry of entries) {
				if (typeof entry !== 'string') throw new Error('Invalid crawler subnet');
				const parts = entry.split('/');
				if (
					parts.length !== 2 ||
					isIP(parts[0]) !== (family === 'ipv4' ? 4 : 6) ||
					!/^\d+$/.test(parts[1])
				)
					throw new Error('Invalid crawler subnet');
				const prefix = Number(parts[1]);
				if (prefix > bits) throw new Error('Invalid crawler prefix');
				ranges.addSubnet(parts[0], prefix, family);
			}
		}
	}
	return ranges;
}

// The deployment script puts the feed in build/; CRAWLER_IP_FILE can override it.
export function loadCrawlerRanges(
	file = process.env.CRAWLER_IP_FILE || resolve(process.cwd(), 'build', 'crawlers.json')
): BlockList | null {
	try {
		return parseCrawlerRanges(JSON.parse(readFileSync(file, 'utf8')));
	} catch {
		return null;
	}
}

const crawlerRanges = loadCrawlerRanges();

export function isCrawlerIP(ip: string): boolean {
	if (crawlerRanges === null) return false;
	const family = isIP(ip);
	return family !== 0 && crawlerRanges.check(ip, family === 4 ? 'ipv4' : 'ipv6');
}

// Configure CRAWLER_RATE_LIMIT_MULTIPLIER as an integer from 1 to 1000 (default 5).
export function crawlerRateMultiplier(ip: string): number {
	if (!isCrawlerIP(ip)) return 1;
	const configured = Number(process.env.CRAWLER_RATE_LIMIT_MULTIPLIER ?? '5');
	return Number.isSafeInteger(configured) && configured >= 1 && configured <= 1000 ? configured : 5;
}
