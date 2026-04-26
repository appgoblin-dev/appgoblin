<script lang="ts" generics="TData, TValue">
	import AppCard from './AppCard.svelte';

	import CompanyButton from './CompanyButton.svelte';

	let { app, size = 'lg' }: { app: any; size: 'lg' | 'sm' | 'md' } = $props();

	const labelClass = 'text-base text-surface-500';
	const valueClass = 'text-base';

	const metricRows = $derived([
		{ label: 'Ads Last Seen', value: app.last_seen },
		{ label: 'Creatives', value: app.unique_creatives },
		{ label: 'Apps seen publishing ads', value: app.unique_publishers },
		...(app.mmp_domains?.length > 0 ? [{ label: 'MMPs', value: app.mmp_domains.length }] : [])
	]);
</script>

<div class="grid grid-cols-1 gap-2">
	<AppCard {app} showHeader={false} />
	<div>
		{#each metricRows as row}
			<p>
				<span class={labelClass}>{row.label}:</span>
				<span class={`${valueClass} mx-2`}>{row.value}</span>
			</p>
		{/each}

		{#if app.ad_networks && app.ad_networks.length > 0}
			<p class={labelClass}>Ad Networks:</p>
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
