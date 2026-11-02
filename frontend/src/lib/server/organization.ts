import { createHash, randomBytes } from 'node:crypto';
import { db } from '#lib/server/auth/db.js';

export const DEFAULT_ORGANIZATION_SEATS = 3;
export type OrganizationRole = 'owner' | 'member';

export interface OrganizationMembership {
	organizationId: number;
	organizationName: string;
	organizationSlug: string;
	userId: number;
	role: OrganizationRole;
}

export interface OrganizationMember {
	userId: number;
	email: string;
	username: string;
	role: OrganizationRole;
	createdAt: Date;
}

export interface OrganizationInvitation {
	id: number;
	email: string;
	expiresAt: Date;
	createdAt: Date;
}

export function normalizeInvitationEmail(email: string): string {
	return email.trim().toLowerCase();
}

export function createInvitationToken(): { token: string; tokenHash: string } {
	const token = randomBytes(32).toString('base64url');
	return { token, tokenHash: hashInvitationToken(token) };
}

export function hashInvitationToken(token: string): string {
	return createHash('sha256').update(token).digest('hex');
}

export async function getOrganizationInvitation(
	token: string,
	email: string
): Promise<{ id: number } | null> {
	return db.queryOne<{ id: number }>(
		`SELECT id
		 FROM organization_invitations
		 WHERE token_hash = $1
		   AND lower(email) = $2
		   AND accepted_at IS NULL
		   AND revoked_at IS NULL
		   AND expires_at > NOW()`,
		[hashInvitationToken(token), normalizeInvitationEmail(email)]
	);
}

export async function acceptOrganizationInvitation(
	invitationId: number,
	userId: number
): Promise<void> {
	await db.transaction(async (client) => {
		const invitation = await client.query<{ organization_id: number }>(
			`SELECT organization_id
			 FROM organization_invitations
			 WHERE id = $1
			   AND accepted_at IS NULL
			   AND revoked_at IS NULL
			   AND expires_at > NOW()
			 FOR UPDATE`,
			[invitationId]
		);
		const row = invitation.rows[0];
		if (!row) throw new Error('Invitation is no longer active.');

		await client.query(
			`INSERT INTO organization_members (organization_id, user_id, role)
			 VALUES ($1, $2, 'member')
			 ON CONFLICT (organization_id, user_id) DO NOTHING`,
			[row.organization_id, userId]
		);
		await client.query(
			`UPDATE organization_invitations
			 SET accepted_at = NOW(), accepted_by_user_id = $1
			 WHERE id = $2`,
			[userId, invitationId]
		);
	});
}

export async function createPersonalOrganization(
	userId: number,
	name: string
): Promise<OrganizationMembership> {
	return db.transaction(async (client) => {
		const organization = await client.query<{ id: number; name: string; slug: string }>(
			`INSERT INTO organizations (name, slug)
			 VALUES ($1, 'account-' || $2 || '-' || floor(extract(epoch from clock_timestamp()) * 1000)::bigint)
			 RETURNING id, name, slug`,
			[name, userId]
		);
		const row = organization.rows[0];
		if (!row) throw new Error('Failed to create organization');

		await client.query(
			`INSERT INTO organization_members (organization_id, user_id, role)
			 VALUES ($1, $2, 'owner')`,
			[row.id, userId]
		);

		return {
			organizationId: row.id,
			organizationName: row.name,
			organizationSlug: row.slug,
			userId,
			role: 'owner'
		};
	});
}

export async function getUserOrganization(userId: number): Promise<OrganizationMembership | null> {
	return db.queryOne<OrganizationMembership>(
		`SELECT om.organization_id AS "organizationId",
		        o.name AS "organizationName", o.slug AS "organizationSlug",
		        om.user_id AS "userId", om.role
		 FROM organization_members om
		 JOIN organizations o ON o.id = om.organization_id
		 WHERE om.user_id = $1
		 ORDER BY om.created_at ASC, om.id ASC
		 LIMIT 1`,
		[userId]
	);
}

export async function getOrganizationMembers(
	organizationId: number
): Promise<OrganizationMember[]> {
	return db.query<OrganizationMember>(
		`SELECT u.id AS "userId", u.email, u.username, om.role,
		        om.created_at AS "createdAt"
		 FROM organization_members om
		 JOIN users u ON u.id = om.user_id
		 WHERE om.organization_id = $1
		 ORDER BY CASE WHEN om.role = 'owner' THEN 0 ELSE 1 END, om.created_at ASC`,
		[organizationId]
	);
}

export async function getOrganizationSeatSummary(organizationId: number) {
	return db.queryOne<{ seatsTotal: number; seatsUsed: number; includedSeats: number }>(
		`SELECT COALESCE(MAX(s.seats_total), ${DEFAULT_ORGANIZATION_SEATS})::int AS "seatsTotal",
		        CASE WHEN BOOL_OR(t.slug = 'b2b_premium') THEN 10 ELSE 3 END::int AS "includedSeats",
		        COUNT(om.id)::int AS "seatsUsed"
		 FROM organizations o
		 LEFT JOIN subscriptions s
		   ON s.organization_id = o.id
		  AND s.status IN ('active', 'trialing')
		  AND (s.cancel_at IS NULL OR s.cancel_at > NOW())
		 LEFT JOIN tier_prices tp ON tp.id = s.tier_price_id
		 LEFT JOIN tiers t ON t.id = tp.tier_id
		 LEFT JOIN organization_members om ON om.organization_id = o.id
		 WHERE o.id = $1
		 GROUP BY o.id`,
		[organizationId]
	);
}

export async function getActiveOrganizationInvitations(
	organizationId: number
): Promise<OrganizationInvitation[]> {
	return db.query<OrganizationInvitation>(
		`SELECT id, email,
		        expires_at AS "expiresAt", created_at AS "createdAt"
		 FROM organization_invitations
		 WHERE organization_id = $1
		   AND accepted_at IS NULL
		   AND revoked_at IS NULL
		   AND expires_at > NOW()
		 ORDER BY created_at DESC`,
		[organizationId]
	);
}

export async function isOrganizationOwner(
	userId: number,
	organizationId: number
): Promise<boolean> {
	const row = await db.queryOne<{ exists: boolean }>(
		`SELECT EXISTS (
			SELECT 1 FROM organization_members
			WHERE user_id = $1 AND organization_id = $2 AND role = 'owner'
		) AS exists`,
		[userId, organizationId]
	);
	return row?.exists ?? false;
}

export async function updateOrganizationName(
	organizationId: number,
	ownerUserId: number,
	name: string
): Promise<void> {
	const trimmedName = name.trim();
	if (trimmedName.length < 2 || trimmedName.length > 120) {
		throw new Error('Organization name must be between 2 and 120 characters.');
	}

	const result = await db.execute(
		`UPDATE organizations o
         SET name = $1, updated_at = NOW()
         WHERE o.id = $2
           AND EXISTS (
               SELECT 1 FROM organization_members om
               WHERE om.organization_id = o.id
                 AND om.user_id = $3
                 AND om.role = 'owner'
           )`,
		[trimmedName, organizationId, ownerUserId]
	);
	if (result.changes === 0) throw new Error('Only the organization owner can rename it.');
}

export async function createOrganizationInvitation(
	organizationId: number,
	invitedByUserId: number,
	email: string
): Promise<{ token: string; expiresAt: Date }> {
	const normalizedEmail = normalizeInvitationEmail(email);
	const membership = await db.queryOne<{ role: OrganizationRole }>(
		`SELECT role FROM organization_members WHERE organization_id = $1 AND user_id = $2`,
		[organizationId, invitedByUserId]
	);
	if (membership?.role !== 'owner') throw new Error('Only organization owners can invite members');

	const seats = await getOrganizationSeatSummary(organizationId);
	if (!seats || seats.seatsUsed >= seats.seatsTotal)
		throw new Error('No organization seats available');

	const existing = await db.queryOne<{ id: number }>(
		`SELECT om.id FROM organization_members om JOIN users u ON u.id = om.user_id
		 WHERE om.organization_id = $1 AND lower(u.email) = $2`,
		[organizationId, normalizedEmail]
	);
	if (existing) throw new Error('User is already a member of this organization');
	const pending = await db.queryOne<{ id: number }>(
		`SELECT id FROM organization_invitations
		 WHERE organization_id = $1 AND lower(email) = $2
		   AND accepted_at IS NULL AND revoked_at IS NULL AND expires_at > NOW()`,
		[organizationId, normalizedEmail]
	);
	if (pending) throw new Error('An active invitation already exists for this email');

	const { token, tokenHash } = createInvitationToken();
	const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);
	await db.execute(
		`INSERT INTO organization_invitations
		 (organization_id, email, token_hash, invited_by_user_id, expires_at)
		 VALUES ($1, $2, $3, $4, $5)`,
		[organizationId, normalizedEmail, tokenHash, invitedByUserId, expiresAt]
	);
	return { token, expiresAt };
}

export async function revokeOrganizationInvitation(
	organizationId: number,
	ownerUserId: number,
	invitationId: number
): Promise<void> {
	const result = await db.execute(
		`UPDATE organization_invitations oi
		 SET revoked_at = NOW()
		 WHERE oi.id = $1
		   AND oi.organization_id = $2
		   AND oi.accepted_at IS NULL
		   AND oi.revoked_at IS NULL
		   AND EXISTS (
		       SELECT 1 FROM organization_members om
		       WHERE om.organization_id = oi.organization_id
		         AND om.user_id = $3
		         AND om.role = 'owner'
		   )`,
		[invitationId, organizationId, ownerUserId]
	);
	if (result.changes === 0) throw new Error('Invitation is no longer active.');
}

export async function getOrganizationSubscriptionAccess(userId: number) {
	return db.queryOne<{
		id: number;
		status: string;
		tier_slug: string | null;
		provider_name: string | null;
	}>(
		`SELECT s.id, s.status, t.slug AS tier_slug, tp.provider_name
		 FROM organization_members om
		 JOIN subscriptions s ON s.organization_id = om.organization_id
		 LEFT JOIN tier_prices tp ON tp.id = s.tier_price_id
		 LEFT JOIN tiers t ON t.id = tp.tier_id
		 WHERE om.user_id = $1
		   AND s.status IN ('active', 'trialing')
		   AND (s.cancel_at IS NULL OR s.cancel_at > NOW())
		 ORDER BY s.updated_at DESC
		 LIMIT 1`,
		[userId]
	);
}
