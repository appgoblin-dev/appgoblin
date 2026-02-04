<script lang="ts">
	import { page } from '$app/state';
	let { companyTypes } = $props();

	function isCurrentTab(tab: string): boolean {
		if (tab === 'all') {
			if (
				page.url.pathname === '/companies' ||
				page.url.pathname.startsWith('/companies/categories')
			) {
				return true;
			} else {
				return false;
			}
		} else if (page.url.pathname.startsWith(`/companies/types/${tab}`)) {
			return true;
		} else return false;
	}

	function textColorClass(tab: string) {
		if (isCurrentTab(tab)) {
			return 'text-primary-900-100';
		} else {
			return '';
		}
	}

	function typeTabClass(tab: string) {
		const selectedClass =
			'px-2 md:px-4 py-2 border-t-2 border-r-2 border-l-2 border-primary-100-900 rounded-t-md relative top-[1px] text-primary-900-100';
		const unselectedClass =
			'px-2 md:px-4 py-2 border-b-2 border-surface-800-200 hover:border-primary-300-700 hover:border-b-2 hover:underline';
		if (isCurrentTab(tab)) {
			return selectedClass;
		} else return unselectedClass;
	}

	function getCategoryUrlPart(url: string, tabType: string, category: string) {
		let newUrl = url;

		if (tabType && category) {
			newUrl = `/companies/types/${tabType}/${category}`;
		}
		if (tabType && !category) {
			newUrl = `/companies/types/${tabType}`;
		}
		if (!tabType && !category) {
			newUrl = '/companies';
		}
		if (!tabType && category) {
			newUrl = `/companies/categories/${category}`;
		}
		return newUrl;
	}
</script>

<div class="flex flex-row flex-wrap text-sm md:text-base">
	<a
		href={getCategoryUrlPart(page.url.pathname.toString(), '', page.params.category!)}
		class={typeTabClass('all')}
	>
		<span class={textColorClass('all')}>All</span></a
	>
	{#each companyTypes.types as tab}
		<a
			href={getCategoryUrlPart(page.url.pathname.toString(), tab.url_slug, page.params.category!)}
			class={typeTabClass(tab.url_slug)}
			><span class={textColorClass(tab.url_slug)}>{tab.name}</span></a
		>
	{/each}
</div>
