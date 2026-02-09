<script lang="ts">
	import { page } from '$app/state';
	const topBarFont = 'text-xs md:text-sm xxl:text-base hover:text-primary-900-100';
	const topBarHighlightedFont = 'text-xs md:text-sm xxl:text-base text-primary-900-100';
	const myDivider = 'h-px w-[50%] md:h-12 md:w-px bg-secondary-100-900';
	const topDivider =
		'w-full border-t-[1px] md:border-t-0 md:border-b-[1px] border-secondary-100-900 p-1 xxl:p-2';
	function isHighlighted(path: string) {
		return page.url.pathname.startsWith(path);
	}

	let { hideLinks = false } = $props();
</script>

<div
	class="flex flex-col md:flex-row gap-1 md:gap-2 xxl:gap-6 text-center items-center {topDivider} mx-2"
>
	<a href="/companies" class={topBarFont}>
		<p class={isHighlighted('/companies') ? topBarHighlightedFont : topBarFont}>COMPANY RANKS</p>
	</a>

	<div class={myDivider}></div>
	<a href="/rankings/store/1/collection/1/category/1/US" class={topBarFont}>
		<p class={isHighlighted('/rankings') ? topBarHighlightedFont : topBarFont}>APP RANKS</p>
	</a>
	{#if !hideLinks}
		<div class={myDivider}></div>
		<a href="/sdks" class={topBarFont}>
			<p class={isHighlighted('/sdks') ? topBarHighlightedFont : topBarFont}>SDKS</p>
		</a>

		<div class={myDivider}></div>
		<a href="/collections/new_monthly/google/overall">
			<p class={isHighlighted('/collections') ? topBarHighlightedFont : topBarFont}>NEW APPS</p>
		</a>
		<div class={myDivider}></div>
		<a href="/fastest-growing-apps/google/overall">
			<p class={isHighlighted('/fastest-growing-apps') ? topBarHighlightedFont : topBarFont}>
				FASTEST GROWING APPS
			</p>
		</a>
		<div class={myDivider}></div>
		<a href="/ad-creatives">
			<p class={isHighlighted('/ad-creatives') ? topBarHighlightedFont : topBarFont}>
				TOP ADVERTISERS
			</p>
		</a>
		<div class={myDivider}></div>
		<a href="/blog">
			<p class={isHighlighted('/blog') ? topBarHighlightedFont : topBarFont}>BLOG</p>
		</a>
		<div class={myDivider}></div>
		<a href="/reports">
			<p class={isHighlighted('/reports') ? topBarHighlightedFont : topBarFont}>REPORTS</p>
		</a>
	{/if}
	<div class={myDivider}></div>
	<a href="/pricing" class={topBarFont}>
		<p class={isHighlighted('/pricing') ? topBarHighlightedFont : topBarFont}>PRICING</p>
	</a>
	<div class={myDivider}></div>
	<a href="/about" class={topBarFont}>
		<p class={isHighlighted('/about') ? topBarHighlightedFont : topBarFont}>ABOUT</p>
	</a>
</div>
