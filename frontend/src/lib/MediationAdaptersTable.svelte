<script lang="ts">
	import ExportAsCSV from '#lib/components/data-table/ExportAsCSV.svelte';
	import Pagination from '#lib/components/data-table/Pagination.svelte';
	import { formatNumberLocale } from '#lib/utils/formatNumber.js';
	import { createAppTable, createTableState } from '#lib/components/data-table/index.js';
	import { genericColumns } from '#lib/components/data-table/generic-column.js';

	import CompanyButton from './CompanyButton.svelte';

	interface MediationAdapter {
		adapter_company_domain: string;
		adapter_company_name?: string | null;
		adapter_logo_url?: string | null;
		app_count: number;
	}

	type DataTableProps = {
		adapters: MediationAdapter[];
	};

	let { adapters }: DataTableProps = $props();
	const [pagination, onPaginationChange] = createTableState({ pageIndex: 0, pageSize: 10 });

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

	const table = createAppTable({
		get data() {
			return adapters;
		},

		columns,
		initialState: {
			sorting: [{ id: 'app_count', desc: true }]
		},
		state: {
			get pagination() {
				return pagination();
			}
		},
		onPaginationChange
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
									companyLogoUrl={row.original.adapter_logo_url ?? undefined}
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
					Adapters detected with this company's mediation platform.
				</span>
			</div>
		</footer>
	</div>
</div>
