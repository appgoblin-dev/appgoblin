export interface QueryDatabase {
	query<T>(sql: string, params?: unknown[]): Promise<T[]>;
	execute(sql: string, params?: unknown[]): Promise<{ changes: number }>;
}

export interface RequestedScan {
	id: number;
	store_id: string;
	created_at: Date | null;
}

export function parsePositiveInteger(value: string | null, defaultValue?: number): number | null {
	if (value === null) return defaultValue ?? null;
	if (!/^[1-9]\d*$/.test(value)) return null;
	const number = Number(value);
	return Number.isSafeInteger(number) ? number : null;
}

export async function listRequestedScans(
	db: QueryDatabase,
	userId: number,
	page: number,
	pageSize: number
) {
	const offset = (page - 1) * pageSize;
	const rows = await db.query<RequestedScan>(
		`SELECT id, store_id, created_at
		 FROM public.user_requested_scan
		 WHERE user_id = $1
		 ORDER BY created_at DESC NULLS LAST, id DESC
		 LIMIT $2 OFFSET $3::bigint`,
		[userId, pageSize + 1, offset]
	);
	return {
		requestedSdkScans: rows.slice(0, pageSize).map((scan) => ({ ...scan, app_name: null })),
		pagination: { page, pageSize, hasNext: rows.length > pageSize }
	};
}

export async function findRequestedScan(db: QueryDatabase, userId: number, id: number) {
	const rows = await db.query<RequestedScan>(
		`SELECT id, store_id, created_at
		 FROM public.user_requested_scan
		 WHERE id = $1 AND user_id = $2`,
		[id, userId]
	);
	return rows[0] ?? null;
}

export function scanProgress(scan: RequestedScan) {
	return {
		id: scan.id,
		store_id: scan.store_id,
		requested_at: scan.created_at,
		stages: {
			request: {
				status: 'recorded',
				at: scan.created_at,
				note: 'The scan request was recorded.'
			},
			download: {
				status: 'unknown',
				at: null,
				note: 'Download activity cannot be linked without a request timestamp.'
			},
			sdk_scan: {
				status: 'unknown',
				at: null,
				note: 'SDK scan activity cannot be linked without a request timestamp.'
			},
			data_import: {
				status: 'unknown',
				at: null,
				note: 'Import progress cannot be estimated without a request timestamp.'
			},
			waydroid: {
				status: 'unknown',
				at: null,
				note: 'Emulation activity cannot be linked without a request timestamp.'
			}
		}
	};
}

export async function insertRequestedScan(db: QueryDatabase, userId: number, storeId: string) {
	await db.execute('INSERT INTO public.user_requested_scan (store_id, user_id) VALUES ($1, $2)', [
		storeId,
		userId
	]);
}
