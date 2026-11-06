<script lang="ts">
	import { resolve } from '$app/paths';

	import WhiteCard from '#lib/WhiteCard.svelte';
	import CompanyButton from '#lib/CompanyButton.svelte';
	import RequestMappingButton from '#lib/RequestMappingButton.svelte';
	import AppDataFlowsNav from '#lib/AppDataFlowsNav.svelte';

	import { countryCodeToEmoji } from '#lib/utils/countryCodeToEmoji.js';
	import type {
		AppAPICall,
		AppAPICategoryOverview,
		AppAPIsOverview,
		AppAPIScanOverview
	} from '../../../../../types';

	type Props = {
		data: {
			apis: AppAPIsOverview;
			myapp: { name: string; store_id: string };
		};
	};

	let { data }: Props = $props();

	const cardClass = 'p-4 bg-surface-100-900 rounded-md';

	const apis = $derived<AppAPICall[]>(data.apis?.apis ?? []);
	const scans = $derived<AppAPIScanOverview[]>(data.apis?.scans ?? []);
	const categories = $derived<AppAPICategoryOverview[]>(data.apis?.categories ?? []);
	const creatives = $derived(data.apis?.creatives ?? []);
	const scanDiff = $derived(data.apis?.scan_diff ?? null);

	const storeId = $derived(data.myapp.store_id);

	const stats = $derived.by(() => {
		const domains = apis.map((api) => api.tld_url).filter((value) => !!value);
		const companies = apis
			.map((api) => api.company_domain)
			.filter((value): value is string => !!value);
		const countries = apis.map((api) => api.country).filter((value): value is string => !!value);
		return {
			callCount: apis.length,
			domainCount: new Set(domains).size,
			companyCount: new Set(companies).size,
			scanCount: scans.length,
			creativeCount: creatives.length,
			countries: [...new Set(countries)].sort()
		};
	});

	const unmappedDomains = $derived.by(() => {
		const counts: Record<string, number> = {};
		for (const api of apis) {
			if (api.company_domain || !api.tld_url) continue;
			counts[api.tld_url] = (counts[api.tld_url] ?? 0) + 1;
		}
		return Object.entries(counts)
			.map(([domain, callCount]) => ({ domain, callCount }))
			.sort((a, b) => b.callCount - a.callCount);
	});

	const recentScans = $derived(scans.slice(0, 5));
	const topCategories = $derived(categories.slice(0, 6));
	const recentCreatives = $derived(creatives.slice(0, 8));

	const topCompanies = $derived.by(() => {
		const companies: AppAPICategoryOverview['companies'] = [];
		for (const category of categories) {
			for (const company of category.companies) {
				if (companies.some((c) => c.company_domain === company.company_domain)) continue;
				companies.push(company);
				if (companies.length >= 40) return companies;
			}
		}
		return companies;
	});

	function formatDate(value: string | null) {
		if (!value) return 'Unknown date';
		return new Date(value).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	function scanLabel(scan: AppAPIScanOverview) {
		const version = scan.version_code ? `v${scan.version_code}` : 'Unknown version';
		return `${formatDate(scan.run_at)} · ${version}`;
	}

	function creativeThumb(hash: string) {
		return `https://media.appgoblin.info/creatives/thumbs/${hash}.jpg`;
	}
</script>

<div class="p-2 md:p-8 mt-2 md:mt-4">
	<section class="space-y-6">
		<div>
			<h2 class="h4 md:h3 p-2">Data calls made by {data.myapp.name}</h2>
			<p class="p-2">
				Overview of network connections made by <strong>{data.myapp.name}</strong> during the first 60
				seconds after installation.
			</p>
		</div>

		<AppDataFlowsNav {storeId} callCount={stats.callCount} hasDiff={!!scanDiff} />

		{#if apis.length === 0}
			<p class="p-2">API calls data not yet available for this app.</p>
		{:else}
			<section class={cardClass}>
				<p class="text-base leading-relaxed">
					<strong>{data.myapp.name}</strong> contacted
					<strong>{stats.domainCount} different domains</strong>
					within the first minute of opening. This data was collected from
					<strong>{stats.scanCount} independent scan{stats.scanCount !== 1 ? 's' : ''}</strong>,
					covering <strong>{stats.callCount} API calls</strong>.
					{#if stats.creativeCount > 0}
						We captured
						<strong>{stats.creativeCount} ad creative{stats.creativeCount !== 1 ? 's' : ''}</strong>
						loaded during those scans.
					{:else}
						No ad creatives were captured in the first 60 seconds of these scans — ads typically
						load after playback begins.
					{/if}
					{#if stats.countries.length > 0}
						Traffic reached servers in {stats.countries
							.map((c) => countryCodeToEmoji(c))
							.join(' ')}.
					{/if}
					This provides transparency into the app's actual network behavior and data sharing practices.
				</p>
			</section>

			<section class="grid grid-cols-2 md:grid-cols-4 gap-4 my-6">
				<div class={cardClass}>
					<p class="text-sm">Scan Runs</p>
					<p class="text-2xl font-bold">{stats.scanCount}</p>
				</div>
				<div class={cardClass}>
					<p class="text-sm">Unique Domains</p>
					<p class="text-2xl font-bold">{stats.domainCount}</p>
				</div>
				<div class={cardClass}>
					<p class="text-sm">Mapped Companies</p>
					<p class="text-2xl font-bold">{stats.companyCount}</p>
				</div>
				<div class={cardClass}>
					<p class="text-sm">Ad Creatives Found</p>
					<p class="text-2xl font-bold">{stats.creativeCount}</p>
				</div>
			</section>

			{#if scanDiff}
				<WhiteCard>
					{#snippet title()}
						Latest changes
					{/snippet}
					<div class="p-2 md:p-4 space-y-3">
						<p class="text-sm">
							Comparing the scan from <strong>{formatDate(scanDiff.previous_run_at)}</strong> with
							<strong>{formatDate(scanDiff.latest_run_at)}</strong>.
						</p>
						<div class="grid grid-cols-3 gap-2 max-w-md">
							<div class="p-2 bg-success-50-950 rounded-md">
								<p class="text-xs">New</p>
								<p class="text-xl font-bold">{scanDiff.new_count}</p>
							</div>
							<div class="p-2 bg-error-50-950 rounded-md">
								<p class="text-xs">No longer observed</p>
								<p class="text-xl font-bold">{scanDiff.removed_count}</p>
							</div>
							<div class="p-2 bg-surface-100-900 rounded-md">
								<p class="text-xs">Unchanged</p>
								<p class="text-xl font-bold">{scanDiff.unchanged_count}</p>
							</div>
						</div>
						<a
							href={resolve('/apps/[id]/(sub)/data-flows/changes', { id: storeId })}
							class="btn preset-tonal-primary text-sm"
						>
							View full scan diff
						</a>
					</div>
				</WhiteCard>
			{/if}

			<div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
				<WhiteCard>
					{#snippet title()}
						Scans
					{/snippet}
					<div class="p-2 md:p-4 space-y-2">
						{#each recentScans as scan (scan.run_id ?? scan.run_at)}
							<a
								href={resolve(`/apps/[id]/(sub)/data-flows/details?run=${String(scan.run_id)}`, {
									id: storeId
								})}
								class="flex items-center justify-between gap-3 p-2 rounded-md hover:bg-surface-100-900"
							>
								<span class="text-sm">{scanLabel(scan)}</span>
								<span class="text-xs text-surface-600-400 whitespace-nowrap">
									{scan.call_count} calls · {scan.domain_count} domains
								</span>
							</a>
						{/each}
						{#if scans.length > recentScans.length}
							<a
								href={resolve('/apps/[id]/(sub)/data-flows/details', { id: storeId })}
								class="block p-2 text-sm underline"
							>
								View all {scans.length} scans
							</a>
						{/if}
					</div>
				</WhiteCard>

				<WhiteCard>
					{#snippet title()}
						Company categories
					{/snippet}
					<div class="p-2 md:p-4 space-y-2">
						{#each topCategories as category (category.category_slug)}
							<a
								href={resolve(
									`/apps/[id]/(sub)/data-flows/details?category=${encodeURIComponent(
										category.category_slug
									)}`,
									{ id: storeId }
								)}
								class="flex items-center justify-between gap-3 p-2 rounded-md hover:bg-surface-100-900"
							>
								<span class="text-sm">{category.category_name}</span>
								<span class="text-xs text-surface-600-400 whitespace-nowrap">
									{category.company_count} compan{category.company_count === 1 ? 'y' : 'ies'} ·
									{category.call_count} calls
								</span>
							</a>
						{/each}
						{#if categories.length > topCategories.length}
							<a
								href={resolve('/apps/[id]/(sub)/data-flows/details', { id: storeId })}
								class="block p-2 text-sm underline"
							>
								View all {categories.length} categories
							</a>
						{/if}
					</div>
				</WhiteCard>
			</div>

			{#if recentCreatives.length > 0}
				<WhiteCard>
					{#snippet title()}
						Ad creatives found
					{/snippet}
					<div class="p-2 md:p-4 space-y-3">
						<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
							{#each recentCreatives as creative (creative.creative_md5_hash)}
								<a
									href={resolve(
										`/apps/[id]/(sub)/data-flows/details?creative=${creative.creative_md5_hash}`,
										{ id: storeId }
									)}
									class="flex flex-col gap-1"
								>
									<img
										src={creativeThumb(creative.creative_md5_hash)}
										alt="Ad creative {creative.creative_md5_hash}"
										class="w-full h-auto object-contain rounded-lg shadow-md"
										loading="lazy"
									/>
									<span class="text-xs text-surface-600-400">
										{creative.file_extension ?? 'image'} · seen in {creative.scan_count} scan{creative.scan_count !==
										1
											? 's'
											: ''}
									</span>
								</a>
							{/each}
						</div>
						<a
							href={resolve('/apps/[id]/(sub)/data-flows/details?creative=1', { id: storeId })}
							class="block text-sm underline"
						>
							View all {creatives.length} creatives
						</a>
					</div>
				</WhiteCard>
			{/if}

			{#if unmappedDomains.length > 0}
				<WhiteCard>
					{#snippet title()}
						Unmapped domains ({unmappedDomains.length})
					{/snippet}
					<div class="p-2 md:p-4 space-y-3">
						<p class="text-sm">
							These domains were contacted but are not yet linked to a company in the AppGoblin
							database. Request a mapping if you know who operates them.
						</p>
						<ul class="space-y-2">
							{#each unmappedDomains.slice(0, 12) as item (item.domain)}
								<li class="flex flex-wrap items-center justify-between gap-2">
									<span class="text-sm break-all">
										{item.domain}
										<span class="text-surface-600-400">({item.callCount} calls)</span>
									</span>
									<RequestMappingButton
										mapType="company_domain_name"
										valueToBeMapped={item.domain}
										label="Request Mapping"
									/>
								</li>
							{/each}
						</ul>
						{#if unmappedDomains.length > 12}
							<p class="text-sm text-surface-600-400">
								... and {unmappedDomains.length - 12} more. See the
								<a
									href={resolve('/apps/[id]/(sub)/data-flows/details?category=unmapped', {
										id: storeId
									})}
									class="underline">full list</a
								>.
							</p>
						{/if}
					</div>
				</WhiteCard>
			{/if}

			<WhiteCard>
				{#snippet title()}
					Top contacted domains
				{/snippet}
				<div class="p-2 md:p-4 flex flex-wrap gap-2">
					{#each topCompanies as company (company.company_domain)}
						<CompanyButton
							companyName={company.company_name ?? company.company_domain}
							companyDomain={company.company_domain}
							companyLogoUrl={company.company_logo_url ?? undefined}
						/>
					{/each}
				</div>
			</WhiteCard>
		{/if}
	</section>
</div>
