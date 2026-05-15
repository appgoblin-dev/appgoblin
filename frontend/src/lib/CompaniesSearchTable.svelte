<script lang="ts" generics="TData, TValue">
	import { type SortingState, getCoreRowModel, getSortedRowModel } from '@tanstack/table-core';

	import type { CompaniesSearchEntries } from '../types';

	import { createSvelteTable, FlexRender } from '$lib/components/data-table/index.js';

	import { genericColumns } from '$lib/components/data-table/generic-column';

	import { formatNumber } from '$lib/utils/formatNumber';
	import { countryCodeToEmoji } from '$lib/utils/countryCodeToEmoji';

	type DataTableProps<CompaniesSearchEntries, TValue> = {
		data: CompaniesSearchEntries[];
	};

	let sorting = $state<SortingState>([]);

	let dataMetric = $state<string>('installs');

	let { data }: DataTableProps<CompaniesSearchEntries, TValue> = $props();

	const columns = genericColumns([
		{
			title: 'Servers',
			accessorKey: 'country_code',
			isSortable: true
		},
		{
			title: 'Matched Company or Domain',
			accessorKey: 'company_name',
			isSortable: true
		},
		// ### SDK Stats
		{
			title: 'SDK Apps',
			accessorKey: 'sdk_app_count',
			isSortable: true
		},
		{
			title: 'API Calls Apps',
			accessorKey: 'api_call_app_count',
			isSortable: true
		},
		// ### Direct Stats
		{
			title: 'App-Ads.txt Apps',
			accessorKey: 'app_ads_direct_app_count',
			isSortable: true
		},
		{
			title: 'App-Ads.txt Reseller Apps',
			accessorKey: 'app_ads_reseller_app_count',
			isSortable: true
		}
	]);

	const table = createSvelteTable({
		get data() {
			return data;
		},
		columns,
		state: {
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

		getCoreRowModel: getCoreRowModel()
	});

	function getCompanyNameColumnWidth(header: any) {
		if (header.column.id === 'company_name') {
			return 'w-[40%]';
		}
		return '';
	}
</script>

<div class="table-container p-0 md:p-2">
	<div class="overflow-x-auto pl-0">
		<table class="table table-hover table-compact table-auto w-full">
			<thead class="text-sm md:text-base">
				{#each table.getHeaderGroups() as headerGroup (headerGroup.id)}
					<tr>
						{#each headerGroup.headers as header (header.id)}
							<th class={getCompanyNameColumnWidth(header)}>
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
				{#each table.getRowModel().rows as row (row.id)}
					<tr class="px-0">
						<td class="text-center">
							{#if row.original.api_ip_resolved_country}
								<span
									class="text-xs md:text-sm"
									title={`API IP addresses for this domain commonly resolve to: ${row.original.api_ip_resolved_country}`}
								>
									{countryCodeToEmoji(row.original.api_ip_resolved_country)}
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
											class="w-12 h-12 rounded-sm mr-2"
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

						<td class="table-cell-fit">
							<p class="text-sm md:text-base">
								{formatNumber(row.original.sdk_app_count)}
							</p>
						</td>

						<td class="table-cell-fit">
							<p class="text-sm md:text-base">
								{formatNumber(row.original.api_call_app_count)}
							</p>
						</td>

						<td class="table-cell-fit">
							<p class="text-sm md:text-base">
								{formatNumber(row.original.app_ads_direct_app_count)}
							</p>
						</td>

						<td class="table-cell-fit">
							<p class="text-sm md:text-base">
								{formatNumber(row.original.app_ads_reseller_app_count)}
							</p>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>
