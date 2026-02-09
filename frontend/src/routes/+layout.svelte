<script lang="ts">
	import '../app.css';
	import { page } from '$app/state';
	import { Menu, Portal } from '@skeletonlabs/skeleton-svelte';

	import IconSearch from '$lib/svg/IconSearch.svelte';
	import MenuIcon from 'lucide-svelte/icons/menu';

	import { AppBar } from '@skeletonlabs/skeleton-svelte';

	import LoginAccountButton from '$lib/LoginAccountButton.svelte';
	import NavTabs from '$lib/NavTabs.svelte';

	import { goto } from '$app/navigation';

	let searchTerm: string = $state('');

	function navigateToSearch(event: any) {
		if (event.key === 'Enter' && searchTerm.trim() !== '') {
			// Replace spaces with '+'
			const encodedSearchTerm = encodeURIComponent(searchTerm.replace(/\s+/g, '+'));

			// Navigate to the search route
			goto(`/search/${encodedSearchTerm}`);
		}
	}

	let { children } = $props();
</script>

<div class="grid h-screen grid grid-rows-[auto_1fr_auto]">
	<header class="sticky top-0 z-10">
		<AppBar class="bg-surface-50-950">
			<AppBar.Toolbar class="grid-cols-[auto_1fr_auto]">
				<AppBar.Lead class="shrink-0 min-w-fit">
					<a href="/" class="flex items-center shrink-0">
						<img
							class="h-8 w-8 shrink-0 md:ml-2 md:h-12 md:w-12"
							src="/goblin_purple_hat_60.png"
							alt="AppGoblin Icon"
						/>
						<strong
							class="hidden md:inline-flex text-xs ml-1 md:ml-2 md:text-lg xl:text-xl uppercase text-primary-900-100"
							>AppGoblin</strong
						>
					</a>
				</AppBar.Lead>

				<AppBar.Headline class="hidden md:inline-flex">
					<div class="gap-1 md:gap-2 justify-center">
						<NavTabs />
					</div>
				</AppBar.Headline>

				<AppBar.Trail class="overflow-hidden flex justify-end">
					<div class="flex gap-1 md:gap-2">
						<div class="input-group grid-cols-[auto_1fr_auto]">
							<div class="ig-cell preset-tonal p-2 md:p-4">
								<IconSearch />
							</div>
							<input
								class="ig-input md:hidden"
								type="search"
								placeholder="Search Apps..."
								bind:value={searchTerm}
								onkeydown={navigateToSearch}
							/>
							<input
								class="ig-input hidden md:block"
								type="search"
								placeholder="Search Apps & Companies"
								bind:value={searchTerm}
								onkeydown={navigateToSearch}
							/>
						</div>

						<LoginAccountButton />
					</div>
				</AppBar.Trail>
			</AppBar.Toolbar>
		</AppBar>
	</header>

	<main>
		{@render children?.()}
	</main>

	<footer>
		<div class="stick bottom-0 z-10 p-2">
			{#if page.url.pathname.startsWith('/blog/')}
				<div class="inline-flex md:hidden">
					<NavTabs hideLinks={true} />
				</div>
			{:else}
				<div class="fixed right-4 bottom-4 p-4 md:hidden">
					<Menu>
						<Menu.Trigger class="btn preset-filled"><MenuIcon /> Menu</Menu.Trigger>
						<Portal>
							<Menu.Positioner>
								<Menu.Content>
									<NavTabs />
								</Menu.Content>
							</Menu.Positioner>
						</Portal>
					</Menu>
				</div>
			{/if}
		</div>
		<!-- Footer -->
		<div class="mt-12 py-8 border-t text-center text-gray-500 text-sm">
			<div class="mb-2">
				<a href="/about" class="underline hover:text-primary-900-100">About AppGoblin</a>
				&nbsp;|&nbsp;
				<a href="/pricing" class="underline hover:text-primary-900-100">Pricing</a>
				&nbsp;|&nbsp;
				<a href="/privacy_policy.html" class="underline hover:text-primary-900-100"
					>Privacy Policy</a
				>
				&nbsp;|&nbsp;
				<a
					href="https://github.com/appgoblin-dev/appgoblin"
					class="underline hover:text-primary-900-100">GitHub</a
				>
				&nbsp;|&nbsp;
				<a
					href="https://linkedin.com/companies/AppGoblin"
					class="underline hover:text-primary-900-100">LinkedIn</a
				>
				&nbsp;|&nbsp;
				<a href="mailto:contact@appgoblin.info" class="underline hover:text-primary-900-100"
					>Contact</a
				>
			</div>
			<div>© {new Date().getFullYear()} AppGoblin. All rights reserved.</div>
		</div>
	</footer>
</div>
