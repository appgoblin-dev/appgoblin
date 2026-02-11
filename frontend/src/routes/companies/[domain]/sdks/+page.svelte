<script lang="ts">
	import type { CompanyFullDetails } from '../../../../../types';
	import CompanySDKs from '$lib/CompanySDKs.svelte';
	import WhiteCard from '$lib/WhiteCard.svelte';

	interface Props {
		data: CompanyFullDetails;
	}

	let { data }: Props = $props();
</script>

{#if !data.companyTree.is_secondary_domain}
	<WhiteCard>
		{#snippet title()}
			<span
				>{data.companyTree.queried_company_name || data.companyTree.queried_company_domain}'s
				Company SDKs</span
			>
		{/snippet}
		{#if typeof data.companySdks == 'string'}
			<p class="text-red-500 text-center">Failed to load company SDKs.</p>
		{:else if data.companySdks}
			<CompanySDKs mySdks={data.companySdks} />
		{:else}
			<p class="text-center p-4">No SDKs found for this company.</p>
		{/if}
	</WhiteCard>
{:else}
	<p class="text-center p-4">SDK information is not available for secondary domains.</p>
{/if}
