<script lang="ts">
	import CompanyTrendsDash from '#lib/CompanyTrendsDash.svelte';
	import CompanySectionLink from '#lib/utils/CompanySectionLink.svelte';
	import type { CompanyTrendsDetails } from '../../../../types';
	import ApiDataNote from '#lib/ApiDataNote.svelte';

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

<section class="mb-4 space-y-2">
	<h2 class="text-xl font-semibold">Quarterly Trends</h2>
	<p class="mb-4 text-sm">
		Quarterly market share trends for {companyName}, separated into iOS and Android signal pools so
		SDK/API and app-ads.txt DIRECT movement can be compared without cross-platform distortion.
		Explore <CompanySectionLink slug="sdks">SDKs</CompanySectionLink>,
		<CompanySectionLink slug="app-adstxt">app-ads.txt publisher IDs</CompanySectionLink>,
		<CompanySectionLink slug="apps-added">recently added apps</CompanySectionLink>, and
		<CompanySectionLink slug="apps-lost">recently lost apps</CompanySectionLink> for more detail.
	</p>
</section>

<CompanyTrendsDash trends={data.companyTrends} />
<ApiDataNote endpoint={'/api/v1/companies/{company_domain}'} />
