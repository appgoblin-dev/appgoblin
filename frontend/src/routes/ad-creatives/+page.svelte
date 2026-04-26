<script lang="ts">
	import AdCreativesReport from '$lib/AdCreativesReport.svelte';
	import type { PageData } from './$types';

	let { data = {} as PageData }: { data?: PageData } = $props();
	let pageTitle = $derived(data.pageTitle || 'Ad Creative Explorer | AppGoblin');
	let pageDescription = $derived(
		data.pageDescription ||
			'Browse top mobile advertising videos and images for inspiration and competitor analysis.'
	);
	let canonicalUrl = $derived(data.canonicalUrl || 'https://appgoblin.info/ad-creatives');
</script>

<svelte:head>
	<title>{pageTitle}</title>
	<meta name="description" content={pageDescription} />
	<meta property="og:title" content={pageTitle} />
	<meta property="og:description" content={pageDescription} />
	<meta property="og:url" content={canonicalUrl} />
	<meta property="og:type" content="website" />
	<meta name="robots" content="index, follow" />
	<link rel="canonical" href={canonicalUrl} />
</svelte:head>

<AdCreativesReport {data} />
