<script lang="ts">
	import IconiOs from './svg/IconiOS.svelte';
	import IconGoogle from './svg/IconGoogle.svelte';

	let { store }: { store: string | number } = $props();
	function getIcon(store: string | number) {
		if (typeof store === 'string' && store.toString().startsWith('Google')) {
			return IconGoogle;
		} else if (typeof store === 'string' && store.toString().startsWith('Apple')) {
			return IconiOs;
		} else if (typeof store === 'number' && store === 1) {
			return IconGoogle;
		} else if (typeof store === 'number' && store === 2) {
			return IconiOs;
		} else {
			// console.log('store', store);
		}
	}
	let icon = $derived(getIcon(store));
</script>

<span class="inline-flex items-center align-middle">
	{#if icon === IconGoogle}
		<IconGoogle size="16" />
	{:else}
		<IconiOs size="16" />
	{/if}
</span>
