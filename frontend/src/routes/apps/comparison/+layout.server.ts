import type { LayoutServerLoad } from './$types';
import { requireAuthOrMachinePayment } from '#lib/server/auth/auth.js';

export const ssr: boolean = true;
export const csr: boolean = true;

export const load: LayoutServerLoad = async (event) => {
	requireAuthOrMachinePayment(event);
	return {};
};
