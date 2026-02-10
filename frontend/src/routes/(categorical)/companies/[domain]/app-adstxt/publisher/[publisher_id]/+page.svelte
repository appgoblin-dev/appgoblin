<script lang="ts">
	import { page } from '$app/state';
	import CompanyPubAppsTable from '$lib/CompanyPubAppsTable.svelte';
	import WhiteCard from '$lib/WhiteCard.svelte';
	let { data } = $props();
	const tree = $derived(
		(data as { companyTree?: { queried_company_name?: string; queried_company_domain?: string } })
			.companyTree
	);
	let companyName = $derived(
		tree?.queried_company_name || tree?.queried_company_domain || page.params.domain
	);
</script>

<div class="space-y-4">
	<h1 class="text-2xl font-bold text-primary-900-100">Publisher ID: {page.params.publisher_id}</h1>
	<WhiteCard>
		{#snippet title()}
			{companyName}'s Publisher Overview
		{/snippet}
		<div class="p-2">
			<p class="">
				This {page.params.domain} publisher ID is related via the developer URL's app-ads.txt to the following
				apps and developers. One or two developers is best with the appropriate number of apps from that
				developer:
			</p>

			<div class="space-y-4">
				{#await data.publishersApps then publishersApps}
					<div class="grid grid-cols-3 gap-4">
						<!-- Header row -->
						<div class="col-start-2 text-center font-semibold">Google Play Store</div>
						<div class="text-center font-semibold">Apple App Store</div>

						<!-- Developers row -->
						<div class="font-semibold">Developers</div>
						<div class="text-center">
							<div>Direct: {publishersApps.totals.direct_google_devs}</div>
							<div>Reseller: {publishersApps.totals.reseller_google_devs}</div>
						</div>
						<div class="text-center">
							<div>Direct: {publishersApps.totals.direct_apple_devs}</div>
							<div>Reseller: {publishersApps.totals.reseller_apple_devs}</div>
						</div>

						<!-- Apps row -->
						<div class="font-semibold">Apps</div>
						<div class="text-center">
							<div>Direct: {publishersApps.totals.direct_google_apps}</div>
							<div>Reseller: {publishersApps.totals.reseller_google_apps}</div>
						</div>
						<div class="text-center">
							<div>Direct: {publishersApps.totals.direct_apple_apps}</div>
							<div>Reseller: {publishersApps.totals.reseller_apple_apps}</div>
						</div>
					</div>
				{/await}
			</div>
		</div>
	</WhiteCard>
	<div class="space-y-4">
		{#await data.publishersApps}
			<loading class="text-center">Loading...</loading>
		{:then publishersApps}
			<h2 class="text-2xl font-bold text-primary-900-100">Apps DIRECT</h2>
			<div class="grid grid-cols-1 md:grid-cols-2 gap-2 md:gap-6">
				{#if publishersApps.apps.google.direct.length > 0}
					<WhiteCard>
						{#snippet title()}
							{companyName}'s Google Apps (Direct)
						{/snippet}
						<CompanyPubAppsTable entries_table={publishersApps.apps.google.direct} />
					</WhiteCard>
				{/if}
				{#if publishersApps.apps.apple.direct.length > 0}
					<WhiteCard>
						{#snippet title()}
							{companyName}'s Apple Apps (Direct)
						{/snippet}
						<CompanyPubAppsTable entries_table={publishersApps.apps.apple.direct} />
					</WhiteCard>
				{/if}
			</div>
			<hr class="my-4" />

			<h2 class="text-2xl font-bold text-primary-900-100">Apps RESELLER</h2>
			<div class="grid grid-cols-1 md:grid-cols-2 gap-2 md:gap-6">
				{#if publishersApps.apps.google.reseller.length == 0 && publishersApps.apps.apple.reseller.length == 0}
					<p>No RESLLER apps found for this publisher ID.</p>
				{:else if publishersApps.apps.google.reseller.length > 0}
					<WhiteCard>
						{#snippet title()}
							{companyName}'s Google Apps
						{/snippet}
						<CompanyPubAppsTable entries_table={publishersApps.apps.google.reseller} />
					</WhiteCard>
				{:else if publishersApps.apps.apple.reseller.length > 0}
					<WhiteCard>
						{#snippet title()}
							{companyName}'s Apple Apps
						{/snippet}
						<CompanyPubAppsTable entries_table={publishersApps.apps.apple.reseller} />
					</WhiteCard>
				{/if}
			</div>
		{/await}
	</div>
	<hr class="my-4" />
	<WhiteCard>
		{#snippet title()}
			{companyName}'s Full List of Apps
		{/snippet}
		<p class="p-2">
			Full lists of apps, app-ads.txt, metrics and more are available. Please see <a href="/pricing"
				>pricing page</a
			>
		</p>
	</WhiteCard>
</div>
