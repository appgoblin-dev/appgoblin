import { error, redirect } from '@sveltejs/kit';
import type { RequestEvent } from '@sveltejs/kit';
import { db } from './db';
import { getOrganizationSubscriptionAccess } from '#lib/server/organization.js';

/**
 * Build login URL with optional redirectTo (current path by default).
 * Caller should pass the path the user should return to after login.
 */
export function loginUrl(redirectTo?: string): string {
	const base = '/auth/login';
	if (redirectTo == null || redirectTo === '') return base;
	const encoded = encodeURIComponent(redirectTo);
	return `${base}?redirectTo=${encoded}`;
}

/**
 * Require authentication for a route
 * Returns the user and session if authenticated, otherwise redirects to login
 * with redirectTo set to the current URL so the user returns here after login.
 */
export function requireAuth(event: RequestEvent) {
	if (event.locals.session === null || event.locals.user === null) {
		const returnTo = event.url.pathname + event.url.search;
		redirect(302, loginUrl(returnTo));
	}
	return {
		session: event.locals.session,
		user: event.locals.user
	};
}

/**
 * Require authentication, returning HTTP 401 instead of redirecting.
 * Use this for routes that should signal "this page needs auth"
 * to crawlers rather than bouncing them through a redirect chain.
 */
export function requireAuthOr401(event: RequestEvent) {
	if (event.locals.session === null || event.locals.user === null) {
		error(401, 'Authentication required');
	}
	return {
		session: event.locals.session,
		user: event.locals.user
	};
}

/**
 * Require either a signed-in user or a single-page machine payment (x402 /
 * Machine Payments Protocol). Use only for pages whose data is not scoped to
 * an individual account: `user` is `null` for a paid machine request.
 */
export function requireAuthOrMachinePayment(event: RequestEvent) {
	if (event.locals.session !== null && event.locals.user !== null) {
		return { session: event.locals.session, user: event.locals.user };
	}
	if (event.locals.machinePaid) {
		return { session: null, user: null };
	}
	error(401, 'Authentication required');
}

/**
 * Require email verification
 * Must be called after requireAuth
 */
export function requireEmailVerified(user: { emailVerified: boolean }) {
	if (!user.emailVerified) {
		redirect(302, '/auth/verify-email');
	}
}

/**
 * Require 2FA setup
 * Must be called after requireAuth
 */
export function require2FASetup(user: { registered2FA: boolean }) {
	if (!user.registered2FA) {
		redirect(302, '/auth/2fa/setup');
	}
}

/**
 * Require 2FA verification for this session
 * Must be called after requireAuth
 */
export function require2FAVerified(session: { twoFactorVerified: boolean }) {
	if (!session.twoFactorVerified) {
		redirect(302, '/auth/2fa');
	}
}

/**
 * Require full authentication (email verified + 2FA setup + 2FA verified)
 * Use this for protected routes that need complete authentication
 */
export function requireFullAuth(event: RequestEvent) {
	const { session, user } = requireAuth(event);
	requireEmailVerified(user);
	//require2FASetup(user);
	//require2FAVerified(session);
	return { session, user };
}

/**
 * Require an active or trialing subscription; redirect to /pricing otherwise.
 * Use for paid-only routes (e.g. data export downloads).
 */
export async function requirePaidSubscription(event: RequestEvent) {
	if (!event.locals.user) {
		redirect(302, '/pricing');
	}
	const organizationSubscription = await getOrganizationSubscriptionAccess(event.locals.user.id);
	if (!organizationSubscription) {
		redirect(302, '/pricing');
	}
}

/**
 * Redirect authenticated users away from auth pages (login, signup).
 * If redirectTo is in the URL and valid, redirect there; otherwise defaultTarget.
 * Users who still need to verify their email go to the verification page, which
 * will then send them to unverifiedDefaultTarget (when set).
 */
export function redirectIfAuthenticated(
	event: RequestEvent,
	defaultTarget = '/',
	unverifiedDefaultTarget = ''
) {
	if (event.locals.session !== null && event.locals.user !== null) {
		if (event.locals.user.emailVerified) {
			const redirectTo = event.url.searchParams.get('redirectTo');
			const target = isSafeRedirect(redirectTo) ? redirectTo : defaultTarget;
			redirect(302, target);
		}
		if (!event.locals.user.emailVerified) {
			const redirectTo = event.url.searchParams.get('redirectTo');
			const target = isSafeRedirect(redirectTo) ? redirectTo : unverifiedDefaultTarget;
			if (target) {
				redirect(302, `/auth/verify-email?redirectTo=${encodeURIComponent(target)}`);
			}
			redirect(302, '/auth/verify-email');
		}
	}
}

/**
 * Valid redirect target: same-origin path only, no auth pages (avoid loops).
 */
export function isSafeRedirect(value: string | null): value is string {
	if (value == null || value === '') return false;
	if (!value.startsWith('/') || value.startsWith('//')) return false;
	if (value.startsWith('/auth')) return false;
	return true;
}
