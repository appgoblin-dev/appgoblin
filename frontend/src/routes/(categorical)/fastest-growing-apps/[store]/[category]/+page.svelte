<script lang="ts">
	let { data } = $props();
	import FastestGrowingAppsTable from '$lib/FastestGrowingAppsTable.svelte';
	import { page } from '$app/state';

	let category_title = $derived(getCategoryTitle(page.params.category || ''));

	let storeTitle = $derived(getStoreTitle(page.params.store || ''));

	function getStoreTitle(store: string) {
		if (store) {
			return store.charAt(0).toUpperCase() + store.slice(1);
		}
		return '';
	}

	function getCategoryTitle(category: string) {
		if (category) {
			return (
				data?.appCats?.categories?.find((cat: { id: string }) => cat.id == category)?.name ||
				category
			);
		}
		return '';
	}

	let title = $derived(`${storeTitle} ${category_title} Fastest Growing Apps`);
	let description = $derived(
		`Explore ${storeTitle} ${category_title} fastest growing apps by weekly installs. See the most recent high growth apps for marketing research and competitor analysis.`
	);
	let keywords = $derived(
		`${storeTitle}, ${category_title}, growth apps, growth hacking, marketing, marketing research, competitor analysis, apps by advertising, apps by in app purchases`
	);
</script>

<svelte:head>
	<title>{title}</title>
	<link rel="canonical" href={page.url.href} />
	<meta name="description" content={description} />
	<meta name="keywords" content={keywords} />
	<meta property="og:title" content={title} />
	<meta property="og:description" content={description} />
	<meta name="twitter:title" content={title} />
	<meta name="twitter:description" content={description} />

	<meta property="og:image" content="https://appgoblin.info/goblin_purple_hat_250.png" />
	<meta property="og:url" content={page.url.href} />
	<meta property="og:type" content="website" />
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:image" content="https://appgoblin.info/goblin_purple_hat_250.png" />
</svelte:head>

<div class="p-2 px-2 md:px-16 lg:px-32">
	<h1 class="text-3xl">Fastest Growing Apps</h1>
	<p class="text-sm">
		AppGoblin's weekly list of the fastest growing apps on the Apple and Google Play App Stores.
	</p>
	<FastestGrowingAppsTable data={data.growthApps.apps} />
</div>
