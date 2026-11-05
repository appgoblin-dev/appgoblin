// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces

declare global {
	namespace App {
		interface Locals {
			user: User | null;
			session: Session | null;
			/** True when this request was paid via x402 or MPP. */
			machinePaid: boolean;
			anonymousSearchQuota?: { remaining: number; limit: number };
		}
		// interface Error {}
		// interface PageData {}
		// interface Platform {}
	}
}

export {};
