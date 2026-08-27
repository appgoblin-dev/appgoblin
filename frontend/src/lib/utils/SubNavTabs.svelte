<script lang="ts">
	import type { Component } from 'svelte';
	import Crown from '@lucide/svelte/icons/crown';
	import LogIn from '@lucide/svelte/icons/log-in';
	import Menu from '@lucide/svelte/icons/menu';
	import X from '@lucide/svelte/icons/x';

	export interface SubNavTabItemBase {
		slug: string;
		label: string;
		href: string;
		icon?: Component<any, any, any>;
		count?: number | null;
		b2b?: boolean;
		/**
		 * Optional extra slugs that should also count this tab as active
		 * (e.g. 'app-adstxt-publisher' matching the 'app-adstxt' tab).
		 */
		matchSlugs?: string[];
		/**
		 * When true and the tab is not active, renders at 50% opacity to indicate
		 * the data comes from a parent company rather than directly.
		 */
		dimmed?: boolean;
		/**
		 * When set, renders as a non-clickable section heading instead of a link.
		 */
		sectionLabel?: never;
		/**
		 * Adds left padding to indent this item under a section header.
		 */
		indent?: boolean;
		/**
		 * When true, shows a lock icon next to the label to indicate the page requires authentication.
		 */
		authRequired?: boolean;
	}

	export interface SubNavTabSection {
		sectionLabel: string;
		slug?: never;
		label?: never;
		href?: never;
		icon?: never;
		count?: never;
		b2b?: never;
		matchSlugs?: never;
		dimmed?: never;
		indent?: never;
		authRequired?: never;
	}

	export type SubNavTabItem = SubNavTabItemBase | SubNavTabSection;

	let {
		tabs,
		currentSlug,
		ariaLabel = 'Navigation tabs',
		menuLabel = 'Page Menu'
	}: {
		tabs: SubNavTabItem[];
		currentSlug: string;
		ariaLabel?: string;
		menuLabel?: string;
	} = $props();

	let isExpanded = $state(false);

	const activeTab = $derived(
		tabs.find((t) => t.slug === currentSlug) ??
			tabs.find((t) => t.matchSlugs?.includes(currentSlug))
	);

	function formatCount(n: number | undefined | null): string {
		if (n == null || n === 0) return '';
		if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
		if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
		return String(n);
	}

	function isTabActive(tab: SubNavTabItem): boolean {
		if (tab.slug === currentSlug) return true;
		// Only fall back to matchSlugs when no other tab has an exact slug match,
		// so subsection tabs (e.g. sdks-history) take priority over the parent tab's matchSlugs.
		const exactMatchExists = tabs.some((t) => 'slug' in t && t.slug === currentSlug);
		if (!exactMatchExists && tab.matchSlugs?.includes(currentSlug)) return true;
		return false;
	}

	function tabClass(tab: SubNavTabItem): string {
		const selectedClass = 'bg-secondary-100-900 font-semibold';
		const unselectedClass = 'hover:text-surface-900-100';

		const isActive = isTabActive(tab);
		let cls = isActive ? selectedClass : unselectedClass;
		return cls;
	}

	function labelClass(tab: SubNavTabItem): string {
		if (tab.dimmed) return 'opacity-60';
		return '';
	}

	function handleTabClick() {
		isExpanded = false;
	}
</script>

<aside class="md:sticky md:top-24 md:self-start">
	<div class="border-r border-surface-200-800 pl-1 md:pl-2 pr-2 md:pr-4">
		<!-- Mobile toggle header -->
		<button
			type="button"
			class="flex w-full items-center justify-between gap-2 border border-surface-300-600 rounded-lg px-3 py-2 text-sm font-medium text-tertiary-900-100 md:hidden"
			onclick={() => (isExpanded = !isExpanded)}
			aria-expanded={isExpanded}
			aria-label="{isExpanded ? 'Collapse' : 'Expand'} section navigation"
		>
			<span class="flex items-center gap-2">
				{#if isExpanded}
					<X size={18} class="shrink-0" aria-hidden="true" />
				{:else}
					<Menu size={18} class="shrink-0" aria-hidden="true" />
				{/if}
				<span class="">{menuLabel}</span>
				{#if activeTab}
					<span class="mx-0.5">·</span>
					{#if activeTab.icon}
						{@const Icon = activeTab.icon}
						<Icon size={16} class="shrink-0" aria-hidden="true" />
					{/if}
					{activeTab.label}
					{#if activeTab.count}
						<span
							class="inline-flex items-center justify-center bg-secondary-100-800 px-2 py-0.5 text-xs font-semibold tabular-nums text-secondary-800-200"
						>
							{formatCount(activeTab.count)}
						</span>
					{/if}
				{/if}
			</span>
		</button>

		<!-- Full nav: always visible on desktop, toggled on mobile -->
		<nav
			class="flex-col gap-2 {isExpanded
				? 'flex border-t border-surface-200-800 pt-2 mt-2'
				: 'hidden'} md:flex md:border-t-0 md:pt-0 md:mt-0"
			aria-label={ariaLabel}
		>
			{#each tabs as tab (tab.slug || tab.sectionLabel)}
				{#if tab.sectionLabel}
					<p class="mt-3 first:mt-0 text-[11px] font-semibold uppercase tracking-[0.12em]">
						{tab.sectionLabel}
					</p>
				{:else}
					<a
						href={tab.href}
						class="px-2 py-2 text-sm transition {tabClass(tab)} {tab.indent ? 'ml-4' : ''}"
						aria-current={isTabActive(tab) ? 'page' : undefined}
						onclick={handleTabClick}
					>
						<span class="flex items-center justify-between gap-2">
							<span class="flex items-center gap-1.5 {labelClass(tab)}">
								{#if tab.icon}
									{@const Icon = tab.icon}
									<Icon size={16} class="shrink-0 {labelClass(tab)}" aria-hidden="true" />
								{/if}
								{tab.label}
								{#if tab.b2b}
									<Crown size={12} class="shrink-0 text-primary-900-100" aria-hidden="true" />
								{/if}
								{#if tab.authRequired}
									<LogIn size={12} class="shrink-0 text-surface-400" aria-hidden="true" />
								{/if}
							</span>
							{#if tab.count}
								<span
									class="inline-flex items-center justify-center bg-secondary-100-800 px-2 py-0.5 text-xs font-semibold tabular-nums text-secondary-800-200"
								>
									{formatCount(tab.count)}
								</span>
							{/if}
						</span>
					</a>
				{/if}
			{/each}
		</nav>
	</div>
</aside>
