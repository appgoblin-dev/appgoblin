<script lang="ts">
	import { page } from '$app/state';

	const title = 'API Docs | AppGoblin Public API';
	const description =
		'Generated OpenAPI reference for the AppGoblin public v1 API, including API token authentication, schemas, and interactive endpoint browsing.';
	const keywords =
		'api docs, openapi, appgoblin api, public api, api token, scalar api reference, api reference';

	const docsUrl = $derived.by(() => {
		const { hostname, origin } = page.url;
		const backendOrigin =
			hostname === 'localhost' || hostname === '127.0.0.1' ? 'http://localhost:8000' : origin;
		return `${backendOrigin}/api/v1/docs/openapi`;
	});
</script>

<svelte:head>
	<title>{title}</title>
	<link rel="canonical" href="https://appgoblin.info/api-docs" />
	<meta name="description" content={description} />
	<meta name="keywords" content={keywords} />
	<meta property="og:title" content={title} />
	<meta property="og:description" content={description} />
	<meta property="og:url" content="https://appgoblin.info/api-docs" />
	<meta property="og:type" content="website" />
	<meta property="og:image" content="https://appgoblin.info/goblin_purple_hat_250.png" />
	<meta name="twitter:title" content={title} />
	<meta name="twitter:description" content={description} />
	<meta name="twitter:card" content="summary" />
</svelte:head>
<div class="space-y-4 py-4 md:py-6">
	<div class="px-4 md:px-6">
		<h1 class="text-2xl font-bold md:text-3xl">API Documentation</h1>
	</div>

	<iframe
		title="API Documentation"
		src={docsUrl}
		class="block min-h-[82vh] w-full border-0 bg-white"
		loading="eager"
	></iframe>
</div>
