// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces

declare global {
	namespace App {
		interface Locals {
			user: User | null;
			session: Session | null;
			/**
			 * Set when a signed-out machine client paid for this single request
			 * via x402 / the Machine Payments Protocol. Page loads accept it in
			 * place of a login for non account-scoped data.
			 */
			machinePaid: boolean;
		}
		// interface Error {}
		// interface PageData {}
		// interface Platform {}
	}
}

export {};
