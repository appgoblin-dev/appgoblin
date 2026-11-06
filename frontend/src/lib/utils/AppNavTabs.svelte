<script lang="ts">
	import { page } from '$app/state';
	import type { AppFullDetail } from '../../types';
	import SubNavTabs from './SubNavTabs.svelte';
	import type { SubNavTabItem } from './SubNavTabs.svelte';
	import ChartLine from '@lucide/svelte/icons/chart-line';
	import ChartBar from '@lucide/svelte/icons/chart-bar';
	import Boxes from '@lucide/svelte/icons/boxes';
	import Key from '@lucide/svelte/icons/key';
	import TrendingUp from '@lucide/svelte/icons/trending-up';
	import FileText from '@lucide/svelte/icons/file-text';
	import Image from '@lucide/svelte/icons/image';
	import History from '@lucide/svelte/icons/history';
	import HelpCircle from '@lucide/svelte/icons/help-circle';
	import Shield from '@lucide/svelte/icons/shield';
	import Search from '@lucide/svelte/icons/search';
	import RadioReceiver from '@lucide/svelte/icons/radio-receiver';
	import Table from '@lucide/svelte/icons/table';
	import GitCompareArrows from '@lucide/svelte/icons/git-compare-arrows';

	let { isAndroidApp, myapp }: { isAndroidApp: boolean; myapp: AppFullDetail } = $props();

	function isTabDimmed(slug: string): boolean {
		if (slug === 'sdks' && !myapp.sdk_successful_last_crawled) return true;
		if (slug === 'data-flows' && !myapp.api_successful_last_crawled) return true;
		return false;
	}

	function getSlugFromPath(pathname: string): string {
		const path = pathname.replace(`/apps/${page.params.id}`, '') || '/';
		if (path === '/') return 'overview';
		const clean = path.replace(/^\//, '');
		// Map nested sub-paths like sdks/history -> sdks-history
		if (clean.includes('/')) {
			return clean.replace(/\//g, '-');
		}
		return clean;
	}

	function isSdkDimmed(): boolean {
		return !myapp.sdk_successful_last_crawled;
	}

	let currentSlug = $derived(getSlugFromPath(page.url.pathname));

	let tabs = $derived.by((): SubNavTabItem[] => {
		const items: SubNavTabItem[] = [
			{
				slug: 'overview',
				label: 'Overview',
				href: `/apps/${page.params.id}`,
				icon: ChartLine
			},
			{
				slug: 'trends',
				label: 'Trends',
				href: `/apps/${page.params.id}/trends`,
				icon: TrendingUp
			},
			{
				sectionLabel: 'SDKs'
			},
			{
				slug: 'sdks',
				label: 'Latest SDKs',
				href: `/apps/${page.params.id}/sdks`,
				icon: Boxes,
				dimmed: isSdkDimmed(),
				matchSlugs: [
					'sdks-history',
					'sdks-unknowns',
					'sdks-permissions',
					'sdks-queries',
					'sdks-skadnetwork'
				],
				indent: true,
				authRequired: true
			},
			{
				slug: 'sdks-history',
				label: 'SDK History',
				href: `/apps/${page.params.id}/sdks/history`,
				icon: History,
				dimmed: isSdkDimmed(),
				indent: true,
				authRequired: true,
				b2b: true
			},
			{
				slug: 'sdks-unknowns',
				label: 'Unmapped SDKs',
				href: `/apps/${page.params.id}/sdks/unknowns`,
				icon: HelpCircle,
				dimmed: isSdkDimmed(),
				indent: true,
				authRequired: true
			},
			...(isAndroidApp
				? [
						{
							slug: 'sdks-queries' as const,
							label: 'App Queries',
							href: `/apps/${page.params.id}/sdks/queries`,
							icon: Search,
							dimmed: isSdkDimmed(),
							indent: true,
							authRequired: true
						},
						{
							slug: 'sdks-permissions' as const,
							label: 'Permissions',
							href: `/apps/${page.params.id}/sdks/permissions`,
							icon: Shield,
							dimmed: isSdkDimmed(),
							indent: true,
							authRequired: true
						}
					]
				: [
						{
							slug: 'sdks-skadnetwork' as const,
							label: 'SKAdNetwork',
							href: `/apps/${page.params.id}/sdks/skadnetwork`,
							icon: RadioReceiver,
							dimmed: isSdkDimmed(),
							indent: true,
							authRequired: true
						}
					]),
			{
				slug: 'keywords',
				label: 'Keywords',
				href: `/apps/${page.params.id}/keywords`,
				icon: Key,
				authRequired: true
			},
			{
				slug: 'ranks',
				label: 'Store Rankings',
				href: `/apps/${page.params.id}/ranks`,
				icon: ChartBar
			}
		];

		if (isAndroidApp) {
			items.push({
				slug: 'data-flows',
				label: 'Data & API Calls',
				href: `/apps/${page.params.id}/data-flows`,
				icon: FileText,
				dimmed: isTabDimmed('data-flows'),
				matchSlugs: ['data-flows-details', 'data-flows-changes']
			});

			items.push({
				slug: 'data-flows-details',
				label: 'All API Calls',
				href: `/apps/${page.params.id}/data-flows/details`,
				icon: Table,
				dimmed: isTabDimmed('data-flows'),
				indent: true
			});

			items.push({
				slug: 'data-flows-changes',
				label: 'Data Flow Changes',
				href: `/apps/${page.params.id}/data-flows/changes`,
				icon: GitCompareArrows,
				dimmed: isTabDimmed('data-flows'),
				indent: true
			});

			if ((myapp.ad_creative_count ?? 0) > 0) {
				items.push({
					slug: 'ad-creatives',
					label: 'Ad Creatives',
					href: `/apps/${page.params.id}/ad-creatives`,
					icon: Image
				});
				items.push({
					slug: 'ad-placements',
					label: 'Ad Placements',
					href: `/apps/${page.params.id}/ad-placements`,
					icon: Image
				});
			}

			if ((myapp.ad_monetized_creative_count ?? 0) > 0) {
				items.push({
					slug: 'monetized-ads',
					label: 'Monetized Ad Creatives',
					href: `/apps/${page.params.id}/monetized-ads`,
					icon: Image
				});
			}
		}

		if (myapp.adstxt_crawl_result === 1) {
			items.push({
				slug: 'ads-txt',
				label: 'App-Ads.txt',
				href: `/apps/${page.params.id}/ads-txt`,
				icon: FileText
			});
		}

		return items;
	});
</script>

<SubNavTabs {tabs} {currentSlug} ariaLabel="App sections" menuLabel="App Menu" />
