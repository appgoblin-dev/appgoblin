import { fail, redirect } from '@sveltejs/kit';
import { checkEmailAvailability, verifyEmailInput } from '$lib/server/auth/email';
import { createUser, verifyUsernameInput } from '$lib/server/auth/user';
import { RefillingTokenBucket } from '$lib/server/auth/rate-limit';
import { verifyPasswordStrength } from '$lib/server/auth/password';
import {
	createSession,
	DEFAULT_SESSION_DURATION_HOURS,
	generateSessionToken,
	setSessionTokenCookie
} from '$lib/server/auth/session';
import {
	createEmailVerificationRequest,
	sendVerificationEmail,
	setEmailVerificationRequestCookie
} from '$lib/server/auth/email-verification';
import { redirectIfAuthenticated } from '$lib/server/auth/auth';

import type { SessionFlags } from '$lib/server/auth/session';
import type { Actions, PageServerLoadEvent, RequestEvent } from './$types';

const ipBucket = new RefillingTokenBucket<string>(3, 10);

export function load(event: PageServerLoadEvent) {
	// Redirect if already authenticated (public route)
	redirectIfAuthenticated(event);
	return {};
}

export const actions: Actions = {
	default: action
};

async function action(event: RequestEvent) {
	// TODO: Assumes X-Forwarded-For is always included.
	const clientIP = event.request.headers.get('X-Forwarded-For');
	if (clientIP !== null && !ipBucket.check(clientIP, 1)) {
		return fail(429, {
			message: 'Too many requests',
			email: '',
			username: ''
		});
	}

	const formData = await event.request.formData();
	const email = formData.get('email');
	const username = formData.get('username');
	const password = formData.get('password');
	if (typeof email !== 'string' || typeof username !== 'string' || typeof password !== 'string') {
		return fail(400, {
			message: 'Invalid or missing fields',
			email: '',
			username: ''
		});
	}
	if (email === '' || password === '' || username === '') {
		return fail(400, {
			message: 'Please enter your username, email, and password',
			email: '',
			username: ''
		});
	}
	if (!verifyEmailInput(email)) {
		return fail(400, {
			message: 'Invalid email',
			email,
			username
		});
	}
	const emailAvailable = await checkEmailAvailability(email);
	if (!emailAvailable) {
		return fail(400, {
			message: 'Email is already used',
			email,
			username
		});
	}
	if (!verifyUsernameInput(username)) {
		return fail(400, {
			message: 'Invalid username',
			email,
			username
		});
	}
	const strongPassword = await verifyPasswordStrength(password);
	if (!strongPassword) {
		return fail(400, {
			message: 'Weak password',
			email,
			username
		});
	}
	if (clientIP !== null && !ipBucket.consume(clientIP, 1)) {
		return fail(429, {
			message: 'Too many requests',
			email,
			username
		});
	}
	const user = await createUser(email, username, password);
	const emailVerificationRequest = await createEmailVerificationRequest(user.id, user.email);
	await sendVerificationEmail(emailVerificationRequest.email, emailVerificationRequest.code);
	setEmailVerificationRequestCookie(event, emailVerificationRequest);

	const sessionFlags: SessionFlags = {
		twoFactorVerified: true
	};
	const sessionToken = generateSessionToken();
	const session = await createSession(
		sessionToken,
		user.id,
		sessionFlags,
		DEFAULT_SESSION_DURATION_HOURS
	);
	setSessionTokenCookie(event, sessionToken, session.expiresAt);
	throw redirect(302, '/auth/verify-email');
}
