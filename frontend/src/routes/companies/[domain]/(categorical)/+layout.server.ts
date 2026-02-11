import type { LayoutServerLoad } from './$types';
import { getCachedData } from '../../../../hooks.server';

export const load: LayoutServerLoad = async () => {
	const { appCats } = await getCachedData();

	return {
		appCats
	};
};
