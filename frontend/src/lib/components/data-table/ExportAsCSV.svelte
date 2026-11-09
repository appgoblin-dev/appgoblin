<script lang="ts">
	import { mkConfig, generateCsv, download } from 'export-to-csv';
	import type { Row } from '@tanstack/table-core';
	let { table, filename } = $props();

	const excludedFields = new Set(['company_logo_url', 'parent_company_logo_url']);

	const csvConfig = $derived(
		mkConfig({
			fieldSeparator: ',',
			filename,
			decimalSeparator: '.',
			useKeysAsHeaders: true
		})
	);

	function toCsvValue(value: unknown): string | number | boolean | null | undefined {
		if (
			value === null ||
			typeof value === 'string' ||
			typeof value === 'number' ||
			typeof value === 'boolean' ||
			typeof value === 'undefined'
		) {
			return value;
		}
		if (typeof value !== 'object') {
			return String(value);
		}
		return JSON.stringify(value) ?? String(value);
	}

	const exportDataCSV = (rows: Row<Record<string, unknown>, unknown>[]) => {
		const rowData = rows.map((row) =>
			Object.fromEntries(
				Object.entries(row.original)
					.filter(([key]) => !excludedFields.has(key))
					.map(([key, value]) => [key, toCsvValue(value)])
			)
		);
		const csv = generateCsv(csvConfig)(rowData);
		download(csvConfig)(csv);
	};
</script>

<button
	type="button"
	class="btn preset-outlined-primary-100-900"
	onclick={() => exportDataCSV(table.getFilteredRowModel().rows)}
>
	Download CSV
</button>
