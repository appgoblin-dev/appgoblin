import { requireAuthOr401 } from '$lib/server/auth/auth';
import { createApiClient } from '$lib/server/api';
import { db } from '$lib/server/auth/db';
import type { PageServerLoad } from './$types';

interface GeneratedReportRow {
	id: number;
	report_name: string;
	s3_key: string;
	row_count: number | null;
	created_at: Date;
}

export const load: PageServerLoad = async (event) => {
	const { user } = requireAuthOr401(event);
	const reports = await db.query<GeneratedReportRow>(
		`SELECT id, report_name, s3_key, row_count, created_at
		 FROM user_generated_reports
		 WHERE user_id = $1
		 ORDER BY created_at DESC
		 LIMIT 25`,
		[user.id]
	);
	const api = createApiClient(event.fetch);
	const generatedReports = await Promise.all(
		reports.map(async (report) => {
			const signed = await api.get(
				`/public/exports/user-report-signed-url?s3_key=${encodeURIComponent(report.s3_key)}`,
				'User Report Download'
			);
			return {
				id: report.id,
				reportName: report.report_name,
				rowCount: report.row_count,
				createdAt: report.created_at.toISOString(),
				url: signed.url as string
			};
		})
	);

	return { generatedReports };
};
