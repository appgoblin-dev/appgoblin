import type { LayoutServerLoad } from './$types';

import { getCachedData } from '../../hooks.server';

export const load: LayoutServerLoad = async () => {
	const cachedData = await getCachedData();
	const { appCats, companyTypes, storeIDLookup, collectionIDLookup, categoryIDLookup } = cachedData;
	return {
		companyTypes,
		appCats,
		storeIDLookup,
		collectionIDLookup,
		categoryIDLookup,
		cacheTimestamp: new Date().toISOString()
	};
};
