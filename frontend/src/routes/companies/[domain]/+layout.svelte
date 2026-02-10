<script lang="ts">
	import { page } from '$app/state';

	import ExternalLink from '$lib/ExternalLink.svelte';
	import CompanyButton from '$lib/CompanyButton.svelte';

	let { children, data } = $props();
	const { domain, category } = page.params;

	let category_title: string = $state(category || '');

	let categoryName = $derived(getAppCategory(page.params.category || ''));

	function getAppCategory(category: string) {
		if (category) {
			return category
				.split('_')
				.map((c) => c.charAt(0).toUpperCase() + c.slice(1))
				.join(' ');
		} else {
			return 'All ';
		}
	}

	function getPageTitle(myTree: any, categoryName: string) {
		if (myTree.parent_company_domain == myTree.queried_company_domain) {
			return `${myTree.parent_company_name || myTree.parent_company_domain}: ${categoryName} Clients, Apps and Competitors`;
		} else {
			return `${myTree.queried_company_name} ${categoryName} Apps, Clients, and Competitors`;
		}
	}
	let pageTitle = $derived(getPageTitle(data.companyTree, categoryName));
	let titleClass = 'h1 text-2xl md:text-3xl font-bold text-primary-900-100';
	let titleSecondaryClass = 'text-xl font-bold text-primary-900-100 mr-2';
	let titleDividerClass = 'md:h-8 w-px bg-gray-300 mx-2';
</script>

<svelte:head>
	<title>{pageTitle}</title>
	<meta
		name="description"
		content="{data.companyTree.queried_company_name ||
			domain} {category_title} sdks, apps and trends. See {domain}'s role in the mobile ecosystem by analyzing API, SDK and trackers."
	/>
	<meta
		name="keywords"
		content="{domain}, {category_title}, adtech, advertising network, data tracking, mobile measurement, programmatic advertising, app-ads.txt, mobile advertising, ad tech analytics, AppGoblin"
	/>
	<meta property="og:title" content={pageTitle} />
	<meta
		property="og:description"
		content="Discover {domain}'s impact in the {category_title} adtech industry. Analyze data on their apps, market presence, and role in mobile advertising. Powered by AppGoblin's comprehensive adtech research."
	/>
	<meta name="twitter:title" content={pageTitle} />
	<meta name="twitter:description" content={pageTitle} />

	<meta property="og:image" content="https://appgoblin.info/goblin_purple_hat_250.png" />
	<meta property="og:url" content={page.url.href} />
	<meta property="og:type" content="website" />
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:image" content="https://appgoblin.info/goblin_purple_hat_250.png" />
	<link rel="canonical" href={page.url.href} />
	<meta name="robots" content="index, follow" />
</svelte:head>

<div class="flex items-center mb-2">
	{#await data.companyTree}
		<span class="text-lg">Loading...</span>
	{:then myTree}
		{#if typeof myTree == 'string'}
			<h1 class={titleClass}>{domain}</h1>
			<p class="text-red-500">Failed to load company tree.</p>
		{:else if myTree}
			<div class="flex flex-col md:flex-row items-left md:items-center">
				{#if page.url.pathname.includes('adstxt/publisher')}
					<h1 class={titleClass}>
						<a href={`/companies/${myTree.parent_company_domain}`}
							>{myTree.parent_company_name || myTree.parent_company_domain}</a
						>
					</h1>
				{:else if myTree.queried_company_domain}
					{#if myTree.queried_company_logo_url}
						<img
							src="https://media.appgoblin.info/{myTree.queried_company_logo_url}"
							alt={myTree.queried_company_logo_url}
							class="w-20 h-20 rounded-sm mr-2 md:mr-8"
						/>
					{:else if myTree.parent_company_logo_url}
						<img
							src="https://media.appgoblin.info/{myTree.parent_company_logo_url}"
							alt={myTree.parent_company_logo_url}
							class="w-20 h-20 rounded-sm mr-2 md:mr-8"
						/>
					{:else}
						<img
							src="/default_company_logo.png"
							alt="Default Company Logo"
							class="w-20 h-20 rounded-sm mr-2 md:mr-8"
						/>
					{/if}

					{#if myTree.is_parent_company}
						<!-- IS PARENT COMPANY -->
						<h1 class={titleClass}>
							{myTree.queried_company_name || myTree.parent_company_domain} / Category: {categoryName}
						</h1>
						<div class={titleDividerClass}></div>
						<ExternalLink domain={myTree.queried_company_domain} />
					{:else if myTree.is_secondary_domain}
						<!-- IS SUB DOMAIN ONLY -->
						<h1 class={titleClass}>{myTree.queried_company_domain} / {categoryName}</h1>
						<div class={titleDividerClass}></div>
						<ExternalLink domain={myTree.queried_company_domain} />
						<!-- HAS PARENT COMPANY -->
						{#if myTree.parent_company_name}
							<div class={titleDividerClass}></div>
							<span class="flex row">
								<h2 class={titleSecondaryClass}>Parent Company:</h2>
								<CompanyButton
									companyName={myTree.parent_company_name}
									companyDomain={myTree.parent_company_domain}
									companyLogoUrl={myTree.parent_company_logo_url}
								/>
							</span>
						{/if}
					{:else}
						<!-- REGULAR COMPANY  -->
						<h1 class={titleClass}>{myTree.queried_company_name} / {categoryName}</h1>
						<div class={titleDividerClass}></div>
						<ExternalLink domain={myTree.queried_company_domain} />
						{#if myTree.parent_company_name}
							<div class={titleDividerClass}></div>
							<!-- HAS PARENT COMPANY -->
							<span class="flex row">
								<h2 class={titleSecondaryClass}>Parent Company:</h2>
								<CompanyButton
									companyName={myTree.parent_company_name}
									companyDomain={myTree.parent_company_domain}
									companyLogoUrl={myTree.parent_company_logo_url}
								/>
							</span>
						{/if}
					{/if}
				{/if}
			</div>
		{/if}
	{:catch error}
		<p class="text-red-500">{error.message}</p>
	{/await}
</div>

<div class="flex flex-wrap gap-2 mb-4 border-b border-surface-200-800 pb-2">
	<a
		href={`/companies/${data.companyTree.queried_company_domain}`}
		class="btn btn-sm {page.url.pathname === `/companies/${data.companyTree.queried_company_domain}`
			? 'variant-filled-primary'
			: 'variant-ghost-surface'}"
	>
		Overview
	</a>
	<a
		href={`/companies/${data.companyTree.queried_company_domain}/mediation`}
		class="btn btn-sm {page.url.pathname.includes('/mediation')
			? 'variant-filled-primary'
			: 'variant-ghost-surface'}"
	>
		Mediation
	</a>
	<a
		href={`/companies/${data.companyTree.queried_company_domain}/creatives`}
		class="btn btn-sm {page.url.pathname.includes('/creatives')
			? 'variant-filled-primary'
			: 'variant-ghost-surface'}"
	>
		Creatives
	</a>
	<a
		href={`/companies/${data.companyTree.queried_company_domain}/sdks`}
		class="btn btn-sm {page.url.pathname.includes('/sdks')
			? 'variant-filled-primary'
			: 'variant-ghost-surface'}"
	>
		SDKs
	</a>
	<a
		href={`/companies/${data.companyTree.queried_company_domain}/app-adstxt`}
		class="btn btn-sm {page.url.pathname.includes('/app-adstxt')
			? 'variant-filled-primary'
			: 'variant-ghost-surface'}"
	>
		App-ads.txt
	</a>
	<a
		href={`/companies/${data.companyTree.queried_company_domain}/data-exports`}
		class="btn btn-sm {page.url.pathname.includes('/data-exports')
			? 'variant-filled-primary'
			: 'variant-ghost-surface'}"
	>
		Data Exports
	</a>
</div>

<div class="space-y-4 md:space-y-8">
	{@render children?.()}
</div>
