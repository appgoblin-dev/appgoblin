<script lang="ts">
	import { page } from '$app/state';
	import ChevronDown from 'lucide-svelte/icons/chevron-down';

	const topBarFont = 'text-xs md:text-base hover:';
	const topBarHighlightedFont = 'text-xs md:text-base ';
	const myDivider = 'h-px w-[50%] md:h-12 md:w-px bg-secondary-100-900';
	const topDivider =
		'w-full border-t-[1px] md:border-t-0 md:border-b-[1px] border-secondary-100-900 p-1 xxl:p-2';
	const dropdownItem =
		'block px-4 py-2 text-xs md:text-base hover: hover:preset-tonal w-full text-left whitespace-nowrap';
	const dropdownHighlightedItem =
		'block px-4 py-2 text-xs md:text-base  preset-tonal w-full text-left whitespace-nowrap';
	const sectionLabel = 'text-xs font-semibold uppercase tracking-widest pt-1';
	const dropdownSectionLabel = 'px-4 pt-2 pb-1 text-[11px] font-semibold uppercase tracking-widest';
	const dropdownSectionDivider = 'mx-4 my-1 border-t border-secondary-100-900';

	function isHighlighted(...paths: string[]) {
		return paths.some((p) => page.url.pathname.startsWith(p));
	}

	let { hideLinks = false, flat = false } = $props();
</script>

{#if flat || hideLinks}
	<!-- Flat list used inside the mobile hamburger menu -->
	<div class="flex flex-col gap-1 {topDivider} mx-2">
		{#if !hideLinks}
			<!-- RANKINGS group -->
			<p class={sectionLabel}>Rankings</p>
			<a
				href="/rankings/store/1/collection/1/category/1/US"
				class={isHighlighted('/rankings') ? topBarHighlightedFont : topBarFont}
				>TOP GOOGLE PLAY APP RANKS</a
			>
			<div class={myDivider}></div>
			<a
				href="/rankings/store/2/collection/4/category/120/US"
				class={isHighlighted('/rankings') ? topBarHighlightedFont : topBarFont}
				>APPLE APP STORE RANKS</a
			>
			<div class={myDivider}></div>
			<a
				href="/fastest-growing-apps/google/overall"
				class={isHighlighted('/fastest-growing-apps') ? topBarHighlightedFont : topBarFont}
				>TOP GROWTH APPS</a
			>
			<div class={myDivider}></div>
			<a
				href="/collections/new_monthly/google/overall"
				class={isHighlighted('/collections') ? topBarHighlightedFont : topBarFont}>NEW APPS</a
			>
			<div class={myDivider}></div>
			<!-- INTELLIGENCE group -->
			<p class={sectionLabel}>Intelligence</p>
			<p class={sectionLabel}>Company Rankings</p>
			<a href="/companies" class={isHighlighted('/companies') ? topBarHighlightedFont : topBarFont}
				>COMPANY RANKS</a
			>
			<div class={myDivider}></div>
			<a
				href="/companies/types/ad-networks"
				class={isHighlighted('/companies/types/ad-networks') ? topBarHighlightedFont : topBarFont}
				>AD NETWORKS</a
			>
			<div class={myDivider}></div>
			<a
				href="/companies/types/ad-attribution"
				class={isHighlighted('/companies/types/ad-attribution')
					? topBarHighlightedFont
					: topBarFont}>ANALYTICS: ATTRIBUTION</a
			>
			<div class={myDivider}></div>
			<a
				href="/companies/types/product-analytics"
				class={isHighlighted('/companies/types/product-analytics')
					? topBarHighlightedFont
					: topBarFont}>ANALYTICS</a
			>
			<div class={myDivider}></div>
			<a
				href="/companies/types/development-tools"
				class={isHighlighted('/companies/types/development-tools')
					? topBarHighlightedFont
					: topBarFont}>DEVELOPMENT TOOLS</a
			>
			<div class={myDivider}></div>
			<a
				href="/companies/types/mediation"
				class={isHighlighted('/companies/types/mediation') ? topBarHighlightedFont : topBarFont}
				>MEDIATION PLATFORMS</a
			>
			<div class={myDivider}></div>
			<a
				href="/companies/types/business-tools"
				class={isHighlighted('/companies/types/business-tools')
					? topBarHighlightedFont
					: topBarFont}>BUSINESS TOOLS</a
			>
			<div class={myDivider}></div>
			<p class={sectionLabel}>Apps</p>
			<a
				href="/ad-creatives"
				class={isHighlighted('/ad-creatives') ? topBarHighlightedFont : topBarFont}>AD CREATIVES</a
			>
			<a
				href="/top-mobile-advertisers"
				class={isHighlighted('/top-mobile-advertisers') ? topBarHighlightedFont : topBarFont}
				>TOP ADVERTISERS</a
			>
			<div class={myDivider}></div>
			<a
				href="/app-explorer"
				class={isHighlighted('/app-explorer') ? topBarHighlightedFont : topBarFont}>APP EXPLORER</a
			>
			<div class={myDivider}></div>
			<a href="/sdks" class={isHighlighted('/sdks') ? topBarHighlightedFont : topBarFont}>SDKS</a>
			<div class={myDivider}></div>
			<!-- RESOURCES group -->
			<p class={sectionLabel}>Resources</p>
			<a href="/blog" class={isHighlighted('/blog') ? topBarHighlightedFont : topBarFont}>BLOG</a>
			<div class={myDivider}></div>
			<a href="/reports" class={isHighlighted('/reports') ? topBarHighlightedFont : topBarFont}
				>REPORTS</a
			>
			<div class={myDivider}></div>
			<a
				href="/free-app-datasets"
				class={isHighlighted('/free-app-datasets') ? topBarHighlightedFont : topBarFont}
			>
				DATA EXPORTS</a
			>
			<div class={myDivider}></div>
		{/if}
		<a href="/pricing" class={isHighlighted('/pricing') ? topBarHighlightedFont : topBarFont}
			>PRICING</a
		>
		<div class={myDivider}></div>
		<a href="/about" class={isHighlighted('/about') ? topBarHighlightedFont : topBarFont}>ABOUT</a>
	</div>
{:else}
	<!-- Desktop dropdown bar -->
	<div class="flex flex-row gap-1 md:gap-2 xxl:gap-6 text-center items-center {topDivider} mx-2">
		<!-- RANKINGS dropdown -->
		<div class="relative group">
			<button
				class="flex items-center gap-0.5 {isHighlighted(
					'/rankings',
					'/fastest-growing-apps',
					'/collections'
				)
					? topBarHighlightedFont
					: topBarFont}"
			>
				RANKINGS <ChevronDown class="h-3 w-3 transition-transform group-hover:rotate-180" />
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
						href="/collections/new_monthly/google/overall"
						class={isHighlighted('/collections') ? dropdownHighlightedItem : dropdownItem}
						>New Apps</a
					>
				</div>
			</div>
		</div>

		<div class={myDivider}></div>

		<!-- INTELLIGENCE dropdown -->
		<div class="relative group">
			<button
				class="flex items-center gap-0.5 {isHighlighted(
					'/companies',
					'/ad-creatives',
					'/top-mobile-advertisers',
					'/app-explorer',
					'/sdks'
				)
					? topBarHighlightedFont
					: topBarFont}"
			>
				INTELLIGENCE <ChevronDown class="h-3 w-3 transition-transform group-hover:rotate-180" />
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
					<div class={dropdownSectionDivider}></div>
					<p class={dropdownSectionLabel}>Apps</p>
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
						>SDKs</a
					>
				</div>
			</div>
		</div>

		<div class={myDivider}></div>

		<!-- RESOURCES dropdown -->
		<div class="relative group">
			<button
				class="flex items-center gap-0.5 {isHighlighted('/blog', '/reports', '/free-app-datasets')
					? topBarHighlightedFont
					: topBarFont}"
			>
				RESOURCES <ChevronDown class="h-3 w-3 transition-transform group-hover:rotate-180" />
			</button>
			<div class="absolute left-0 top-full pt-1 hidden group-hover:block z-50 min-w-max">
				<div class="card bg-surface-50-950 shadow-xl rounded-md py-1">
					<a href="/blog" class={isHighlighted('/blog') ? dropdownHighlightedItem : dropdownItem}
						>Blog</a
					>
					<a
						href="/reports"
						class={isHighlighted('/reports') ? dropdownHighlightedItem : dropdownItem}>Reports</a
					>
					<a
						href="/free-app-datasets"
						class={isHighlighted('/free-app-datasets') ? dropdownHighlightedItem : dropdownItem}
						>Data Exports</a
					>
				</div>
			</div>
		</div>

		<div class={myDivider}></div>

		<a href="/pricing" class={isHighlighted('/pricing') ? topBarHighlightedFont : topBarFont}
			>PRICING</a
		>

		<div class={myDivider}></div>

		<a href="/about" class={isHighlighted('/about') ? topBarHighlightedFont : topBarFont}>ABOUT</a>
	</div>
{/if}
