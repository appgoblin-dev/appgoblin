<script lang="ts">
	import { page } from '$app/state';

	import type { CompanyTabIndicators } from '../../types';
	import SubNavTabs from './SubNavTabs.svelte';
	import type { SubNavTabItem } from './SubNavTabs.svelte';
	import { companySectionHasData } from './companySectionAvailability.js';
	import Home from '@lucide/svelte/icons/home';
	import Image from '@lucide/svelte/icons/image';
	import TrendingUp from '@lucide/svelte/icons/trending-up';
	import PlusCircle from '@lucide/svelte/icons/plus-circle';
	import MinusCircle from '@lucide/svelte/icons/minus-circle';
	import Boxes from '@lucide/svelte/icons/boxes';
	import Puzzle from '@lucide/svelte/icons/puzzle';
	import FileText from '@lucide/svelte/icons/file-text';
	import Download from '@lucide/svelte/icons/download';
	import Network from '@lucide/svelte/icons/network';

	let {
		tabIndicators,
		mediationPartnerCount,
		companyDomain,
		companyDisplayName
	}: {
		tabIndicators: CompanyTabIndicators | null;
		mediationPartnerCount: number | null;
		companyDomain: string;
		companyDisplayName: string;
	} = $props();

	function getSectionSlug(pathname: string): string {
		if (pathname.includes('/app-adstxt/publisher/')) return 'app-adstxt-publisher';
		if (pathname.includes('/app-adstxt')) return 'app-adstxt';
		if (pathname.includes('/apps-added-adstxt')) return 'apps-added-adstxt';
		if (pathname.includes('/apps-lost-adstxt')) return 'apps-lost-adstxt';
		if (pathname.includes('/apps-added')) return 'apps-added';
		if (pathname.includes('/apps-lost')) return 'apps-lost';
		if (pathname.includes('/api-calls')) return 'api-apps';
		if (pathname.includes('/creatives')) return 'creatives';
		if (pathname.includes('/data-exports')) return 'data-exports';
		if (pathname.includes('/mediation/partners')) return 'mediation-partners';
		if (pathname.includes('/mediation')) return 'mediation';
		if (pathname.includes('/trends')) return 'trends';
		if (pathname.includes('/sdks')) return 'sdks';
		return 'overview';
	}

	function isParentOnlyData(tabSlug: string): boolean {
		if (!tabIndicators) return false;
		switch (tabSlug) {
			case 'creatives':
				return (
					tabIndicators.creatives_app_count > 0 &&
					tabIndicators.creatives_app_count_direct === 0 &&
					!tabIndicators.is_parent_domain
				);
			case 'trends':
				return (
					tabIndicators.has_trends > 0 &&
					tabIndicators.has_trends_direct === 0 &&
					!tabIndicators.is_parent_domain
				);
			case 'apps-added':
			case 'apps-lost':
				return (
					(tabIndicators.apps_sdk_added_count > 0 || tabIndicators.apps_sdk_lost_count > 0) &&
					tabIndicators.apps_sdk_added_count_direct === 0 &&
					tabIndicators.apps_sdk_lost_count_direct === 0 &&
					!tabIndicators.is_parent_domain
				);
			case 'sdks':
				return (
					tabIndicators.sdk_count > 0 &&
					tabIndicators.sdk_count_direct === 0 &&
					!tabIndicators.is_parent_domain
				);
			case 'mediation':
				return (
					tabIndicators.mediation_adapter_count > 0 &&
					tabIndicators.mediation_adapter_count_direct === 0 &&
					!tabIndicators.is_parent_domain
				);
			case 'app-adstxt':
			case 'apps-added-adstxt':
			case 'apps-lost-adstxt':
				return false;
			default:
				return false;
		}
	}

	function tabHasData(slug: string): boolean {
		return companySectionHasData(slug, tabIndicators, mediationPartnerCount);
	}

	let sectionSlug = $derived(getSectionSlug(page.url.pathname));

	let hasAnyAppsAdded = $derived(
		Boolean(tabIndicators?.apps_sdk_added_count) ||
			Boolean(tabIndicators?.apps_adstxt_direct_added_count)
	);
	let hasAnyAppsLost = $derived(
		Boolean(tabIndicators?.apps_sdk_lost_count) ||
			Boolean(tabIndicators?.apps_adstxt_direct_lost_count)
	);

	let sectionLinks = $derived.by((): SubNavTabItem[] => {
		const topLinks: SubNavTabItem[] = [
			{
				slug: 'overview',
				label: `${companyDisplayName} Apps Overview`,
				href: `/companies/${companyDomain}`,
				icon: Home,
				count: null
			},
			{
				slug: 'api-apps',
				label: 'Apps Using API',
				href: `/companies/${companyDomain}/api-calls`,
				icon: Network
			},
			{
				slug: 'creatives',
				label: 'Creatives',
				href: `/companies/${companyDomain}/creatives`,
				icon: Image,
				count: tabIndicators?.creatives_app_count ?? null,
				dimmed: isParentOnlyData('creatives')
			},
			{
				slug: 'trends',
				label: 'Trends',
				href: `/companies/${companyDomain}/trends`,
				icon: TrendingUp,
				count: null,
				dimmed: isParentOnlyData('trends')
			},
			{
				slug: 'sdks',
				label: 'SDKs',
				href: `/companies/${companyDomain}/sdks`,
				icon: Boxes,
				count: null,
				dimmed: isParentOnlyData('sdks')
			},
			{
				slug: 'app-adstxt',
				label: 'App-ads.txt',
				href: `/companies/${companyDomain}/app-adstxt`,
				icon: FileText,
				matchSlugs: ['app-adstxt-publisher'],
				count:
					tabIndicators?.adstxt_parent_app_count ?? tabIndicators?.adstxt_direct_app_count ?? null
			},
			{
				slug: 'data-exports',
				label: 'Full Client App CSVs',
				href: `/companies/${companyDomain}/data-exports`,
				icon: Download,
				b2b: true,
				count: null
			}
		].filter((l) => tabHasData(l.slug));

		const bottomSections: SubNavTabItem[] = [
			...(tabHasData('mediation') || (mediationPartnerCount ?? 0) > 0
				? [
						{ sectionLabel: 'Mediation' } as SubNavTabItem,
						...(tabHasData('mediation')
							? [
									{
										slug: 'mediation',
										label: 'As Mediation Partner',
										href: `/companies/${companyDomain}/mediation`,
										icon: Puzzle,
										count: tabIndicators?.mediation_adapter_count ?? null,
										dimmed: isParentOnlyData('mediation'),
										indent: true
									}
								]
							: []),
						...((mediationPartnerCount ?? 0) > 0
							? [
									{
										slug: 'mediation-partners',
										label: 'As Adapter',
										href: `/companies/${companyDomain}/mediation/partners`,
										icon: Puzzle,
										count: mediationPartnerCount,
										indent: true
									}
								]
							: [])
					]
				: []),
			...(hasAnyAppsAdded
				? [
						{ sectionLabel: 'Apps Recently Added' } as SubNavTabItem,
						...(tabHasData('apps-added')
							? [
									{
										slug: 'apps-added',
										label: 'SDK Verified',
										href: `/companies/${companyDomain}/apps-added`,
										icon: PlusCircle,
										b2b: true,
										count: tabIndicators?.apps_sdk_added_count ?? null,
										dimmed: isParentOnlyData('apps-added'),
										indent: true
									}
								]
							: []),
						...(tabHasData('apps-added-adstxt')
							? [
									{
										slug: 'apps-added-adstxt',
										label: 'App-ads.txt',
										href: `/companies/${companyDomain}/apps-added-adstxt`,
										icon: PlusCircle,
										b2b: true,
										count: tabIndicators?.apps_adstxt_direct_added_count ?? null,
										indent: true
									}
								]
							: [])
					]
				: []),
			...(hasAnyAppsLost
				? [
						{ sectionLabel: 'Apps Recently Lost' } as SubNavTabItem,
						...(tabHasData('apps-lost')
							? [
									{
										slug: 'apps-lost',
										label: 'SDK Verified',
										href: `/companies/${companyDomain}/apps-lost`,
										icon: MinusCircle,
										b2b: true,
										count: tabIndicators?.apps_sdk_lost_count ?? null,
										dimmed: isParentOnlyData('apps-lost'),
										indent: true
									}
								]
							: []),
						...(tabHasData('apps-lost-adstxt')
							? [
									{
										slug: 'apps-lost-adstxt',
										label: 'App-ads.txt',
										href: `/companies/${companyDomain}/apps-lost-adstxt`,
										icon: MinusCircle,
										b2b: true,
										count: tabIndicators?.apps_adstxt_direct_lost_count ?? null,
										indent: true
									}
								]
							: [])
					]
				: [])
		];

		return [...topLinks, ...bottomSections];
	});
</script>

<SubNavTabs
	tabs={sectionLinks}
	currentSlug={sectionSlug}
	ariaLabel="Company sections"
	menuLabel="Company Menu"
/>
