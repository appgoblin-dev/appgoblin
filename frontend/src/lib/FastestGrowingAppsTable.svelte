<script lang="ts" generics="TData, TValue">
	import {
		type PaginationState,
		type SortingState,
		type ColumnFiltersState,
		getCoreRowModel,
		getPaginationRowModel,
		getSortedRowModel,
		getFilteredRowModel
	} from '@tanstack/table-core';

	import { Popover, Portal } from '@skeletonlabs/skeleton-svelte';
	import Pagination from '$lib/components/data-table/Pagination.svelte';
	import ExportAsCSV from '$lib/components/data-table/ExportAsCSV.svelte';
	import type { CompaniesOverviewEntries } from '../types';

	import { createSvelteTable, FlexRender } from '$lib/components/data-table/index.js';

	import { genericColumns } from '$lib/components/data-table/generic-column';

	import { page } from '$app/state';

	import Check from 'lucide-svelte/icons/check';
	import X from 'lucide-svelte/icons/x';

	import { formatNumber } from '$lib/utils/formatNumber';
	import ZScoreMeter from '$lib/components/ZScoreMeter.svelte';

	type DataTableProps<CompaniesOverviewEntries, TValue> = {
		data: CompaniesOverviewEntries[];
	};

	let pagination = $state<PaginationState>({ pageIndex: 0, pageSize: 50 });
	let sorting = $state<SortingState>([]);
	let columnFilters = $state<ColumnFiltersState>([]);
	const ratingsHiddenDefaults = {
		rating_count: false,
		ratings_sum_1w: false,
		ratings_z_score_2w: false,
		ratings_z_score_4w: false
	};

	const installsHiddenDefaults = {
		installs: false,
		installs_sum_1w: false,
		installs_avg_2w: false,
		installs_z_score_2w: false,
		installs_sum_4w: false,
		installs_z_score_4w: false
	};

	function isGoogleStore(store: string) {
		return store === 'google';
	}

	function getHiddenDefaults(store: string) {
		if (isGoogleStore(store)) {
			return ratingsHiddenDefaults;
		} else {
			return installsHiddenDefaults;
		}
	}

	let globalFilter = $state<string>('');
	let dataSource = $state<string>('both');
	let columnVisibility = $state<Record<string, boolean>>(getHiddenDefaults(page.params.store!));

	// Update column visibility when store changes
	$effect(() => {
		columnVisibility = getHiddenDefaults(page.params.store!);
	});

	let { data }: DataTableProps<CompaniesOverviewEntries, TValue> = $props();

	const myColumns = [
		{
			title: 'App',
			accessorKey: 'app_name',
			isSortable: true
		},
		{
			title: 'Total Installs',
			accessorKey: 'installs',
			isSortable: true
		},
		{
			title: 'Total Ratings',
			accessorKey: 'rating_count',
			isSortable: true
		},
		// Weekly growth metrics
		{
			title: 'Installs (7d)',
			accessorKey: 'installs_sum_1w',
			isSortable: true
		},
		{
			title: 'Ratings (7d)',
			accessorKey: 'ratings_sum_1w',
			isSortable: true
		},
		// 2-Week growth metrics
		{
			title: 'Installs (14d)',
			accessorKey: 'installs_avg_2w',
			isSortable: true
		},
		{
			title: 'Ratings Avg (14d)',
			accessorKey: 'ratings_avg_2w',
			isSortable: true
		},
		{
			title: 'Installs Growth Score (14d)',
			accessorKey: 'installs_z_score_2w',
			isSortable: true
		},
		{
			title: 'Ratings Growth Score (14d)',
			accessorKey: 'ratings_z_score_2w',
			isSortable: true
		},
		// Monthly growth metrics
		{
			title: 'Installs (30d)',
			accessorKey: 'installs_sum_4w',
			isSortable: true
		},
		{
			title: 'Ratings (30d)',
			accessorKey: 'ratings_sum_4w',
			isSortable: true
		},
		{
			title: 'Installs Growth Score (30d)',
			accessorKey: 'installs_z_score_4w',
			isSortable: true
		},
		{
			title: 'Ratings Growth Score (30d)',
			accessorKey: 'ratings_z_score_4w',
			isSortable: true
		},
		// Monetization indicators
		{
			title: 'IAP',
			accessorKey: 'in_app_purchases',
			isSortable: true
		},
		{
			title: 'Ads',
			accessorKey: 'ad_supported',
			isSortable: true
		}
	];

	const columns = genericColumns(myColumns);

	const hideableColumns = $state<string[]>(
		columns
			.filter((column) => {
				const key = (column as any).accessorKey as string;
				return (
					key === 'in_app_purchases' ||
					key === 'ad_supported' ||
					key?.includes('ratings') ||
					key?.includes('installs')
				);
			})
			.map((column) => (column as any).accessorKey as string)
	);

	const globalFilterFn = (row: any, columnId: string, filterValue: string) => {
		const name = row.original.app_name?.toLowerCase() ?? '';
		const query = filterValue.toLowerCase();
		return name.includes(query);
	};

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
			},
			get columnFilters() {
				return columnFilters;
			},
			get globalFilter() {
				return globalFilter;
			},
			get columnVisibility() {
				return columnVisibility;
			}
		},

		getSortedRowModel: getSortedRowModel(),

		globalFilterFn,

		onSortingChange: (updater) => {
			if (typeof updater === 'function') {
				sorting = updater(sorting);
			} else {
				sorting = updater;
			}
		},
		onColumnFiltersChange: (updater) => {
			if (typeof updater === 'function') {
				columnFilters = updater(columnFilters);
			} else {
				columnFilters = updater;
			}
		},
		onColumnVisibilityChange: (updater) => {
			if (typeof updater === 'function') {
				columnVisibility = updater(columnVisibility);
			} else {
				columnVisibility = updater;
			}
		},
		onPaginationChange: (updater) => {
			if (typeof updater === 'function') {
				pagination = updater(pagination);
			} else {
				pagination = updater;
			}
		},
		onGlobalFilterChange: (updater) => {
			globalFilter = typeof updater === 'function' ? updater(globalFilter) : updater;
		},
		getCoreRowModel: getCoreRowModel(),
		getPaginationRowModel: getPaginationRowModel(),
		getFilteredRowModel: getFilteredRowModel()
	});

	let openState = $state(false);
</script>

<div class="table-container p-0 md:p-2">
	<div class="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-8 m-2">
		<Popover>
			<Popover.Trigger>
				<button class="btn preset-tonal">Show/Hide Columns</button>
			</Popover.Trigger>
			<Portal>
				<Popover.Positioner>
					<Popover.Content>
						<form class="space-y-2 card bg-surface-200-800 p-4 space-y-4 max-w-[320px]">
							{#each table.getAllColumns().filter((col) => col.getCanHide()) as column (column.id)}
								{#if hideableColumns.includes(column.id)}
									<label class="label flex items-center space-x-2">
										<input
											class="checkbox"
											type="checkbox"
											checked={column.getIsVisible()}
											onchange={(e) => column.toggleVisibility(e.currentTarget.checked)}
										/>
										<p>{myColumns.find((c) => c.accessorKey === column.id)?.title}</p>
									</label>
								{/if}
							{/each}
						</form>
					</Popover.Content>
				</Popover.Positioner>
			</Portal>
		</Popover>

		<div class="card preset-tonal flex items-center flex-col p-2">
			<input
				placeholder="Filter apps..."
				value={globalFilter}
				oninput={(e) => {
					const value = e.currentTarget.value;
					table.setGlobalFilter(value);
				}}
				class="max-w-sm p-1"
			/>
		</div>
		<div class="card preset-tonal flex items-center p-2">
			<label for="data-source" class="px-4 text-sm md:text-base">Revenue Source: </label>
			<form class="flex flex-row space-x-4">
				<label class="flex flex-row items-center space-x-1">
					<input
						class="radio"
						type="radio"
						checked={dataSource == 'iap'}
						name="radio-direct"
						value="iap"
						onchange={() => {
							dataSource = 'iap';
						}}
					/>
					<p class="text-xs md:text-sm text-primary-900-100">IAP</p>
				</label>
				<label class="flex flex-row items-center space-x-1">
					<input
						class="radio"
						type="radio"
						checked={dataSource == 'ads'}
						name="radio-direct"
						value="ads"
						onchange={() => {
							dataSource = 'ads';
						}}
					/>
					<p class="text-xs md:text-sm text-primary-900-100">Ads</p>
				</label>
				<label class="flex flex-row items-center space-x-1">
					<input
						class="radio"
						type="radio"
						checked={dataSource == 'both'}
						name="radio-direct"
						value="both"
						onchange={() => {
							dataSource = 'both';
						}}
					/>
					<p class="text-xs md:text-sm text-primary-900-100">Both</p>
				</label>
			</form>
		</div>
	</div>
	<div class="overflow-x-auto pl-0">
		<table class="md:table table-hover md:table-compact table-auto w-full">
			<thead>
				{#each table.getHeaderGroups() as headerGroup (headerGroup.id)}
					<tr>
						{#each headerGroup.headers as header (header.id)}
							{#if !header.isPlaceholder && header.column.getIsVisible()}
								<th>
									<FlexRender
										content={header.column.columnDef.header}
										context={header.getContext()}
									/>
								</th>
							{/if}
						{/each}
					</tr>
				{/each}
			</thead>
			<tbody>
				{#each table.getRowModel().rows as row (row.id)}
					{#if dataSource == 'both' || (row.original.ad_supported && dataSource == 'ads') || (row.original.in_app_purchases && dataSource == 'iap')}
						<tr class="px-0 hover:bg-surface-100-900">
							{#each row.getVisibleCells() as cell (cell.id)}
								<td class="p-2">
									{#if cell.column.id == 'app_name'}
										<a
											href="/apps/{row.original.store_id}"
											style="cursor: pointer;"
											class="text-xs md:text-sm font-medium text-blue-600 hover:text-blue-800"
										>
											<div class="inline-flex gap-2">
												{row.original.app_name}
											</div>
										</a>
									{:else if ['installs_z_score_2w', 'ratings_z_score_2w', 'installs_z_score_4w', 'ratings_z_score_4w'].includes(cell.column.id)}
										<ZScoreMeter
											value={cell.getValue() as number}
											min={isGoogleStore(page.params.store!) ? 0 : 0}
											max={isGoogleStore(page.params.store!) ? 1000 : 500}
											size="sm"
											showValue={false}
										/>
									{:else if ['installs', 'rating_count', 'installs_sum_1w', 'ratings_sum_1w', 'installs_avg_2w', 'installs_sum_4w', 'ratings_avg_2w', 'ratings_sum_4w'].includes(cell.column.id)}
										<p class="text-xs md:text-sm">
											{#if (cell.getValue() ?? 0) === 0}
												-
											{:else}
												{formatNumber(cell.getValue() as number)}
											{/if}
										</p>
									{:else if ['in_app_purchases', 'ad_supported'].includes(cell.column.id)}
										<div class="flex justify-center">
											{#if cell.getValue()}
												<Check class="w-4 h-4 text-success-900-100" />
											{:else}
												<X class="w-4 h-4 text-error-900-100" />
											{/if}
										</div>
									{:else}
										<p class="text-xs md:text-sm">
											{cell.getValue()}
										</p>
									{/if}
								</td>
							{/each}
						</tr>
					{/if}
				{/each}
			</tbody>
		</table>
		<footer class="flex justify-between">
			<div class="flex items-center justify-end space-x-2 py-4">
				<Pagination tableModel={table} />
				<ExportAsCSV {table} filename="appgoblin_companies" />
			</div>
		</footer>
	</div>
</div>
