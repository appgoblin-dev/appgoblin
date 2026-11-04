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
	<!-- Cross-link to data exports docs -->
	<div class="px-4 md:px-6">
		<div class="preset-tonal p-3 rounded-lg flex flex-wrap items-center gap-2">
			<p class="text-sm flex-1">
				Looking for CSV column definitions?
				<a href="/docs/data-exports" class="underline font-semibold whitespace-nowrap"
					>View the Data Exports Guide →</a
				>
			</p>
		</div>
	</div>

	<div class="px-4 md:px-6">
		<h1 class="text-2xl font-bold md:text-3xl">API Documentation</h1>
	</div>

	<div class="px-4 md:px-6">
		<h2 class="mb-2 text-lg font-semibold">AI Agents & MCP Setup</h2>
		<p class="mb-1">Connect your AI agent using the MCP Streamable HTTP endpoint:</p>
		<code class="mb-2 block px-3 py-2 font-mono text-sm break-all"
			>https://appgoblin.info/api/v1/mcp</code
		>
		<p>
			Authenticate with your API key via the <code class="px-1"
				>Authorization: Bearer <token></token></code
			>
			header.
		</p>
	</div>

	<div class="px-4 md:px-6">
		<h2 class="mb-2 text-lg font-semibold">B2B SDK Intelligence</h2>
		<p class="text-sm md:text-base">
			The public API also exposes app version timelines and SDK change history through
			<code class="px-1">/api/v1/apps/{'{store_id}'}/versions</code> and
			<code class="px-1">/api/v1/apps/{'{store_id}'}/sdks/history</code>. These endpoints require a
			B2B SDK or B2B Premium API token.
		</p>
		<div class="mt-3 flex flex-wrap items-center gap-3">
			<a href="/pricing" class="btn preset-filled-primary-500 p-2 text-sm font-semibold">
				See Paid API Plans & Pricing
			</a>
			<a href="/docs/data-exports" class="btn preset-outlined-surface-100-900 p-2 text-sm">
				Paid Datasets Guide
			</a>
		</div>
	</div>

	<iframe
		title="API Documentation"
		src={docsUrl}
		class="block min-h-[82vh] w-full border-0 bg-white"
		loading="eager"
	></iframe>
</div>
