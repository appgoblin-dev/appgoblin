import { fail, redirect } from '@sveltejs/kit';
import { requireFullAuth } from '#lib/server/auth/auth.js';
import { db } from '#lib/server/auth/db.js';
import {
	createOrganizationInvitation,
	getActiveOrganizationInvitations,
	getOrganizationMembers,
	getOrganizationSeatSummary,
	getUserOrganization,
	isOrganizationOwner,
	revokeOrganizationInvitation,
	updateOrganizationName
} from '#lib/server/organization.js';
import { sendOrganizationInvitationEmail } from '#lib/server/contact.js';
import { createPortalSession } from '#lib/server/stripe.js';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async (event) => {
	const { user } = requireFullAuth(event);
	const organization = await getUserOrganization(user.id);
	if (!organization) return { organization: null, members: [], seats: null, invitations: [] };

	const paidSubscription = await db.queryOne<{ id: number }>(
		`SELECT s.id
		 FROM subscriptions s
		 JOIN tier_prices tp ON tp.id = s.tier_price_id
		 WHERE s.organization_id = $1
		   AND tp.provider_name = 'stripe'
		   AND (
		     (s.cancel_at IS NOT NULL AND s.cancel_at > NOW())
		     OR (s.cancel_at IS NULL AND s.status IN ('active', 'trialing'))
		   )
		 LIMIT 1`,
		[organization.organizationId]
	);
	if (!paidSubscription) {
		return { organization, members: [], seats: null, invitations: [], paid: false };
	}

	const [members, seats, invitations] = await Promise.all([
		getOrganizationMembers(organization.organizationId),
		getOrganizationSeatSummary(organization.organizationId),
		getActiveOrganizationInvitations(organization.organizationId)
	]);
	return { organization, members, seats, invitations, paid: true };
};

export const actions: Actions = {
	portal: async (event) => {
		const { user } = requireFullAuth(event);
		const organization = await getUserOrganization(user.id);
		if (!organization || !(await isOrganizationOwner(user.id, organization.organizationId))) {
			return fail(403, { message: 'Only the organization owner can manage the subscription.' });
		}

		try {
			const url = await createPortalSession(user.id);
			if (!url) return fail(500, { message: 'Failed to create portal session' });
			return redirect(303, url, { external: true });
		} catch (error) {
			console.error('Failed to create Stripe portal session', error);
			return fail(500, { message: 'Unable to open Stripe billing.' });
		}
	},
	rename: async (event) => {
		const { user } = requireFullAuth(event);
		const organization = await getUserOrganization(user.id);
		if (!organization || !(await isOrganizationOwner(user.id, organization.organizationId))) {
			return fail(403, { message: 'Only the organization owner can rename it.' });
		}

		const formData = await event.request.formData();
		const name = formData.get('name');
		if (typeof name !== 'string') return fail(400, { message: 'Enter an organization name.' });

		try {
			await updateOrganizationName(organization.organizationId, user.id, name);
			return { renameSuccess: true };
		} catch (error) {
			return fail(400, {
				message: error instanceof Error ? error.message : 'Unable to update organization name.'
			});
		}
	},
	invite: async (event) => {
		const { user } = requireFullAuth(event);
		const organization = await getUserOrganization(user.id);
		if (!organization || !(await isOrganizationOwner(user.id, organization.organizationId))) {
			return fail(403, { message: 'Only the organization owner can invite members.' });
		}

		const formData = await event.request.formData();
		const email = formData.get('email');
		if (typeof email !== 'string' || !email.includes('@')) {
			return fail(400, { message: 'Enter a valid email address.' });
		}

		try {
			const invitation = await createOrganizationInvitation(
				organization.organizationId,
				user.id,
				email
			);
			await sendOrganizationInvitationEmail(
				email.trim().toLowerCase(),
				organization.organizationName,
				invitation.token
			);
			console.info('Organization invitation created', {
				organizationId: organization.organizationId,
				email,
				expiresAt: invitation.expiresAt
			});
			return { success: true };
		} catch (error) {
			console.error('Failed to create organization invitation', error);
			return fail(400, {
				message: error instanceof Error ? error.message : 'Unable to create invitation.'
			});
		}
	},
	revokeInvitation: async (event) => {
		const { user } = requireFullAuth(event);
		const organization = await getUserOrganization(user.id);
		if (!organization || !(await isOrganizationOwner(user.id, organization.organizationId))) {
			return fail(403, { message: 'Only the organization owner can remove invitations.' });
		}

		const formData = await event.request.formData();
		const invitationId = Number(formData.get('invitationId'));
		if (!Number.isInteger(invitationId) || invitationId < 1) {
			return fail(400, { message: 'Invalid invitation.' });
		}

		try {
			await revokeOrganizationInvitation(organization.organizationId, user.id, invitationId);
			return { revokeSuccess: true };
		} catch (error) {
			return fail(400, {
				message: error instanceof Error ? error.message : 'Unable to remove invitation.'
			});
		}
	}
};
