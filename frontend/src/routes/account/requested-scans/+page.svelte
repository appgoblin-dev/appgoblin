<script lang="ts">
	import type { PageData } from './$types';
	import type { AccountFormResult } from '#lib/components/account/types.js';
	import RequestedSdkScansSection from '#lib/components/account/RequestedSdkScansSection.svelte';

	let { data, form }: { data: PageData; form?: AccountFormResult | null } = $props();
</script>

<svelte:head>
	<title>My SDK Scans - AppGoblin</title>
</svelte:head>

<div class="p-6 md:p-8 space-y-6">
	<div class="border-b border-surface-300-700 pb-4">
		<h1 class="text-2xl font-bold">My SDK Scans</h1>
		<p class="text-sm text-surface-600-400">Request an SDK scan and follow its progress.</p>
	</div>

	<RequestedSdkScansSection
		scans={data.requestedSdkScans}
		pagination={data.pagination}
		form={form ?? undefined}
	/>
</div>
