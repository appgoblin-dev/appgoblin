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

{#if typeof myPackageInfo == 'string'}
	<p>Permissions, SDKs and trackers info not yet available for {myapp.name}.</p>
{:else if myPackageInfo.company_categories && myapp.sdk_successful_last_crawled}
	<div class="">
		<p class="p-2 md:p-4">
			<span class="text-primary-900-100">{myapp.name}</span> was last scanned for SDKs
			<span class="text-primary-900-100">{myapp.sdk_last_crawled}</span>.
			{#if Object.keys(myPackageInfo.company_categories).length == 0}
				No known SDKs were detected, so check the <a href="/apps/{page.params.id}/sdks"
					>raw list of SDK parts detected here</a
				> and feel free to request unknown SDKs and companies be added to AppGoblin.
			{:else}
				Below is the overview of third party companies detected in the app. The full list of raw <a
					href="/apps/{page.params.id}/sdks"
				>
					SDKs, app permissions and unknown SDKs is available here</a
				>.
			{/if}
		</p>
	</div>
	{#if Object.keys(myPackageInfo.company_categories).length > 0}
		<div class="grid grid-cols-1 md:grid-cols-2 gap-1">
			{#each Object.keys(myPackageInfo.company_categories) as category}
				<WhiteCard>
					{#snippet title()}
						<span class="text-sm font-semibold">
							AppGoblin saw {myapp.name} uses
							{myPackageInfo.company_categories[category].length}
							{companyTypes.types.find((x: { url_slug: string }) => x.url_slug === category)
								?.name || category}
						</span>
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
