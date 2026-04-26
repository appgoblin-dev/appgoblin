<script lang="ts">
	import type { RankedAppList } from '../types';

	import AppCard from './AppCard.svelte';

	interface Props {
		myTable: RankedAppList;
	}

	let { myTable }: Props = $props();
</script>

<div class="grid grid-cols-[auto_minmax(0,1fr)] items-start gap-x-4 gap-y-3">
	{#each Object.entries(myTable.ranks) as [_prop, values]}
		<div class="inline-flex">
			<p class="text-sm md:text-base">#</p>
			<p class="text-sm md:text-xl2">
				{values.rank}
			</p>
		</div>
		<div class="min-w-0">
			<AppCard app={values} showHeader={false} />
		</div>
	{/each}
</div>
