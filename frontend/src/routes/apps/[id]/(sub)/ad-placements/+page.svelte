<script>
	import AdPlacementsTable from '$lib/AdPlacementsTable.svelte';
	import WhiteCard from '$lib/WhiteCard.svelte';
	let { data } = $props();
</script>

<div class="p-2 px-2 md:px-16 lg:px-32">
	<h1 class="text-3xl font-bold">Ad Placements for {data.myapp.name}</h1>
	<p>
		These are ad spots that were bought by {data.myapp.name}. The publishing apps are the apps that
		where the creatives for {data.myapp.name} were found.
	</p>

	<br />

	{#await data.creatives}
		loading...
	{:then creatives}
		<div class="p-2 md:p-8 mt-2 md:mt-4">
			<WhiteCard>
				{#if creatives && creatives.by_vhash.length > 0}
					<AdPlacementsTable data={creatives.by_vhash} />
				{:else}
					<p>
						No app ad placements found. This means that AppGoblin has not found any ads that this
						app is running in other apps.
					</p>
				{/if}
			</WhiteCard>
		</div>
	{/await}
</div>
