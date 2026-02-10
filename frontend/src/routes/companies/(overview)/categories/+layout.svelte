<script lang="ts">
	import { page } from '$app/state';

	let { data, children } = $props();

	let category_title = $derived(getCategoryName(page.params.category || ''));

	function getCategoryName(category: string) {
		if (category) {
			return (
				data?.appCats?.categories?.find((cat: { id: string }) => cat.id == category)?.name ||
				category
			);
		}
		return '';
	}

	let title = $derived(`${category_title} Apps Top Companies | AppGoblin`);
	let description = $derived(
		`Explore ${category_title} apps' biggest companies. Detailed analytics for ${category_title} apps and competitor analysis.`
	);
	let keywords = $derived(
		`${category_title}, android, ios, adtech, advertising network, data tracking, mobile measurement, programmatic advertising, app-ads.txt, mobile advertising, ad tech analytics, AppGoblin`
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

<main>
	{@render children()}
</main>
