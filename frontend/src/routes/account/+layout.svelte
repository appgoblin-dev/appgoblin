<script lang="ts">
	import { page } from '$app/state';
	import type { LayoutData } from './$types';
	import UserRound from 'lucide-svelte/icons/user-round';
	import Settings from 'lucide-svelte/icons/settings';
	import ShieldCheck from 'lucide-svelte/icons/shield-check';
	import CreditCard from 'lucide-svelte/icons/credit-card';
	import LayoutDashboard from 'lucide-svelte/icons/layout-dashboard';
	import ListTodo from 'lucide-svelte/icons/list-todo';
	import Code from 'lucide-svelte/icons/code';

	let { data, children }: { data: LayoutData; children: any } = $props();

	let currentPath = $derived(page.url.pathname);

	const navItems = [
		{ href: '/account', label: 'Overview', icon: LayoutDashboard },
		{ href: '/account/watchlist', label: 'Watchlists', icon: ListTodo },
		{ href: '/account/api-keys', label: 'API Keys', icon: Code },
		{ href: '/account/settings', label: 'Settings', icon: Settings },
		{ href: '/account/security', label: 'Security', icon: ShieldCheck },
		{ href: '/account/subscription', label: 'Subscription', icon: CreditCard }
	];
</script>

<div class="container mx-auto max-w-6xl px-4 py-8">
	<div class="flex flex-col md:flex-row gap-8">
		<!-- Sidebar Navigation -->
		<aside class="w-full md:w-64 shrink-0">
			<div class="p-4 md:sticky md:top-24">
				<div class="flex items-center gap-3 mb-6 p-2">
					<div class="p-2 rounded-full bg-primary-500/20">
						<UserRound size={24} class="text-primary-500" />
					</div>
					<div class="overflow-hidden">
						<p class="font-bold truncate">{data.user.username}</p>
						<p class="text-xs truncate">{data.user.email}</p>
					</div>
				</div>

				<nav class="flex flex-col gap-1">
					{#each navItems as { href, label, icon: Icon }}
						{@const isActive = currentPath === href}
						<a
							{href}
							class="flex items-center gap-3 px-4 py-3 rounded-lg transition-colors {isActive
								? 'bg-primary-500/10  font-medium'
								: 'hover:bg-surface-200-800 text-surface-700-300'}"
						>
							<Icon size={18} class={isActive ? 'text-primary-500' : 'text-surface-500'} />
							{label}
						</a>
					{/each}
				</nav>
			</div>
		</aside>

		<!-- Main Content Area -->
		<main class="flex-1 min-w-0">
			{@render children()}
		</main>
	</div>
</div>
