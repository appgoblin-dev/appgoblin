import { fail, redirect } from '@sveltejs/kit';
import {
	EMAIL_VERIFICATION_LIMIT_MESSAGE,
	createEmailVerificationRequest,
	deleteEmailVerificationRequestCookie,
	deleteUserEmailVerificationRequest,
	getRemainingVerificationEmailSends,
	getUserEmailVerificationRequestFromRequest,
	sendVerificationEmail,
	sendVerificationEmailBucket,
	setEmailVerificationRequestCookie
} from '$lib/server/auth/email-verification';
import { invalidateUserPasswordResetSessions } from '$lib/server/auth/password-reset';
import { updateUserEmailAndSetEmailAsVerified } from '$lib/server/auth/user';
import { ExpiringTokenBucket } from '$lib/server/auth/rate-limit';

import type { Actions, RequestEvent } from './$types';

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
			return redirect(302, '/');
		}
		if (!sendVerificationEmailBucket.consume(event.locals.user.id, 1)) {
			return {
				email: event.locals.user.email,
				notice: EMAIL_VERIFICATION_LIMIT_MESSAGE,
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
	return {
		email: verificationRequest.email,
		notice: null,
		...getVerificationEmailState(event.locals.user.id)
	};
}

const bucket = new ExpiringTokenBucket<number>(5, 60 * 30);

export const actions: Actions = {
	verify: verifyCode,
	resend: resendEmail
};

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

	let verificationRequest = await getUserEmailVerificationRequestFromRequest(event);
	if (verificationRequest === null) {
		return fail(401, {
			verify: {
				message: 'Not authenticated',
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
	if (Date.now() >= verificationRequest.expiresAt.getTime()) {
		if (!sendVerificationEmailBucket.consume(event.locals.user.id, 1)) {
			return fail(429, {
				verify: {
					message: EMAIL_VERIFICATION_LIMIT_MESSAGE,
					...getVerificationEmailState(event.locals.user.id)
				}
			});
		}
		verificationRequest = await createEmailVerificationRequest(
			verificationRequest.userId,
			verificationRequest.email
		);
		await sendVerificationEmail(verificationRequest.email, verificationRequest.code);
		setEmailVerificationRequestCookie(event, verificationRequest);
		return {
			verify: {
				message:
					'The verification code expired. We sent another code to your inbox. Check spam or junk if it does not arrive.',
				...getVerificationEmailState(event.locals.user.id)
			}
		};
	}
	if (verificationRequest.code !== code) {
		return fail(400, {
			verify: {
				message: 'Incorrect code.',
				...getVerificationEmailState(event.locals.user.id)
			}
		});
	}
	await deleteUserEmailVerificationRequest(event.locals.user.id);
	await invalidateUserPasswordResetSessions(event.locals.user.id);
	await updateUserEmailAndSetEmailAsVerified(event.locals.user.id, verificationRequest.email);
	sendVerificationEmailBucket.reset(event.locals.user.id);
	deleteEmailVerificationRequestCookie(event);
	return redirect(302, '/');
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
