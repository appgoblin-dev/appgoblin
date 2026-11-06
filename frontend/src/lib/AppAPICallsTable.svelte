<script lang="ts">
	import type { ColumnFiltersState, SortingState } from '@tanstack/svelte-table';

	import CompanyButton from './CompanyButton.svelte';
	import RequestMappingButton from './RequestMappingButton.svelte';

	import { countryCodeToEmoji } from './utils/countryCodeToEmoji';

	import Pagination from '#lib/components/data-table/Pagination.svelte';
	import ExportAsCSV from '#lib/components/data-table/ExportAsCSV.svelte';
	import type { AppAPICall } from '../types';

	import {
		createAppTable,
		createTableState,
		FlexRender
	} from '#lib/components/data-table/index.js';

	import { genericColumns } from '#lib/components/data-table/generic-column.js';

	type DataTableProps = {
		data: AppAPICall[];
		initialFilter?: string;
	};

	function formatDate(date: string | null) {
		if (!date) return '—';
		return new Date(date).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit',
			second: '2-digit',
			hour12: false
		});
	}

	const [pagination, onPaginationChange] = createTableState({ pageIndex: 0, pageSize: 50 });
	const [sorting, onSortingChange] = createTableState<SortingState>([]);
	const [columnFilters, onColumnFiltersChange] = createTableState<ColumnFiltersState>([]);
	const [globalFilter, onGlobalFilterChange] = createTableState('');

	let { data, initialFilter = '' }: DataTableProps = $props();

	const columns = genericColumns([
		{
			title: 'Called At',
			accessorKey: 'called_at',
			isSortable: true
		},
		{
			title: 'URL',
			accessorKey: 'url',
			isSortable: true
		},
		{ title: 'Servers', accessorKey: 'servers', isSortable: true },
		{ title: 'Content Type', accessorKey: 'response_mime_type', isSortable: true },
		{ title: 'Ad Creative Found', accessorKey: 'creative_md5_hash', isSortable: true }
	]);

	// eslint-disable-next-line @typescript-eslint/no-explicit-any -- tanstack row type is not exported for this feature set
	const globalFilterFn = (row: any, _columnId: string, filterValue: string) => {
		const tld_url = row.original.tld_url?.toLowerCase() ?? '';
		const url = row.original.url?.toLowerCase() ?? '';
		const company = row.original.company_name?.toLowerCase() ?? '';
		const query = filterValue.toLowerCase();
		return tld_url.includes(query) || url.includes(query) || company.includes(query);
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

	$effect(() => {
		if (initialFilter) {
			table.setGlobalFilter(initialFilter);
		}
	});
</script>

<div class="table-container">
	<div class="flex items-center p-2">
		<input
			placeholder="Filter by URL or company..."
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
							<th class="">
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
					<tr class="px-0 text-xs md:text-sm overflow-x-auto">
						<td>
							{formatDate(row.original.called_at)}
						</td>
						<td class="flex flex-col space-y-1">
							{#if row.original.company_domain}
								<CompanyButton
									companyName={row.original.company_name ?? row.original.company_domain}
									companyDomain={row.original.company_domain}
									companyLogoUrl={row.original.company_logo_url ?? undefined}
								/>
							{:else}
								<div class="flex flex-wrap items-center gap-2">
									<span class="text-sm">{row.original.tld_url}</span>
									<RequestMappingButton
										mapType="company_domain_name"
										valueToBeMapped={row.original.tld_url}
										label="Request Mapping"
									/>
								</div>
							{/if}
							<p class="text-xs md:text-sm break-all">{row.original.url}</p>
						</td>
						<td>
							{#if row.original.country}
								{countryCodeToEmoji(row.original.country)}
							{/if}
							{row.original.servers}
						</td>
						<td class="flex-col"
							><p>Request: {row.original.request_mime_type}</p>
							<p>Response: {row.original.response_mime_type}</p></td
						>
						<td
							>{#if row.original.creative_md5_hash}
								<img
									src={'https://media.appgoblin.info/creatives/thumbs/' +
										row.original.creative_md5_hash +
										'.jpg'}
									alt={row.original.creative_md5_hash}
									class="w-16 h-auto object-contain rounded-lg shadow-md"
									loading="lazy"
								/>
							{/if}
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
		<footer class="flex justify-between">
			<div class="flex items-center justify-end space-x-2 py-4">
				<Pagination tableModel={table} />
				<ExportAsCSV {table} filename="appgoblin_apps" />
			</div>
		</footer>
	</div>
</div>
