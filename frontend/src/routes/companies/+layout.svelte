<script lang="ts">
	import { page } from '$app/state';
	import type { Crumb } from '../../types';
	import Breadcrumbs from '$lib/Breadcrumbs.svelte';
	import CompanyTypesTabs from '$lib/utils/CompanyTypesTabs.svelte';
	import type { MyCrumbMetadata } from '../../types';

	let { data, children } = $props();

	let pageDataCrumbs = $derived(page.data.crumbs as Crumb<MyCrumbMetadata>[] | undefined);

	let customCrumbs = $derived.by((): Crumb<MyCrumbMetadata>[] | undefined => {
		if (!page.params.domain) return undefined;
		const companyDetails = page.data.companyDetails as { company_types?: string[] } | undefined;
		const companyTree = page.data.companyTree as
			| { company_name?: string; company_domain?: string; queried_domain?: string }
			| undefined;
		const primaryType = companyDetails?.company_types?.[0];
		const typeName = primaryType
			? data.companyTypes?.types.find(
					(t: { url_slug: string; name: string }) => t.url_slug === primaryType
				)?.name
			: undefined;
		const companyName =
			companyTree?.company_name ||
			companyTree?.company_domain ||
			companyTree?.queried_domain ||
			page.params.domain;

		const crumbs: Crumb<MyCrumbMetadata>[] = [{ title: 'Companies', url: '/companies' }];
		if (typeName && primaryType) {
			crumbs.push({ title: typeName, url: `/companies/types/${primaryType}` });
		}
		crumbs.push({ title: companyName });
		return crumbs;
	});
</script>

<div class="px-1 md:px-4 mb-4">
	<Breadcrumbs
		url={page.url}
		routeId={page.route.id}
		pageData={page.data}
		crumbs={pageDataCrumbs ?? customCrumbs}
	>
		{#snippet children({ crumbs })}
			<div>
				<span><a href="/" class="text-surface-900-100 hover:">Home</a></span>
				{#each crumbs as c}
					<span>/</span>
					<span>
						{#if c.title != 'Types' && c.title != 'Categories' && c.title != 'Publisher' && c.title != 'App-adstxt'}
							<a href={c.url} class="text-surface-900-100 hover:">
								{c.title}
								{c.metadata ? `(${c.metadata.extraValue})` : ''}
							</a>
						{:else}
							{c.title}
							{c.metadata ? `(${c.metadata.extraValue})` : ''}
						{/if}
					</span>
				{/each}
			</div>
		{/snippet}
	</Breadcrumbs>
</div>

<div class="px-1 md:px-4">
	{#if !page.params.domain && !page.url.pathname.includes('adstxt') && data.companyTypes && data.companyTypes.types.length > 0}
		<CompanyTypesTabs companyTypes={data.companyTypes} />
	{/if}

	{@render children?.()}
</div>
