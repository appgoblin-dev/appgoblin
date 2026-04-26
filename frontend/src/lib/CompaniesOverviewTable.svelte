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

	import Pagination from '$lib/components/data-table/Pagination.svelte';
	import ExportAsCSV from '$lib/components/data-table/ExportAsCSV.svelte';
	import type { CompaniesOverviewEntries } from '../types';

	import { createSvelteTable, FlexRender } from '$lib/components/data-table/index.js';

	import { genericColumns } from '$lib/components/data-table/generic-column';
	import Shield from 'lucide-svelte/icons/shield';
	import CircleHalf from 'lucide-svelte/icons/shield-half';
	import Eye from 'lucide-svelte/icons/eye';

	import { formatNumber } from '$lib/utils/formatNumber';
	import { countryCodeToEmoji } from '$lib/utils/countryCodeToEmoji';

	type DataTableProps<CompaniesOverviewEntries, TValue> = {
		data: CompaniesOverviewEntries[];
	};

	let pagination = $state<PaginationState>({ pageIndex: 0, pageSize: 50 });
	let sorting = $state<SortingState>([]);
	let columnFilters = $state<ColumnFiltersState>([]);

	let globalFilter = $state<string>('');
	let dataMetric = $state<string>('installs');

	let { data }: DataTableProps<CompaniesOverviewEntries, TValue> = $props();

	import { page } from '$app/state';

	const columns = genericColumns([
		{
			title: 'Tracking',
			accessorKey: 'percent_open_source',
			isSortable: true
		},
		{
			title: 'Servers',
			accessorKey: 'most_common_country',
			isSortable: true
		},
		{
			title: 'Company',
			accessorKey: 'company_name',
			isSortable: true
		},
		// ### SDK Stats
		{
			title: 'SDK Android',
			accessorKey: 'google_sdk_installs_d30',
			isSortable: true
		},
		{
			title: 'SDK iOS',
			accessorKey: 'apple_sdk_installs_d30',
			isSortable: true
		},
		{
			title: 'SDK Android',
			accessorKey: 'google_sdk_percentage',
			isSortable: true
		},
		{
			title: 'SDK iOS',
			accessorKey: 'apple_sdk_percentage',
			isSortable: true
		},
		// ### Direct Stats
		{
			title: 'Direct Android',
			accessorKey: 'google_app_ads_direct_installs_d30',
			isSortable: true
		},
		{
			title: 'Direct iOS',
			accessorKey: 'apple_app_ads_direct_installs_d30',
			isSortable: true
		},
		{
			title: 'Direct Android',
			accessorKey: 'google_app_ads_direct_percentage',
			isSortable: true
		},
		{
			title: 'Direct iOS',
			accessorKey: 'apple_app_ads_direct_percentage',
			isSortable: true
		}
	]);

	const globalFilterFn = (row: any, columnId: string, filterValue: string) => {
		const name = row.original.company_name?.toLowerCase() ?? '';
		const domain = row.original.company_domain?.toLowerCase() ?? '';
		const query = filterValue.toLowerCase();
		return name.includes(query) || domain.includes(query);
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

	function formatPercentage(num: number) {
		if (num && num > 0) {
			num = num * 100;
			if (num < 10) {
				return num.toFixed(2) + '%';
			} else {
				return num.toFixed(0) + '%';
			}
		}
		return '';
	}

	let isAdsPage = $derived(!page.params.type || page.params.type == 'ad-networks');

	function shouldShowHeader(header: any) {
		if (header.column.id === 'percent_open_source') return true;
		if (header.column.id === 'most_common_country') return true;
		if (header.column.id === 'company_name') return true;

		let headerHasInstall = header.column.id.includes('install');
		let headerHasPercent = header.column.id.includes('percentage');
		let headerIsDirect = header.column.id.includes('direct');
		let doShowAdsCol = isAdsPage && headerIsDirect;
		let doNotShowAdsCol = !isAdsPage && headerIsDirect;

		if (dataMetric === 'installs' && headerHasInstall) {
			if (doShowAdsCol) {
				return true;
			} else if (doNotShowAdsCol) {
				return false;
			}
			return true;
		} else if (dataMetric === 'percent' && headerHasPercent) {
			if (doShowAdsCol) {
				return true;
			} else if (doNotShowAdsCol) {
				return false;
			}
			return true;
		}
		return false;
	}

	function getCompanyNameColumnWidth(header: any) {
		if (header.column.id === 'company_name') {
			if (isAdsPage) {
				return 'w-[40%]';
			} else {
				return 'w-[50%]';
			}
		}
		return '';
	}
</script>

<div class="table-container p-0 md:p-2">
	<div class="grid grid-cols-1 md:grid-cols-2 gap-2 md:gap-8 m-2">
		<div class="preset-outlined-surface-100-900 flex items-center flex-col p-0 md:p-2">
			<input
				placeholder="Filter companies..."
				value={globalFilter}
				oninput={(e) => {
					const value = e.currentTarget.value;
					table.setGlobalFilter(value);
				}}
				class="max-w-sm p-1"
			/>
		</div>
		<div class="flex items-center p-2">
			<label for="data-source" class="px-4 text-sm md:text-base">Metric: </label>
			<form class="flex flex-row space-x-4">
				<label class="flex flex-row items-center space-x-1">
					<input
						class="radio"
						type="radio"
						checked={dataMetric == 'installs'}
						name="radio-direct"
						value="installs"
						onchange={() => {
							dataMetric = 'installs';
						}}
					/>
					<p class="text-xs md:text-sm">Installs Last 30 Days</p>
				</label>
				<label class="flex flex-row items-center space-x-1">
					<input
						class="radio"
						type="radio"
						checked={dataMetric == 'percent'}
						name="radio-direct"
						value="percent"
						onchange={() => {
							dataMetric = 'percent';
						}}
					/>
					<p class="text-xs md:text-sm">Percent</p>
				</label>
			</form>
		</div>
	</div>
	<div class="overflow-x-auto pl-0">
		<table class="table table-hover table-compact table-auto w-full">
			<thead class="text-sm md:text-base">
				{#each table.getHeaderGroups() as headerGroup (headerGroup.id)}
					<tr>
						{#each headerGroup.headers as header (header.id)}
							{#if shouldShowHeader(header)}
								<th class={getCompanyNameColumnWidth(header)}>
									{#if !header.isPlaceholder}
										<FlexRender
											content={header.column.columnDef.header}
											context={header.getContext()}
										/>
									{/if}
								</th>
							{/if}
						{/each}
					</tr>
				{/each}
			</thead>
			<tbody>
				{#each table.getRowModel().rows as row (row.id)}
					<tr class="px-0">
						<td class="text-center">
							{#if row.original.percent_open_source > 0.75}
								<div
									class="flex items-center justify-center gap-1 text-success-900-100"
									title="Mostly open source - minimal tracking"
								>
									<Shield class="w-4 h-4" />
									<span class="text-xs">Open Source</span>
								</div>
							{:else if row.original.percent_open_source > 0.3}
								<div
									class="flex items-center justify-center gap-1 text-warning-900-100"
									title="Mixed open/closed source"
								>
									<CircleHalf class="w-4 h-4" />
									<span class="text-xs">Mixed</span>
								</div>
							{:else if row.original.percent_open_source == 0}
								<div
									class="flex items-center justify-center gap-1 text-error-900-100"
									title="Closed source - likely tracking"
								>
									<Eye class="w-4 h-4" />
									<span class="text-xs">Tracking</span>
								</div>
							{:else}
								<div
									class="flex items-center justify-center gap-1 text-gray-500"
									title="Unknown tracking status"
								>
									<span class="text-xs">Unknown</span>
								</div>
							{/if}
						</td>
						<td class="text-center">
							{#if row.original.most_common_country}
								<span
									class="text-xs md:text-sm"
									title={`IP addresses for this domain commonly resolve to: ${row.original.most_common_country}`}
								>
									{countryCodeToEmoji(row.original.most_common_country)}
								</span>
							{/if}
						</td>
						<td class="w-0">
							<a
								href="/companies/{row.original.company_domain}"
								style="cursor: pointer;"
								class=" text-xs md:text-sm"
							>
								<div class="flex items-center">
									{#if row.original.company_logo_url}
										<img
											src={`https://media.appgoblin.info/${row.original.company_logo_url}`}
											alt={row.original.company_name}
											class="w-8 h-8 rounded-sm mr-2"
											loading="lazy"
										/>
									{:else}
										<img
											src="/default_company_logo.png"
											alt="Default Company Logo"
											class="w-8 h-8 rounded-sm mr-2"
											loading="lazy"
										/>
									{/if}
									{#if row.original.company_name}
										{row.original.company_name}
										({row.original.company_domain})
									{:else}
										{row.original.company_domain}
									{/if}
								</div>
							</a>
						</td>

						{#if dataMetric == 'installs'}
							<td class="table-cell-fit">
								<p class="text-xs md:text-sm">
									{formatNumber(row.original.google_sdk_installs_d30)}
								</p>
							</td>
							<td class="table-cell-fit">
								<p class="text-xs md:text-sm">
									{formatNumber(row.original.apple_sdk_installs_d30)}
								</p>
							</td>
							{#if isAdsPage}
								<td class="table-cell-fit">
									<p class="text-xs md:text-sm">
										{formatNumber(row.original.google_app_ads_direct_installs_d30)}
									</p>
								</td>

								<td class="table-cell-fit">
									<p class="text-xs md:text-sm">
										{formatNumber(row.original.apple_app_ads_direct_installs_d30)}
									</p>
								</td>
							{/if}
						{/if}

						{#if dataMetric == 'percent'}
							<td class="table-cell-fit">
								<p class="text-xs md:text-sm">
									{formatPercentage(row.original.google_sdk_percentage)}
								</p>
							</td>

							<td class="table-cell-fit">
								<p class="text-xs md:text-sm">
									{formatPercentage(row.original.apple_sdk_percentage)}
								</p>
							</td>

							{#if isAdsPage}
								<td class="table-cell-fit">
									<p class="text-xs md:text-sm">
										{formatPercentage(row.original.google_app_ads_direct_percentage)}
									</p>
								</td>

								<td class="table-cell-fit">
									<p class="text-xs md:text-sm">
										{formatPercentage(row.original.apple_app_ads_direct_percentage)}
									</p>
								</td>
							{/if}
						{/if}
					</tr>
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
