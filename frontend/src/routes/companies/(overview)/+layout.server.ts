import type { LayoutServerLoad } from '../../$types';

import { getCachedData } from '../../../hooks.server';

export const csr = false;

export const load: LayoutServerLoad = async () => {
	const cachedData = await getCachedData();
	const { appCats, companyTypes, categoryIDLookup } = cachedData;
	return {
		companyTypes,
		appCats,
		categoryIDLookup,
		cacheTimestamp: new Date().toISOString()
	};
};
