import { redirectIfAuthenticated, isSafeRedirect } from '#lib/server/auth/auth.js';
import { handleSignup } from '#lib/server/auth/signup.js';
import {
	acceptOrganizationInvitation,
	getOrganizationInvitation
} from '#lib/server/organization.js';
import type { Actions, PageServerLoadEvent } from './$types';

export const ssr = true;
export const csr = true;

export async function load(event: PageServerLoadEvent) {
	const invitationToken = event.url.searchParams.get('token') ?? '';

	// A signed-in user does not need to sign up; accept the invitation for their
	// account (when it matches their email) and send them to their account page.
	if (event.locals.session !== null && event.locals.user !== null) {
		if (invitationToken) {
			const invitation = await getOrganizationInvitation(invitationToken, event.locals.user.email);
			if (invitation) {
				try {
					await acceptOrganizationInvitation(invitation.id, event.locals.user.id);
				} catch (error) {
					console.error('Failed to accept organization invitation for signed-in user', error);
				}
			}
		}
		redirectIfAuthenticated(event, '/account', '/account');
	}

	const requestedRedirect = event.url.searchParams.get('redirectTo') ?? '/account';
	return {
		redirectTo: isSafeRedirect(requestedRedirect) ? requestedRedirect : '/account',
		invitationToken
	};
}

export const actions: Actions = {
	default: handleSignup
};
