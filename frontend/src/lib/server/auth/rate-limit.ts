export class RefillingTokenBucket<_Key> {
	public max: number;
	public refillIntervalSeconds: number;

	constructor(max: number, refillIntervalSeconds: number) {
		this.max = max;
		this.refillIntervalSeconds = refillIntervalSeconds;
	}

	private storage = new Map<_Key, RefillBucket>();

	public check(key: _Key, cost: number): boolean {
		const bucket = this.storage.get(key) ?? null;
		if (bucket === null) {
			return true;
		}
		const now = Date.now();
		const refill = Math.floor((now - bucket.refilledAt) / (this.refillIntervalSeconds * 1000));
		if (refill > 0) {
			return Math.min(bucket.count + refill, this.max) >= cost;
		}
		return bucket.count >= cost;
	}

	public consume(key: _Key, cost: number): boolean {
		let bucket = this.storage.get(key) ?? null;
		const now = Date.now();
		if (bucket === null) {
			bucket = {
				count: this.max - cost,
				refilledAt: now
			};
			this.storage.set(key, bucket);
			return true;
		}
		const intervalMs = this.refillIntervalSeconds * 1000;
		const refill = Math.floor((now - bucket.refilledAt) / intervalMs);
		if (refill > 0) {
			bucket.count = Math.min(bucket.count + refill, this.max);
			// Advance by whole intervals only; setting this to `now` would discard
			// the partial interval on every request, so a client polling faster
			// than the refill interval would never refill.
			bucket.refilledAt += refill * intervalMs;
		}
		if (bucket.count < cost) {
			return false;
		}
		bucket.count -= cost;
		this.storage.set(key, bucket);
		return true;
	}
}

export class Throttler<_Key> {
	public timeoutSeconds: number[];

	private storage = new Map<_Key, ThrottlingCounter>();

	constructor(timeoutSeconds: number[]) {
		this.timeoutSeconds = timeoutSeconds;
	}

	public consume(key: _Key): boolean {
		let counter = this.storage.get(key) ?? null;
		const now = Date.now();
		if (counter === null) {
			counter = {
				timeout: 0,
				updatedAt: now
			};
			this.storage.set(key, counter);
			return true;
		}
		const allowed = now - counter.updatedAt >= this.timeoutSeconds[counter.timeout] * 1000;
		if (!allowed) {
			return false;
		}
		counter.updatedAt = now;
		counter.timeout = Math.min(counter.timeout + 1, this.timeoutSeconds.length - 1);
		this.storage.set(key, counter);
		return true;
	}

	public reset(key: _Key): void {
		this.storage.delete(key);
	}
}

export class ExpiringTokenBucket<_Key> {
	public max: number;
	public expiresInSeconds: number;

	private storage = new Map<_Key, ExpiringBucket>();

	constructor(max: number, expiresInSeconds: number) {
		this.max = max;
		this.expiresInSeconds = expiresInSeconds;
	}

	public check(key: _Key, cost: number): boolean {
		const bucket = this.storage.get(key) ?? null;
		const now = Date.now();
		if (bucket === null) {
			return true;
		}
		if (now - bucket.createdAt >= this.expiresInSeconds * 1000) {
			return true;
		}
		return bucket.count >= cost;
	}

	public getRemaining(key: _Key): number {
		const bucket = this.storage.get(key) ?? null;
		const now = Date.now();
		if (bucket === null) {
			return this.max;
		}
		if (now - bucket.createdAt >= this.expiresInSeconds * 1000) {
			return this.max;
		}
		return bucket.count;
	}

	public consume(key: _Key, cost: number): boolean {
		let bucket = this.storage.get(key) ?? null;
		const now = Date.now();
		if (bucket === null) {
			bucket = {
				count: this.max - cost,
				createdAt: now
			};
			this.storage.set(key, bucket);
			return true;
		}
		if (now - bucket.createdAt >= this.expiresInSeconds * 1000) {
			// Start a fresh window. Leaving `createdAt` stale would keep the bucket
			// permanently "expired", so every later request would refill it and the
			// limit would never apply again.
			bucket.count = this.max;
			bucket.createdAt = now;
		}
		if (bucket.count < cost) {
			return false;
		}
		bucket.count -= cost;
		this.storage.set(key, bucket);
		return true;
	}

	public reset(key: _Key): void {
		this.storage.delete(key);
	}
}

interface RefillBucket {
	count: number;
	refilledAt: number;
}

interface ExpiringBucket {
	count: number;
	createdAt: number;
}

interface ThrottlingCounter {
	timeout: number;
	updatedAt: number;
}
