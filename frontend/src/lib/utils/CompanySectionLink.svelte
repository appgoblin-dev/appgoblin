<script lang="ts">
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import type { Snippet } from 'svelte';
	import type { CompanyLayoutDetails } from '../../types';
	import { companySectionHasData } from './companySectionAvailability.js';

	const routes = {
		sdks: '/companies/[domain]/sdks',
		'api-apps': '/companies/[domain]/api-calls',
		trends: '/companies/[domain]/trends',
		creatives: '/companies/[domain]/creatives',
		'app-adstxt': '/companies/[domain]/app-adstxt',
		'data-exports': '/companies/[domain]/data-exports',
		mediation: '/companies/[domain]/mediation',
		'mediation-partners': '/companies/[domain]/mediation/partners',
		'apps-added': '/companies/[domain]/apps-added',
		'apps-lost': '/companies/[domain]/apps-lost',
		'apps-added-adstxt': '/companies/[domain]/apps-added-adstxt',
		'apps-lost-adstxt': '/companies/[domain]/apps-lost-adstxt'
	} as const;

	let { slug, children }: { slug: keyof typeof routes; children: Snippet } = $props();
	let companyData = $derived(page.data as CompanyLayoutDetails);
	let available = $derived(
		companySectionHasData(slug, companyData.tabIndicators, companyData.mediationPartners?.length)
	);
</script>

{#if available}
	<a
		href={resolve(routes[slug], { domain: page.params.domain ?? '' })}
		class="underline hover:text-primary-600-400">{@render children()}</a
	>
{:else}
	{@render children()}
{/if}
