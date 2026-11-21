<script lang="ts">
	import type { PageData } from './$types';
	import AdCard from '#lib/AdCard.svelte';
	import WhiteCard from '#lib/WhiteCard.svelte';
	import ChevronLeft from '@lucide/svelte/icons/chevron-left';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import ApiDataNote from '#lib/ApiDataNote.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	const PAGE_SIZE = 8;
	let currentPage = $state(0);

	let totalPages = $derived(
		data.companyCreatives ? Math.ceil(data.companyCreatives.length / PAGE_SIZE) : 0
	);

	let paginatedCreatives = $derived(
		data.premiumB2B && data.companyCreatives
			? data.companyCreatives.slice(currentPage * PAGE_SIZE, (currentPage + 1) * PAGE_SIZE)
			: (data.companyCreatives ?? [])
	);

	function goToPage(page: number) {
		currentPage = page;
	}
</script>

<section class="mb-4 space-y-2">
	<h2 class="text-xl font-semibold">Creatives</h2>
	<p class="mb-3">These are some of the recent creatives tracked by AppGoblin.</p>
	<p class="text-base">
		Full creatives for a company are available on
		<a href="/pricing">B2B plans</a>. Some additional creatives can be browsed free on AppGoblin's
		<a href="/ad-creatives">ad creatives explorer</a>.
	</p>
</section>

{#if data.companyCreatives && data.companyCreatives.length > 0}
	<WhiteCard>
		{#snippet title()}
			<span
				>Recent Creatives from {data.companyTree.company_name ||
					data.companyTree.company_domain ||
					data.companyTree.queried_domain}</span
			>
		{/snippet}
		<div class="grid grid-cols-3 gap-2 p-2">
			{#each paginatedCreatives as creative (creative.md5_hash)}
				<div class="card p-2">
					<AdCard {creative} />
				</div>
			{/each}
		</div>
	</WhiteCard>

	{#if data.premiumB2B && totalPages > 1}
		<div class="flex items-center justify-center gap-4 mt-4">
			<button
				type="button"
				class="btn btn-sm preset-outlined-primary-100-900 p-2"
				disabled={currentPage === 0}
				onclick={() => goToPage(currentPage - 1)}
			>
				<ChevronLeft size={16} />
			</button>
			<span class="text-sm font-medium">
				Page {currentPage + 1} of {totalPages}
			</span>
			<button
				type="button"
				class="btn btn-sm preset-outlined-primary-100-900 p-2"
				disabled={currentPage >= totalPages - 1}
				onclick={() => goToPage(currentPage + 1)}
			>
				<ChevronRight size={16} />
			</button>
		</div>
	{/if}
{:else}
	<p class="text-center p-4">No creatives found for this company.</p>
{/if}
<ApiDataNote endpoint={'/api/v1/advertisers/{host_domain}/creatives'} />
