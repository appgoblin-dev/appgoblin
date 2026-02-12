<script lang="ts">
	import { page } from '$app/state';
	import ChartLine from 'lucide-svelte/icons/chart-line';
	import ChartBar from 'lucide-svelte/icons/chart-bar';
	import Boxes from 'lucide-svelte/icons/boxes';
	import Key from 'lucide-svelte/icons/key';
	import TrendingUp from 'lucide-svelte/icons/trending-up';
	import FileText from 'lucide-svelte/icons/file-text';
	import Image from 'lucide-svelte/icons/image';

	let { isAndroidApp, myapp } = $props();

	const textGreyedOutColor = 'text-surface-700-300';

	const myTabs = $derived({
		types: [
			{
				name: 'Overview',
				url_slug: '',
				icon: ChartLine
			},
			{
				name: 'Trends',
				url_slug: '/trends',
				icon: TrendingUp
			},
			{
				name: 'SDKs',
				url_slug: '/sdks',
				icon: Boxes
			},
			{
				name: 'Keywords',
				url_slug: '/keywords',
				icon: Key
			},
			{
				name: 'Store Rankings',
				url_slug: '/ranks',
				icon: ChartBar
			},
			...(isAndroidApp
				? [
						{
							name: 'Data & API Calls',
							url_slug: '/data-flows',
							icon: FileText
						},
						{
							name: 'Ad Creatives',
							url_slug: '/ad-creatives',
							icon: Image
						},
						{
							name: 'Ad Placements',
							url_slug: '/ad-placements',
							icon: Image
						},
						{
							name: 'Monetized Ad Creatives',
							url_slug: '/monetized-ads',
							icon: Image
						}
					]
				: []),

			{
				name: 'App-Ads.txt',
				url_slug: '/ads-txt',
				icon: FileText
			}
		]
	});

	function typeTabClass(tab: string) {
		const baseClass =
			'flex items-center gap-1 md:gap-2 px-4 py-1 md:py-3 font-medium transition-colors duration-200';
		const selectedClass = 'text-primary-500 bg-surface-100-900 hover:bg-primary-500/5';
		const unselectedClass =
			'border-transparent hover:text-primary-400 hover:border-primary-400/30 hover:bg-primary-900-100/50';
		const unselectedGreyClass =
			'border-transparent hover:text-surface-700-200-token hover:border-surface-700-200-token/30 hover:bg-surface-100-900/50';
		if (tab === '') {
			if (page.url.pathname === `/apps/${page.params.id}`) {
				return `${baseClass} ${selectedClass}`;
			} else {
				return `${baseClass} ${unselectedClass}`;
			}
		}

		if (page.url.pathname.startsWith(`/apps/${page.params.id}${tab}`)) {
			return `${baseClass} ${selectedClass}`;
		} else {
			if (tab === '/sdks') {
				return `${baseClass} ${unselectedGreyClass}`;
			} else {
				return `${baseClass} ${unselectedClass}`;
			}
		}
	}

	function tabTextClass(tab: string) {
		if (tab === '/sdks' && !myapp.sdk_successful_last_crawled) {
			return textGreyedOutColor;
		} else if (tab === '/data-flows' && !myapp.api_successful_last_crawled) {
			return textGreyedOutColor;
		} else if (tab === '/ads-txt' && myapp.adstxt_crawl_result != 1) {
			return textGreyedOutColor;
		} else if (tab === '/ad-creatives' && myapp.ad_creative_count == 0) {
			return textGreyedOutColor;
		} else if (tab === '/ad-placements' && myapp.ad_creative_count == 0) {
			return textGreyedOutColor;
		} else if (tab === '/monetized-ads' && myapp.ad_monetized_creative_count == 0) {
			return textGreyedOutColor;
		} else {
			return '';
		}
	}
</script>

<div class="flex flex-wrap gap-1 text-xs md:text-sm overflow-x-auto">
	{#each myTabs.types as tab}
		{@const Component = tab.icon}
		<a
			href={`/apps/${page.params.id}${tab.url_slug}`}
			class={typeTabClass(tab.url_slug)}
			data-sveltekit-preload-data
		>
			<Component size={20} strokeWidth={1.5} class={tabTextClass(tab.url_slug)} />
			<span class={tabTextClass(tab.url_slug)}>{tab.name}</span>
		</a>
	{/each}
</div>
