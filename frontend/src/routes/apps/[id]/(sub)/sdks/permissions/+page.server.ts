import type { PageServerLoad } from './$types';
import { requireAuthOrMachinePayment } from '#lib/server/auth/auth.js';

export const load: PageServerLoad = async (event) => {
	requireAuthOrMachinePayment(event);
	const { myapp, myPackageInfo } = await event.parent();

	return {
		myPackageInfo,
		myapp,
		toFollow: 'noindex, nofollow',
		title: `Permissions in ${myapp.name}`,
		description: `Android permissions requested by ${myapp.name}.`
	};
};
