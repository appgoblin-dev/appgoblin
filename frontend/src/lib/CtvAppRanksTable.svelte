<script lang="ts">
	import type { ColumnFiltersState, Row, SortingState } from '@tanstack/svelte-table';
	import { resolve } from '$app/paths';

	import Pagination from '#lib/components/data-table/Pagination.svelte';
	import ExportAsCSV from '#lib/components/data-table/ExportAsCSV.svelte';
	import type { CtvAppRank } from '../types';

	import {
		createAppTable,
		createTableState,
		FlexRender
	} from '#lib/components/data-table/index.js';

	import { genericColumns } from '#lib/components/data-table/generic-column.js';
	import type { FullFeatures } from '#lib/components/data-table/features.js';

	import { formatNumber, getRevenueBucket } from '#lib/utils/formatNumber.js';
	import { prettyName } from '#lib/utils/prettyNames.js';
	import ZScoreMeter from '#lib/components/ZScoreMeter.svelte';

	type DataTableProps = {
		data: CtvAppRank[];
	};

	const [pagination, onPaginationChange] = createTableState({ pageIndex: 0, pageSize: 50 });
	const [sorting, onSortingChange] = createTableState<SortingState>([]);
	const [columnFilters, onColumnFiltersChange] = createTableState<ColumnFiltersState>([]);
	const [globalFilter, onGlobalFilterChange] = createTableState('');

	let { data }: DataTableProps = $props();

	const myColumns = [
		{ title: 'Rank', accessorKey: 'rank_num', isSortable: true },
		{ title: 'App', accessorKey: 'app_name', isSortable: true },
		{ title: 'Category', accessorKey: 'app_category', isSortable: true },
		{ title: 'Total Installs', accessorKey: 'installs', isSortable: true },
		{ title: 'Monthly Installs', accessorKey: 'monthly_installs', isSortable: true },
		{ title: 'Monthly Revenue', accessorKey: 'monthly_revenue', isSortable: true },
		{ title: 'Installs Growth Score (14d)', accessorKey: 'installs_z_score_2w', isSortable: true },
		{ title: 'Total Ratings', accessorKey: 'rating_count', isSortable: true }
	];

	const columns = genericColumns(myColumns);

	// CTV z-scores span roughly -1.2 to 3.7, far below the growth table's 0-1000
	// range, so use a z-score scale instead of the growth page's meter bounds.
	const Z_SCORE_MAX = 5;

	const globalFilterFn = (
		row: Row<FullFeatures, Record<string, unknown>>,
		columnId: string,
		filterValue: string
	) => {
		const app = row.original as unknown as CtvAppRank;
		const name = app.app_name?.toLowerCase() ?? '';
		const developer = app.developer_name?.toLowerCase() ?? '';
		const query = filterValue.toLowerCase();
		return name.includes(query) || developer.includes(query);
	};

	const table = createAppTable({
		get data() {
			return data;
		},
		columns,
		state: {
			get pagination() {
				return pagination();
			},
			get sorting() {
				return sorting();
			},
			get columnFilters() {
				return columnFilters();
			},
			get globalFilter() {
				return globalFilter();
			}
		},
		globalFilterFn,
		onSortingChange,
		onColumnFiltersChange,
		onPaginationChange,
		onGlobalFilterChange
	});
</script>

<div class="table-container p-0 md:p-2">
	<div class="flex items-center p-2">
		<input
			placeholder="Filter apps..."
			value={globalFilter()}
			oninput={(e) => {
				const value = e.currentTarget.value;
				table.setGlobalFilter(value);
			}}
			class="bg-surface-50-950 max-w-sm p-1"
		/>
	</div>
	<div class="overflow-x-auto pl-0">
		<table class="md:table table-hover md:table-compact table-auto w-full">
			<thead>
				{#each table.getHeaderGroups() as headerGroup (headerGroup.id)}
					<tr>
						{#each headerGroup.headers as header (header.id)}
							<th>
								{#if !header.isPlaceholder}
									<FlexRender {header} />
								{/if}
							</th>
						{/each}
					</tr>
				{/each}
			</thead>
			<tbody>
				{#each table.getRowModel().rows as row (row.id)}
					<tr class="px-0 hover:bg-surface-100-900">
						{#each row.getVisibleCells() as cell (cell.id)}
							<td class="p-2">
								{#if cell.column.id == 'app_name'}
									<a
										href={resolve('/apps/[id]', { id: row.original.store_id })}
										style="cursor: pointer;"
										class="block max-w-[170px] md:max-w-[260px] text-xs md:text-sm font-medium text-blue-600 hover:text-blue-800"
									>
										<div class="flex items-center gap-2">
											{#if row.original.app_icon_url}
												<img
													src={row.original.app_icon_url}
													alt={row.original.app_name}
													class="w-8 h-8 shrink-0 rounded"
													loading="lazy"
												/>
											{/if}
											<div class="flex flex-col min-w-0 max-w-[120px] md:max-w-[210px]">
												<span class="text-xs md:text-sm truncate" title={row.original.app_name}
													>{row.original.app_name}</span
												>
												<span
													class="text-[10px] md:text-xs text-surface-500 truncate"
													title={row.original.developer_name ?? ''}
													>{row.original.developer_name ?? ''}</span
												>
											</div>
										</div>
									</a>
								{:else if cell.column.id == 'app_category'}
									<p class="text-xs md:text-sm">
										{cell.getValue() ? prettyName(cell.getValue() as string) : '-'}
									</p>
								{:else if cell.column.id == 'installs_z_score_2w'}
									<ZScoreMeter
										value={(cell.getValue() as number) ?? 0}
										min={0}
										max={Z_SCORE_MAX}
										size="sm"
									/>
								{:else if ['installs', 'monthly_installs', 'rating_count'].includes(cell.column.id)}
									<p class="text-xs md:text-sm">
										{#if Number(cell.getValue() ?? 0) <= 0}
											-
										{:else}
											{formatNumber(Number(cell.getValue()))}
										{/if}
									</p>
								{:else if cell.column.id == 'monthly_revenue'}
									<p class="text-xs md:text-sm">
										{#if Number(cell.getValue() ?? 0) <= 0}
											-
										{:else}
											{getRevenueBucket(Number(cell.getValue()))}
										{/if}
									</p>
								{:else}
									<p class="text-xs md:text-sm">
										{cell.getValue() ?? '-'}
									</p>
								{/if}
							</td>
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
		<footer class="flex justify-between">
			<div class="flex items-center justify-end space-x-2 py-4">
				<Pagination tableModel={table} />
				<ExportAsCSV {table} filename="appgoblin_ctv_app_ranks" />
			</div>
		</footer>
	</div>
</div>
