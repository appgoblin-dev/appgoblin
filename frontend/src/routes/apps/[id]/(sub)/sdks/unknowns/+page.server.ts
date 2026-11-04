import type { PageServerLoad } from './$types';
import { requireAuthOrMachinePayment } from '#lib/server/auth/auth.js';

export const load: PageServerLoad = async (event) => {
	requireAuthOrMachinePayment(event);
	const { myapp, companyTypes, myPackageInfo } = await event.parent();

	return {
		myPackageInfo,
		myapp,
		companyTypes,
		toFollow: 'noindex, nofollow',
		title: `Unmapped SDKs in ${myapp.name}`,
		description: `Unrecognized SDKs and trackers found in ${myapp.name}.`
	};
};
