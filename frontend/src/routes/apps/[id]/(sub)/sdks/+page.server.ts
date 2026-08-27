import type { PageServerLoad } from './$types';
import { requireAuthOr401 } from '$lib/server/auth/auth';

export const load: PageServerLoad = async (event) => {
	requireAuthOr401(event);
	const { myapp, companyTypes, myPackageInfo } = await event.parent();

	return {
		myPackageInfo,
		companyTypes,
		myapp,
		// Meta Tags
		toFollow: 'noindex, nofollow',
		title: `SDKs and Trackers in ${myapp.name}`,
		description: `Explore the SDKs, trackers and permissions in ${myapp.name}. See which SDKs, trackers and permissions are used in ${myapp.name}.`,
		keywords: `SDKs, competitor analysis, trackers, permissions, ad networks, ad publishers, ad networks, ad publishers`
	};
};
