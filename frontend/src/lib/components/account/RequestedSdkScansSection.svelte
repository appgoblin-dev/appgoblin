<script lang="ts">
	import { enhance } from '$app/forms';
	import type { AccountFormResult, RequestedSdkScan } from './types';

	let {
		scans,
		form
	}: {
		scans: RequestedSdkScan[];
		form?: AccountFormResult;
	} = $props();
</script>

<section class="space-y-4">
	<h2 class="text-lg font-semibold">Requested SDK Scans</h2>
	<p class="text-sm text-surface-500">
		Submit new scan requests and view your recent request history.
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
			<p class="text-sm text-surface-500">No scan requests yet.</p>
		{:else}
			{#each scans as scan (scan.id)}
				<div class="rounded-lg border border-surface-100-900 p-3">
					<p class="font-medium">
						{#if scan.app_name}
							<a class="hover:underline" href={`/apps/${scan.store_id}`}>{scan.app_name}</a>
						{:else}
							<a class="hover:underline" href={`/apps/${scan.store_id}`}>{scan.store_id}</a>
						{/if}
					</p>
					<p class="text-xs text-surface-500">
						Requested {new Date(scan.created_at).toLocaleString()}
					</p>
				</div>
			{/each}
		{/if}
	</div>
</section>
