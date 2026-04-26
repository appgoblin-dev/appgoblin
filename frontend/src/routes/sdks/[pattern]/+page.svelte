<script lang="ts">
	import { page } from '$app/state';
	let pattern = page.params.pattern;
	import SDKOverviewTable from '$lib/SDKOverviewTable.svelte';
	let { data } = $props();
	import WhiteCard from '$lib/WhiteCard.svelte';
	import CompanyButton from '$lib/CompanyButton.svelte';
</script>

<h1 class="text-2xl font-bold break-all">{pattern}</h1>

<div class="p-2 md:p-4">
	<div class="grid grid-cols-1 md:grid-cols-2 gap-2 md:gap-6 p-2 md:p-4">
		<WhiteCard>
			{#snippet title()}
				Info
			{/snippet}
			<p class="p-2 md:p-4 text-sm md:text-base">
				These are apps and companies that had some part of an Android Manifest, Info.plist,
				directories or files that matched this string. Matching apps:
			</p>
		</WhiteCard>

		{#await data.matchedCompanies}
			loading
		{:then myMatchedCompanies}
			{#if myMatchedCompanies.companies.length > 0}
				<WhiteCard>
					{#snippet title()}
						Companies
					{/snippet}
					<p class="p-2 md:p-4 text-sm md:text-base">
						These are the companies that have apps that matched this string.
					</p>
					<div class="flex flex-wrap gap-2 justify-center p-2 md:p-4">
						{#each myMatchedCompanies.companies as company}
							<CompanyButton
								companyName={company.company_name}
								companyDomain={company.company_domain}
							/>
						{/each}
					</div>
				</WhiteCard>
			{:else}
				<p class="p-2 md:p-4 text-sm md:text-base">
					No companies matched this string, if you know how to match this string, please contact us
					on Discord.
				</p>
			{/if}
		{/await}

		{#await data.matchedApps}
			loading
		{:then myMatchedApps}
			<div>
				<WhiteCard>
					{#snippet title()}
						Android Apps
					{/snippet}
					{#if myMatchedApps.android_overview.length > 0}
						<SDKOverviewTable entries_table={myMatchedApps.android_overview} is_ios={false} />
					{:else}
						<p class="p-2 md:p-4 text-sm md:text-base">No matching Android apps found.</p>
					{/if}
				</WhiteCard>
			</div>
			<div>
				<WhiteCard>
					{#snippet title()}
						iOS Apps
					{/snippet}
					{#if myMatchedApps.ios_overview.length > 0}
						<SDKOverviewTable entries_table={myMatchedApps.ios_overview} is_ios={true} />
					{:else}
						<p class="p-2 md:p-4 text-sm md:text-base">No matching iOS apps found.</p>
					{/if}
				</WhiteCard>
			</div>
		{/await}
	</div>
</div>
