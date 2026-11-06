<script lang="ts">
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import Layers from '@lucide/svelte/icons/layers';
	import Table from '@lucide/svelte/icons/table';
	import GitCompareArrows from '@lucide/svelte/icons/git-compare-arrows';

	type Props = {
		storeId: string;
		callCount?: number;
		hasDiff?: boolean;
	};

	let { storeId, callCount = 0, hasDiff = false }: Props = $props();

	const isActive = (pathname: string) =>
		page.url.pathname.replace(/\/$/, '') === pathname.replace(/\/$/, '');
</script>

<nav class="p-1 md:p-3" aria-label="Data flows sections">
	<div class="flex gap-2 overflow-x-auto pb-1">
		<a
			href={resolve('/apps/[id]/(sub)/data-flows', { id: storeId })}
			class="whitespace-nowrap px-3 py-2 text-sm font-medium {isActive(
				resolve('/apps/[id]/(sub)/data-flows', { id: storeId })
			)
				? 'bg-secondary-100-900'
				: 'hover:bg-secondary-100-900'}"
			aria-current={isActive(resolve('/apps/[id]/(sub)/data-flows', { id: storeId }))
				? 'page'
				: undefined}
		>
			<span class="inline-flex items-center gap-1.5">
				<Layers class="h-4 w-4" aria-hidden="true" />
				Overview
			</span>
		</a>

		<a
			href={resolve('/apps/[id]/(sub)/data-flows/details', { id: storeId })}
			class="whitespace-nowrap px-3 py-2 text-sm font-medium {isActive(
				resolve('/apps/[id]/(sub)/data-flows/details', { id: storeId })
			)
				? 'bg-secondary-100-900'
				: 'hover:bg-secondary-100-900'}"
			aria-current={isActive(resolve('/apps/[id]/(sub)/data-flows/details', { id: storeId }))
				? 'page'
				: undefined}
		>
			<span class="inline-flex items-center gap-1.5">
				<Table class="h-4 w-4" aria-hidden="true" />
				All API Calls
				{#if callCount}
					<span
						class="inline-flex items-center justify-center bg-secondary-100-800 px-2 py-0.5 text-xs font-semibold tabular-nums text-secondary-800-200"
					>
						{callCount}
					</span>
				{/if}
			</span>
		</a>

		{#if hasDiff}
			<a
				href={resolve('/apps/[id]/(sub)/data-flows/changes', { id: storeId })}
				class="whitespace-nowrap px-3 py-2 text-sm font-medium {isActive(
					resolve('/apps/[id]/(sub)/data-flows/changes', { id: storeId })
				)
					? 'bg-secondary-100-900'
					: 'hover:bg-secondary-100-900'}"
				aria-current={isActive(resolve('/apps/[id]/(sub)/data-flows/changes', { id: storeId }))
					? 'page'
					: undefined}
			>
				<span class="inline-flex items-center gap-1.5">
					<GitCompareArrows class="h-4 w-4" aria-hidden="true" />
					Changes
				</span>
			</a>
		{/if}
	</div>
</nav>
