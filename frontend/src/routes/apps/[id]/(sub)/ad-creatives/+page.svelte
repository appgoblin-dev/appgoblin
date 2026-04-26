<script>
	import WhiteCard from '$lib/WhiteCard.svelte';
	let { data } = $props();
</script>

<div class="p-2 px-2 md:p-8">
	<h1 class="text-3xl font-bold">{data.myapp.name}: Ad Creatives</h1>
	<p>
		This is an overview of the creatives that are used to advertise for {data.myapp.name}. Below are
		the thumbnails of the images and videos found.
	</p>

	<br />
	{#await data.creatives}
		loading...
	{:then creatives}
		<WhiteCard>
			{#if creatives && creatives.by_creative.length > 0}
				<div class="grid grid-cols-2 md:grid-cols-4 gap-2">
					{#each creatives.by_creative as creative}
						<div class="flex flex-col items-center justify-center">
							<div class="card">
								<img
									src="https://media.appgoblin.info/creatives/thumbs/{creative.md5_hash}.jpg"
									alt="Creative thumbnail for {creative.md5_hash}"
								/>
								<p>{creative.file_extension}</p>
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<p>
					No ad creatives found. This means that AppGoblin has not found any ads that this app is
					running in other apps.
				</p>
			{/if}
		</WhiteCard>
	{/await}
</div>
