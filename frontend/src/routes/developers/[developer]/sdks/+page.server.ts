import type { PageServerLoad } from './$types';
import { requireAuthOrMachinePayment } from '#lib/server/auth/auth.js';
import { getCachedData } from '../../../../hooks.server';

export const ssr: boolean = true;
export const csr: boolean = true;

function checkStatus(resp: Response, name: string) {
	if (resp.status === 200 || resp.status === 201) {
		return resp.json();
	} else if (resp.status === 404) {
		console.log(`${name} Not found`);
		return `${name} Not Found`;
	} else if (resp.status === 500) {
		console.log(`${name} API Server error`);
		return `${name} API Server error`;
	} else {
		throw new Error('Unknown error');
	}
}

export const load: PageServerLoad = async (event) => {
	requireAuthOrMachinePayment(event);
	const { parent, fetch } = event;
	const { devs } = await parent();

	const google_store_ids = devs.google.apps.apps.map((app: any) => app.store_id);
	const apple_store_ids = devs.apple.apps.apps.map((app: any) => app.store_id);

	const store_ids = [...google_store_ids, ...apple_store_ids];

	console.log(`load started developerSDKs apps:${store_ids.length}`);

	let mySDKs = async () => 'No SDKs Result';
	mySDKs = async () => {
		const res = await fetch(`http://localhost:8000/api/developers/sdks`, {
			method: 'POST',
			body: JSON.stringify({ store_ids })
		});

		return checkStatus(res, 'Developer SDKs');
	};

	const { companyTypes } = await getCachedData();

	try {
		return {
			devSDKs: mySDKs(),
			companyTypes
		};
	} catch (error) {
		console.error('Failed to load data:', error);
		return {
			devs: {},
			status: 500,
			error: 'Failed to load trending apps'
		};
	}
};
