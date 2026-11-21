<script lang="ts">
	import type { CompanyFullDetails } from '../../../../types';
	import MediationAdaptersTable from '#lib/MediationAdaptersTable.svelte';
	import WhiteCard from '#lib/WhiteCard.svelte';
	import CompanySectionLink from '#lib/utils/CompanySectionLink.svelte';

	interface Props {
		data: CompanyFullDetails;
	}

	let { data }: Props = $props();
</script>

<section class="mb-4 space-y-2">
	<h2 class="text-xl font-semibold">As a Mediation Partner: Top Adapters</h2>
	<p class="text-sm mb-3">
		These adapters are detected in apps where this company acts as the mediation partner. Counts
		show the apps associated with each adapter. Explore this company
		<CompanySectionLink slug="mediation-partners">as an adapter</CompanySectionLink> to see its mediation
		partners.
	</p>
</section>

{#if data.companyDetails?.mediation_adapters?.length}
	<WhiteCard>
		{#snippet title()}
			<span
				>{data.companyTree.company_name ||
					data.companyTree.company_domain ||
					data.companyTree.queried_domain}'s Mediation Adapters</span
			>
		{/snippet}
		<MediationAdaptersTable adapters={data.companyDetails.mediation_adapters} />
	</WhiteCard>
{:else}
	<p class="text-center p-4">No mediation adapters found for this company.</p>
{/if}
