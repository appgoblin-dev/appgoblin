import type { RequestEvent } from '@sveltejs/kit';
import { generateRandomOTP, encodeBase32 } from './utils';
import { db } from './db';
import { ExpiringTokenBucket } from './rate-limit';
import nodemailer from 'nodemailer';
import { EMAIL_PASSWORD, EMAIL_HOST, EMAIL_PORT, EMAIL_USER } from '$env/static/private';

export async function getUserEmailVerificationRequest(
	userId: number,
	id: string
): Promise<EmailVerificationRequest | null> {
	const row = await db.queryOne<{
		id: string;
		user_id: number;
		code: string;
		email: string;
		expires_at: string;
	}>(
		'SELECT id, user_id, code, email, expires_at FROM email_verification_requests WHERE id = $1 AND user_id = $2',
		[id, userId]
	);
	if (row === null) {
		return row;
	}
	const request: EmailVerificationRequest = {
		id: row.id,
		userId: row.user_id,
		code: row.code,
		email: row.email,
		expiresAt: new Date(row.expires_at)
	};
	return request;
}

export async function getUserEmailVerificationRequestByUserId(
	userId: number
): Promise<EmailVerificationRequest | null> {
	const row = await db.queryOne<{
		id: string;
		user_id: number;
		code: string;
		email: string;
		expires_at: string;
	}>(
		'SELECT id, user_id, code, email, expires_at FROM email_verification_requests WHERE user_id = $1',
		[userId]
	);
	if (row === null) {
		return null;
	}
	return {
		id: row.id,
		userId: row.user_id,
		code: row.code,
		email: row.email,
		expiresAt: new Date(row.expires_at)
	};
}

export async function createEmailVerificationRequest(
	userId: number,
	email: string
): Promise<EmailVerificationRequest> {
	await deleteUserEmailVerificationRequest(userId);
	const idBytes = new Uint8Array(20);
	crypto.getRandomValues(idBytes);
	const id = encodeBase32(idBytes).toLowerCase();

	const code = generateRandomOTP();
	const expiresAt = new Date(Date.now() + 1000 * 60 * 10);
	await db.queryOne<{ id: string }>(
		'INSERT INTO email_verification_requests (id, user_id, code, email, expires_at) VALUES ($1, $2, $3, $4, $5) RETURNING id',
		[id, userId, code, email, expiresAt]
	);

	const request: EmailVerificationRequest = {
		id,
		userId,
		code,
		email,
		expiresAt
	};
	return request;
}

export async function deleteUserEmailVerificationRequest(userId: number): Promise<void> {
	await db.execute('DELETE FROM email_verification_requests WHERE user_id = $1', [userId]);
}

export function setEmailVerificationRequestCookie(
	event: RequestEvent,
	request: EmailVerificationRequest
): void {
	event.cookies.set('email_verification', request.id, {
		httpOnly: true,
		path: '/',
		secure: import.meta.env.PROD,
		sameSite: 'lax',
		expires: request.expiresAt
	});
}

export function deleteEmailVerificationRequestCookie(event: RequestEvent): void {
	event.cookies.set('email_verification', '', {
		httpOnly: true,
		path: '/',
		secure: import.meta.env.PROD,
		sameSite: 'lax',
		maxAge: 0
	});
}

export async function getUserEmailVerificationRequestFromRequest(
	event: RequestEvent
): Promise<EmailVerificationRequest | null> {
	if (event.locals.user === null) {
		return null;
	}
	const id = event.cookies.get('email_verification') ?? null;
	if (id !== null) {
		const request = await getUserEmailVerificationRequest(event.locals.user.id, id);
		if (request !== null) {
			return request;
		}
		deleteEmailVerificationRequestCookie(event);
	}
	const request = await getUserEmailVerificationRequestByUserId(event.locals.user.id);
	if (request === null) {
		return null;
	}
	setEmailVerificationRequestCookie(event, request);
	return request;
}

// Create reusable transporter
// Will be null if EMAIL_PASSWORD is not configured (development fallback to console.log)
let transporter: ReturnType<typeof nodemailer.createTransport> | null = null;

const initializeTransporter = () => {
	const emailPassword = EMAIL_PASSWORD;

	if (!emailPassword) {
		// In development, allow missing email config (will fall back to console.log)
		if (import.meta.env.DEV) {
			console.warn('EMAIL_PASSWORD not set - emails will be logged to console in development');
			return null;
		}
		throw new Error('EMAIL_PASSWORD environment variable is required in production');
	}

	return nodemailer.createTransport({
		host: EMAIL_HOST,
		port: parseInt(EMAIL_PORT),
		secure: true,
		auth: {
			user: EMAIL_USER,
			pass: emailPassword
		}
	});
};

transporter = initializeTransporter();

/**
 * Send a verification email with a code
 */
export async function sendVerificationEmail(email: string, code: string): Promise<void> {
	// Fallback to console.log if transporter is not configured (development)
	if (!transporter) {
		console.log(`[DEV] To ${email}: Your verification code is ${code}`);
		return;
	}

	try {
		await transporter.sendMail({
			from: `"AppGoblin Admin" <${EMAIL_USER}>`,
			to: email,
			subject: 'AppGoblin - Email Verification Code',
			text: `Your verification code is: ${code}`,
			html: `
				<div>
					<h2>Email Verification</h2>
					<p>Your verification code is: <strong>${code}</strong></p>
					<p>This code will expire in 10 minutes.</p>
				</div>
			`
		});
	} catch (error) {
		console.error('Failed to send verification email:', error);
		// In development, fall back to console.log if email fails
		if (import.meta.env.DEV) {
			console.log(`[DEV] To ${email}: Your verification code is ${code}`);
		} else {
			throw error;
		}
	}
}

/**
 * Send a password reset email with a code
 */
export async function sendPasswordResetEmail(email: string, code: string): Promise<void> {
	// Fallback to console.log if transporter is not configured (development)
	if (!transporter) {
		console.log(`[DEV] To ${email}: Your reset code is ${code}`);
		return;
	}

	try {
		await transporter.sendMail({
			from: `"AppGoblin Admin" <${EMAIL_USER}>`,
			to: email,
			subject: 'AppGoblin - Password Reset Code',
			text: `Your password reset code is: ${code}`,
			html: `
				<div>
					<h2>Password Reset</h2>
					<p>Your password reset code is: <strong>${code}</strong></p>
					<p>This code will expire in 10 minutes.</p>
					<p>If you did not request this, please ignore this email or contact support.</p>
				</div>
			`
		});
	} catch (error) {
		console.error('Failed to send password reset email:', error);
		// In development, fall back to console.log if email fails
		if (import.meta.env.DEV) {
			console.log(`[DEV] To ${email}: Your reset code is ${code}`);
		} else {
			throw error;
		}
	}
}

export const EMAIL_VERIFICATION_SEND_LIMIT = 3;
const EMAIL_VERIFICATION_SEND_WINDOW_SECONDS = 60 * 60;

export const EMAIL_VERIFICATION_LIMIT_MESSAGE =
	'You can request up to 3 verification emails for now. Check spam or junk for the latest AppGoblin email.';

export const sendVerificationEmailBucket = new ExpiringTokenBucket<number>(
	EMAIL_VERIFICATION_SEND_LIMIT,
	EMAIL_VERIFICATION_SEND_WINDOW_SECONDS
);

export function getRemainingVerificationEmailSends(userId: number): number {
	return sendVerificationEmailBucket.getRemaining(userId);
}

export interface EmailVerificationRequest {
	id: string;
	userId: number;
	code: string;
	email: string;
	expiresAt: Date;
}
