<script lang="ts">
	import { page } from '$app/state';
	import type { Crumb } from '../../types';
	import Breadcrumbs from '$lib/Breadcrumbs.svelte';
	import CompanyTypesTabs from '$lib/utils/CompanyTypesTabs.svelte';
	import type { MyCrumbMetadata } from '../../types';

	let { data, children } = $props();

	let pageDataCrumbs = $derived(page.data.crumbs as Crumb<MyCrumbMetadata>[] | undefined);
</script>

<div class="text-surface-900-100 text-sm p-2 md:p-4">
	<Breadcrumbs url={page.url} routeId={page.route.id} pageData={page.data} crumbs={pageDataCrumbs}>
		{#snippet children({ crumbs })}
			<div>
				<span><a href="/" class="text-surface-900-100 hover:text-primary-900-100">Home</a></span>
				{#each crumbs as c}
					<span>/</span>
					<span>
						{#if c.title != 'Types' && c.title != 'Categories' && c.title != 'Publisher' && c.title != 'App-adstxt'}
							<a href={c.url} class="text-surface-900-100 hover:text-primary-900-100">
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

{#if !page.url.pathname.includes('adstxt') && data.companyTypes && data.companyTypes.types.length > 0}
	<CompanyTypesTabs companyTypes={data.companyTypes} />
{/if}
<div class="card-content p-1 md:p-6 shadow-md rounded-lg">
	{@render children?.()}
</div>
