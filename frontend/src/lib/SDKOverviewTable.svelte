<script lang="ts">
	import StoreIcon from './StoreIcon.svelte';
	import { formatNumber } from '#lib/utils/formatNumber.js';
	import type { SdkOverview } from '../types';
	import { createAppTable } from '#lib/components/data-table/index.js';
	import { genericColumns } from '#lib/components/data-table/generic-column.js';

	interface Props {
		entries_table: SdkOverview[];
		previewMode?: boolean;
		showMatchPath?: boolean;
	}

	let { entries_table, previewMode = false, showMatchPath = false }: Props = $props();

	function tableHasRemoved(table: SdkOverview[]) {
		return table.some((row) => row.is_removed != null);
	}

	const baseColumns = [
		{ title: 'Matched SDK String', accessorKey: 'value_name', isSortable: true },
		{ title: 'Match Path', accessorKey: 'xml_path', isSortable: true },
		{ title: 'App', accessorKey: 'app_name', isSortable: true },
		{ title: 'Store', accessorKey: 'store', isSortable: true },
		{ title: 'Category', accessorKey: 'category', isSortable: true },
		{ title: 'Developer', accessorKey: 'developer_name', isSortable: true },
		{ title: 'Installs', accessorKey: 'installs', isSortable: true },
		{ title: 'Monthly Installs', accessorKey: 'installs_sum_4w', isSortable: true },
		{ title: 'Removed', accessorKey: 'is_removed', isSortable: true }
	];

	const table = createAppTable({
		get data() {
			return previewMode ? entries_table.slice(0, 3) : entries_table;
		},
		get columns() {
			return genericColumns(
				baseColumns.filter(
					(column) =>
						(column.accessorKey !== 'is_removed' || tableHasRemoved(entries_table)) &&
						(column.accessorKey !== 'xml_path' || showMatchPath)
				)
			);
		}
	});
</script>

<div class="table-container space-y-4 p-2 md:p-4">
	<div class="overflow-x-auto pl-0">
		<table class="table table-hover table-auto w-full text-xs md:text-sm">
			<thead>
				<tr>
					<th class="table-cell-fit">#</th>
					<th class="table-cell-fit">Matched SDK String</th>
					{#if showMatchPath}<th class="table-cell-fit">Match Path</th>{/if}
					<th class="table-cell-fit">App</th>
					<th class="table-cell-fit">Store</th>
					<th class="table-cell-fit">Category</th>
					<th class="table-cell-fit">Developer</th>
					<th class="table-cell-fit">Installs</th>
					<th class="table-cell-fit">Monthly Installs</th>
					{#if tableHasRemoved(entries_table)}<th class="table-cell-fit">Removed</th>{/if}
				</tr>
			</thead>
			<tbody>
				{#each table.getRowModel().rows as row (row.id)}
					<tr class="px-0">
						<td class="table-cell-fit text-gray-500">{row.index + 1}</td>
						<td class="table-cell-fit truncate max-w-48">
							<a href={`/sdks/${row.original.value_name}`} rel="nofollow"
								>{row.original.value_name}</a
							>
						</td>
						{#if showMatchPath}<td class="table-cell-fit">{row.original.xml_path ?? '-'}</td>{/if}
						<td class="table-cell-fit">
							<a href={`/apps/${row.original.store_id}`} class="flex items-center gap-2">
								<img
									src={row.original.app_icon_url}
									alt={row.original.app_name}
									class="w-8 h-8 rounded"
								/>
								<div class="flex flex-col">
									{row.original.app_name}
									<p class="text-xs text-surface-900-100">{row.original.developer_name ?? '-'}</p>
								</div>
							</a>
						</td>
						<td class="table-cell-fit"><StoreIcon store={row.original.store} /></td>
						<td class="table-cell-fit">{row.original.category ?? '-'}</td>
						<td class="table-cell-fit">{row.original.developer_name ?? '-'}</td>
						<td class="table-cell-fit">{formatNumber(row.original.installs)}</td>
						<td class="table-cell-fit">{formatNumber(row.original.installs_sum_4w)}</td>
						{#if tableHasRemoved(entries_table)}<td class="table-cell-fit"
								>{row.original.is_removed === true ? 'Yes' : '-'}</td
							>{/if}
					</tr>
				{/each}
				{#if previewMode && entries_table.length > 3}
					{#each { length: Math.min(2, entries_table.length - 3) } as _, index}
						<tr class="px-0 opacity-30">
							<td class="table-cell-fit text-gray-500">{index + 4}</td>
							<td class="table-cell-fit"><div class="h-3 w-32 rounded bg-surface-200-800"></div></td
							>
							{#if showMatchPath}
								<td class="table-cell-fit"
									><div class="h-3 w-32 rounded bg-surface-200-800"></div></td
								>
							{/if}
							<td class="table-cell-fit"><div class="h-3 w-40 rounded bg-surface-200-800"></div></td
							>
							<td class="table-cell-fit"><div class="h-3 w-20 rounded bg-surface-200-800"></div></td
							>
							<td class="table-cell-fit"><div class="h-3 w-20 rounded bg-surface-200-800"></div></td
							>
							<td class="table-cell-fit"><div class="h-3 w-24 rounded bg-surface-200-800"></div></td
							>
							<td class="table-cell-fit"><div class="h-3 w-16 rounded bg-surface-200-800"></div></td
							>
							<td class="table-cell-fit"><div class="h-3 w-20 rounded bg-surface-200-800"></div></td
							>
							{#if tableHasRemoved(entries_table)}
								<td class="table-cell-fit"
									><div class="h-3 w-10 rounded bg-surface-200-800"></div></td
								>
							{/if}
						</tr>
					{/each}
					<tr class="px-0">
						<td colspan="99" class="text-center py-4">
							<p class="text-sm opacity-70">
								<a href="/pricing" class="font-semibold underline hover:text-primary-600-400"
									>Upgrade to B2B</a
								>
								{showMatchPath ? 'to access the full report' : 'to see all apps'}
							</p>
						</td>
					</tr>
				{/if}
			</tbody>
		</table>
	</div>
</div>
