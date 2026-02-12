<script lang="ts">
	import type { CompanyFullDetails } from '../../../../types';
	import MediationAdaptersTable from '$lib/MediationAdaptersTable.svelte';
	import WhiteCard from '$lib/WhiteCard.svelte';

	interface Props {
		data: CompanyFullDetails;
	}

	let { data }: Props = $props();
</script>

{#if data.companyDetails && data.companyDetails.mediation_adapters}
	<WhiteCard>
		{#snippet title()}
			<span
				>{data.companyTree.queried_company_name || data.companyTree.queried_company_domain}'s
				Mediation Adapters</span
			>
		{/snippet}
		<MediationAdaptersTable adapters={data.companyDetails.mediation_adapters} />
	</WhiteCard>
{:else}
	<p class="text-center p-4">No mediation adapters found for this company.</p>
{/if}
