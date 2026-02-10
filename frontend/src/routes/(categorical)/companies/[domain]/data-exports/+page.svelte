<script lang="ts">
	import WhiteCard from '$lib/WhiteCard.svelte';
	import { page } from '$app/state';

	const { domain } = page.params;
</script>

<WhiteCard>
	{#snippet title()}
		<span>Data Exports</span>
	{/snippet}
	<div class="p-4 flex flex-col gap-4">
		<p>Download available data for {domain}.</p>
		<div class="flex flex-wrap gap-4">
			<a href={`/companies/${domain}/app-adstxt/download`} class="btn preset-filled-primary-500">
				Download app-ads.txt
			</a>
			<!-- Add more download buttons here as needed -->
		</div>
	</div>
</WhiteCard>
