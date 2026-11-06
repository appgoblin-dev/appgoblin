<script lang="ts">
	import type { PageData } from './$types';
	import type { AccountFormResult } from '#lib/components/account/types.js';
	import TrackedAppsSection from '#lib/components/account/TrackedAppsSection.svelte';
	import TrackedCompaniesSection from '#lib/components/account/TrackedCompaniesSection.svelte';
	import TrackedKeywordsSection from '#lib/components/account/TrackedKeywordsSection.svelte';

	let { data, form }: { data: PageData; form?: AccountFormResult | null } = $props();
	let accountData = $derived(data);
	let accountForm = $derived(form);
</script>

<svelte:head>
	<title>Watchlists - AppGoblin</title>
</svelte:head>

<div class="space-y-6">
	<div class="p-6 md:p-8 space-y-6">
		<div class="border-b border-surface-300-700 pb-4">
			<h1 class="text-2xl font-bold">Watchlists</h1>
			<p class="text-sm text-surface-600-400">
				Manage the apps, companies, and keywords tied to your account.
			</p>
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
	</div>
</div>
