<script lang="ts">
	import type {
		ColumnFiltersState,
		ColumnVisibilityState,
		SortingState
	} from '@tanstack/svelte-table';
	import { createAtom } from '@tanstack/svelte-store';
	import { Popover, Portal } from '@skeletonlabs/skeleton-svelte';

	import Pagination from '#lib/components/data-table/Pagination.svelte';
	import ExportAsCSV from '#lib/components/data-table/ExportAsCSV.svelte';
	import type { CompaniesOverviewEntries } from '../types';

	import {
		createAppTable,
		createTableState,
		FlexRender
	} from '#lib/components/data-table/index.js';

	import { genericColumns } from '#lib/components/data-table/generic-column.js';
	import Shield from '@lucide/svelte/icons/shield';
	import CircleHalf from '@lucide/svelte/icons/shield-half';
	import Eye from '@lucide/svelte/icons/eye';

	import { formatNumber } from '#lib/utils/formatNumber.js';
	import { countryCodeToEmoji } from '#lib/utils/countryCodeToEmoji.js';

	type ViewMode = 'auto' | 'sdk' | 'ads' | 'both' | 'api';

	type DataTableProps = {
		data: CompaniesOverviewEntries[];
		viewMode?: ViewMode;
		showLimitNote?: boolean;
	};

	const paginationAtom = createAtom({ pageIndex: 0, pageSize: 50 });
	const columnVisibilityAtom = createAtom<ColumnVisibilityState>({
		google_sdk_app_count: false,
		apple_sdk_app_count: false,
		google_sdk_installs_d30: false,
		apple_sdk_installs_d30: false,
		google_sdk_percentage: false,
		apple_sdk_percentage: false,
		google_sdk_latest_pct_market_share_change: true,
		apple_sdk_latest_pct_market_share_change: true,
		google_sdk_latest_apps_lost: false,
		apple_sdk_latest_apps_lost: false,
		google_api_call_app_count: false,
		google_app_ads_direct_app_count: false,
		apple_app_ads_direct_app_count: false,
		google_app_ads_direct_installs_d30: false,
		apple_app_ads_direct_installs_d30: false,
		google_app_ads_direct_percentage: false,
		apple_app_ads_direct_percentage: false,
		google_app_ads_direct_latest_pct_market_share_change: true,
		apple_app_ads_direct_latest_pct_market_share_change: true,
		google_app_ads_direct_latest_apps_lost: false,
		apple_app_ads_direct_latest_apps_lost: false
	});
	const [sorting, onSortingChange] = createTableState<SortingState>([]);
	const [columnFilters, onColumnFiltersChange] = createTableState<ColumnFiltersState>([]);
	const [globalFilter, onGlobalFilterChange] = createTableState('');

	let { data, viewMode = 'auto', showLimitNote = false }: DataTableProps = $props();

	import { page } from '$app/state';

	// ===== View mode resolution =====
	let resolvedViewMode = $derived.by<ViewMode>(() => {
		if (viewMode !== 'auto') {
			return viewMode;
		}
		if (!page.params.type) {
			return 'both';
		}
		if (page.params.type == 'ad-networks') return 'ads';
		if (page.params.type == 'app-publishers') return 'api';
		return 'sdk';
	});
	let showsSdkColumns = $derived(resolvedViewMode !== 'api');
	let showsApiColumns = $derived(resolvedViewMode === 'api');
	let showsAdsColumns = $derived(resolvedViewMode === 'ads' || resolvedViewMode === 'both');
	let isAdsPage = $derived(resolvedViewMode === 'ads');

	// ===== Dynamic column definitions =====
	let columns = $derived.by<ReturnType<typeof genericColumns>>(() => {
		// In app-publishers mode: show per-store app counts + per-store installs
		if (showsApiColumns) {
			return genericColumns([
				{ title: 'Tracking', accessorKey: 'percent_open_source', isSortable: true },
				{ title: 'Country', accessorKey: 'country', isSortable: true },
				{ title: 'Company', accessorKey: 'company_name', isSortable: true },
				{ title: 'Parent Company', accessorKey: 'parent_company_name', isSortable: true },
				{ title: 'Tickers', accessorKey: 'company_tickers', isSortable: false },
				{ title: 'Total Apps', accessorKey: 'total_app_count', isSortable: true },
				{ title: 'Android Apps', accessorKey: 'google_app_count', isSortable: true },
				{ title: 'iOS Apps', accessorKey: 'apple_app_count', isSortable: true },
				{ title: 'Total Installs (30d)', accessorKey: 'installs_d30', isSortable: true },
				{ title: 'Android Installs', accessorKey: 'google_installs_d30', isSortable: true },
				{ title: 'iOS Installs', accessorKey: 'apple_installs_d30', isSortable: true }
			]);
		}

		const sdkMetricColDefs = [
			{ title: 'SDK Android Apps', accessorKey: 'google_sdk_app_count', isSortable: true },
			{ title: 'SDK iOS Apps', accessorKey: 'apple_sdk_app_count', isSortable: true },
			{
				title: 'SDK Android Installs (30d)',
				accessorKey: 'google_sdk_installs_d30',
				isSortable: true
			},
			{ title: 'SDK iOS Installs (30d)', accessorKey: 'apple_sdk_installs_d30', isSortable: true },
			{ title: 'SDK Android Market Share', accessorKey: 'google_sdk_percentage', isSortable: true },
			{ title: 'SDK iOS Market Share', accessorKey: 'apple_sdk_percentage', isSortable: true },
			{
				title: 'SDK Android Q/Q Market Share Change',
				accessorKey: 'google_sdk_latest_pct_market_share_change',
				isSortable: true
			},
			{
				title: 'SDK iOS Q/Q Market Share Change',
				accessorKey: 'apple_sdk_latest_pct_market_share_change',
				isSortable: true
			},
			{
				title: 'SDK Android Q/Q Apps Lost',
				accessorKey: 'google_sdk_latest_apps_lost',
				isSortable: true
			},
			{
				title: 'SDK iOS Q/Q Apps Lost',
				accessorKey: 'apple_sdk_latest_apps_lost',
				isSortable: true
			}
		];
		const apiColDefs = [
			{ title: 'API Android Apps', accessorKey: 'google_api_call_app_count', isSortable: true }
		];

		const rawCols = [
			{ title: 'Tracking', accessorKey: 'percent_open_source', isSortable: true },
			{ title: 'Country', accessorKey: 'country', isSortable: true },
			{ title: 'Company', accessorKey: 'company_name', isSortable: true },
			{ title: 'Parent Company', accessorKey: 'parent_company_name', isSortable: true },
			{ title: 'Tickers', accessorKey: 'company_tickers', isSortable: false },
			{ title: 'Total Apps', accessorKey: 'total_app_count', isSortable: true },
			// App counts
			...sdkMetricColDefs.filter((c) => c.accessorKey.endsWith('_app_count')),
			...apiColDefs,
			// Ad counts
			{
				title: 'App-Ads.txt Direct Android Apps',
				accessorKey: 'google_app_ads_direct_app_count',
				isSortable: true
			},
			{
				title: 'App-Ads.txt Direct iOS Apps',
				accessorKey: 'apple_app_ads_direct_app_count',
				isSortable: true
			},

			// Metric columns — installs + market share
			...sdkMetricColDefs.filter(
				(c) => c.accessorKey.includes('installs_d30') || c.accessorKey.includes('percentage')
			),
			{
				title: 'App-Ads.txt Direct Android Installs (30d)',
				accessorKey: 'google_app_ads_direct_installs_d30',
				isSortable: true
			},
			{
				title: 'App-Ads.txt Direct iOS Installs (30d)',
				accessorKey: 'apple_app_ads_direct_installs_d30',
				isSortable: true
			},
			{
				title: 'App-Ads.txt Direct Android Market Share',
				accessorKey: 'google_app_ads_direct_percentage',
				isSortable: true
			},
			{
				title: 'App-Ads.txt Direct iOS Market Share',
				accessorKey: 'apple_app_ads_direct_percentage',
				isSortable: true
			},
			// Trend columns
			...sdkMetricColDefs.filter(
				(c) =>
					c.accessorKey.includes('latest_pct_market_share_change') ||
					c.accessorKey.includes('latest_apps_lost')
			),
			{
				title: 'App-Ads.txt Direct Android Q/Q Market Share Change',
				accessorKey: 'google_app_ads_direct_latest_pct_market_share_change',
				isSortable: true
			},
			{
				title: 'App-Ads.txt Direct iOS Q/Q Market Share Change',
				accessorKey: 'apple_app_ads_direct_latest_pct_market_share_change',
				isSortable: true
			},
			{
				title: 'App-Ads.txt Direct Android Q/Q Apps Lost',
				accessorKey: 'google_app_ads_direct_latest_apps_lost',
				isSortable: true
			},
			{
				title: 'App-Ads.txt Direct iOS Q/Q Apps Lost',
				accessorKey: 'apple_app_ads_direct_latest_apps_lost',
				isSortable: true
			}
		];
		return genericColumns(rawCols);
	});

	function getCompanyTickers(company: unknown): string[] {
		if (typeof company !== 'object' || company === null) return [];
		const companyTickers =
			'company_tickers' in company && Array.isArray(company.company_tickers)
				? company.company_tickers
				: [];
		const directTickers =
			'tickers_direct' in company && Array.isArray(company.tickers_direct)
				? company.tickers_direct
				: [];
		const tickers: unknown[] = [...companyTickers, ...directTickers];
		return [...new Set(tickers.filter((ticker): ticker is string => typeof ticker === 'string'))];
	}

	const globalFilterFn = (row: any, columnId: string, filterValue: string) => {
		const name = row.original.company_name?.toLowerCase() ?? '';
		const domain = row.original.company_domain?.toLowerCase() ?? '';
		const parentName = row.original.parent_company_name?.toLowerCase() ?? '';
		const parentDomain = row.original.parent_company_domain?.toLowerCase() ?? '';
		const query = filterValue.toLowerCase();
		const tickers = getCompanyTickers(row.original);
		return (
			name.includes(query) ||
			domain.includes(query) ||
			parentName.includes(query) ||
			parentDomain.includes(query) ||
			tickers.some((ticker: string) => ticker.toLowerCase().includes(query))
		);
	};

	const table = createAppTable({
		get data() {
			return data;
		},
		get columns() {
			return columns;
		},
		state: {
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
		onGlobalFilterChange,
		atoms: {
			pagination: paginationAtom,
			columnVisibility: columnVisibilityAtom
		}
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

	function formatTrimmed(num: number, digits: number) {
		return num.toFixed(digits).replace(/\.0+$|(?<=\.[0-9]*[1-9])0+$/, '');
	}

	function getShareDigits(num: number) {
		const absolute = Math.abs(num);
		if (absolute >= 10) return 2;
		if (absolute >= 1) return 3;
		if (absolute >= 0.1) return 4;
		if (absolute >= 0.01) return 5;
		return 6;
	}

	const MAX_QOQ_SHARE_CHANGE_PCT = 500;

	function formatQoqShareChangePct(num: number | null | undefined) {
		if (typeof num !== 'number' || Number.isNaN(num)) {
			return '';
		}
		const capped = Math.min(num, MAX_QOQ_SHARE_CHANGE_PCT);
		const absolute = Math.abs(capped);
		const digits = absolute >= 100 ? 0 : absolute >= 10 ? 1 : 2;
		const prefix = capped > 0 ? '+' : '';
		const suffix = capped >= MAX_QOQ_SHARE_CHANGE_PCT ? '%+' : '%';
		return `${prefix}${formatTrimmed(capped, digits)}${suffix}`;
	}

	function formatOptionalNumber(num: number | null | undefined) {
		if (typeof num !== 'number' || Number.isNaN(num)) {
			return '';
		}
		return formatNumber(num);
	}
	function shouldShowHeader(header: any) {
		if (!header.column.getIsVisible()) return false;
		if (header.column.id.includes('direct')) return showsAdsColumns;
		if (showsApiColumns) {
			return (
				!header.column.id.startsWith('google_sdk_') &&
				!header.column.id.startsWith('apple_sdk_') &&
				!header.column.id.startsWith('google_api_')
			);
		}
		return true;
	}

	function getCompanyNameColumnWidth(header: any) {
		if (header.column.id === 'company_name') {
			if (resolvedViewMode === 'both') {
				return 'w-[20%]';
			}
			if (isAdsPage || showsApiColumns) {
				return 'w-[20%]';
			} else {
				return 'w-[20%]';
			}
		}
		if (header.column.id === 'parent_company_name') {
			return 'w-[10%]';
		}
		return '';
	}

	function hasDistinctParentCompany(company: any) {
		return Boolean(
			company.parent_company_domain && company.parent_company_domain !== company.company_domain
		);
	}

	function columnLabel(columnId: string) {
		return columnId
			.replace(/^(google|apple)_/, '$1 ')
			.replace(/_d30$/, ' (30d)')
			.replace(/_app_count$/, ' apps')
			.replace(/_percentage$/, ' market share')
			.replace(/_latest_pct_market_share_change$/, ' Q/Q share change')
			.replace(/_latest_apps_lost$/, ' Q/Q apps lost')
			.replace(/_/g, ' ')
			.replace(/\b\w/g, (letter) => letter.toUpperCase())
			.replace(/\bSdk\b/g, 'SDK')
			.replace(/\bApi\b/g, 'API')
			.replace(/App Ads Txt/g, 'App-Ads.txt');
	}

	const CORE_COLUMN_IDS = new Set([
		'percent_open_source',
		'country',
		'company_name',
		'parent_company_name',
		'company_tickers'
	]);

	const COLUMN_GROUPS = [
		{ label: 'App Counts', matches: (id: string) => id.endsWith('_app_count') },
		{ label: 'Installs (Last 30 Days)', matches: (id: string) => id.includes('installs_d30') },
		{ label: 'Market Share', matches: (id: string) => id.includes('percentage') },
		{
			label: 'Q/Q Market Share Change',
			matches: (id: string) => id.includes('latest_pct_market_share_change')
		},
		{ label: 'Q/Q Apps Lost', matches: (id: string) => id.includes('latest_apps_lost') }
	];

	function getColumnGroup(columnId: string) {
		return COLUMN_GROUPS.find((group) => group.matches(columnId))?.label ?? 'Other';
	}

	function isColumnVisible(columnId: string) {
		return table.getColumn(columnId)?.getIsVisible() ?? true;
	}

	function isColumnAvailable(columnId: string) {
		if (columnId.includes('direct')) return showsAdsColumns;
		if (showsApiColumns) {
			return (
				!columnId.startsWith('google_sdk_') &&
				!columnId.startsWith('apple_sdk_') &&
				!columnId.startsWith('google_api_')
			);
		}
		return true;
	}
</script>

{#if showLimitNote}
	<p class="text-xs mb-1">
		Table shows the top 1,000 company domains. Use the site wide search for specific domains or
		companies that may not make the top 1000.
	</p>
{/if}
<div class="table-container p-0 md:p-2">
	<div class="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-8 m-2">
		<div class="preset-outlined-surface-100-900 flex items-center flex-col p-0 md:p-2">
			<input
				placeholder="Filter top companies..."
				value={globalFilter()}
				oninput={(e) => {
					const value = e.currentTarget.value;
					table.setGlobalFilter(value);
				}}
				class="bg-surface-50-950 max-w-sm p-1"
			/>
		</div>
		<div class="flex items-center p-2">
			<Popover>
				<Popover.Trigger>
					<span class="btn preset-outlined-primary-100-900" role="button" tabindex="0">
						Show/Hide Columns
					</span>
				</Popover.Trigger>
				<Portal>
					<Popover.Positioner>
						<Popover.Content>
							<form class="space-y-3 bg-surface-100-900 p-4 max-w-[360px]">
								{#each COLUMN_GROUPS as group (group.label)}
									<div class="space-y-1">
										<p class="text-xs font-semibold text-surface-500-400">{group.label}</p>
										{#each table
											.getAllLeafColumns()
											.filter((column) => !CORE_COLUMN_IDS.has(column.id) && isColumnAvailable(column.id) && group.matches(column.id)) as column (column.id)}
											<label class="label flex items-center space-x-2">
												<input
													type="checkbox"
													checked={column.getIsVisible()}
													disabled={!column.getCanHide()}
													onchange={(event) => column.toggleVisibility(event.currentTarget.checked)}
													class="checkbox"
												/>
												<span class="text-xs">{columnLabel(column.id)}</span>
											</label>
										{/each}
									</div>
								{/each}
							</form>
						</Popover.Content>
					</Popover.Positioner>
				</Portal>
			</Popover>
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
										<FlexRender {header} />
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
						<td class="text-center" class:hidden={!isColumnVisible('percent_open_source')}>
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
						<td class="text-center" class:hidden={!isColumnVisible('country')}>
							{#if row.original.country}
								<span
									class="text-xs md:text-sm whitespace-nowrap inline-flex items-center gap-1.5"
									title={row.original.country}
								>
									{countryCodeToEmoji(row.original.country)}
								</span>
							{/if}
						</td>
						<td class="w-0" class:hidden={!isColumnVisible('company_name')}>
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
									{#if row.original.company_name && row.original.company_name != row.original.company_domain}
										{row.original.company_name}
									{:else}
										{row.original.company_domain}
									{/if}
								</div>
							</a>
						</td>
						<td class="w-0" class:hidden={!isColumnVisible('parent_company_name')}>
							{#if hasDistinctParentCompany(row.original)}
								<a
									href="/companies/{row.original.parent_company_domain}"
									style="cursor: pointer;"
									class="text-xs md:text-sm"
								>
									<div class="flex items-center">
										{#if row.original.parent_company_logo_url}
											<img
												src={`https://media.appgoblin.info/${row.original.parent_company_logo_url}`}
												alt={row.original.parent_company_name ?? row.original.parent_company_domain}
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
										{#if row.original.parent_company_name}
											{row.original.parent_company_name}
										{:else}
											{row.original.parent_company_domain}
										{/if}
									</div>
								</a>
							{:else}
								<span class="text-xs text-surface-500-400">-</span>
							{/if}
						</td>
						<td class="text-xs md:text-sm" class:hidden={!isColumnVisible('company_tickers')}>
							{#each getCompanyTickers(row.original) as ticker (ticker)}
								<span class="badge preset-filled-surface-200-800 mr-1">{ticker}</span>
							{/each}
						</td>
						{#if showsApiColumns}
							<td class="table-cell-fit" class:hidden={!isColumnVisible('total_app_count')}>
								<p class="text-xs md:text-sm">
									{formatOptionalNumber(row.original.total_app_count)}
								</p>
							</td>
							<td class="table-cell-fit" class:hidden={!isColumnVisible('google_app_count')}>
								<p class="text-xs md:text-sm">
									{formatOptionalNumber(row.original.google_app_count)}
								</p>
							</td>
							<td class="table-cell-fit" class:hidden={!isColumnVisible('apple_app_count')}>
								<p class="text-xs md:text-sm">
									{formatOptionalNumber(row.original.apple_app_count)}
								</p>
							</td>
						{/if}
						{#if showsApiColumns}
							<td class="table-cell-fit" class:hidden={!isColumnVisible('installs_d30')}>
								<p class="text-xs md:text-sm">{formatNumber(row.original.installs_d30 ?? 0)}</p>
							</td>
							<td class="table-cell-fit" class:hidden={!isColumnVisible('google_installs_d30')}>
								<p class="text-xs md:text-sm">
									{formatNumber(row.original.google_installs_d30 ?? 0)}
								</p>
							</td>
							<td class="table-cell-fit" class:hidden={!isColumnVisible('apple_installs_d30')}>
								<p class="text-xs md:text-sm">
									{formatNumber(row.original.apple_installs_d30 ?? 0)}
								</p>
							</td>
						{/if}

						{#if !showsApiColumns}
							<td class="table-cell-fit" class:hidden={!isColumnVisible('total_app_count')}>
								<p class="text-xs md:text-sm">
									{formatOptionalNumber(row.original.total_app_count)}
								</p>
							</td>
							{#if showsSdkColumns}
								<td class="table-cell-fit" class:hidden={!isColumnVisible('google_sdk_app_count')}>
									<p class="text-xs md:text-sm">
										{formatOptionalNumber(row.original.google_sdk_app_count)}
									</p>
								</td>
								<td class="table-cell-fit" class:hidden={!isColumnVisible('apple_sdk_app_count')}>
									<p class="text-xs md:text-sm">
										{formatOptionalNumber(row.original.apple_sdk_app_count)}
									</p>
								</td>
							{/if}
							{#if showsSdkColumns || isAdsPage}
								<td
									class="table-cell-fit"
									class:hidden={!isColumnVisible('google_api_call_app_count')}
								>
									<p class="text-xs md:text-sm">
										{formatOptionalNumber(row.original.google_api_call_app_count)}
									</p>
								</td>
							{/if}
							{#if showsAdsColumns}
								<td
									class="table-cell-fit"
									class:hidden={!isColumnVisible('google_app_ads_direct_app_count')}
								>
									<p class="text-xs md:text-sm">
										{formatOptionalNumber(row.original.google_app_ads_direct_app_count)}
									</p>
								</td>
								<td
									class="table-cell-fit"
									class:hidden={!isColumnVisible('apple_app_ads_direct_app_count')}
								>
									<p class="text-xs md:text-sm">
										{formatOptionalNumber(row.original.apple_app_ads_direct_app_count)}
									</p>
								</td>
							{/if}
						{/if}

						{#if !showsApiColumns}
							{#if showsSdkColumns}
								<td
									class="table-cell-fit"
									class:hidden={!isColumnVisible('google_sdk_installs_d30')}
								>
									<p class="text-xs md:text-sm">
										{formatNumber(row.original.google_sdk_installs_d30)}
									</p>
								</td>
								<td
									class="table-cell-fit"
									class:hidden={!isColumnVisible('apple_sdk_installs_d30')}
								>
									<p class="text-xs md:text-sm">
										{formatNumber(row.original.apple_sdk_installs_d30)}
									</p>
								</td>
							{/if}
							{#if showsAdsColumns}
								<td
									class="table-cell-fit"
									class:hidden={!isColumnVisible('google_app_ads_direct_installs_d30')}
								>
									<p class="text-xs md:text-sm">
										{formatNumber(row.original.google_app_ads_direct_installs_d30)}
									</p>
								</td>

								<td
									class="table-cell-fit"
									class:hidden={!isColumnVisible('apple_app_ads_direct_installs_d30')}
								>
									<p class="text-xs md:text-sm">
										{formatNumber(row.original.apple_app_ads_direct_installs_d30)}
									</p>
								</td>
							{/if}
						{/if}

						{#if !showsApiColumns}
							{#if showsSdkColumns}
								<td class="table-cell-fit" class:hidden={!isColumnVisible('google_sdk_percentage')}>
									<p class="text-xs md:text-sm">
										{formatPercentage(row.original.google_sdk_percentage)}
									</p>
								</td>

								<td class="table-cell-fit" class:hidden={!isColumnVisible('apple_sdk_percentage')}>
									<p class="text-xs md:text-sm">
										{formatPercentage(row.original.apple_sdk_percentage)}
									</p>
								</td>
							{/if}

							{#if showsAdsColumns}
								<td
									class="table-cell-fit"
									class:hidden={!isColumnVisible('google_app_ads_direct_percentage')}
								>
									<p class="text-xs md:text-sm">
										{formatPercentage(row.original.google_app_ads_direct_percentage)}
									</p>
								</td>

								<td
									class="table-cell-fit"
									class:hidden={!isColumnVisible('apple_app_ads_direct_percentage')}
								>
									<p class="text-xs md:text-sm">
										{formatPercentage(row.original.apple_app_ads_direct_percentage)}
									</p>
								</td>
							{/if}
						{/if}

						{#if !showsApiColumns}
							{#if showsSdkColumns}
								<td
									class="table-cell-fit"
									class:hidden={!isColumnVisible('google_sdk_latest_pct_market_share_change')}
								>
									<p class="text-xs md:text-sm">
										{formatQoqShareChangePct(
											row.original.google_sdk_latest_pct_market_share_change
										)}
									</p>
								</td>

								<td
									class="table-cell-fit"
									class:hidden={!isColumnVisible('apple_sdk_latest_pct_market_share_change')}
								>
									<p class="text-xs md:text-sm">
										{formatQoqShareChangePct(row.original.apple_sdk_latest_pct_market_share_change)}
									</p>
								</td>
							{/if}

							{#if showsAdsColumns}
								<td
									class="table-cell-fit"
									class:hidden={!isColumnVisible(
										'google_app_ads_direct_latest_pct_market_share_change'
									)}
								>
									<p class="text-xs md:text-sm">
										{formatQoqShareChangePct(
											row.original.google_app_ads_direct_latest_pct_market_share_change
										)}
									</p>
								</td>

								<td
									class="table-cell-fit"
									class:hidden={!isColumnVisible(
										'apple_app_ads_direct_latest_pct_market_share_change'
									)}
								>
									<p class="text-xs md:text-sm">
										{formatQoqShareChangePct(
											row.original.apple_app_ads_direct_latest_pct_market_share_change
										)}
									</p>
								</td>
							{/if}
						{/if}

						{#if !showsApiColumns}
							{#if showsSdkColumns}
								<td
									class="table-cell-fit"
									class:hidden={!isColumnVisible('google_sdk_latest_apps_lost')}
								>
									<p class="text-xs md:text-sm">
										{formatOptionalNumber(row.original.google_sdk_latest_apps_lost)}
									</p>
								</td>

								<td
									class="table-cell-fit"
									class:hidden={!isColumnVisible('apple_sdk_latest_apps_lost')}
								>
									<p class="text-xs md:text-sm">
										{formatOptionalNumber(row.original.apple_sdk_latest_apps_lost)}
									</p>
								</td>
							{/if}

							{#if showsAdsColumns}
								<td
									class="table-cell-fit"
									class:hidden={!isColumnVisible('google_app_ads_direct_latest_apps_lost')}
								>
									<p class="text-xs md:text-sm">
										{formatOptionalNumber(row.original.google_app_ads_direct_latest_apps_lost)}
									</p>
								</td>

								<td
									class="table-cell-fit"
									class:hidden={!isColumnVisible('apple_app_ads_direct_latest_apps_lost')}
								>
									<p class="text-xs md:text-sm">
										{formatOptionalNumber(row.original.apple_app_ads_direct_latest_apps_lost)}
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
