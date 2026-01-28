<script lang="ts" generics="TData, TValue">
	import AppCard from './AppCard.svelte';

	import CompanyButton from './CompanyButton.svelte';

	let { app, size = 'lg' }: { app: any; size: 'lg' | 'sm' | 'md' } = $props();
</script>

<div class="grid grid-cols-1 gap-2">
	<AppCard {app} showHeader={false} />
	<div>
		<p class="text-primary-700-300">
			Ads Last Seen:<span class="text-primary-900-100 mx-2">{app.last_seen}</span>
		</p>
		<p class="text-primary-700-300">
			Creatives:<span class="text-primary-900-100 mx-2">{app.unique_creatives}</span>
		</p>
		<p class="text-primary-700-300">
			Apps seen publishing ads:<span class="text-primary-900-100 mx-2">{app.unique_publishers}</span
			>
		</p>
		{#if app.mmp_domains && app.mmp_domains.length > 0}
			<p class="text-primary-700-300">
				MMPs:<span class="text-primary-900-100 mx-2">{app.mmp_domains.length}</span>
			</p>
		{/if}

		{#if app.ad_networks && app.ad_networks.length > 0}
			<p class="text-primary-700-300">Ad Networks:</p>
			<div class="grid grid-cols-2 md:grid-cols-3 gap-1 md:gap-2">
				{#each app.ad_networks as ad_network}
					<CompanyButton
						companyDomain={ad_network.domain}
						companyLogoUrl={ad_network.company_logo_url}
						{size}
					/>
				{/each}
			</div>
		{/if}
	</div>
</div>
