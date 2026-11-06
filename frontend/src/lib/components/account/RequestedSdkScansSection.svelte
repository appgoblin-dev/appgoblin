<script lang="ts">
	import { enhance } from '$app/forms';
	import { resolve } from '$app/paths';
	import type { AccountFormResult, RequestedSdkScan } from './types';
	import RequestedScanDetails from './RequestedScanDetails.svelte';
	import AppSummary from './AppSummary.svelte';

	let {
		scans,
		pagination,
		form
	}: {
		scans: RequestedSdkScan[];
		pagination: { page: number; pageSize: number; hasNext: boolean };
		form?: AccountFormResult;
	} = $props();
</script>

<section class="space-y-4">
	<p class="text-sm text-surface-500">
		Submit new scan requests and view your request history, newest first.
	</p>

	<form method="POST" action="?/addRequestedSdkScan" use:enhance class="flex gap-2">
		<input
			type="text"
			name="store_id"
			class="input flex-1"
			placeholder="App store ID (example: com.example.app)"
			required
		/>
		<button type="submit" class="btn preset-tonal">Request Scan</button>
	</form>

	{#if form?.section === 'requested-scans' && form?.message}
		<p class="text-sm {form.success ? 'text-success-600' : 'text-error-600'}">{form.message}</p>
	{/if}

	<div class="space-y-2">
		{#if scans.length === 0}
			<p class="text-sm text-surface-500">
				{pagination.page === 1 ? 'No scan requests yet.' : 'No scan requests on this page.'}
			</p>
		{:else}
			{#each scans as scan (scan.id)}
				<div class="rounded-lg border border-surface-100-900 p-3">
					<div class="flex flex-wrap items-start justify-between gap-3">
						<div class="min-w-0">
							<AppSummary
								storeId={scan.store_id}
								href={resolve('/apps/[id]', { id: scan.store_id })}
							/>
							<p class="mt-1 text-xs text-surface-500">
								{scan.created_at
									? `Requested ${new Date(scan.created_at).toLocaleString()}`
									: 'Request date unavailable'}
							</p>
						</div>
						<a
							href={resolve('/apps/[id]/(sub)/sdks', { id: scan.store_id })}
							class="btn btn-sm preset-tonal">View Latest SDKs</a
						>
					</div>
					<RequestedScanDetails id={scan.id} />
				</div>
			{/each}
		{/if}
	</div>
	{#if pagination.page > 1 || pagination.hasNext}
		<nav aria-label="Scan request pages" class="flex items-center gap-3 text-sm">
			{#if pagination.page > 1}<a
					class="btn btn-sm preset-tonal"
					href={resolve(
						`/account/requested-scans?page=${pagination.page - 1}&pageSize=${pagination.pageSize}`
					)}>Previous</a
				>{/if}
			<span>Page {pagination.page}</span>
			{#if pagination.hasNext}<a
					class="btn btn-sm preset-tonal"
					href={resolve(
						`/account/requested-scans?page=${pagination.page + 1}&pageSize=${pagination.pageSize}`
					)}>Next</a
				>{/if}
		</nav>
	{/if}
</section>
