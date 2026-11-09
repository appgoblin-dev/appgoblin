<script lang="ts">
	import { resolve } from '$app/paths';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	type Summary = {
		total: number;
		api: number;
		sdk: number;
		app_ads: number;
		publishers: number;
		listed: number;
		countries: { country: string; company_count: number }[];
		listed_companies: {
			company_domain: string;
			company_name: string | null;
			tickers_direct: string[] | null;
			company_tickers: string[] | null;
		}[];
	};

	let summary = $derived(data.summary as Summary | null);
	const descriptions: Record<string, string> = {
		'ad-networks': 'Help apps monetize by serving advertising.',
		mediation: 'Manage competition between ad networks for app inventory.',
		'ad-attribution': 'Measure installs and connect them to marketing campaigns.',
		'product-analytics': 'Help developers understand app usage and performance.',
		'development-tools': 'Provide libraries and tools for building and running apps.',
		'business-tools': 'Provide services such as cloud, CRM and revenue management.',
		'app-publishers': 'Develop and publish apps across the app stores.'
	};
	const number = (value: number) => value.toLocaleString('en-US');
	const title = 'Mobile App Companies & Ad Networks | AppGoblin';
	const description =
		'Explore companies powering mobile apps through SDKs, API calls and app-ads.txt, from ad networks to app publishers.';
</script>

<svelte:head>
	<title>{title}</title>
	<meta name="description" content={description} />
	<meta property="og:title" content={title} />
	<meta property="og:description" content={description} />
	<meta property="og:url" content="https://appgoblin.info/companies" />
	<meta
		property="og:image"
		content="https://appgoblin.info/previews/appgoblin_companies_smaller.png"
	/>
	<meta name="twitter:card" content="summary_large_image" />
	<link rel="canonical" href="https://appgoblin.info/companies" />
	<meta name="robots" content="index, follow" />
</svelte:head>

<div class="mx-auto max-w-7xl space-y-10 pb-12">
	<section
		class="rounded-2xl border border-secondary-900-100/20 bg-secondary-100-900/30 p-6 md:p-10"
	>
		<p class="text-sm font-semibold uppercase tracking-wider text-secondary-700-300">
			Company intelligence
		</p>
		<h1 class="mt-2 text-3xl font-bold md:text-4xl">Explore the companies behind mobile apps</h1>
		<p class="mt-4 max-w-3xl text-base leading-relaxed md:text-lg">
			Discover ad networks, app publishers, analytics providers and more. AppGoblin connects
			companies and domains to apps through observed API calls, mapped SDKs and app-ads.txt records.
		</p>
		<a
			class="btn preset-filled-primary-500 mt-6 inline-flex"
			href={resolve('/companies/(overview)/(tables)/browse-data')}
			>Browse the company data table →</a
		>
	</section>

	<section aria-labelledby="signals-heading">
		<h2 id="signals-heading" class="text-2xl font-bold">The mobile ecosystem at a glance</h2>
		<p class="mt-2 text-sm text-surface-600-400">
			Counts are company domains in AppGoblin's directory. Signals can overlap, and parent and
			related domains may be counted separately.
		</p>
		{#if summary}
			<div class="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
				{#each [{ label: 'With API calls', count: summary.api, detail: 'Observed app network requests' }, { label: 'With mapped SDKs', count: summary.sdk, detail: 'Companies with mapped SDKs' }, { label: 'In app-ads.txt', count: summary.app_ads, detail: 'Direct or reseller records' }, { label: 'App publishers', count: summary.publishers, detail: 'Companies linked to published apps' }] as metric (metric.label)}
					<div class="rounded-xl border border-surface-300-700 p-4 md:p-5">
						<p class="text-2xl font-bold md:text-3xl">{number(metric.count)}</p>
						<h3 class="mt-1 font-semibold">{metric.label}</h3>
						<p class="mt-1 text-sm text-surface-600-400">{metric.detail}</p>
					</div>
				{/each}
			</div>
			<p class="mt-3 text-sm text-surface-600-400">
				{number(summary.total)} company domains in total.
				<a class="anchor" href={resolve('/companies/(overview)/(tables)/browse-data')}
					>Compare companies in the table</a
				>.
			</p>
		{:else}
			<p class="mt-4 text-surface-600-400">
				Summary counts are temporarily unavailable. You can still browse the company data below.
			</p>
		{/if}
	</section>

	<section aria-labelledby="types-heading">
		<h2 id="types-heading" class="text-2xl font-bold">Explore by company type</h2>
		<p class="mt-2 text-surface-600-400">
			Company types describe the role a company plays in the app ecosystem.
		</p>
		<div class="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
			{#each data.companyTypes?.types ?? [] as type (type.url_slug)}
				<a
					class="rounded-xl border border-surface-300-700 p-5 transition-colors hover:bg-surface-100-900"
					href={resolve('/companies/(overview)/(tables)/types/[type]', { type: type.url_slug })}
				>
					<h3 class="font-semibold text-secondary-700-300">{type.name} →</h3>
					<p class="mt-2 text-sm text-surface-600-400">
						{descriptions[type.url_slug] ??
							'Explore companies in this part of the mobile app ecosystem.'}
					</p>
				</a>
			{/each}
		</div>
	</section>

	<section aria-labelledby="categories-heading">
		<h2 id="categories-heading" class="text-2xl font-bold">Explore by app category</h2>
		<p class="mt-2 text-surface-600-400">
			App categories describe the apps where these companies are found, not the companies
			themselves. Compare providers across games, news, books and more.
		</p>
		<div class="mt-4 flex flex-wrap gap-2">
			{#each data.appCats?.categories ?? [] as category (category.id)}
				{#if category.id !== 'overall' && (category.android || category.id === 'games')}
					<a
						class="rounded-full border border-surface-300-700 px-4 py-2 text-sm hover:bg-surface-100-900"
						href={resolve('/companies/(overview)/(tables)/categories/[category]', {
							category: category.id
						})}>{category.name} →</a
					>
				{/if}
			{/each}
		</div>
	</section>

	{#if summary}
		<div class="grid gap-8 lg:grid-cols-2">
			<section
				aria-labelledby="countries-heading"
				class="rounded-xl border border-surface-300-700 p-5"
			>
				<h2 id="countries-heading" class="text-2xl font-bold">Companies by country</h2>
				<p class="mt-2 text-sm text-surface-600-400">
					Top known headquarters countries, by company domain. Domains without a country are
					excluded.
				</p>
				{#if summary.countries.length}
					<ul class="mt-4 divide-y divide-surface-300-700">
						{#each summary.countries as country (country.country)}
							<li class="flex justify-between gap-4 py-2">
								<span>{country.country}</span><span class="font-semibold"
									>{number(country.company_count)}</span
								>
							</li>
						{/each}
					</ul>
				{:else}<p class="mt-4 text-sm">No country data available.</p>{/if}
				<p class="mt-4 text-sm">
					<a class="anchor" href={resolve('/companies/(overview)/(tables)/browse-data')}
						>Explore country data in the table →</a
					>
				</p>
			</section>
			<section
				aria-labelledby="listed-heading"
				class="rounded-xl border border-surface-300-700 p-5"
			>
				<h2 id="listed-heading" class="text-2xl font-bold">Publicly listed companies</h2>
				<p class="mt-2 text-sm text-surface-600-400">
					{number(summary.listed)} company domains have a direct or associated company ticker. Examples
					are listed alphabetically; associated tickers may belong to a parent company.
				</p>
				{#if summary.listed_companies.length}
					<ul class="mt-4 divide-y divide-surface-300-700">
						{#each summary.listed_companies as company (company.company_domain)}
							<li class="flex justify-between gap-4 py-2">
								<a
									class="anchor"
									href={resolve('/companies/[domain]/(categorical)', { domain: company.company_domain })}
									>{company.company_name || company.company_domain}</a
								><span class="text-right text-sm text-surface-600-400"
									>{[
										...new Set([
											...(company.tickers_direct ?? []),
											...(company.company_tickers ?? [])
										])
									].join(', ')}</span
								>
							</li>
						{/each}
					</ul>
				{:else}<p class="mt-4 text-sm">No ticker data available.</p>{/if}
				<p class="mt-4 text-sm">
					<a class="anchor" href={resolve('/companies/(overview)/(tables)/browse-data')}
						>Search tickers in the company table →</a
					>
				</p>
			</section>
		</div>
	{/if}
</div>
