<script lang="ts">
	import { enhance } from '$app/forms';
	import type { AppFullDetails } from '../../../../types';
	import RankChart from '$lib/RankChart.svelte';
	import { countryCodeToEmoji } from '$lib/utils/countryCodeToEmoji';

	interface Props {
		data: AppFullDetails;
	}
	import { page } from '$app/state';
	let { data }: Props = $props();

	let country = $state(page.url.searchParams.get('country') || 'US');
	let countryTitle = $derived(data.countries[country as keyof typeof data.countries]);
	let isLoadingRanks = $state(false);
	const dataMyranks = $derived(data.myranks);
	let overrideRanks = $state<Promise<any> | null>(null);
	const currentRanks = $derived(overrideRanks ?? dataMyranks);
	let formElement = $state<HTMLFormElement | undefined>(undefined);

	$effect(() => setDefaultCountry(data.myranksOverview));

	// Clear override when data changes (e.g. navigation to another app)
	$effect(() => {
		data.myranks;
		overrideRanks = null;
	});

	function setDefaultCountry(ranks: { countries: string[] }) {
		if (country == '' && ranks.countries && ranks.countries.length > 0) {
			country = ranks.countries[0];
		}
	}

	function handleCountryChange(newCountry: string) {
		country = newCountry;
		// Trigger form submission
		if (formElement) {
			formElement.requestSubmit();
		}
	}

	function handleEnhance() {
		return async ({ result }: { result: any }) => {
			isLoadingRanks = false;
			if (result.type === 'success' && result.data) {
				// Update the current ranks with the new data
				overrideRanks = Promise.resolve(result.data);
				// Update URL without reload
				const url = new URL(window.location.href);
				url.searchParams.set('country', country);
				window.history.replaceState({}, '', url.toString());
			}
		};
	}
</script>

<div class="card preset-tonal p-2 md:p-8 mt-2 md:mt-4">
	<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
		<div>
			<h4 class="h4 md:h3 p-2">Best App Store Ranks This Month</h4>
			{#await data.myranksOverview}
				Loading app ranks...
			{:then ranks}
				{#if typeof ranks == 'string'}
					{ranks}
					<p>
						No official ranks available for this app. This app is not ranked on the store's top 200
						apps for it's categories.
					</p>
				{:else if ranks.best_ranks && ranks.best_ranks.length > 0}
					{#each ranks.best_ranks.slice(0, 10) as myrow}
						<div class="px-4">
							#{myrow.best_rank}
							in: {myrow.collection}
							{myrow.category}
							({countryCodeToEmoji(myrow.country)}
							{data.countries[myrow.country as keyof typeof data.countries]})
						</div>
					{/each}
					{#if ranks.best_ranks.length > 10}
						<div class="px-4 mt-2 text-surface-600">
							+ {ranks.best_ranks.length - 10} more rankings
						</div>
					{/if}
				{/if}
			{:catch}
				<p>The server caught an error.</p>
			{/await}
		</div>
		<div class="">
			<h4 class="h4 md:h3 p-2 mt-2">App Store Ranks: {countryTitle}</h4>
			{#await data.myranksOverview then ranks}
				<form
					method="POST"
					action="?/updateRanks"
					use:enhance={handleEnhance}
					bind:this={formElement}
					class="max-w-sm"
				>
					<p class="p-2">Breakdown App Store Ranks by Country</p>
					<input type="hidden" name="country" value={country} />
					<select
						class="select p-1 md:p-2 m-2"
						bind:value={country}
						onchange={(e) => {
							isLoadingRanks = true;
							handleCountryChange(e.currentTarget.value);
						}}
					>
						{#if typeof ranks != 'string' && ranks.countries && ranks.countries.length > 0}
							{#each ranks.countries as countryCode}
								<option value={countryCode}
									>{countryCodeToEmoji(countryCode)}
									{data.countries[countryCode as keyof typeof data.countries]}</option
								>
							{/each}
						{:else}
							{#each Object.keys(data.countries) as countryCode}
								<option value={countryCode}
									>{countryCodeToEmoji(countryCode)}
									{data.countries[countryCode as keyof typeof data.countries]}</option
								>
							{/each}
						{/if}
					</select>
				</form>
			{/await}
			{#if isLoadingRanks}
				<p class="p-4">Loading app ranks for {countryTitle}...</p>
			{:else}
				{#await currentRanks}
					Loading app ranks...
				{:then ranks}
					{#if typeof ranks == 'string'}
						<p>
							No official ranks available for this app. This app is not ranked on the store's top
							200 apps for it's categories.
						</p>
					{:else if ranks.history && ranks.history.length > 0}
						<div class="card preset-tonal mt-2 md:mt-4">
							<RankChart plotData={ranks.history} narrowBool={true} />
						</div>
					{:else}
						<p>No ranking data available for this app.</p>
					{/if}
				{/await}
			{/if}
		</div>
	</div>
</div>
