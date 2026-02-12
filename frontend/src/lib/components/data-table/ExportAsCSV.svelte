<script lang="ts">
	import { mkConfig, generateCsv, download } from 'export-to-csv';
	import type { Row } from '@tanstack/table-core';
	let { table, filename } = $props();

	const csvConfig = $derived(
		mkConfig({
			fieldSeparator: ',',
			filename,
			decimalSeparator: '.',
			useKeysAsHeaders: true
		})
	);

	const exportDataCSV = (rows: Row<any>[]) => {
		const rowData = rows.map((row) => row.original);
		const csv = generateCsv(csvConfig)(rowData);
		download(csvConfig)(csv);
	};
</script>

<button
	type="button"
	class="btn btn-sm preset-outlined-primary-100-900 p-0"
	onclick={() => exportDataCSV(table.getFilteredRowModel().rows)}
>
	Download CSV
</button>
