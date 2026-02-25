<script lang="ts">
	import { page } from '$app/state';

	import SideBarRankings from './SideBarRankings.svelte';
	import SideBarCollections from './SideBarCollections.svelte';
	import SideBarCompanies from './SideBarCompanies.svelte';
	import SideBarFastestGrowingApps from './SideBarFastestGrowingApps.svelte';
	import type { CatData, StoreIDLookup } from '../types';

	interface Props {
		myCatData: CatData;
		storeIDLookup: StoreIDLookup;
		collectionIDLookup: Record<number, any>;
		categoryIDLookup: Record<number, any>;
	}

	let { myCatData, storeIDLookup, collectionIDLookup, categoryIDLookup }: Props = $props();

	let store = $state(1);
	$effect(() => {
		store = +page.params.store!;
	});
	let collection = $state(1);
	$effect(() => {
		collection = +page.params.collection!;
	});
	let category = $state(1);
	$effect(() => {
		category = +page.params.category!;
	});
	// Logic to adjust collection and category based on the store's value
	$effect(() => {
		// If store is not a number (NaN), default it to 1
		if (isNaN(store)) {
			store = 1;
		}

		switch (store) {
			case 2:
				collection = 4;
				category = 120;
				break;
			case 1:
			default: // Defaults for store=1 or any other value not explicitly handled
				collection = 1;
				category = 1;
				break;
		}
	});
</script>

{#if page.url.pathname.startsWith('/collections')}
	<SideBarCollections {myCatData} baseUrl="/collections" {storeIDLookup} />
{/if}

{#if page.url.pathname.startsWith('/rankings')}
	<SideBarRankings {storeIDLookup} {collectionIDLookup} {categoryIDLookup} />
{/if}

{#if (page.url.pathname == '/companies' || page.url.pathname.startsWith('/companies')) && !page.url.pathname.includes('adstxt')}
	<SideBarCompanies {myCatData} />
{/if}

{#if page.url.pathname.startsWith('/fastest-growing-apps')}
	<SideBarFastestGrowingApps {myCatData} baseUrl="/fastest-growing-apps" {storeIDLookup} />
{/if}
