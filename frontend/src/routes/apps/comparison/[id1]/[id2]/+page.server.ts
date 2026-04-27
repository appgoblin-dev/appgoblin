import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './';

export const load: PageServerLoad = () => {
	redirect(308, '/apps/comparison');
};
