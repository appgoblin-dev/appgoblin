<script lang="ts">
	import type { StoreCategoryRanks } from '../../../../../../../../../../types.js';
	import { page } from '$app/state';
	import RankChart from '$lib/RankChart.svelte';
	import AppRankTable from '$lib/AppRankTable.svelte';
	import { countryCodeToEmoji } from '$lib/utils/countryCodeToEmoji';
	import { prettyName } from '$lib/utils/prettyNames';

	interface Props {
		data: StoreCategoryRanks;
	}

	let { data }: Props = $props();

	let store = $derived(+page.params.store!);
	let collection = $derived(+page.params.collection!);
	let category = $derived(+page.params.category!);

	let collectionName = $derived(
		prettyName(data.collectionIDLookup[store][collection].collection_name)
	);
	let categoryName = $derived(
		prettyName(data.categoryIDLookup[collection][category].category_name)
	);

	let country = $state(page.params.country || 'US');

	function getTitle(): string {
		const title =
			data.storeIDLookup[store].store_name +
			' ' +
			'Daily App Ranks ' +
			collectionName +
			' for ' +
			categoryName +
			' in ' +
			country +
			' ';
		return title;
	}

	function getDescription(): string {
		const description =
			'Free app store charts. Top ranked ' +
			data.storeIDLookup[store].store_name +
			' ' +
			collectionName +
			' ' +
			categoryName +
			' Apps. Sort by category and view historical data all for free. Get valuable ASO insights for your app strategy with AppGoblin.';
		return description;
	}
	const title = $derived(getTitle());
	const description = $derived(getDescription());
</script>

<svelte:head>
	<title>{title}</title>
	<meta name="description" content={description} />
	<meta
		name="keywords"
		content="free, free aso, {data.storeIDLookup[store].store_name}, {data.collectionIDLookup[
			store
		][collection].collection_name}, {data.categoryIDLookup[collection][category]
			.category_name}, app rankings, top apps, Google Play charts, iOS App Store charts, free, ASO, marketing, competitor analysis, app category rankings, app performance tracking, mobile app trends"
	/>

	<!-- Open Graph meta tags -->
	<meta property="og:title" content={title} />
	<meta property="og:description" content={description} />
	<meta property="og:image" content="https://appgoblin.info/goblin_purple_hat_250.png" />
	<meta property="og:url" content={page.url.href} />
	<meta property="og:type" content="website" />

	<!-- Twitter Card meta tags -->
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content={title} />
	<meta name="twitter:description" content={description} />
	<meta name="twitter:image" content="https://appgoblin.info/goblin_purple_hat_250.png" />

	<!-- Additional meta tags -->
	<meta name="robots" content="index, follow" />
	<link rel="canonical" href={page.url.href} />
</svelte:head>

<div class="card p-2 md:p-8">
	<div class="md:mx-16">
		<h1 class="text-2xl p-2">
			<p class="">
				The {collectionName}
				{categoryName} Apps on
				{data.storeIDLookup[store].store_name}
				in
				{country}
			</p>
		</h1>
		<div class="p-1 md:p-2">
			<div class="max-w-sm mb-2 md:mb-8">
				<p class=" p-1 md:p-2">Select Country</p>
				<select
					class="select p-1 md:p-2 m-2"
					bind:value={country}
					onchange={() => {
						const newUrl = `/rankings/store/${store}/collection/${collection}/category/${category}/${country}`;
						window.location.href = newUrl;
					}}
				>
					{#each Object.entries(data.countries) as [key, value]}
						<option value={key}>{countryCodeToEmoji(key)} {value.langen}</option>
					{/each}
				</select>
			</div>

			{#await data.history then history}
				<RankChart plotData={history.history} maxValue={10.5} />
			{/await}
		</div>
		<br />
		<div class="p-1 md:p-2">
			{#await data.ranks}
				Loading App Ranks...
			{:then ranks}
				{#if ranks && ranks.ranks.length > 0}
					<AppRankTable data={ranks.ranks} />
				{:else}
					No data found
				{/if}
			{:catch}
				Problem loading data
			{/await}
		</div>
	</div>
</div>
