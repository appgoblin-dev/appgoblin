<script lang="ts">
	import { page } from '$app/state';

	const title = 'API Docs | AppGoblin Public API';
	const description =
		'AppGoblin API and MCP docs for free and paid users, including API token auth, schemas, and interactive endpoint browsing.';
	const keywords =
		'api docs, appgoblin api, mcp, public api, api token, scalar api reference, api reference';

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

	<div class="grid gap-4 px-4 md:grid-cols-2 md:px-6">
		<section>
			<h2 class="mb-2 text-lg font-semibold">API key</h2>
			<p class="mb-1">
				Get an API key from <a href="https://appgoblin.info/account/api-keys"
					>your AppGoblin account</a
				>.
			</p>
			<p>
				Authenticate with your API key via the
				<code class="px-1">Authorization: Bearer &lt;token&gt;</code> header.
			</p>
		</section>

		<section>
			<h2 class="mb-2 text-lg font-semibold">AI Agents & MCP Setup</h2>
			<p class="mb-1">Connect your AI agent using the MCP Streamable HTTP endpoint:</p>
			<code class="mb-2 block px-3 py-2 font-mono text-sm break-all"
				>https://appgoblin.info/api/v1/mcp</code
			>
		</section>

		<section>
			<h2 class="mb-2 text-lg font-semibold">Paid B2B SDK and Premium Intelligence</h2>
			<p class="text-sm md:text-base">
				Some endpoints are marked as paid and require a B2B subscription.
			</p>
			<div class="mt-3 flex flex-wrap items-center gap-3">
				<a href="/pricing" class="btn preset-filled-primary-50-950 p-2 text-sm font-semibold">
					See Paid API Plans & Pricing
				</a>
				<!-- Cross-link to data exports docs -->
				<div class="px-4 md:px-6">
					<p>Looking for CSV column definitions?</p>
					<a href="/docs/data-exports">View the Data Exports Guide →</a>
				</div>
			</div>
		</section>
	</div>

	<iframe
		title="API Documentation"
		src={docsUrl}
		class="block min-h-[82vh] w-full border-0 bg-white"
		loading="eager"
	></iframe>
</div>
