<script lang="ts">
	import type { Snippet } from 'svelte';
	let { title, children }: { title?: Snippet; children: Snippet } = $props();
</script>

<div class="rounded-lg preset-outlined-surface-100-900 overflow-hidden">
	{#if title}
		<div class="card-header bg-surface-100-900 md:p-2">
			<div class="text-large md:text-2xl">
				{@render title?.()}
			</div>
		</div>
	{/if}
	<div class="card-content">
		{@render children()}
	</div>
</div>
