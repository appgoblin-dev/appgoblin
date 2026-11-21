import { db } from '#lib/server/auth/db.js';
import { sendMappingRequestEmail } from '#lib/server/contact.js';
import type { RequestHandler } from './$types';

type MappingType = 'company_domain_name' | 'app_sdk';

type MappingRequest = {
	mapType: MappingType;
	valueToBeMapped: string;
	additionalInfo?: { store_id?: string };
};

function badRequest(error: string) {
	return Response.json({ success: false, error }, { status: 400 });
}

export const POST: RequestHandler = async ({ request, locals }) => {
	if (!locals.user) {
		return Response.json({ success: false, error: 'Authentication required' }, { status: 401 });
	}

	const body = (await request.json()) as MappingRequest;
	const valueToBeMapped = body.valueToBeMapped?.trim();

	if (!body.mapType || !valueToBeMapped) {
		return badRequest('mapType and valueToBeMapped are required');
	}

	if (body.mapType !== 'company_domain_name' && body.mapType !== 'app_sdk') {
		return badRequest('Unsupported mapping type');
	}

	let additionalInfo: { store_id: string } | null = null;
	if (body.mapType === 'app_sdk' && body.additionalInfo != null) {
		const storeId = body.additionalInfo.store_id?.trim();
		if (!storeId) {
			return badRequest('store_id is required when additional info is provided');
		}
		additionalInfo = { store_id: storeId };
	}

	await db.execute(
		`INSERT INTO public.user_requested_mapping
			(user_id, map_type, value_to_be_mapped, additional_info)
		 VALUES ($1, $2, $3, $4)`,
		[locals.user.id, body.mapType, valueToBeMapped, additionalInfo]
	);

	void sendMappingRequestEmail(
		locals.user.id,
		locals.user.email,
		locals.user.username,
		body.mapType,
		valueToBeMapped,
		additionalInfo
	).catch((error) => {
		console.error('Failed to send mapping request notification:', error);
	});

	return Response.json({ success: true });
};
