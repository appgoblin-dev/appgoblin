<script>
	import CreativesTable from '$lib/CreativesTable.svelte';
	import WhiteCard from '$lib/WhiteCard.svelte';
	let { data } = $props();
</script>

<div class="p-2 px-2 md:px-16 lg:px-72">
	<h1 class="text-3xl font-bold">{data.myapp.name}: Ad Placements</h1>
	<p>
		This is an overview of the records of ad placements advertising for {data.myapp.name}. The
		publishing apps are the apps that were opened and where the creatives were found.
	</p>

	<br />

	{#await data.creativerecords}
		loading...
	{:then creativerecords}
		<div class="preset-filled-surface-100-900 p-2 md:p-8 mt-2 md:mt-4">
			<WhiteCard>
				{#if creativerecords && creativerecords.by_publisher.length > 0}
					<CreativesTable data={creativerecords.by_publisher} />
				{:else}
					<p>No apps found</p>
				{/if}
			</WhiteCard>
		</div>
	{/await}
</div>
