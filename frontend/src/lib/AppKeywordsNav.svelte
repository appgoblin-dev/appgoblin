<script lang="ts">
	import { page } from '$app/state';
	import LogIn from 'lucide-svelte/icons/log-in';

	type Props = {
		storeId: string;
	};

	let { storeId }: Props = $props();

	const items = $derived([
		{ href: `/apps/${storeId}/keywords`, label: 'Keywords Overview' },
		{ href: `/apps/${storeId}/keywords/ranking`, label: 'Keyword Ranking' },
		{ href: `/apps/${storeId}/keywords/discovery`, label: 'Keyword Discovery' },
		{ href: `/apps/${storeId}/keywords/tracked`, label: 'My Keywords', requiresAuth: true },
		{ href: `/apps/${storeId}/keywords/compare`, label: 'Keywords Compare', requiresAuth: true }
	]);

	const isActive = (href: string) => page.url.pathname === href;
</script>

<nav class="p-3">
	<div class="flex gap-2 overflow-x-auto pb-1">
		{#each items as item (item.href)}
			<a
				href={item.href}
				class={`whitespace-nowrap px-3 py-2 text-sm font-medium  ${
					isActive(item.href) ? 'bg-secondary-100-900' : 'hover:bg-secondary-100-900'
				}`}
			>
				<span class="inline-flex items-center gap-1.5">
					{#if item.requiresAuth}
						<LogIn class="h-3.5 w-3.5" aria-hidden="true" />
					{/if}
					{item.label}
				</span>
			</a>
		{/each}
	</div>
</nav>
