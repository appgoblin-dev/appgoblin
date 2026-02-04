import { db } from './db';
import { encodeBase32, encodeHexLowerCase, sha256 } from '$lib/server/auth/utils';
import type { User } from './user';
import type { RequestEvent } from '@sveltejs/kit';

export interface SessionFlags {
	twoFactorVerified: boolean;
}

export interface Session extends SessionFlags {
	id: string;
	expiresAt: Date;
	userId: number;
}

type SessionValidationResult = { session: Session; user: User } | { session: null; user: null };

// Default persistent login duration (hours).
export const DEFAULT_SESSION_DURATION_HOURS = 24 * 30;

interface SessionRow {
	id: string;
	user_id: number;
	expires_at: string | Date;
	two_factor_verified: boolean;
	email: string;
	username: string;
	email_verified: boolean;
	has_totp: boolean;
}

export async function validateSessionToken(token: string): Promise<SessionValidationResult> {
	const sessionId = encodeHexLowerCase(await sha256(new TextEncoder().encode(token)));
	const row = await db.queryOne<SessionRow>(
		`
SELECT 
    s.id, 
    s.user_id, 
    s.expires_at, 
    s.two_factor_verified, 
    u.email, 
    u.username, 
    u.email_verified, 
    (u.totp_key IS NOT NULL) AS has_totp
FROM sessions s
INNER JOIN users u ON s.user_id = u.id
WHERE s.id = $1
`,
		[sessionId]
	);

	if (row === null) {
		return { session: null, user: null };
	}

	const session: Session = {
		id: row.id,
		userId: row.user_id,
		expiresAt: new Date(row.expires_at),
		twoFactorVerified: row.two_factor_verified
	};

	const user: User = {
		id: row.user_id,
		email: row.email,
		username: row.username,
		emailVerified: row.email_verified,
		registered2FA: row.has_totp
	};

	// Check if session has expired
	if (Date.now() >= session.expiresAt.getTime()) {
		await db.execute('DELETE FROM sessions WHERE id = $1', [session.id]);
		return { session: null, user: null };
	}

	// No auto-refresh - sessions expire naturally
	return { session, user };
}

export async function invalidateSession(sessionId: string): Promise<void> {
	await db.execute('DELETE FROM sessions WHERE id = $1', [sessionId]);
}

export async function invalidateUserSessions(userId: number): Promise<void> {
	await db.execute('DELETE FROM sessions WHERE user_id = $1', [userId]);
}

export function setSessionTokenCookie(
	event: RequestEvent,
	token: string,
	expiresAt: Date | null = null
): void {
	// If expiresAt is null, create a session-only cookie (expires when browser closes)
	// Otherwise use the provided expiration
	const cookieOptions: Parameters<typeof event.cookies.set>[2] = {
		httpOnly: true,
		path: '/',
		secure: import.meta.env.PROD,
		sameSite: 'lax'
	};

	if (expiresAt !== null) {
		cookieOptions.expires = expiresAt;
	}
	// If expiresAt is null, don't set expires - this makes it a session cookie

	event.cookies.set('session', token, cookieOptions);
}

export function deleteSessionTokenCookie(event: RequestEvent): void {
	event.cookies.set('session', '', {
		httpOnly: true,
		path: '/',
		secure: import.meta.env.PROD,
		sameSite: 'lax',
		maxAge: 0
	});
}

export function generateSessionToken(): string {
	const tokenBytes = new Uint8Array(20);
	crypto.getRandomValues(tokenBytes);
	const token = encodeBase32(tokenBytes, false, false);
	return token;
}

export async function createSession(
	token: string,
	userId: number,
	flags: SessionFlags,
	// Session duration in hours (0 = session-only, expires when browser closes)
	// For session-only cookies, DB expiration is still set for cleanup purposes
	sessionDurationHours: number = 0
): Promise<Session> {
	const sessionId = encodeHexLowerCase(await sha256(new TextEncoder().encode(token)));
	// For session-only (0 hours), set a reasonable DB expiration for cleanup
	// The cookie itself won't have expires, so it clears on browser close
	const expiresAt =
		sessionDurationHours > 0
			? new Date(Date.now() + 1000 * 60 * 60 * sessionDurationHours)
			: new Date(Date.now() + 1000 * 60 * 60 * 24); // 24h for DB cleanup, cookie is session-only

	const session: Session = {
		id: sessionId,
		userId,
		expiresAt,
		twoFactorVerified: flags.twoFactorVerified
	};

	await db.execute(
		'INSERT INTO sessions (id, user_id, expires_at, two_factor_verified) VALUES ($1, $2, $3, $4)',
		[session.id, session.userId, session.expiresAt, session.twoFactorVerified]
	);

	return session;
}

export async function setSessionAs2FAVerified(sessionId: string): Promise<void> {
	await db.execute('UPDATE sessions SET two_factor_verified = true WHERE id = $1', [sessionId]);
}
