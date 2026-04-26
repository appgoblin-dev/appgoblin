<script lang="ts">
	import type { PageData } from './$types';
	import type { AccountFormResult } from '$lib/components/account/types';
	import TrackedAppsSection from '$lib/components/account/TrackedAppsSection.svelte';
	import TrackedCompaniesSection from '$lib/components/account/TrackedCompaniesSection.svelte';
	import TrackedKeywordsSection from '$lib/components/account/TrackedKeywordsSection.svelte';
	import RequestedSdkScansSection from '$lib/components/account/RequestedSdkScansSection.svelte';

	let { data, form }: { data: PageData; form?: AccountFormResult | null } = $props();
	let accountData = $derived(data);
	let accountForm = $derived(form);
</script>

<svelte:head>
	<title>Account Overview - AppGoblin</title>
</svelte:head>

<div class="space-y-6">
	<div class="p-6 md:p-8 space-y-6">
		<div class="border-b border-surface-300-700 pb-4">
			<h1 class="text-2xl font-bold">Account Overview</h1>
			<p class="text-sm">Manage your watchlists for apps, companies, and keywords</p>
		</div>

		<TrackedAppsSection apps={accountData.followedApps ?? []} form={accountForm ?? undefined} />
		<TrackedCompaniesSection
			companies={accountData.followedCompanies ?? []}
			form={accountForm ?? undefined}
		/>
		<TrackedKeywordsSection
			keywords={accountData.trackedKeywords ?? []}
			form={accountForm ?? undefined}
		/>
		<RequestedSdkScansSection
			scans={accountData.requestedSdkScans ?? []}
			form={accountForm ?? undefined}
		/>
	</div>
</div>
