<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		header?: Snippet;
		footer?: Snippet;
		children: Snippet;
	}
	let { header, footer, children }: Props = $props();
</script>

<div class="p-2 border border-surface-100-900 rounded-lg">
	{#if header}
		<header>
			{@render header()}
			<hr class="mb-2 border-surface-100-900" />
		</header>
	{/if}

	{@render children()}

	{#if footer}
		<footer>
			{@render footer()}
		</footer>
	{/if}
</div>
