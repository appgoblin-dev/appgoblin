import type { LayoutServerLoad } from '../$types';

import { getCachedData } from '../../hooks.server';

export const csr = false;

export const load: LayoutServerLoad = async () => {
	const cachedData = await getCachedData();
	const { companyTypes } = cachedData;
	return {
		companyTypes
	};
};
