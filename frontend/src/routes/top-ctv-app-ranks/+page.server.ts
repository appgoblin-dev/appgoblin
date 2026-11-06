import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
	redirect(303, '/top-ctv-app-ranks/google');
};
