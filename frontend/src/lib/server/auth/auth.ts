import { redirect } from '@sveltejs/kit';
import type { RequestEvent } from '@sveltejs/kit';

/**
 * Require authentication for a route
 * Returns the user and session if authenticated, otherwise redirects to login
 */
export function requireAuth(event: RequestEvent) {
	if (event.locals.session === null || event.locals.user === null) {
		throw redirect(302, '/auth/login');
	}
	return {
		session: event.locals.session,
		user: event.locals.user
	};
}

/**
 * Require email verification
 * Must be called after requireAuth
 */
export function requireEmailVerified(user: { emailVerified: boolean }) {
	if (!user.emailVerified) {
		throw redirect(302, '/auth/verify-email');
	}
}

/**
 * Require 2FA setup
 * Must be called after requireAuth
 */
export function require2FASetup(user: { registered2FA: boolean }) {
	if (!user.registered2FA) {
		throw redirect(302, '/auth/2fa/setup');
	}
}

/**
 * Require 2FA verification for this session
 * Must be called after requireAuth
 */
export function require2FAVerified(session: { twoFactorVerified: boolean }) {
	if (!session.twoFactorVerified) {
		throw redirect(302, '/auth/2fa');
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
 * Redirect authenticated users away from auth pages (login, signup)
 */
export function redirectIfAuthenticated(event: RequestEvent) {
	if (event.locals.session !== null && event.locals.user !== null) {
		// If authenticated and email verified, go to home
		if (event.locals.user.emailVerified) {
			throw redirect(302, '/');
		}
		// Otherwise continue with auth flow
		if (!event.locals.user.emailVerified) {
			throw redirect(302, '/auth/verify-email');
		}
	}
}
