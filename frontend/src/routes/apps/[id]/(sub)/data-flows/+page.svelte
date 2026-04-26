<script lang="ts">
	import WhiteCard from '$lib/WhiteCard.svelte';
	import AppAPICallsTable from '$lib/AppAPICallsTable.svelte';
	import CompanyButton from '$lib/CompanyButton.svelte';

	import RequestSDKScanButton from '$lib/RequestSDKScanButton.svelte';
	import { countryCodeToEmoji } from '$lib/utils/countryCodeToEmoji';

	let { data }: { data: any } = $props();

	function getDataStats(apis: any) {
		const uniqueRunIds = new Set(apis.map((api: any) => api.run_id)).size;
		const uniqueTldUrls = new Set(apis.map((api: any) => api.tld_url)).size;
		const creativesFound = apis.filter((api: any) => api.creative_md5_hash).length;
		const countries = [...new Set(apis.map((api: any) => api.country).filter(Boolean))] as string[];

		// Get unique TLD URLs with their company names
		const tldUrlsMap = new Map<string, { tld_url: string; company_name: string | null }>();
		apis.forEach((api: any) => {
			if (api.tld_url && !tldUrlsMap.has(api.tld_url)) {
				tldUrlsMap.set(api.tld_url, {
					tld_url: api.tld_url,
					company_name: api.company_name || null
				});
			}
		});
		const uniqueTldUrlsList = Array.from(tldUrlsMap.values());

		return {
			uniqueRunIds,
			uniqueTldUrls,
			creativesFound,
			countries,
			uniqueTldUrlsList
		};
	}
	const cardClass = 'p-4 bg-surface-100-900 rounded-md';
</script>

<div class="p-2 md:p-16 mt-2 md:mt-4">
	<h4 class="h4 md:h3 p-2">Data calls made by {data.myapp.name}</h4>

	{#await data.apis}
		Loading API data...
	{:then apis}
		{#if typeof apis == 'string' || apis.apis.length == 0}
			<p>API calls data not yet available for this app.</p>
			<RequestSDKScanButton />
		{:else if apis.apis && Object.keys(apis.apis).length > 0}
			{@const stats = getDataStats(apis.apis)}
			<p class="mb-4">
				Overview of network connections made by <strong>{data.myapp.name}</strong> during the first 60
				seconds after installation.
			</p>

			<div class={cardClass}>
				<p class="text-base leading-relaxed">
					<strong class="">{data.myapp.name}</strong> contacted
					<strong>{stats.uniqueTldUrls} different domains</strong>
					within the first minute of opening. This data was collected from
					<strong>{stats.uniqueRunIds} independent scan{stats.uniqueRunIds !== 1 ? 's' : ''}</strong
					>
					We identified
					<strong>{stats.creativesFound} ad creative{stats.creativesFound !== 1 ? 's' : ''}</strong>
					being loaded, confirming active ad monetization.
					{#if stats.countries.length > 0}
						across servers in {stats.countries.map((c) => countryCodeToEmoji(c)).join(' ')}
					{/if}, providing transparency into the app's actual network behavior and data sharing
					practices.
				</p>
			</div>

			<!-- Data Statistics Summary -->
			<div class="grid grid-cols-2 md:grid-cols-4 gap-4 my-6">
				<div class={cardClass}>
					<p class="text-sm">Scan Runs</p>
					<p class="text-2xl font-bold">{stats.uniqueRunIds}</p>
				</div>
				<div class={cardClass}>
					<p class="text-sm">Unique Domains</p>
					<p class="text-2xl font-bold">{stats.uniqueTldUrls}</p>
				</div>
				<div class={cardClass}>
					<p class="text-sm">Ad Creatives Found</p>
					<p class="text-2xl font-bold">{stats.creativesFound}</p>
				</div>
				<div class={cardClass}>
					<p class="text-sm">Countries</p>
					<p class="text-2xl">
						{#each stats.countries as country}
							<span class="mr-1">{countryCodeToEmoji(country)}</span>
						{/each}
					</p>
				</div>
			</div>

			<!-- Unique Domain Companies -->
			<div class="my-6">
				<h5 class="text-lg font-semibold mb-3">Contacted Domains ({stats.uniqueTldUrls})</h5>
				<div class="flex flex-wrap gap-2">
					{#each stats.uniqueTldUrlsList as tldInfo}
						<CompanyButton
							companyName={`${tldInfo.tld_url} (${tldInfo.company_name || 'Unknown'})`}
							companyDomain={tldInfo.tld_url}
						/>
					{/each}
				</div>
			</div>

			<WhiteCard>
				{#snippet title()}
					APIs
				{/snippet}
				<AppAPICallsTable data={apis.apis} />
			</WhiteCard>
		{/if}
	{/await}
</div>
