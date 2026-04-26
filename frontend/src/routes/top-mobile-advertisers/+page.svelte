<script>
	import AdvertiserCreativeRankingsTable from '$lib/AdvertiserCreativeRankingsTable.svelte';
	import WhiteCard from '$lib/WhiteCard.svelte';
	let { data } = $props();

	let pageTitle = 'Top Mobile Advertisers and Creatives';
	let pageDescription =
		'See the top mobile ad buyers this month and their creative strategies based on live android ad campaigns.';
</script>

<svelte:head>
	<title>{pageTitle}</title>

	<!-- Standard meta tags -->
	<meta name="description" content={pageDescription} />
	<meta
		name="keywords"
		content="ad buyers, mobile advertisers, ad creatives, mobile advertising, app marketing, advertising insights, AppGoblin, ad campaigns, ad creatives, ad networks, ad tracking, ad analytics"
	/>

	<!-- Open Graph meta tags -->
	<meta property="og:title" content={pageTitle} />
	<meta property="og:description" content={pageDescription} />
	<meta property="og:image" content="https://appgoblin.info/goblin_purple_hat_250.png" />
	<meta property="og:url" content="https://appgoblin.info/top-mobile-advertisers" />
	<meta property="og:type" content="website" />

	<!-- Twitter Card meta tags -->
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content={pageTitle} />
	<meta name="twitter:description" content={pageDescription} />
	<meta name="twitter:image" content="https://appgoblin.info/goblin_purple_hat_250.png" />

	<!-- Additional meta tags -->
	<meta name="robots" content="index, follow" />
	<link rel="canonical" href="https://appgoblin.info/top-mobile-advertisers" />
</svelte:head>

<div class="p-2 px-2 md:px-16 lg:px-32">
	<h1 class="text-3xl font-bold">Top Mobile Ad Buyers & Their Ad Creatives</h1>

	<br />

	<div class="p-4">
		<p>
			These are top mobile ad buyers (advertisers) from this month. The top advertisers and their
			creatives are based on actual ads seen in publishing apps in the past month.
		</p>
		<div class="mt-4">
			<a href="/ad-creatives" class="btn variant-filled-secondary">
				View Ad Creative Clusters Dashboard 📈
			</a>
		</div>
	</div>

	<WhiteCard>
		{#if data.creatives && data.creatives.length > 0}
			<AdvertiserCreativeRankingsTable data={data.creatives} />
		{:else}
			<p>No apps found</p>
		{/if}
	</WhiteCard>
</div>
