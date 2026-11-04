<script lang="ts">
	import ArrowRight from '@lucide/svelte/icons/arrow-right';

	let { class: className = '' }: { class?: string } = $props();
</script>

<div class={`preset-outlined-surface-100-900 rounded-lg p-4 ${className}`}>
	<p class="font-semibold">Need the full company dataset?</p>
	<p class="mt-1 text-sm">
		Bulk company and SDK app lists, app-ads.txt datasets, and the full API are included with paid
		B2B plans.
	</p>
	<div class="mt-3 flex flex-wrap items-center gap-3">
		<a href="/pricing" class="btn preset-filled-primary-500 p-2 text-sm font-semibold">
			See Paid API & Dataset Pricing
			<ArrowRight class="h-4 w-4" />
		</a>
		<a href="/docs/data-exports" class="btn preset-outlined-surface-100-900 p-2 text-sm">
			Paid Datasets Guide
		</a>
	</div>
</div>
