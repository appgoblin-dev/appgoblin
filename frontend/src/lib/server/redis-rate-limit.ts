import { createHash } from 'node:crypto';
import { createClient } from 'redis';

export const REQUESTS_PER_MINUTE = 30;
export const REQUESTS_PER_DAY = 1000;
export const ANONYMOUS_SEARCHES_PER_DAY = 5;
const SEARCH_WINDOW_SECONDS = 24 * 60 * 60;

const REQUEST_SCRIPT = `
local clock = redis.call('TIME')
local now = tonumber(clock[1]) + tonumber(clock[2]) / 1000000
local day = math.floor(now / 86400)
local daily_key = KEYS[1] .. ':daily:' .. day
local count = tonumber(redis.call('GET', daily_key)) or 0
if count < tonumber(ARGV[2]) + 1 then
    count = redis.call('INCR', daily_key)
    if count == 1 then redis.call('EXPIREAT', daily_key, (day + 1) * 86400) end
end
if count > tonumber(ARGV[2]) then
    return {0, tonumber(ARGV[2]), 0, math.ceil((day + 1) * 86400 - now), 1, -1}
end
local state = redis.call('HMGET', KEYS[1] .. ':minute', 'tokens', 'last')
local limit = tonumber(ARGV[1])
local tokens = tonumber(state[1]) or limit
local last = tonumber(state[2]) or now
tokens = math.min(limit, tokens + math.max(0, now - last) * limit / 60)
local allowed = tokens >= 1
local retry = 0
if allowed then
    tokens = tokens - 1
else
    retry = math.max(1, math.ceil((1 - tokens) * 60 / limit))
end
redis.call('HSET', KEYS[1] .. ':minute', 'tokens', string.format('%.17g', tokens), 'last', string.format('%.6f', now))
redis.call('EXPIRE', KEYS[1] .. ':minute', 60)
if not allowed then
    return {0, limit, math.floor(tokens), retry, 2, -1}
end
if ARGV[3] == '1' then
    local searches = redis.call('GET', KEYS[2])
    if not searches then
        redis.call('SET', KEYS[2], 1, 'EX', tonumber(ARGV[5]))
        searches = 1
    else
        searches = tonumber(searches)
        if searches >= tonumber(ARGV[4]) then
            return {0, tonumber(ARGV[4]), 0, math.max(1, redis.call('TTL', KEYS[2])), 3, 0}
        end
        searches = redis.call('INCR', KEYS[2])
    end
    return {1, limit, math.floor(tokens), 0, 0, tonumber(ARGV[4]) - searches}
end
return {1, limit, math.floor(tokens), 0, 0, -1}
`;

const PRE_AUTH_SCRIPT = `
local clock = redis.call('TIME')
local now = tonumber(clock[1]) + tonumber(clock[2]) / 1000000
local state = redis.call('HMGET', KEYS[1], 'tokens', 'last')
local tokens = math.min(600, (tonumber(state[1]) or 600) + math.max(0, now - (tonumber(state[2]) or now)))
local allowed = tokens >= 1
if allowed then tokens = tokens - 1 end
redis.call('HSET', KEYS[1], 'tokens', string.format('%.17g', tokens), 'last', string.format('%.6f', now))
redis.call('EXPIRE', KEYS[1], 600)
return {allowed and 1 or 0, math.floor(tokens), allowed and 0 or math.max(1, math.ceil(1 - tokens))}
`;

export interface RedisLimitResult {
	allowed: boolean;
	limit: number;
	remaining: number;
	retryAfterSeconds: number;
	reason?: 'searchQuota';
	searchRemaining?: number;
}

export class RedisRateLimiter {
	private client;
	private connecting: Promise<void> | undefined;
	private prefix: string;
	private hashes = new Map<string, string>();

	constructor(
		url = process.env.FRONTEND_REDIS_URL || 'redis://127.0.0.1:6379',
		prefix = 'appgoblin:frontend:rate'
	) {
		this.prefix = prefix;
		this.client = createClient({
			url,
			disableOfflineQueue: true,
			socket: { connectTimeout: 1000, reconnectStrategy: false }
		});
		this.client.on('error', () => {});
	}

	private key(kind: string, identity: string): string {
		return `${this.prefix}:${kind}:${createHash('sha256').update(identity).digest('hex')}`;
	}

	private async eval(script: string, keys: string[], args: string[]): Promise<number[]> {
		if (!this.client.isReady) {
			if (!this.connecting) {
				this.connecting = this.client
					.connect()
					.then(() => {})
					.finally(() => {
						this.connecting = undefined;
					});
			}
			await this.connecting;
		}
		const options = { keys, arguments: args };
		let hash = this.hashes.get(script);
		if (!hash) {
			hash = createHash('sha1').update(script).digest('hex');
			this.hashes.set(script, hash);
		}
		try {
			return (await this.client
				.withAbortSignal(AbortSignal.timeout(1000))
				.evalSha(hash, options)) as number[];
		} catch (error) {
			if (!(error instanceof Error) || !error.message.startsWith('NOSCRIPT')) throw error;
			return (await this.client
				.withAbortSignal(AbortSignal.timeout(1000))
				.eval(script, options)) as number[];
		}
	}

	async check(identity: string, search: boolean): Promise<RedisLimitResult> {
		const [allowed, limit, remaining, retry, reason, searchRemaining] = await this.eval(
			REQUEST_SCRIPT,
			[this.key('client', identity), this.key('search', identity)],
			[
				REQUESTS_PER_MINUTE.toString(),
				REQUESTS_PER_DAY.toString(),
				search ? '1' : '0',
				ANONYMOUS_SEARCHES_PER_DAY.toString(),
				SEARCH_WINDOW_SECONDS.toString()
			]
		);
		return {
			allowed: allowed === 1,
			limit,
			remaining,
			retryAfterSeconds: retry,
			...(reason === 3 ? { reason: 'searchQuota' as const } : {}),
			...(searchRemaining >= 0 ? { searchRemaining } : {})
		};
	}

	async checkPreAuth(ip: string): Promise<RedisLimitResult> {
		const [allowed, remaining, retry] = await this.eval(
			PRE_AUTH_SCRIPT,
			[this.key('preauth', ip)],
			[]
		);
		return { allowed: allowed === 1, limit: 600, remaining, retryAfterSeconds: retry };
	}

	close(): void {
		if (this.client.isOpen) this.client.destroy();
	}
}
