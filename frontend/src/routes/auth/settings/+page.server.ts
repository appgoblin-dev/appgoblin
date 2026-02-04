import {
	createEmailVerificationRequest,
	sendVerificationEmail,
	sendVerificationEmailBucket,
	setEmailVerificationRequestCookie
} from '$lib/server/auth/email-verification';
import { fail, redirect } from '@sveltejs/kit';
import { checkEmailAvailability, verifyEmailInput } from '$lib/server/auth/email';
import { verifyPasswordHash, verifyPasswordStrength } from '$lib/server/auth/password';
import { getUserPasswordHash, getUserRecoverCode, updateUserPassword } from '$lib/server/auth/user';
import {
	createSession,
	DEFAULT_SESSION_DURATION_HOURS,
	generateSessionToken,
	invalidateUserSessions,
	setSessionTokenCookie
} from '$lib/server/auth/session';
import { requireAuth } from '$lib/server/auth/auth';
import { ExpiringTokenBucket } from '$lib/server/auth/rate-limit';

import type { Actions, RequestEvent } from './$types';
import type { SessionFlags } from '$lib/server/auth/session';

const passwordUpdateBucket = new ExpiringTokenBucket<string>(5, 60 * 30);

export async function load(event: RequestEvent) {
	// This route requires authentication (but not necessarily full 2FA)
	const { session, user } = requireAuth(event);

	// If 2FA is set up, require it to be verified
	if (user.registered2FA && !session.twoFactorVerified) {
		throw redirect(302, '/auth/2fa');
	}

	let recoveryCode: string | null = null;
	if (user.registered2FA) {
		recoveryCode = await getUserRecoverCode(user.id);
	}
	return {
		recoveryCode,
		user
	};
}

export const actions: Actions = {
	password: updatePasswordAction,
	email: updateEmailAction
};

async function updatePasswordAction(event: RequestEvent) {
	const { session, user } = requireAuth(event);

	// If 2FA is set up, require it to be verified
	if (user.registered2FA && !session.twoFactorVerified) {
		return fail(403, {
			password: {
				message: 'Forbidden'
			}
		});
	}
	if (!passwordUpdateBucket.check(session.id, 1)) {
		return fail(429, {
			password: {
				message: 'Too many requests'
			}
		});
	}

	const formData = await event.request.formData();
	const password = formData.get('password');
	const newPassword = formData.get('new_password');
	if (typeof password !== 'string' || typeof newPassword !== 'string') {
		return fail(400, {
			password: {
				message: 'Invalid or missing fields'
			}
		});
	}
	const strongPassword = await verifyPasswordStrength(newPassword);
	if (!strongPassword) {
		return fail(400, {
			password: {
				message: 'Weak password'
			}
		});
	}

	if (!passwordUpdateBucket.consume(session.id, 1)) {
		return fail(429, {
			password: {
				message: 'Too many requests'
			}
		});
	}

	const passwordHash = await getUserPasswordHash(user.id);
	const validPassword = await verifyPasswordHash(passwordHash, password);
	if (!validPassword) {
		return fail(400, {
			password: {
				message: 'Incorrect password'
			}
		});
	}
	passwordUpdateBucket.reset(session.id);
	invalidateUserSessions(user.id);
	await updateUserPassword(user.id, newPassword);

	const sessionToken = generateSessionToken();
	const sessionFlags: SessionFlags = {
		twoFactorVerified: session.twoFactorVerified
	};
	const newSession = await createSession(
		sessionToken,
		user.id,
		sessionFlags,
		DEFAULT_SESSION_DURATION_HOURS
	);
	setSessionTokenCookie(event, sessionToken, newSession.expiresAt);
	return {
		password: {
			message: 'Updated password'
		}
	};
}

async function updateEmailAction(event: RequestEvent) {
	const { session, user } = requireAuth(event);

	// If 2FA is set up, require it to be verified
	if (user.registered2FA && !session.twoFactorVerified) {
		return fail(403, {
			email: {
				message: 'Forbidden'
			}
		});
	}
	if (!sendVerificationEmailBucket.check(user.id, 1)) {
		return fail(429, {
			email: {
				message: 'Too many requests'
			}
		});
	}

	const formData = await event.request.formData();
	const email = formData.get('email');
	if (typeof email !== 'string') {
		return fail(400, {
			email: {
				message: 'Invalid or missing fields'
			}
		});
	}
	if (email === '') {
		return fail(400, {
			email: {
				message: 'Please enter your email'
			}
		});
	}
	if (!verifyEmailInput(email)) {
		return fail(400, {
			email: {
				message: 'Please enter a valid email'
			}
		});
	}
	const emailAvailable = await checkEmailAvailability(email);
	if (!emailAvailable) {
		return fail(400, {
			email: {
				message: 'This email is already used'
			}
		});
	}
	if (!sendVerificationEmailBucket.consume(user.id, 1)) {
		return fail(429, {
			email: {
				message: 'Too many requests'
			}
		});
	}
	const verificationRequest = await createEmailVerificationRequest(user.id, email);
	await sendVerificationEmail(verificationRequest.email, verificationRequest.code);
	await setEmailVerificationRequestCookie(event, verificationRequest);
	return redirect(302, '/auth/verify-email');
}
