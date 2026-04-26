<script lang="ts">
	import { page } from '$app/state';
	import SideBarCatsListBoxItem from './SideBarCatsListBoxItem.svelte';
	import CardFirst from './CardFirst.svelte';
	import type { CatData, StoreIDLookup } from '../types';

	interface Props {
		myCatData: CatData;
		baseUrl: string;
		storeIDLookup: StoreIDLookup;
	}
	let store = $state('google');

	$effect(() => {
		store = page.params.store!;
	});
	let { myCatData, baseUrl, storeIDLookup }: Props = $props();

	let selectedCategory = $state('overall');

	$effect(() => {
		if (page.params.category) {
			selectedCategory = page.params.category;
		} else {
			selectedCategory = 'overall';
		}
	});

	const buttonSelectedClass = 'p-1 preset-filled-secondary-100-900';
	const buttonDeselectedClass = 'p-1';

	function classesActiveStore(store: string) {
		return page.params.store!.toLowerCase() == store.toLowerCase()
			? buttonSelectedClass
			: buttonDeselectedClass;
	}
</script>

<div class="p-1 md:p-2">
	<CardFirst>
		{#snippet header()}
			<h4 class="h5 md:h4">Stores</h4>
		{/snippet}
		<nav class="list-nav">
			<ul>
				{#each Object.entries(storeIDLookup) as [_prop, values]}
					<li>
						<a href={`${baseUrl}/${values.store_name.toLowerCase()}/${selectedCategory}`}>
							<p class={classesActiveStore(values.store_name)}>
								{values.store_name}
							</p>
						</a>
					</li>
				{/each}
			</ul>
		</nav>
	</CardFirst>
</div>

<div class="p-1 md:p-2">
	<CardFirst>
		{#snippet header()}
			<h4 class="h5 md:h4">App Categories</h4>
		{/snippet}
		{#if myCatData && myCatData.categories}
			{#each Object.entries(myCatData.categories) as [_prop, values]}
				{#if values.id && (Number(values.android) > 0 || values.name == 'Games')}
					<a href="{baseUrl}/{store}/{values.id}" class="text-tertiary-900-100 hover:underline">
						<SideBarCatsListBoxItem {values} {selectedCategory} />
					</a>
				{/if}
			{/each}
		{/if}
	</CardFirst>
</div>
