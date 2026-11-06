<script lang="ts">
	import { page } from '$app/state';
	import ChevronDown from '@lucide/svelte/icons/chevron-down';

	const topBarFont = 'text-xs md:text-base hover:';
	const topBarHighlightedFont = 'text-xs md:text-base ';
	const myDivider = 'md:p-1';
	const topDivider = 'p-1 xxl:p-2';
	const dropdownItem =
		'block px-4 py-2 text-xs md:text-base hover: hover:preset-tonal w-full text-left whitespace-nowrap';
	const dropdownHighlightedItem =
		'block px-4 py-2 text-xs md:text-base  preset-tonal w-full text-left whitespace-nowrap';
	const sectionLabel = 'text-xs font-semibold uppercase tracking-widest pt-1';
	const dropdownSectionLabel = 'px-4 pt-2 pb-1 text-[11px] font-semibold uppercase tracking-widest';

	function isHighlighted(...paths: string[]) {
		return paths.some((p) => page.url.pathname.startsWith(p));
	}

	let { hideLinks = false, flat = false } = $props();
</script>

{#if flat || hideLinks}
	<!-- Flat list used inside the mobile hamburger menu -->
	<div class="flex flex-col gap-1 {topDivider} mx-2">
		{#if !hideLinks}
			<!-- B2B INTELLIGENCE group -->
			<p class={sectionLabel}>B2B Intelligence</p>
			<p class={sectionLabel}>Company Rankings</p>
			<a href="/companies" class={isHighlighted('/companies') ? topBarHighlightedFont : topBarFont}
				>Company Ranks</a
			>
			<div class={myDivider}></div>
			<a
				href="/companies/types/ad-networks"
				class={isHighlighted('/companies/types/ad-networks') ? topBarHighlightedFont : topBarFont}
				>Ad Networks</a
			>
			<div class={myDivider}></div>
			<a
				href="/companies/types/ad-attribution"
				class={isHighlighted('/companies/types/ad-attribution')
					? topBarHighlightedFont
					: topBarFont}>Analytics: Attribution</a
			>
			<div class={myDivider}></div>
			<a
				href="/companies/types/product-analytics"
				class={isHighlighted('/companies/types/product-analytics')
					? topBarHighlightedFont
					: topBarFont}>Analytics</a
			>
			<div class={myDivider}></div>
			<a
				href="/companies/types/development-tools"
				class={isHighlighted('/companies/types/development-tools')
					? topBarHighlightedFont
					: topBarFont}>Development Tools</a
			>
			<div class={myDivider}></div>
			<a
				href="/companies/types/mediation"
				class={isHighlighted('/companies/types/mediation') ? topBarHighlightedFont : topBarFont}
				>Mediation Platforms</a
			>
			<div class={myDivider}></div>
			<a
				href="/companies/types/business-tools"
				class={isHighlighted('/companies/types/business-tools')
					? topBarHighlightedFont
					: topBarFont}>Business Tools</a
			>
			<div class={myDivider}></div>
			<!-- APP INTELLIGENCE group -->
			<p class={sectionLabel}>App Intelligence</p>
			<a
				href="/ad-creatives"
				class={isHighlighted('/ad-creatives') ? topBarHighlightedFont : topBarFont}>Ad Creatives</a
			>
			<a
				href="/top-mobile-advertisers"
				class={isHighlighted('/top-mobile-advertisers') ? topBarHighlightedFont : topBarFont}
				>Top Advertisers</a
			>
			<div class={myDivider}></div>
			<a
				href="/app-explorer"
				class={isHighlighted('/app-explorer') ? topBarHighlightedFont : topBarFont}>App Explorer</a
			>
			<div class={myDivider}></div>
			<a href="/sdks" class={isHighlighted('/sdks') ? topBarHighlightedFont : topBarFont}
				>Free SDK Scans</a
			>
			<div class={myDivider}></div>
			<!-- RANKINGS group -->
			<p class={sectionLabel}>Rankings</p>
			<a
				href="/rankings/store/1/collection/1/category/1/US"
				class={isHighlighted('/rankings') ? topBarHighlightedFont : topBarFont}
				>Top Google Play App Ranks</a
			>
			<div class={myDivider}></div>
			<a
				href="/rankings/store/2/collection/4/category/120/US"
				class={isHighlighted('/rankings') ? topBarHighlightedFont : topBarFont}
				>Apple App Store Ranks</a
			>
			<div class={myDivider}></div>
			<a
				href="/fastest-growing-apps/google/overall"
				class={isHighlighted('/fastest-growing-apps') ? topBarHighlightedFont : topBarFont}
				>Top Growth Apps</a
			>
			<div class={myDivider}></div>
			<a
				href="/top-ctv-app-ranks/google"
				class={isHighlighted('/top-ctv-app-ranks') ? topBarHighlightedFont : topBarFont}
				>Top CTV Apps</a
			>
			<div class={myDivider}></div>
			<a
				href="/collections/new_monthly/google/overall"
				class={isHighlighted('/collections') ? topBarHighlightedFont : topBarFont}>New Apps</a
			>
			<div class={myDivider}></div>

			<!-- RESOURCES group -->
			<p class={sectionLabel}>Resources</p>
			<a href="/reports" class={isHighlighted('/reports') ? topBarHighlightedFont : topBarFont}
				>Free Reports</a
			>
			<div class={myDivider}></div>
			<a
				href="/free-app-datasets"
				class={isHighlighted('/free-app-datasets') ? topBarHighlightedFont : topBarFont}
			>
				Free Datasets</a
			>
			<div class={myDivider}></div>
			<a href="/api-docs" class={isHighlighted('/api-docs') ? topBarHighlightedFont : topBarFont}
				>Docs: API & MCP</a
			>
			<div class={myDivider}></div>
			<a
				href="/docs/data-exports"
				class={isHighlighted('/docs/data-exports') ? topBarHighlightedFont : topBarFont}
				>Docs: Paid Datasets</a
			>
			<div class={myDivider}></div>
			<a href="/blog" class={isHighlighted('/blog') ? topBarHighlightedFont : topBarFont}>Blog</a>
			<div class={myDivider}></div>
		{/if}
		<a href="/pricing" class={isHighlighted('/pricing') ? topBarHighlightedFont : topBarFont}
			>Pricing</a
		>
	</div>
{:else}
	<!-- Desktop dropdown bar -->
	<div class="flex flex-row gap-1 md:gap-2 xxl:gap-6 text-center items-center mx-2">
		<!-- B2B INTELLIGENCE dropdown -->
		<div class="relative group">
			<button
				class="flex items-center gap-0.5 {isHighlighted('/companies')
					? topBarHighlightedFont
					: topBarFont}"
			>
				B2B Intelligence <ChevronDown class="h-3 w-3 transition-transform group-hover:rotate-180" />
			</button>
			<div class="absolute left-0 top-full pt-1 hidden group-hover:block z-50 min-w-max">
				<div class="bg-surface-50-950 shadow-xl py-1">
					<p class={dropdownSectionLabel}>Company Rankings</p>
					<a
						href="/companies"
						class={isHighlighted('/companies') ? dropdownHighlightedItem : dropdownItem}
						>All Companies</a
					>
					<div class="ml-2">
						<a
							href="/companies/types/ad-networks"
							class={isHighlighted('/companies/types/ad-networks')
								? dropdownHighlightedItem
								: dropdownItem}>Ad Networks</a
						>
						<a
							href="/companies/types/ad-attribution"
							class={isHighlighted('/companies/types/ad-attribution')
								? dropdownHighlightedItem
								: dropdownItem}>Analytics: Attribution</a
						>
						<a
							href="/companies/types/product-analytics"
							class={isHighlighted('/companies/types/product-analytics')
								? dropdownHighlightedItem
								: dropdownItem}>Analytics</a
						>
						<a
							href="/companies/types/development-tools"
							class={isHighlighted('/companies/types/development-tools')
								? dropdownHighlightedItem
								: dropdownItem}>Development Tools</a
						>
						<a
							href="/companies/types/mediation"
							class={isHighlighted('/companies/types/mediation')
								? dropdownHighlightedItem
								: dropdownItem}>Mediation Platforms</a
						>
						<a
							href="/companies/types/business-tools"
							class={isHighlighted('/companies/types/business-tools')
								? dropdownHighlightedItem
								: dropdownItem}>Business Tools</a
						>
					</div>
				</div>
			</div>
		</div>

		<div class={myDivider}></div>

		<!-- APP INTELLIGENCE dropdown -->
		<div class="relative group">
			<button
				class="flex items-center gap-0.5 {isHighlighted(
					'/ad-creatives',
					'/top-mobile-advertisers',
					'/app-explorer',
					'/sdks'
				)
					? topBarHighlightedFont
					: topBarFont}"
			>
				App Intelligence <ChevronDown class="h-3 w-3 transition-transform group-hover:rotate-180" />
			</button>
			<div class="absolute left-0 top-full pt-1 hidden group-hover:block z-50 min-w-max">
				<div class="card bg-surface-50-950 shadow-xl rounded-md py-1">
					<a
						href="/ad-creatives"
						class={isHighlighted('/ad-creatives') ? dropdownHighlightedItem : dropdownItem}
						>Ad Creatives</a
					>
					<a
						href="/top-mobile-advertisers"
						class={isHighlighted('/top-mobile-advertisers')
							? dropdownHighlightedItem
							: dropdownItem}>Top Mobile Advertisers</a
					>
					<a
						href="/app-explorer"
						class={isHighlighted('/app-explorer') ? dropdownHighlightedItem : dropdownItem}
						>App Explorer</a
					>
					<a href="/sdks" class={isHighlighted('/sdks') ? dropdownHighlightedItem : dropdownItem}
						>Free SDK Scans</a
					>
				</div>
			</div>
		</div>

		<div class={myDivider}></div>
		<!-- RANKINGS dropdown -->
		<div class="relative group">
			<button
				class="flex items-center gap-0.5 {isHighlighted(
					'/rankings',
					'/fastest-growing-apps',
					'/top-ctv-app-ranks',
					'/collections'
				)
					? topBarHighlightedFont
					: topBarFont}"
			>
				Rankings <ChevronDown class="h-3 w-3 transition-transform group-hover:rotate-180" />
			</button>
			<div class="absolute left-0 top-full pt-1 hidden group-hover:block z-50 min-w-max">
				<div class="card bg-surface-50-950 shadow-xl rounded-md py-1">
					<a
						href="/rankings/store/1/collection/1/category/1/US"
						class={isHighlighted('/rankings') ? dropdownHighlightedItem : dropdownItem}
						>Top Google Play App Ranks</a
					>
					<a
						href="/rankings/store/2/collection/4/category/120/US"
						class={isHighlighted('/rankings') ? dropdownHighlightedItem : dropdownItem}
						>Apple App Store Ranks</a
					>
					<a
						href="/fastest-growing-apps/google/overall"
						class={isHighlighted('/fastest-growing-apps') ? dropdownHighlightedItem : dropdownItem}
						>Top Growth Apps</a
					>
					<a
						href="/top-ctv-app-ranks/google"
						class={isHighlighted('/top-ctv-app-ranks') ? dropdownHighlightedItem : dropdownItem}
						>Top CTV Apps</a
					>
					<a
						href="/collections/new_monthly/google/overall"
						class={isHighlighted('/collections') ? dropdownHighlightedItem : dropdownItem}
						>New Apps</a
					>
				</div>
			</div>
		</div>

		<div class={myDivider}></div>
		<!-- RESOURCES dropdown -->
		<div class="relative group">
			<button
				class="flex items-center gap-0.5 {isHighlighted(
					'/blog',
					'/api-docs',
					'/docs',
					'/reports',
					'/free-app-datasets'
				)
					? topBarHighlightedFont
					: topBarFont}"
			>
				Resources <ChevronDown class="h-3 w-3 transition-transform group-hover:rotate-180" />
			</button>
			<div class="absolute left-0 top-full pt-1 hidden group-hover:block z-50 min-w-max">
				<div class="card bg-surface-50-950 shadow-xl rounded-md py-1">
					<a
						href="/reports"
						class={isHighlighted('/reports') ? dropdownHighlightedItem : dropdownItem}
						>Free Reports</a
					>
					<a
						href="/free-app-datasets"
						class={isHighlighted('/free-app-datasets') ? dropdownHighlightedItem : dropdownItem}
						>Free Datasets</a
					>
					<a
						href="/api-docs"
						class={isHighlighted('/api-docs') ? dropdownHighlightedItem : dropdownItem}
						>Docs: API & MCP</a
					>
					<a
						href="/docs/data-exports"
						class={isHighlighted('/docs/data-exports') ? dropdownHighlightedItem : dropdownItem}
						>Docs: Paid Datasets</a
					>
					<a href="/blog" class={isHighlighted('/blog') ? dropdownHighlightedItem : dropdownItem}
						>Blog</a
					>
				</div>
			</div>
		</div>

		<div class={myDivider}></div>

		<a href="/pricing" class={isHighlighted('/pricing') ? topBarHighlightedFont : topBarFont}
			>Pricing</a
		>
	</div>
{/if}
