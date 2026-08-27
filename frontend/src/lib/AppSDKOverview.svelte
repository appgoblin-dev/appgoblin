<script lang="ts">
	import WhiteCard from '$lib/WhiteCard.svelte';
	import CompanyButton from '$lib/CompanyButton.svelte';

	import { page } from '$app/state';

	import type { AppSDKsOverview, CompanyTypes, AppFullDetail } from '../types';

	interface Props {
		myapp: AppFullDetail;
		myPackageInfo: AppSDKsOverview;
		companyTypes: CompanyTypes;
	}

	let { myapp, myPackageInfo, companyTypes }: Props = $props();
</script>

<h2 class="text-lg font-bold">{myapp.name} SDKs Summary</h2>
{#if typeof myPackageInfo == 'string'}
	<p>Permissions, SDKs and trackers info not yet available for {myapp.name}.</p>
{:else if myPackageInfo.company_categories && myapp.sdk_successful_last_crawled}
	<div class="space-y-3 text-sm leading-relaxed">
		<p>
			<strong>{myapp.name}</strong> was last scanned for SDKs on
			<span class="font-semibold">{myapp.sdk_last_crawled}</span>.
			{#if Object.keys(myPackageInfo.company_categories).length == 0}
				No known SDKs were detected. Check the
				<a href="/apps/{page.params.id}/sdks" class="anchor">raw list of SDK parts detected here</a>
				and feel free to request unknown SDKs be added to AppGoblin.
			{:else}
				Below is the overview of third-party companies detected in the app. The full list of
				<a href="/apps/{page.params.id}/sdks" class="anchor"
					>SDKs, permissions and unknowns is available here</a
				>.
			{/if}
		</p>
	</div>
	{#if Object.keys(myPackageInfo.company_categories).length > 0}
		<div class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-1 md:gap-4">
			{#each Object.keys(myPackageInfo.company_categories) as category (category)}
				<WhiteCard>
					{#snippet title()}
						<a href="/apps/{page.params.id}/sdks" class="text-base anchor">
							{myapp.name} has
							{myPackageInfo.company_categories[category].length}
							{companyTypes.types.find((x: { url_slug: string }) => x.url_slug === category)
								?.name || category} SDKs
						</a>
					{/snippet}
					<div class="grid grid-cols-2 gap-1 p-2">
						{#each myPackageInfo.company_categories[category].slice(0, 4) as company}
							<CompanyButton
								companyName={company.company_name}
								companyDomain={company.company_domain}
								companyLogoUrl={company.company_logo_url}
							/>
						{/each}
					</div>
				</WhiteCard>
			{/each}
		</div>
	{/if}
{:else}
	<p>App not yet scanned for SDKs.</p>
{/if}
