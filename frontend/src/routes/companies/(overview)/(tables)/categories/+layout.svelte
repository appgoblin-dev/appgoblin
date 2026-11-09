<script lang="ts">
	import { page } from '$app/state';
	import MainContent from '#lib/MainContent.svelte';

	let { data, children } = $props();

	let category_title = $derived(getCategoryName(page.params.category || ''));
	let resolvedCategoryTitle = $derived(category_title || 'All App Categories');

	function getCategoryName(category: string) {
		if (category) {
			return (
				data?.appCats?.categories?.find((cat: { id: string }) => cat.id == category)?.name ||
				category
			);
		}
		return '';
	}

	let title = $derived(`Top Companies in ${resolvedCategoryTitle} Apps | AppGoblin`);
	let description = $derived(
		`Explore the largest companies found in ${resolvedCategoryTitle} apps with SDK, API, and app-ads.txt intelligence for competitor and market analysis.`
	);
	let keywords = $derived(
		`${resolvedCategoryTitle}, android, ios, adtech, advertising network, data tracking, mobile measurement, programmatic advertising, app-ads.txt, mobile advertising, ad tech analytics, AppGoblin`
	);
	let structuredData = $derived({
		'@context': 'https://schema.org',
		'@type': 'CollectionPage',
		name: title,
		description,
		url: page.url.href,
		inLanguage: 'en',
		isPartOf: {
			'@type': 'WebSite',
			name: 'AppGoblin',
			url: 'https://appgoblin.info'
		},
		about: {
			'@type': 'Thing',
			name: resolvedCategoryTitle
		}
	});
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

	<meta
		property="og:image"
		content="https://appgoblin.info/previews/appgoblin_companies_smaller.png"
	/>
	<meta property="og:url" content={page.url.href} />
	<meta property="og:type" content="website" />
	<meta name="twitter:card" content="summary_large_image" />
	<meta
		name="twitter:image"
		content="https://appgoblin.info/previews/appgoblin_companies_smaller.png"
	/>
	<meta name="robots" content="index, follow" />
	{@html `<script type="application/ld+json">${JSON.stringify(structuredData)}</script>`}
</svelte:head>

<MainContent>
	{@render children()}
</MainContent>
