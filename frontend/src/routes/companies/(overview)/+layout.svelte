<script lang="ts">
	import CompaniesLayout from '$lib/CompaniesLayout.svelte';
	import WhiteCard from '$lib/WhiteCard.svelte';
	import CompaniesBarChart from '$lib/CompaniesBarChart.svelte';
	import TotalsBox from '$lib/TotalsBox.svelte';
	import { page } from '$app/state';
	import SideBar from '$lib/SideBar.svelte';
	import { Dialog, Portal } from '@skeletonlabs/skeleton-svelte';

	let { data, children } = $props();

	let currentType = $derived(
		page.data.companyTypes.types.find(
			(type: { url_slug: string }) => type.url_slug === page.params.type
		) || { name: 'All Companies & Domains', url_slug: 'all-companies' }
	);

	let currentCategoryName = $derived(getCategoryName(page.params.category));

	function getCategoryName(category: string | undefined) {
		return (
			page.data?.appCats?.categories?.find((cat: { id: string }) => cat.id == category)?.name ||
			category ||
			'All'
		);
	}
</script>

<div class="flex items-center mb-2">
	<h1 class="h1 text-3xl font-bold text-primary-900-100">
		<span class="text-primary-700-300">{currentType ? currentType.name : ''}</span>
		for
		<span class="text-primary-700-300">{currentCategoryName ? currentCategoryName : 'All'}</span>
		Apps
	</h1>
</div>
<!-- 
<CompaniesLayout>
	{#snippet card1()}
		<WhiteCard>
			{#snippet title()}
				Totals
			{/snippet}
			{#if typeof page.data.companiesOverview == 'string'}
				<p class="text-red-500 text-center">Failed to load company details.</p>
			{:else}
				<TotalsBox
					companyName=""
					myTotals={page.data.companiesOverview.categories.categories.all}
					myType={currentType}
				/>
			{/if}
		</WhiteCard>
	{/snippet}

	{#snippet card2()}
		<WhiteCard>
			{#snippet title()}
				Top Companies (Android SDKs)
			{/snippet}
			<CompaniesBarChart plotData={page.data.companiesOverview.top.sdk_android} />
		</WhiteCard>
	{/snippet}
	{#snippet card3()}
		<WhiteCard>
			{#snippet title()}
				Top Companies (iOS SDKs)
			{/snippet}
			<CompaniesBarChart plotData={page.data.companiesOverview.top.sdk_ios} />
		</WhiteCard>
	{/snippet}
</CompaniesLayout> -->

<div class="grid grid-cols-1 md:grid-cols-[auto_1fr]">
	<aside class="hidden md:block">
		<div>
			<SideBar
				myCatData={data.appCats}
				storeIDLookup={data.storeIDLookup}
				collectionIDLookup={data.collectionIDLookup}
				categoryIDLookup={data.categoryIDLookup}
			/>
		</div>
	</aside>

	<main>
		{@render children?.()}
	</main>

	<div class="md:hidden sticky bottom-0 bg-surface-50-950 p-2">
		<!-- Small screen version of the side bar -->
		<Dialog>
			<Dialog.Trigger class="btn preset-filled">APP FILTERS</Dialog.Trigger>
			<Portal>
				<Dialog.Positioner class="fixed inset-0 z-50 flex justify-start">
					<Dialog.Content
						class="h-screen card bg-surface-100-900 w-sm p-4 space-y-4 shadow-xl max-w-[320px]"
					>
						<SideBar
							myCatData={data.appCats}
							storeIDLookup={data.storeIDLookup}
							collectionIDLookup={data.collectionIDLookup}
							categoryIDLookup={data.categoryIDLookup}
						/>
					</Dialog.Content>
				</Dialog.Positioner>
			</Portal>
		</Dialog>
	</div>
</div>
