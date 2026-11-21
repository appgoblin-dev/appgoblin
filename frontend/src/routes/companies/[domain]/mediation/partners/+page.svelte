<script lang="ts">
	import type { CompanyLayoutDetails } from '../../../../../types';
	import CompanyButton from '#lib/CompanyButton.svelte';
	import WhiteCard from '#lib/WhiteCard.svelte';
	import CompanySectionLink from '#lib/utils/CompanySectionLink.svelte';
	import { formatNumberLocale } from '#lib/utils/formatNumber.js';

	let { data }: { data: CompanyLayoutDetails } = $props();
</script>

<section class="mb-4 space-y-2">
	<h2 class="text-xl font-semibold">As an Adapter: Top Mediation Partners</h2>
	<p class="text-sm mb-3">
		These mediation platforms are associated with this company's adapter in detected apps. Results
		use the exact domain and sum the available adapter counts across app categories; apps present in
		multiple source rows may be counted more than once. Explore this company
		<CompanySectionLink slug="mediation">as a mediation partner</CompanySectionLink> to see its adapters.
	</p>
</section>

{#if data.mediationPartners === null}
	<p class="text-center p-4">Mediation partner data is currently unavailable.</p>
{:else if data.mediationPartners.length}
	<WhiteCard>
		{#snippet title()}
			<span>Top Mediation Partners</span>
		{/snippet}
		<div class="overflow-x-auto p-4">
			<table class="table table-hover w-full text-xs md:text-sm">
				<thead>
					<tr>
						<th class="text-left">Mediation partner</th>
						<th class="text-left">Summed app count</th>
					</tr>
				</thead>
				<tbody>
					{#each data.mediationPartners as partner (partner.mediation_domain)}
						<tr>
							<td><CompanyButton companyDomain={partner.mediation_domain} /></td>
							<td>{formatNumberLocale(partner.app_count)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</WhiteCard>
{:else}
	<p class="text-center p-4">No mediation partners found for this adapter domain.</p>
{/if}
