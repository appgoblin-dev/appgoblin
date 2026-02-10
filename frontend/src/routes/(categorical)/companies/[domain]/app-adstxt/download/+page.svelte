<script lang="ts">
	import { page } from '$app/state';
	import { onMount } from 'svelte';

	export let data: { downloadUrl: string | null };

	onMount(() => {
		if (data.downloadUrl) {
			window.location.href = data.downloadUrl;
		}
	});
</script>

<p>Download for {page.params.domain} app-ads.txt. Download should start automatically.</p>

{#if data.downloadUrl}
	<p>
		If it didn't start,
		<a href={data.downloadUrl} download target="_blank" rel="noopener noreferrer"
			>click here to download</a
		>.
	</p>
{:else}
	<p>Download is not available (missing configuration).</p>
{/if}
