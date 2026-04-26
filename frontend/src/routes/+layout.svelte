<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { Menu, Portal } from '@skeletonlabs/skeleton-svelte';

	import IconSearch from '$lib/svg/IconSearch.svelte';
	import MenuIcon from 'lucide-svelte/icons/menu';
	import MoonIcon from 'lucide-svelte/icons/moon';
	import SunIcon from 'lucide-svelte/icons/sun';

	import { AppBar } from '@skeletonlabs/skeleton-svelte';

	import LoginAccountButton from '$lib/LoginAccountButton.svelte';
	import NavTabs from '$lib/NavTabs.svelte';
	import { initializeTheme, resolvedThemeMode, toggleTheme } from '$lib/stores/theme.svelte';

	let { children } = $props();

	onMount(() => {
		initializeTheme();
	});
</script>

<div class="grid h-screen grid grid-rows-[auto_1fr_auto]">
	<header class="sticky top-0 z-10">
		<AppBar class="bg-surface-50-950">
			<AppBar.Toolbar class="grid-cols-[auto_1fr_auto]">
				<AppBar.Lead class="shrink-0 min-w-fit">
					<a href="/" class="flex items-center shrink-0">
						<img
							class="h-8 w-8 shrink-0 lg:ml-2 lg:h-12 lg:w-12"
							src="/goblin_purple_hat_60.png"
							alt="AppGoblin Icon"
						/>
						<strong
							class="hidden lg:inline-flex text-xs ml-1 lg:ml-2 lg:text-lg xl:text-xl uppercase text-secondary-800-200"
							>AppGoblin</strong
						>
					</a>
				</AppBar.Lead>

				<AppBar.Headline class="hidden md:inline-flex md:ml-8 ">
					<div>
						<NavTabs />
					</div>
				</AppBar.Headline>

				<AppBar.Trail class="overflow-hidden flex justify-end">
					<div class="flex gap-1 md:gap-2">
						<form
							class="input-group grid-cols-[1fr_auto]"
							role="search"
							onsubmit={(e) => {
								e.preventDefault();
								const term = (e.currentTarget as HTMLFormElement).term.value.trim();
								if (term) goto(`/search/${encodeURIComponent(term)}`);
							}}
						>
							<input
								class="ig-input"
								type="search"
								name="term"
								placeholder="Search Apps & Companies"
								required
							/>
							<button class="ig-cell preset-tonal p-2 md:p-4" type="submit" aria-label="Search">
								<IconSearch />
							</button>
						</form>

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
									<NavTabs flat={true} />
								</Menu.Content>
							</Menu.Positioner>
						</Portal>
					</Menu>
				</div>
			{/if}
		</div>
		<!-- Footer -->
		<div class="mt-12 border-t py-8 text-sm text-surface-600 dark:text-surface-400">
			<div class="mx-auto max-w-6xl px-4">
				<div class="flex flex-col gap-4 md:relative md:items-center">
					<div class="self-start md:absolute md:left-0 md:top-1/2 md:-translate-y-1/2">
						<button
							type="button"
							class="inline-flex items-center gap-2 rounded-full border border-surface-300 px-3 py-1.5 font-medium text-surface-700 transition-colors hover:bg-surface-100 dark:border-surface-700 dark:text-surface-200 dark:hover:bg-surface-800"
							onclick={toggleTheme}
							aria-label={$resolvedThemeMode === 'dark'
								? 'Switch to light mode'
								: 'Switch to dark mode'}
							aria-pressed={$resolvedThemeMode === 'dark'}
						>
							{#if $resolvedThemeMode === 'dark'}
								<SunIcon class="size-4" />
								<span>Light mode</span>
							{:else}
								<MoonIcon class="size-4" />
								<span>Dark mode</span>
							{/if}
						</button>
					</div>

					<div class="flex flex-wrap items-center justify-center gap-x-2 gap-y-3 text-center">
						<a href="/about" class="underline hover:">About AppGoblin</a>
						&nbsp;|&nbsp;
						<a href="/blog" class="underline hover:">Blog</a>
						&nbsp;|&nbsp;
						<a href="/reports" class="underline hover:">Reports</a>
						&nbsp;|&nbsp;
						<a href="/pricing" class="underline hover:">Pricing</a>
						&nbsp;|&nbsp;
						<a href="/privacy_policy.html" class="underline hover:">Privacy Policy</a>
						&nbsp;|&nbsp;
						<a href="https://github.com/appgoblin-dev/appgoblin" class="underline hover:">GitHub</a>
						&nbsp;|&nbsp;
						<a href="https://linkedin.com/companies/AppGoblin" class="underline hover:">LinkedIn</a>
						&nbsp;|&nbsp;
						<a href="/contact" class="underline hover:">Contact</a>
					</div>
				</div>
			</div>
			<div>© {new Date().getFullYear()} AppGoblin. All rights reserved.</div>
		</div>
	</footer>
</div>
