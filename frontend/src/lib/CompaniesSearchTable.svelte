<script lang="ts">
	import Check from '@lucide/svelte/icons/check';
	import X from '@lucide/svelte/icons/x';

	import type { CompaniesSearchEntries } from '../types';

	import type { SortingState } from '@tanstack/svelte-table';

	import {
		createAppTable,
		createTableState,
		FlexRender
	} from '$lib/components/data-table/index.js';

	import { genericColumns } from '$lib/components/data-table/generic-column';

	type DataTableProps = {
		data: CompaniesSearchEntries[];
	};

	const [sorting, onSortingChange] = createTableState<SortingState>([]);
	const checkIconClass = 'w-4 h-4 text-success-700-300';
	const xIconClass = 'w-4 h-4 text-error-200';

	let { data }: DataTableProps = $props();

	const columns = genericColumns([
		{
			title: 'Matched Company or Domain',
			accessorKey: 'company_name',
			isSortable: true
		},
		{
			title: 'API Calls',
			accessorKey: 'has_api_signal',
			isSortable: true
		},
		{
			title: 'SDKs',
			accessorKey: 'has_sdk_signal',
			isSortable: true
		},
		{
			title: 'Published Apps',
			accessorKey: 'has_publisher_signal',
			isSortable: true
		},
		{
			title: 'App-Ads.txt Direct',
			accessorKey: 'has_app_ads_direct',
			isSortable: true
		},
		{
			title: 'App-Ads.txt Reseller',
			accessorKey: 'has_app_ads_reseller',
			isSortable: true
		}
	]);

	const table = createAppTable({
		get data() {
			return data;
		},
		columns,
		state: {
			get sorting() {
				return sorting();
			}
		},
		onSortingChange
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
									<FlexRender {header} />
								{/if}
							</th>
						{/each}
					</tr>
				{/each}
			</thead>
			<tbody>
				{#each table.getRowModel().rows as row (row.id)}
					<tr class="px-0">
						<td class="w-0">
							<a
								href="/companies/{row.original.company_domain}"
								style="cursor: pointer;"
								class="text-sm md:text-base"
							>
								<div class="flex items-center gap-2">
									{#if row.original.logo_url}
										<img
											src={`https://media.appgoblin.info/${row.original.logo_url}`}
											alt={row.original.company_name || row.original.company_domain}
											class="w-8 h--8 md:w-14 md:h-14 rounded-sm"
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
							{#if row.original.has_api_signal}
								<Check class={checkIconClass} />
							{:else}
								<X class={xIconClass} />
							{/if}
						</td>

						<td class="table-cell-fit">
							{#if row.original.has_sdk_signal}
								<Check class={checkIconClass} />
							{:else}
								<X class={xIconClass} />
							{/if}
						</td>

						<td class="table-cell-fit">
							{#if row.original.has_publisher_signal}
								<Check class={checkIconClass} />
							{:else}
								<X class={xIconClass} />
							{/if}
						</td>

						<td class="table-cell-fit">
							{#if row.original.has_app_ads_direct}
								<Check class={checkIconClass} />
							{:else}
								<X class={xIconClass} />
							{/if}
						</td>

						<td class="table-cell-fit">
							{#if row.original.has_app_ads_reseller}
								<Check class={checkIconClass} />
							{:else}
								<X class={xIconClass} />
							{/if}
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>
