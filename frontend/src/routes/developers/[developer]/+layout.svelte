<script lang="ts">
	import { Tabs } from '@skeletonlabs/skeleton-svelte';

	import { page } from '$app/state';

	let { children, data } = $props();
</script>

<svelte:head>
	<link rel="canonical" href={page.url.href} />
	{#await data.devs then dev}
		<title>{dev.title} | {page.params.developer} | Apps, SDKs and Market Data</title>
		<meta
			name="description"
			content="Explore {dev.title}'s Android & iOS apps, their SDKs, trackers and analytics with AppGoblin. Gather free ASO information on the top mobile developers."
		/>
		<meta
			name="keywords"
			content="{dev.title}, {page.params
				.developer}, developer, app publisher, analytics, ads, market data, Android app rankings, app reviews, download statistics, Google Play data, app comparison, mobile app insights, Android"
		/>
		<meta
			property="og:title"
			content="{dev.title} Developer Stats & App Info - AppGoblin | {page.params.developer}"
		/>
		<meta
			property="og:description"
			content="Explore {dev.title} Android & iOS app analytics and market trends with AppGoblin. {dev.title} by {page
				.params
				.developer}. Dive into detailed app rankings and download statistics to inform your Android & iOS app strategy and discover top-performing apps."
		/>
		<meta
			name="twitter:title"
			content="{dev.title} Android & iOS | {page.params.developer} | App Stats & Info - AppGoblin"
		/>
		<meta
			name="twitter:description"
			content="Explore {dev.title} Android & iOS app analytics and market trends with AppGoblin. {dev.title} by {page
				.params
				.developer}. Dive into detailed app rankings and download statistics to inform your Android & iOS app strategy and discover top-performing apps."
		/>

		<meta property="og:image" content="https://appgoblin.info/goblin_purple_hat_250.png" />
		<meta property="og:url" content={page.url.href} />
		<meta property="og:type" content="website" />
		<meta name="twitter:card" content="summary_large_image" />
		<meta name="twitter:image" content="https://appgoblin.info/goblin_purple_hat_250.png" />
		<meta name="robots" content="index, follow" />
	{/await}
</svelte:head>

<div>
	<h1 class="h2 p-2">
		Developer: <p class="">{page.params.developer}</p>
	</h1>
	<Tabs defaultValue="apps">
		<Tabs.List>
			<Tabs.Trigger value="apps"
				><a href={`/developers/${page.params.developer}`}>Apps</a></Tabs.Trigger
			>
			<Tabs.Trigger value="sdks"
				><a href={`/developers/${page.params.developer}/sdks`}>SDKs</a></Tabs.Trigger
			>
		</Tabs.List>

		{@render children?.()}
	</Tabs>
</div>
