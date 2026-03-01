<script lang="ts">
	import Check from 'lucide-svelte/icons/check';
	import X from 'lucide-svelte/icons/x';
	import {
		type PaginationState,
		type SortingState,
		getCoreRowModel,
		getPaginationRowModel,
		getSortedRowModel
	} from '@tanstack/table-core';
	import { createSvelteTable, FlexRender } from '$lib/components/data-table/index.js';
	import { genericColumns } from '$lib/components/data-table/generic-column';
	import Pagination from '$lib/components/data-table/Pagination.svelte';
	import ExportAsCSV from '$lib/components/data-table/ExportAsCSV.svelte';
	import StoreIcon from '$lib/StoreIcon.svelte';
	import { formatNumber } from '$lib/utils/formatNumber';

	import type { CrossfilterApp } from '../types.js';

	type CrossfilterAppsTableProps = {
		apps: CrossfilterApp[];
		filename: string;
		sorting: SortingState;
	};

	let { apps, filename, sorting = $bindable() }: CrossfilterAppsTableProps = $props();

	let pagination = $state<PaginationState>({ pageIndex: 0, pageSize: 50 });

	const myColumns = [
		{
			title: 'App',
			accessorKey: 'name',
			isSortable: true
		},
		{
			title: 'Store',
			accessorKey: 'store',
			isSortable: true
		},
		{
			title: 'Installs',
			accessorKey: 'installs',
			isSortable: true
		},
		{
			title: 'Ratings',
			accessorKey: 'rating_count',
			isSortable: true
		},
		{
			title: 'Monthly Installs',
			accessorKey: 'installs_d30',
			isSortable: true
		},
		{
			title: 'Estimated Monthly Revenue',
			accessorKey: 'estimated_monthly_revenue',
			isSortable: true
		},
		{
			title: 'Monthly Active Users',
			accessorKey: 'monthly_active_users',
			isSortable: true
		},
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

	const table = createSvelteTable({
		get data() {
			return apps;
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
		getCoreRowModel: getCoreRowModel(),
		getPaginationRowModel: getPaginationRowModel(),
		getSortedRowModel: getSortedRowModel(),
		onPaginationChange: (updater) => {
			if (typeof updater === 'function') {
				pagination = updater(pagination);
			} else {
				pagination = updater;
			}
		},
		onSortingChange: (updater) => {
			if (typeof updater === 'function') {
				sorting = updater(sorting);
			} else {
				sorting = updater;
			}
		}
	});

	const headerGroups = $derived(() => table.getHeaderGroups());
	const tableRows = $derived(() => table.getRowModel().rows);
</script>

<div class="table-container overflow-x-auto">
	<table class="table table-hover table-auto w-full text-xs md:text-sm">
		<thead>
			{#each headerGroups() as headerGroup (headerGroup.id)}
				<tr>
					{#each headerGroup.headers as header (header.id)}
						{#if !header.isPlaceholder}
							<th class="p-2">
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
			{#each tableRows() as row (row.id)}
				<tr class="hover:bg-surface-100-900">
					{#each row.getVisibleCells() as cell (cell.id)}
						<td class="p-2">
							{#if cell.column.id === 'name'}
								<a
									href="/apps/{row.original.store_id}"
									class="text-blue-600 hover:text-blue-800 hover:underline font-medium"
								>
									{#if row.original.app_icon_url}
										<img
											src={row.original.app_icon_url}
											alt="Icon"
											class="w-8 h-8 rounded inline-block mr-2"
											loading="lazy"
											decoding="async"
										/>
									{/if}
									{cell.getValue()}
								</a>
							{:else if cell.column.id === 'store'}
								<StoreIcon store={row.original.store} />
							{:else if ['installs', 'rating_count', 'installs_d30'].includes(cell.column.id)}
								<div class="text-right font-mono">
									{formatNumber(cell.getValue() as number)}
								</div>
							{:else if ['in_app_purchases', 'ad_supported'].includes(cell.column.id)}
								<div class="flex justify-center">
									{#if cell.getValue()}
										<Check class="w-4 h-4 text-success-900-100" />
									{:else}
										<X class="w-4 h-4 text-error-900-100" />
									{/if}
								</div>
							{:else}
								{cell.getValue()}
							{/if}
						</td>
					{/each}
				</tr>
			{/each}
		</tbody>
	</table>

	<div class="flex items-center justify-between p-2 mt-4">
		<Pagination tableModel={table} />
		<ExportAsCSV {table} {filename} />
	</div>
</div>
