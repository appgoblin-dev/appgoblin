<script lang="ts">
	import {
		type PaginationState,
		type SortingState,
		getCoreRowModel,
		getPaginationRowModel,
		getSortedRowModel
	} from '@tanstack/table-core';

	import Pagination from '$lib/components/data-table/Pagination.svelte';
	import ExportAsCSV from '$lib/components/data-table/ExportAsCSV.svelte';

	import { createSvelteTable, FlexRender } from '$lib/components/data-table/index.js';
	import type { KeywordScore } from '../types';

	import { genericColumns } from '$lib/components/data-table/generic-column';

	type DataTableProps = {
		data: KeywordScore[];
		storeId?: string;
		linkMode?: 'app' | 'global';
	};

	let pagination = $state<PaginationState>({ pageIndex: 0, pageSize: 25 });
	let sorting = $state<SortingState>([]);

	let { data, storeId, linkMode = 'app' }: DataTableProps = $props();

	const formatScore = (value: number | string | null | undefined, digits = 0) => {
		if (value === null || value === undefined || value === '' || value === 'NA') {
			return '—';
		}

		const numericValue = typeof value === 'string' ? Number(value) : value;

		if (Number.isNaN(numericValue)) {
			return String(value);
		}

		return numericValue.toLocaleString(undefined, {
			minimumFractionDigits: digits,
			maximumFractionDigits: digits
		});
	};

	const formatRank = (value: number | string | null | undefined) => {
		if (value === null || value === undefined || value === '' || value === 'NA') {
			return '—';
		}

		if (typeof value === 'string') {
			const numeric = Number(value);
			if (!Number.isNaN(numeric)) {
				return numeric.toLocaleString();
			}
			return value;
		}

		return value.toLocaleString();
	};

	const columns = genericColumns([
		{ title: 'Keyword', accessorKey: 'keyword_text', isSortable: true },
		{
			title: 'Action',
			accessorKey: 'keyword_action',
			isSortable: false
		},
		{
			title: 'Opportunity',
			accessorKey: 'opportunity_score',
			isSortable: true
		},
		{
			title: 'Volume Score',
			accessorKey: 'volume_competition_score',
			isSortable: true
		},
		{
			title: 'Difficulty',
			accessorKey: 'keyword_difficulty',
			isSortable: true
		},
		{
			title: 'Competitiveness',
			accessorKey: 'competitiveness_score',
			isSortable: true
		},
		{
			title: 'Latest Rank',
			accessorKey: 'latest_app_rank',
			isSortable: true
		},
		{
			title: '30 Day Best',
			accessorKey: 'd30_best_rank',
			isSortable: true
		},
		{
			title: 'Major Competitors',
			accessorKey: 'major_competitors',
			isSortable: false
		}
	]);

	const table = createSvelteTable({
		get data() {
			return data;
		},
		columns,
		state: {
			get pagination() {
				return pagination;
			},
			get sorting() {
				return sorting;
			}
		},

		getSortedRowModel: getSortedRowModel(),
		onSortingChange: (updater) => {
			if (typeof updater === 'function') {
				sorting = updater(sorting);
			} else {
				sorting = updater;
			}
		},

		onPaginationChange: (updater) => {
			if (typeof updater === 'function') {
				pagination = updater(pagination);
			} else {
				pagination = updater;
			}
		},
		getCoreRowModel: getCoreRowModel(),
		getPaginationRowModel: getPaginationRowModel()
	});
</script>

<div class="space-y-4">
	<div class="overflow-x-auto rounded-lg border border-surface-300-700">
		<table class="w-full min-w-[720px] text-xs md:text-lg">
			<thead class="bg-surface-200-800">
				{#each table.getHeaderGroups() as headerGroup (headerGroup.id)}
					<tr>
						{#each headerGroup.headers as header (header.id)}
							<th class="px-4 py-3 text-left text-xs font-semibold md:tracking-wide">
								{#if !header.isPlaceholder}
									<FlexRender
										content={header.column.columnDef.header}
										context={header.getContext()}
									/>
								{/if}
							</th>
						{/each}
					</tr>
				{/each}
			</thead>
			<tbody>
				{#each table.getRowModel().rows as row, index (`${row.id}-${index}`)}
					<tr class="border-t border-surface-200-800 hover:bg-surface-100-900/70">
						<td class="px-4 py-3 align-top text-xs md:text-lg">
							{row.original.keyword_text}
						</td>
						<td class="px-4 py-3 align-top text-xs md:text-sm">
							{#if linkMode === 'global'}
								<a
									class="btn btn-sm preset-tonal"
									href={`/keywords/en/${encodeURIComponent(row.original.keyword_text)}`}
								>
									View Keyword Global Page
								</a>
								<p class="mt-1 text-xs -200">Leaves this app dashboard</p>
							{:else if storeId}
								<div class="grid grid-cols-1 space-y-1">
									<a
										class="btn btn-sm preset-tonal"
										href={`/apps/${storeId}/keywords/compare?k=${encodeURIComponent(row.original.keyword_text)}`}
									>
										View App's Keyword History
									</a>
									<a
										class="btn btn-sm preset-tonal"
										href={`/keywords/en/${encodeURIComponent(row.original.keyword_text)}`}
									>
										View Keyword Global Page
									</a>
								</div>
							{/if}
						</td>
						<td class="px-4 py-3 align-top text-sm md:text-lg">
							{formatScore(row.original.opportunity_score)}
						</td>
						<td class="px-4 py-3 align-top text-sm md:text-lg">
							{formatScore(row.original.volume_competition_score)}
						</td>
						<td class="px-4 py-3 align-top text-sm md:text-lg">
							{formatScore(row.original.keyword_difficulty)}
						</td>
						<td class="px-4 py-3 align-top text-sm md:text-lg">
							{formatScore(row.original.competitiveness_score)}
							<p class="text-xs -200 mt-1">
								{row.original.app_count?.toLocaleString()} competing apps
							</p>
							{#if row.original.median_competitor_installs}
								<p class="mt-1 text-xs -200">
									Median installs: {formatScore(row.original.median_competitor_installs, 0)}
								</p>
							{/if}
							{#if row.original.avg_competitor_rating}
								<p class="text-xs -200">
									Avg rating: {formatScore(row.original.avg_competitor_rating, 1)}
								</p>
							{/if}
						</td>
						<td class="px-4 py-3 align-top text-sm md:text-lg">
							{formatRank(row.original.latest_app_rank)}
						</td>
						<td class="px-4 py-3 align-top text-sm md:text-lg">
							{formatRank(row.original.d30_best_rank)}
						</td>
						<td class="px-4 py-3 align-top">
							<div class="space-y-1">
								<p class="font-medium">{formatScore(row.original.major_competitors, 0)}</p>
								<p class="text-xs -200">major competitor apps</p>
							</div>
						</td>
					</tr>
				{:else}
					<tr>
						<td colspan={columns.length} class="h-24 px-4 text-center text-secondary-400-600">
							No results.
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
	<footer class="flex items-center justify-end gap-3">
		<div class="flex items-center gap-3">
			<div class="text-xs text-primary-700-300">
				{table.getPrePaginationRowModel().rows.length.toLocaleString()} keywords
			</div>
			<div class="flex items-center gap-2">
				<Pagination tableModel={table} />
				<ExportAsCSV {table} filename="appgoblin_data" />
			</div>
		</div>
	</footer>
</div>
