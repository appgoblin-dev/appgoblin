<script lang="ts">
	import { page } from '$app/state';
	import SideBarCatsListBoxItem from './SideBarCatsListBoxItem.svelte';
	import CardFirst from './CardFirst.svelte';
	import type { CatData } from '../types';

	const listClass = 'flex flex-col';

	interface Props {
		myCatData: CatData;
		baseUrl: string;
		storeIDLookup: Record<number, any>;
	}
	let store = $state('google');

	$effect(() => {
		store = page.params.store!;
	});
	let { myCatData, baseUrl, storeIDLookup }: Props = $props();

	let selectedStore = $state('google');
	let selectedCategory = $state('overall');

	$effect(() => {
		selectedStore = page.params.store!;
	});

	$effect(() => {
		if (page.params.category) {
			selectedCategory = page.params.category;
		} else {
			selectedCategory = 'overall';
		}
	});

	const buttonSelectedClass = 'preset-outlined-primary-900-100 text-left relative  rounded-md p-2';
	const buttonDeselectedClass = 'p-1 md:p-2 text-tertiary-900-100 text-left hover:';

	function classesActiveStore(store: string) {
		return page.params.store!.toLowerCase() == store.toLowerCase()
			? buttonSelectedClass
			: buttonDeselectedClass;
	}

	function classesActiveCollection(period: string) {
		return page.params.period!.toLowerCase() == period.toLowerCase()
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
						<a
							href={`${baseUrl}/${page.params.period}/${values.store_name.toLowerCase()}/${selectedCategory}`}
						>
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
			<h4 class="h5 md:h4">Time</h4>
		{/snippet}
		<div class={listClass}>
			<a href={`${baseUrl}/new_yearly/${store}/${selectedCategory}`}>
				<p class={classesActiveCollection('new_yearly')}>New this Year</p>
			</a>
			<a href={`${baseUrl}/new_monthly/${store}/${selectedCategory}`}>
				<p class={classesActiveCollection('new_monthly')}>New this Month</p>
			</a>
			<a href={`${baseUrl}/new_weekly/${store}/${selectedCategory}`}>
				<p class={classesActiveCollection('new_weekly')}>New this Week</p>
			</a>
		</div>
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
					<a
						href="{baseUrl}/{page.params.period}/{store}/{values.id}"
						class="text-tertiary-900-100 hover:underline"
					>
						<SideBarCatsListBoxItem {values} {selectedCategory} />
					</a>
				{/if}
			{/each}
		{/if}
	</CardFirst>
</div>
