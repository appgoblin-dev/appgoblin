<script lang="ts">
	import FileText from '@lucide/svelte/icons/file-text';
	import Download from '@lucide/svelte/icons/download';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	function formatReportDate(date: string): string {
		return new Date(date).toLocaleString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: 'numeric',
			minute: '2-digit'
		});
	}

	function formatRowCount(rowCount: number | null): string {
		if (rowCount === null) return 'Row count unavailable';
		return `${rowCount.toLocaleString('en-US')} ${rowCount === 1 ? 'row' : 'rows'}`;
	}
</script>

<svelte:head>
	<title>Generated Reports - AppGoblin</title>
	<meta name="description" content="Download your generated AppGoblin reports." />
</svelte:head>

<div class="p-6 md:p-8 space-y-8">
	<div class="flex items-start justify-between gap-3">
		<div>
			<h1 class="text-2xl font-bold">Generated Reports</h1>
			<p class="mt-2 text-sm">Download your recent reports.</p>
		</div>
		<FileText size={28} class="text-primary-500" />
	</div>

	{#if data.generatedReports.length === 0}
		<div class="rounded-lg border border-surface-300-700 p-6 text-sm text-surface-500">
			No reports generated yet. Reports can be created from the App Explorer and SDK detail pages.
		</div>
	{:else}
		<div class="divide-y divide-surface-300-700 rounded-lg border border-surface-300-700">
			{#each data.generatedReports as report}
				<div class="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
					<div class="min-w-0">
						<p class="truncate font-semibold">{report.reportName}</p>
						<p class="mt-1 text-xs text-surface-500">
							Created {formatReportDate(report.createdAt)} · {formatRowCount(report.rowCount)}
						</p>
					</div>
					<a
						href={report.url}
						class="btn btn-sm preset-tonal flex items-center justify-center gap-2 sm:shrink-0"
						download
					>
						<Download size={16} />
						Download CSV
					</a>
				</div>
			{/each}
		</div>
	{/if}
</div>
