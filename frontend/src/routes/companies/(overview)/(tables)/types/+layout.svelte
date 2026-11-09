<script lang="ts">
	import MainContent from '#lib/MainContent.svelte';

	let { children } = $props();
</script>

<svelte:head>
	<meta name="robots" content="index, follow" />
</svelte:head>

<MainContent>
	{@render children?.()}
</MainContent>
