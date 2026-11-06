<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';

	import WhiteCard from '#lib/WhiteCard.svelte';
	import AppAPICallsTable from '#lib/AppAPICallsTable.svelte';
	import AppDataFlowsNav from '#lib/AppDataFlowsNav.svelte';
	import CompanyButton from '#lib/CompanyButton.svelte';
	import RequestMappingButton from '#lib/RequestMappingButton.svelte';

	import type {
		AppAPICall,
		AppAPICategoryOverview,
		AppAPIsOverview,
		AppAPIScanOverview
	} from '../../../../../../types';

	type Props = {
		data: {
			apis: AppAPIsOverview;
			myapp: { name: string; store_id: string };
		};
	};

	let { data }: Props = $props();

	const apis = $derived<AppAPICall[]>(data.apis?.apis ?? []);
	const scans = $derived<AppAPIScanOverview[]>(data.apis?.scans ?? []);
	const categories = $derived<AppAPICategoryOverview[]>(data.apis?.categories ?? []);
	const creatives = $derived(data.apis?.creatives ?? []);
	const scanDiff = $derived(data.apis?.scan_diff ?? null);

	const runParam = $derived(page.url.searchParams.get('run'));
	const categoryParam = $derived(page.url.searchParams.get('category'));
	const creativeParam = $derived(page.url.searchParams.get('creative'));

	const activeScan = $derived(
		runParam ? (scans.find((scan) => String(scan.run_id) === runParam) ?? null) : null
	);
	const activeCategory = $derived(
		categoryParam ? (categories.find((c) => c.category_slug === categoryParam) ?? null) : null
	);
	const activeCreative = $derived(
		creativeParam && creativeParam !== '1'
			? (creatives.find((c) => c.creative_md5_hash === creativeParam) ?? null)
			: null
	);
	const creativesOnly = $derived(creativeParam === '1');

	const filteredApis = $derived.by(() => {
		let rows = apis;

		if (runParam) {
			rows = rows.filter((row) => String(row.run_id) === runParam);
		}

		if (activeCategory) {
			const domains = new Set(activeCategory.companies.map((company) => company.company_domain));
			rows = rows.filter((row) =>
				activeCategory.category_slug === 'unmapped'
					? !row.company_domain && domains.has(row.tld_url)
					: row.company_domain !== null && domains.has(row.company_domain)
			);
		}

		if (activeCreative) {
			rows = rows.filter((row) => row.creative_md5_hash === activeCreative.creative_md5_hash);
		} else if (creativesOnly) {
			rows = rows.filter((row) => !!row.creative_md5_hash);
		}

		return rows;
	});

	const initialFilter = $derived(activeCreative ? activeCreative.creative_md5_hash : '');

	const activeFilterLabel = $derived.by(() => {
		if (activeScan) {
			const version = activeScan.version_code ? `v${activeScan.version_code}` : 'unknown version';
			return `Scan from ${formatDate(activeScan.run_at)} (${version})`;
		}
		if (activeCategory) return `Category: ${activeCategory.category_name}`;
		if (activeCreative) return `Creative ${activeCreative.creative_md5_hash}`;
		if (creativesOnly) return 'Calls that captured an ad creative';
		return 'All API calls';
	});

	function formatDate(value: string | null) {
		if (!value) return 'Unknown date';
		return new Date(value).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	function setFilter(key: 'run' | 'category' | 'creative', value: string | null) {
		const id = data.myapp.store_id;
		const target = value
			? resolve(`/apps/[id]/(sub)/data-flows/details?${key}=${encodeURIComponent(value)}`, { id })
			: resolve('/apps/[id]/(sub)/data-flows/details', { id });
		void goto(target, { reset: false, replace: true });
	}
</script>

<div class="p-2 md:p-8 mt-2 md:mt-4">
	<section class="space-y-6">
		<div>
			<h2 class="h4 md:h3 p-2">API calls made by {data.myapp.name}</h2>
			<p class="p-2">
				Every captured network request, filterable by scan run, company category, or ad creative.
			</p>
		</div>

		<AppDataFlowsNav storeId={data.myapp.store_id} callCount={apis.length} hasDiff={!!scanDiff} />

		{#if apis.length === 0}
			<p class="p-2">API calls data not yet available for this app.</p>
		{:else}
			<div class="grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-6">
				<aside class="space-y-4">
					<WhiteCard>
						{#snippet title()}
							Scans
						{/snippet}
						<ul class="p-2 space-y-1 max-h-72 overflow-y-auto">
							<li>
								<button
									type="button"
									class="w-full text-left p-2 text-sm rounded-md {!runParam
										? 'bg-secondary-100-900 font-semibold'
										: 'hover:bg-surface-100-900'}"
									onclick={() => setFilter('run', null)}
								>
									All scans ({scans.length})
								</button>
							</li>
							{#each scans as scan (scan.run_id ?? scan.run_at)}
								<li>
									<button
										type="button"
										class="w-full text-left p-2 text-sm rounded-md {runParam === String(scan.run_id)
											? 'bg-secondary-100-900 font-semibold'
											: 'hover:bg-surface-100-900'}"
										onclick={() => setFilter('run', String(scan.run_id ?? ''))}
									>
										<span class="block">{formatDate(scan.run_at)}</span>
										<span class="block text-xs text-surface-600-400">
											{scan.version_code ? `v${scan.version_code} · ` : ''}{scan.call_count} calls
										</span>
									</button>
								</li>
							{/each}
						</ul>
					</WhiteCard>

					<WhiteCard>
						{#snippet title()}
							Categories
						{/snippet}
						<ul class="p-2 space-y-1 max-h-72 overflow-y-auto">
							<li>
								<button
									type="button"
									class="w-full text-left p-2 text-sm rounded-md {!categoryParam
										? 'bg-secondary-100-900 font-semibold'
										: 'hover:bg-surface-100-900'}"
									onclick={() => setFilter('category', null)}
								>
									All categories
								</button>
							</li>
							{#each categories as category (category.category_slug)}
								<li>
									<button
										type="button"
										class="w-full text-left p-2 text-sm rounded-md {categoryParam ===
										category.category_slug
											? 'bg-secondary-100-900 font-semibold'
											: 'hover:bg-surface-100-900'}"
										onclick={() => setFilter('category', category.category_slug)}
									>
										<span class="block">{category.category_name}</span>
										<span class="block text-xs text-surface-600-400">
											{category.company_count} compan{category.company_count === 1 ? 'y' : 'ies'} ·
											{category.call_count} calls
										</span>
									</button>
								</li>
							{/each}
						</ul>
					</WhiteCard>

					{#if creatives.length > 0}
						<WhiteCard>
							{#snippet title()}
								Ad creatives
							{/snippet}
							<div class="p-2 space-y-2">
								<button
									type="button"
									class="w-full text-left p-2 text-sm rounded-md {creativesOnly
										? 'bg-secondary-100-900 font-semibold'
										: 'hover:bg-surface-100-900'}"
									onclick={() => setFilter('creative', '1')}
								>
									Only calls with creatives ({creatives.length})
								</button>
								<div class="grid grid-cols-3 gap-2">
									{#each creatives.slice(0, 12) as creative (creative.creative_md5_hash)}
										<button
											type="button"
											class="rounded-md overflow-hidden border-2 {activeCreative?.creative_md5_hash ===
											creative.creative_md5_hash
												? 'border-primary-500'
												: 'border-transparent'}"
											onclick={() => setFilter('creative', creative.creative_md5_hash)}
											title={creative.creative_md5_hash}
										>
											<img
												src={`https://media.appgoblin.info/creatives/thumbs/${creative.creative_md5_hash}.jpg`}
												alt="Ad creative {creative.creative_md5_hash}"
												class="w-full h-auto object-contain"
												loading="lazy"
											/>
										</button>
									{/each}
								</div>
							</div>
						</WhiteCard>
					{/if}
				</aside>

				<div class="min-w-0 space-y-4">
					<div class="flex flex-wrap items-center justify-between gap-2">
						<div>
							<p class="text-sm font-semibold">{activeFilterLabel}</p>
							<p class="text-xs text-surface-600-400">
								{filteredApis.length} of {apis.length} calls
							</p>
						</div>
						{#if runParam || categoryParam || creativeParam}
							<button
								type="button"
								class="btn preset-tonal-surface text-sm"
								onclick={() => setFilter('run', null)}
							>
								Clear filters
							</button>
						{/if}
					</div>

					{#if activeCategory && activeCategory.companies.length > 0}
						<WhiteCard>
							{#snippet title()}
								{activeCategory.category_name} companies
							{/snippet}
							<div class="p-2 md:p-4 flex flex-wrap gap-2">
								{#each activeCategory.companies as company (company.company_domain)}
									{#if activeCategory.category_slug === 'unmapped'}
										<div class="flex items-center gap-2">
											<span class="text-sm">{company.company_domain}</span>
											<RequestMappingButton
												mapType="company_domain_name"
												valueToBeMapped={company.company_domain}
												label="Request Mapping"
											/>
										</div>
									{:else}
										<CompanyButton
											companyName={company.company_name ?? company.company_domain}
											companyDomain={company.company_domain}
											companyLogoUrl={company.company_logo_url ?? undefined}
										/>
									{/if}
								{/each}
							</div>
						</WhiteCard>
					{/if}

					<WhiteCard>
						{#snippet title()}
							API calls
						{/snippet}
						<AppAPICallsTable data={filteredApis} {initialFilter} />
					</WhiteCard>
				</div>
			</div>
		{/if}
	</section>
</div>
