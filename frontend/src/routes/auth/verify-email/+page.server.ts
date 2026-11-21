import { fail, redirect } from '@sveltejs/kit';
import { loginUrl, isSafeRedirect } from '#lib/server/auth/auth.js';
import {
	EMAIL_VERIFICATION_LIMIT_MESSAGE,
	createEmailVerificationRequest,
	deleteEmailVerificationRequestCookie,
	deleteUserEmailVerificationRequest,
	findEmailVerificationCodeMatch,
	getRemainingVerificationEmailSends,
	getUserEmailVerificationRequestFromRequest,
	sendVerificationEmail,
	sendVerificationEmailBucket,
	setEmailVerificationRequestCookie
} from '#lib/server/auth/email-verification.js';
import { deleteSessionTokenCookie, invalidateSession } from '#lib/server/auth/session.js';
import { invalidateUserPasswordResetSessions } from '#lib/server/auth/password-reset.js';
import { updateUserEmailAndSetEmailAsVerified } from '#lib/server/auth/user.js';
import { ExpiringTokenBucket } from '#lib/server/auth/rate-limit.js';

import type { Actions, RequestEvent } from './$types';

export const ssr = true;
export const csr = true;

function getVerificationEmailState(userId: number) {
	const verificationEmailsRemaining = getRemainingVerificationEmailSends(userId);
	return {
		verificationEmailsRemaining,
		highlightSpamNotice: verificationEmailsRemaining === 0
	};
}

export async function load(event: RequestEvent) {
	if (event.locals.user === null) {
		return redirect(302, '/auth/login');
	}
	let verificationRequest = await getUserEmailVerificationRequestFromRequest(event);
	if (verificationRequest === null || Date.now() >= verificationRequest.expiresAt.getTime()) {
		if (event.locals.user.emailVerified) {
			const redirectTo = event.url.searchParams.get('redirectTo');
			if (isSafeRedirect(redirectTo)) {
				return redirect(302, redirectTo);
			}
			return redirect(302, '/');
		}
		if (!sendVerificationEmailBucket.consume(event.locals.user.id, 1)) {
			return {
				email: event.locals.user.email,
				notice: EMAIL_VERIFICATION_LIMIT_MESSAGE,
				redirectTo: event.url.searchParams.get('redirectTo') ?? '',
				...getVerificationEmailState(event.locals.user.id)
			};
		}
		verificationRequest = await createEmailVerificationRequest(
			event.locals.user.id,
			event.locals.user.email
		);
		await sendVerificationEmail(verificationRequest.email, verificationRequest.code);
		await setEmailVerificationRequestCookie(event, verificationRequest);
	}
	const redirectTo = event.url.searchParams.get('redirectTo') ?? '';
	return {
		email: verificationRequest.email,
		notice: null,
		redirectTo: isSafeRedirect(redirectTo) ? redirectTo : '',
		...getVerificationEmailState(event.locals.user.id)
	};
}

const bucket = new ExpiringTokenBucket<number>(5, 60 * 30);

export const actions: Actions = {
	verify: verifyCode,
	resend: resendEmail,
	logout: logout
};

async function logout(event: RequestEvent) {
	if (event.locals.session === null) {
		return fail(401, {
			message: 'Not authenticated'
		});
	}

	await invalidateSession(event.locals.session.id);
	deleteSessionTokenCookie(event);
	deleteEmailVerificationRequestCookie(event);
	return redirect(302, loginUrl('/auth/verify-email'));
}

async function verifyCode(event: RequestEvent) {
	if (event.locals.session === null || event.locals.user === null) {
		return fail(401, {
			verify: {
				message: 'Not authenticated',
				verificationEmailsRemaining: 0,
				highlightSpamNotice: false
			}
		});
	}
	if (event.locals.user.registered2FA && !event.locals.session.twoFactorVerified) {
		return fail(403, {
			verify: {
				message: 'Forbidden',
				...getVerificationEmailState(event.locals.user.id)
			}
		});
	}
	if (!bucket.check(event.locals.user.id, 1)) {
		return fail(429, {
			verify: {
				message: 'Too many attempts',
				...getVerificationEmailState(event.locals.user.id)
			}
		});
	}

	const formData = await event.request.formData();
	const code = formData.get('code');
	if (typeof code !== 'string') {
		return fail(400, {
			verify: {
				message: 'Invalid or missing fields',
				...getVerificationEmailState(event.locals.user.id)
			}
		});
	}
	if (code === '') {
		return fail(400, {
			verify: {
				message: 'Enter your code',
				...getVerificationEmailState(event.locals.user.id)
			}
		});
	}
	if (!bucket.consume(event.locals.user.id, 1)) {
		return fail(400, {
			verify: {
				message: 'Too many attempts',
				...getVerificationEmailState(event.locals.user.id)
			}
		});
	}

	// Accept any unexpired code the user has been sent. The match query
	// filters by user_id, code, and expires_at > now() in one shot.
	const matchedRequest = await findEmailVerificationCodeMatch(event.locals.user.id, code);
	if (matchedRequest === null) {
		return fail(400, {
			verify: {
				message: 'Incorrect code.',
				...getVerificationEmailState(event.locals.user.id)
			}
		});
	}
	await deleteUserEmailVerificationRequest(event.locals.user.id);
	await invalidateUserPasswordResetSessions(event.locals.user.id);
	await updateUserEmailAndSetEmailAsVerified(event.locals.user.id, matchedRequest.email);
	sendVerificationEmailBucket.reset(event.locals.user.id);
	deleteEmailVerificationRequestCookie(event);
	const redirectTo = formData.get('redirectTo');
	if (typeof redirectTo === 'string' && isSafeRedirect(redirectTo)) {
		return redirect(302, redirectTo);
	}
	return redirect(302, '/pricing');
}

async function resendEmail(event: RequestEvent) {
	if (event.locals.session === null || event.locals.user === null) {
		return fail(401, {
			resend: {
				message: 'Not authenticated',
				verificationEmailsRemaining: 0,
				highlightSpamNotice: false
			}
		});
	}
	if (event.locals.user.registered2FA && !event.locals.session.twoFactorVerified) {
		return fail(403, {
			resend: {
				message: 'Forbidden',
				...getVerificationEmailState(event.locals.user.id)
			}
		});
	}
	if (!sendVerificationEmailBucket.check(event.locals.user.id, 1)) {
		return fail(429, {
			resend: {
				message: EMAIL_VERIFICATION_LIMIT_MESSAGE,
				...getVerificationEmailState(event.locals.user.id)
			}
		});
	}

	let verificationRequest = await getUserEmailVerificationRequestFromRequest(event);
	if (verificationRequest === null) {
		if (event.locals.user.emailVerified) {
			return fail(403, {
				resend: {
					message: 'Forbidden',
					...getVerificationEmailState(event.locals.user.id)
				}
			});
		}
		if (!sendVerificationEmailBucket.consume(event.locals.user.id, 1)) {
			return fail(429, {
				resend: {
					message: EMAIL_VERIFICATION_LIMIT_MESSAGE,
					...getVerificationEmailState(event.locals.user.id)
				}
			});
		}
		verificationRequest = await createEmailVerificationRequest(
			event.locals.user.id,
			event.locals.user.email
		);
	} else {
		if (!sendVerificationEmailBucket.consume(event.locals.user.id, 1)) {
			return fail(429, {
				resend: {
					message: EMAIL_VERIFICATION_LIMIT_MESSAGE,
					...getVerificationEmailState(event.locals.user.id)
				}
			});
		}
		verificationRequest = await createEmailVerificationRequest(
			event.locals.user.id,
			verificationRequest.email
		);
	}
	if (verificationRequest === null) {
		return fail(401, {
			resend: {
				message: 'Email verification request not found',
				...getVerificationEmailState(event.locals.user.id)
			}
		});
	}
	await sendVerificationEmail(verificationRequest.email, verificationRequest.code);
	setEmailVerificationRequestCookie(event, verificationRequest);
	const verificationEmailState = getVerificationEmailState(event.locals.user.id);
	return {
		resend: {
			message: verificationEmailState.highlightSpamNotice
				? 'A new code was sent to your inbox. This is your last verification email for now, so please check spam or junk.'
				: 'A new code was sent to your inbox.',
			...verificationEmailState
		}
	};
}
