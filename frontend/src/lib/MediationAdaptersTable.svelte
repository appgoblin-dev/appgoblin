<script lang="ts" generics="TValue">
	import {
		type PaginationState,
		getCoreRowModel,
		getPaginationRowModel,
		getSortedRowModel,
		getFilteredRowModel
	} from '@tanstack/table-core';

	import ExportAsCSV from '$lib/components/data-table/ExportAsCSV.svelte';
	import Pagination from '$lib/components/data-table/Pagination.svelte';
	import { formatNumberLocale } from '$lib/utils/formatNumber';
	import { createSvelteTable } from '$lib/components/data-table/index.js';
	import { genericColumns } from '$lib/components/data-table/generic-column';

	import CompanyButton from './CompanyButton.svelte';

	interface MediationAdapter {
		adapter_string: string;
		adapter_company_domain: string;
		adapter_company_name: string;
		adapter_logo_url: string;
		app_category: string;
		app_count: number;
	}

	type DataTableProps<TValue> = {
		adapters: MediationAdapter[];
	};

	let { adapters }: DataTableProps<TValue> = $props();
	let pagination = $state<PaginationState>({ pageIndex: 0, pageSize: 10 });

	const columns = genericColumns([
		{
			title: 'Adapter',
			accessorKey: 'adapter_company_domain',
			isSortable: true
		},
		{
			title: 'Apps',
			accessorKey: 'app_count',
			isSortable: true
		}
	]);

	const table = createSvelteTable({
		get data() {
			return adapters;
		},

		columns,
		initialState: {
			sorting: [{ id: 'app_count', desc: true }]
		},
		state: {
			get pagination() {
				return pagination;
			}
		},
		getSortedRowModel: getSortedRowModel(),
		getCoreRowModel: getCoreRowModel(),
		getPaginationRowModel: getPaginationRowModel(),
		getFilteredRowModel: getFilteredRowModel(),
		onPaginationChange: (updater) => {
			if (typeof updater === 'function') {
				pagination = updater(pagination);
			} else {
				pagination = updater;
			}
		}
	});
</script>

<div class="table-container space-y-4">
	<div class="overflow-x-auto pl-0">
		<table class="table table-hover table-auto w-full text-xs md:text-sm">
			<thead>
				<tr>
					<th class="table-cell-fit"></th>
					<th class="table-cell-fit">Adapter</th>
					<th class="table-cell-fit">Apps</th>
				</tr>
			</thead>
			<tbody>
				{#each table.getRowModel().rows as row (row.id)}
					<tr class="px-0">
						<td class="table-cell-fit text-gray-500 text-xs md:text-sm">
							{row.index + 1}
						</td>
						<td class="table-cell-fit">
							{#if row.original.adapter_company_name}
								<CompanyButton
									companyName={row.original.adapter_company_name}
									companyDomain={row.original.adapter_company_domain}
									companyLogoUrl={row.original.adapter_logo_url}
									size="md"
								/>
							{:else}
								<CompanyButton companyDomain={row.original.adapter_company_domain} size="md" />
							{/if}
						</td>
						<td class="table-cell-fit">
							{formatNumberLocale(row.original.app_count)}
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
		<footer class="flex justify-between">
			<div class="flex items-center justify-end space-x-2 py-4 gap-2">
				<Pagination tableModel={table} />
				<ExportAsCSV {table} filename="mediation_adapters" />
				<span class="text-xs md:text-sm text-gray-500">
					Mediation adapters used by this company's apps.
				</span>
			</div>
		</footer>
	</div>
</div>
