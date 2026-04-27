<script lang="ts">
	import PublicApiDocsFrame from '$lib/components/docs/PublicApiDocsFrame.svelte';

	const title = 'API Docs | AppGoblin Public API';
	const description =
		'Generated OpenAPI reference for the AppGoblin public v1 API, including authentication, schemas, and interactive endpoint browsing.';
	const keywords =
		'api docs, openapi, appgoblin api, public api, stoplight elements, api reference';
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

<PublicApiDocsFrame
	title="API Documentation"
	description="Generated OpenAPI reference for the AppGoblin public v1 API, including authentication requirements, schemas, and interactive endpoint browsing."
	backendPath="/api/v1/docs/openapi"
	primaryLabel="Open Raw OpenAPI Docs"
	secondaryHref="/account/api-keys"
	secondaryLabel="Get an API Key"
/>
