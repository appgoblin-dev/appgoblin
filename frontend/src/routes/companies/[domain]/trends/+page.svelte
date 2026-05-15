<script lang="ts">
	import CompanyTrendsDash from '$lib/CompanyTrendsDash.svelte';
	import WhiteCard from '$lib/WhiteCard.svelte';
	import type { CompanyTrendsDetails } from '../../../../types';

	interface Props {
		data: CompanyTrendsDetails;
	}

	let { data }: Props = $props();

	let companyName = $derived(
		data.companyTree.is_secondary_domain
			? data.companyTree.queried_domain
			: data.companyTree.company_name ||
					data.companyTree.company_domain ||
					data.companyTree.queried_domain
	);
</script>

<p class="mb-4 text-sm">
	Quarterly market share trends for {companyName}, separated into iOS and Android signal pools so
	SDK/API and app-ads.txt DIRECT movement can be compared without cross-platform distortion.
</p>

<WhiteCard>
	{#snippet title()}
		<span>{companyName}'s Quarterly Trends</span>
	{/snippet}
	<CompanyTrendsDash trends={data.companyTrends} companyName={companyName || ''} />
</WhiteCard>
