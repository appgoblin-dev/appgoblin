<script lang="ts">
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import CtvAppRanksTable from '#lib/CtvAppRanksTable.svelte';
	import type { CtvAppRanksResponse } from '../../../types.js';

	interface Props {
		data: {
			ranks: CtvAppRanksResponse;
			storeId: number;
		};
	}

	let { data }: Props = $props();

	const storeTitle = $derived(page.params.store === 'apple' ? 'Apple App Store' : 'Google Play');

	const title = $derived(`Top CTV Apps on ${storeTitle} by Monthly Installs`);
	const description = $derived(
		`The top connected TV (CTV) supported apps on ${storeTitle}, ranked by estimated monthly installs. Compare installs, revenue, and growth for TV apps.`
	);
	const keywords = $derived(
		`CTV apps, connected TV apps, ${storeTitle}, top TV apps, app installs, app revenue, app growth, app store rankings, ASO, competitor analysis`
	);
</script>

<svelte:head>
	<title>{title}</title>
	<link rel="canonical" href={page.url.href} />
	<meta name="description" content={description} />
	<meta name="keywords" content={keywords} />
	<meta property="og:title" content={title} />
	<meta property="og:description" content={description} />
	<meta property="og:image" content="https://appgoblin.info/goblin_purple_hat_250.png" />
	<meta property="og:url" content={page.url.href} />
	<meta property="og:type" content="website" />
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content={title} />
	<meta name="twitter:description" content={description} />
	<meta name="twitter:image" content="https://appgoblin.info/goblin_purple_hat_250.png" />
	<meta name="robots" content="index, follow" />
</svelte:head>

<div class="p-2 px-2 md:px-16 lg:px-32">
	<h1 class="text-3xl">Top CTV Apps</h1>
	<p class="text-sm">
		The top connected TV (CTV) supported apps on {storeTitle}, ranked by estimated monthly installs.
	</p>

	<div class="my-4 flex flex-wrap items-center gap-2">
		<a
			href={resolve('/top-ctv-app-ranks/[store]', { store: 'google' })}
			class={page.params.store === 'google'
				? 'btn preset-filled-secondary-100-900'
				: 'btn preset-tonal'}>Google Play</a
		>
		<a
			href={resolve('/top-ctv-app-ranks/[store]', { store: 'apple' })}
			class={page.params.store === 'apple'
				? 'btn preset-filled-secondary-100-900'
				: 'btn preset-tonal'}>Apple App Store</a
		>
	</div>

	{#if data.ranks?.apps?.length}
		<CtvAppRanksTable data={data.ranks.apps} />
	{:else}
		<p>No CTV apps found for this store.</p>
	{/if}
</div>
