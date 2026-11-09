<script lang="ts">
	import { page } from '$app/state';
	import SideBarCatsListBoxItem from './SideBarCatsListBoxItem.svelte';
	import type { SideBarCategoryData } from '../types';

	function getBaseUrl(url: string, type: string | undefined) {
		const parts = url.split('/').filter(Boolean);
		let newUrl = url;

		if (type) {
			// This is working on /companies/types/[type]
			// returns current url as baseUrl

			if (parts.length == 4) {
				// This is working on /companies/types/[type]/[category]
				newUrl = `/companies/types/${parts[2]}`;
			}
		} else if (parts[0] === 'companies') {
			if (parts.length == 1 || (parts.length == 2 && parts[1] === 'browse-data')) {
				// All-company table and category routes share the same category base.
				// console.log("newURL hardcoded");
				newUrl = '/companies/categories';
			} else if (parts.length == 2) {
				// this is not used
			} else if (parts.length == 3) {
				if (parts[2] == 'overall') {
					newUrl = `/companies/${parts[1]}`;
				} else {
					// this is working on /companies/[company]/[category]
					// this is working on /companies/categories[category]
					// console.log("newURL 3", parts.slice(2).join('/'));
					newUrl = `/companies/${parts[1]}`;
				}
			}
		}
		// console.log("newURL",newUrl);

		return newUrl;
	}

	let baseUrl = $derived(getBaseUrl(page.url.pathname.toString(), page.params.type));

	interface Props {
		myCatData: SideBarCategoryData;
	}

	let { myCatData }: Props = $props();

	let selectedCategory = $derived(page.params.category || 'overall');
</script>

<div class="p-1 md:p-2">
	<div class="rounded border border-surface-100-900 bg-surface-100-900/30 p-4 md:p-5">
		<header>
			<h4 class="h5 md:h4">App Categories</h4>
			<hr class="mb-2 border-surface-100-900" />
		</header>
		{#if myCatData}
			{#each Object.entries(myCatData.categories) as [_prop, values] (values.id)}
				{#if values.id && (values.android || values.name == 'Games')}
					{#if values.id != 'overall'}
						<a href="{baseUrl}/{values.id}" class="text-tertiary-900-100 hover:underline">
							<SideBarCatsListBoxItem {values} {selectedCategory} />
						</a>
					{:else if baseUrl == '/companies/categories' && values.id == 'overall'}
						<a href="/companies/browse-data" class="text-tertiary-900-100 hover:underline">
							<SideBarCatsListBoxItem {values} {selectedCategory} />
						</a>
					{:else}
						<a href={baseUrl} class="text-tertiary-900-100 hover:underline">
							<SideBarCatsListBoxItem {values} {selectedCategory} />
						</a>
					{/if}
				{/if}
			{/each}
		{/if}
	</div>
</div>
