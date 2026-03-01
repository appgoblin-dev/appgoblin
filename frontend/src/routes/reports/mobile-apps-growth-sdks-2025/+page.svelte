<script lang="ts">
	import CompanyButton from '$lib/CompanyButton.svelte';

	let { data } = $props();

	// State for filtering and sorting
	let selectedCategory = $state<string>('all');
	let searchQuery = $state<string>('');
	let sortColumn = $state<string>('changePercent');
	let sortDirection = $state<'asc' | 'desc'>('desc');
	let currentPage = $state<number>(1);
	const pageSize = 25;

	// Filtered data based on category and search
	let filteredData = $derived.by(() => {
		let result = data.allData;

		// Filter by category
		if (selectedCategory !== 'all') {
			result = result.filter((d) => d.category === selectedCategory);
		}

		// Filter by search query
		if (searchQuery.trim()) {
			const query = searchQuery.toLowerCase();
			result = result.filter(
				(d) =>
					d.companyName.toLowerCase().includes(query) || d.company.toLowerCase().includes(query)
			);
		}

		// Sort
		result = [...result].sort((a, b) => {
			let aVal = a[sortColumn as keyof typeof a];
			let bVal = b[sortColumn as keyof typeof b];

			if (typeof aVal === 'string') {
				aVal = aVal.toLowerCase();
				bVal = (bVal as string).toLowerCase();
			}

			if (aVal && bVal && aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
			if (aVal && bVal && aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
			return 0;
		});

		return result;
	});

	// Reset page when filters change
	$effect(() => {
		selectedCategory;
		searchQuery;
		currentPage = 1;
	});

	// Pagination
	let totalPages = $derived(Math.max(1, Math.ceil(filteredData.length / pageSize)));
	let paginatedData = $derived(
		filteredData.slice((currentPage - 1) * pageSize, currentPage * pageSize)
	);

	function handleSort(column: string) {
		if (sortColumn === column) {
			sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
		} else {
			sortColumn = column;
			sortDirection = 'desc';
		}
	}

	function formatPercent(num: number): string {
		const sign = num > 0 ? '+' : '';
		return sign + num.toFixed(2) + '%';
	}

	function getGrowthColor(growth: number): string {
		if (growth > 100) return 'text-tertiary-200';
		if (growth > 30) return 'text-tertiary-400';
		if (growth > 10) return 'text-green-400';
		if (growth > 0) return 'text-green-600';
		if (growth > -5) return 'text-orange-400';
		if (growth > -10) return 'text-red-400';
		return 'text-red-500';
	}

	function downloadCSV() {
		window.location.href = '/reports/mobile-apps-growth-sdks-2025/download';
	}

	const sectionTitleClass =
		'p-4 text-3xl font-bold bg-gradient-to-r from-primary-900-100 to-secondary-900-100 bg-clip-text text-transparent';
	const sectionContainerClass = 'mb-16 pt-8 border-t-2 border-surface-200-800';
	const sectionHeaderBaseClass = 'my-8 p-4 border-t-2 border-l-1';
	const sectionHeaderSubtitleClass = 'text-sm ml-4';

	const kpiCardBaseClass = 'card p-6 bg-gradient-to-br text-white shadow-lg';
	const kpiLabelClass = 'text-center text-xl font-semibold mb-2';
	const kpiValueClass = 'text-center text-4xl font-bold mb-1';

	const tableRowClass =
		'border-b border-surface-200 dark:border-surface-700 hover:bg-surface-100-900 transition-colors';
	const cardTableWrapperClass = 'card overflow-hidden';
	const tableWrapperClass = 'table-container overflow-x-auto';
	const tableHeaderText = 'text-lg font-bold text-primary-900-100';
	const tableHeaderLeftClass = `px-4 py-3 text-left ${tableHeaderText}`;
	const tableHeaderRightClass = `px-4 py-3 text-right ${tableHeaderText}`;
	const rankPillBaseClass =
		'inline-flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm';

	const tHeadGrowthClass = 'bg-gradient-to-r from-tertiary-600-400 to-tertiary-200-800 text-white';
	const tHeadShrinkClass = 'bg-gradient-to-r from-error-600-400 to-error-400-600 text-white';
</script>

<svelte:head>
	<title>{data.title}</title>
	<meta name="description" content={data.description} />
	<meta name="keywords" content={data.keywords} />

	{@html `<script type="application/ld+json">${JSON.stringify({
		'@context': 'https://schema.org',
		'@type': 'Report',
		name: data.title,
		headline: 'App SDK Growth Report 2025',
		description: data.description,
		url: 'https://appgoblin.info/reports/mobile-apps-growth-sdks-2025',
		datePublished: '2025-01-14',
		dateModified: new Date().toISOString().split('T')[0],
		publisher: {
			'@type': 'Organization',
			name: 'AppGoblin',
			logo: {
				'@type': 'ImageObject',
				url: 'https://appgoblin.info/AppGoblin_Large_Logo.png'
			}
		},
		author: {
			'@type': 'Organization',
			name: 'AppGoblin Intelligence'
		},
		keywords: data.keywords
	})}<\/script>`}
</svelte:head>

<div class="container mx-auto px-4 py-8 max-w-6xl">
	<!-- Header Section -->
	<div class="mb-12 text-center">
		<div
			class="inline-block px-4 py-2 bg-surface-100-900 text-white rounded-full text-sm font-semibold mb-4"
		>
			SDK Intelligence Report
		</div>
		<h1
			class="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-primary-900-100 to-secondary-900-100 bg-clip-text text-transparent"
		>
			App SDK Growth Report 2025
		</h1>
		<p class="text-xl max-w-3xl mx-auto text-surface-600 dark:text-surface-400">
			Comparing H1 vs H2 2025 SDK adoption trends across {data.summary.appsAnalyzed.toLocaleString()}
			mobile apps. See which mobile SaaS companies are growing and which are losing market share.
		</p>
	</div>

	<!-- Key Metrics Dashboard -->
	<div class="grid grid-cols-2 gap-2 md:gap-4 mb-12 mx-24">
		<div class={`${kpiCardBaseClass} bg-gradient-to-br from-primary-700-300 to-primary-200-800`}>
			<div class={kpiValueClass}>{data.summary.totalCompanies}</div>
			<div class={kpiLabelClass}>SDK Companies</div>
		</div>

		<div class={`${kpiCardBaseClass} bg-gradient-to-br from-tertiary-700-300 to-tertiary-200-800`}>
			<div class={kpiValueClass}>{data.summary.growingCompanies}</div>
			<div class={kpiLabelClass}>Growing</div>
		</div>

		<div class={`${kpiCardBaseClass} bg-gradient-to-br from-error-400-600 to-error-400-600`}>
			<div class={kpiValueClass}>{data.summary.shrinkingCompanies}</div>
			<div class={kpiLabelClass}>Shrinking</div>
		</div>

		<div class={`${kpiCardBaseClass} bg-gradient-to-br from-surface-600 to-surface-700`}>
			<div class={kpiValueClass}>{data.summary.flatCompanies}</div>
			<div class={kpiLabelClass}>Flat</div>
		</div>
	</div>

	<!-- Download Button -->
	<div class="flex justify-center mb-12">
		<button
			onclick={downloadCSV}
			class="inline-flex items-center gap-2 px-6 py-3 bg-white dark:bg-surface-800 border-2 border-white-200 rounded-lg hover:bg-white-50 dark:hover:bg-surface-700 transition-all shadow-md hover:shadow-lg"
		>
			<svg class="w-5 h-5 text-white-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
				/>
			</svg>
			<span class="font-semibold text-primary-800-200">Download AppGoblin SDK Report (CSV)</span>
		</button>
	</div>

	<div class="card preset-tonal p-4 mb-6">
		<h2 class="text-2xl font-bold text-primary-900-100 mb-4">Methodology</h2>
		<p class="text-base">
			The AppGoblin SDK Growth Report is based on a 50k app subset of AppGoblin's 200k apps that
			analyzed for SDKs in 2025. This smaller group of apps were selected for this report because
			they were analyzed in both H1 and H2 for an accurate comparison between the two periods. This
			is sample of the whole market and should be used as a guide rather than a definitive source.
			If you have questions please feel free to reach out to <a href="mailto:contact@appgoblin.info"
				>contact@appgoblin.info</a
			>.
		</p>
	</div>

	<!-- SECTION 1: TOP GROWTH COMPANIES -->
	<div class={sectionContainerClass}>
		<div
			class={`${sectionHeaderBaseClass} border-emerald-200 dark:border-emerald-800 pl-4 border-l-emerald-500`}
		>
			<h2 class={sectionTitleClass}>🚀 Top 10 Growing Mobile SDKs</h2>
			<p class={sectionHeaderSubtitleClass}>
				Mobile SDK providers with the highest growth in app integrations from H1 to H2 2025 based on
				AppGoblin free SDK analytics.
			</p>
			<h3 class="text-lg font-bold text-primary-900-100 mt-4">What Stands Out:</h3>
			<ul class="list-disc list-inside space-y-1 px-8">
				<li>
					Verve Holdings, which also owns <a href="/companies/pubnative.com">PubNative</a> and
					<a href="/companies/smaato.com">Smaato</a>, launched their own SDK for behaivor targeting.
					Verve
					<a
						href="https://verve.com/press/verve-group-atom-3-0-brings-id-less-on-device-behavioral-targeting-to-10000-apps/"
						target="_blank"
						rel="noopener noreferrer"
						>self reports this rolled out to 10k apps across their existing clients.</a
					> PubNative and Smaato SDKs are counted separately, hence Verve's impressive percentage growth.
				</li>
				<li>
					X3M has been growing for a couple years but 2025 looks to have been a breakout year for
					them.
				</li>
				<li>
					Flarelane's push notification SDK has a small base of apps but it's growing rapidly.
				</li>
			</ul>
			<p class={sectionHeaderSubtitleClass}>
				AppGoblin free SDK analytics is used to track the number of apps that use each SDK.
			</p>
		</div>

		<div class={cardTableWrapperClass}>
			<div class={tableWrapperClass}>
				<table class="w-full">
					<thead class={tHeadGrowthClass}>
						<tr>
							<th class={tableHeaderLeftClass}>Rank</th>
							<th class={tableHeaderLeftClass}>Company</th>
							<th class={tableHeaderLeftClass}>Category</th>
							<th class={tableHeaderRightClass}>H1 Apps</th>
							<th class={tableHeaderRightClass}>H2 Apps</th>
							<th class={tableHeaderRightClass}>Net Change</th>
							<th class={tableHeaderRightClass}>Growth</th>
						</tr>
					</thead>
					<tbody>
						{#each data.topGrowth as company, index}
							<tr class={tableRowClass}>
								<td class="px-4 py-4">
									<span
										class={`${rankPillBaseClass} ${
											index === 0
												? 'bg-gradient-to-br from-yellow-400 to-yellow-600 text-white'
												: index === 1
													? 'bg-gradient-to-br from-gray-300 to-gray-500 text-white'
													: index === 2
														? 'bg-gradient-to-br from-orange-400 to-orange-600 text-white'
														: 'bg-emerald-100 dark:bg-emerald-900 text-emerald-800 dark:text-emerald-300'
										}`}
									>
										{index + 1}
									</span>
								</td>
								<td class="px-4 py-4">
									<CompanyButton
										companyDomain={company.company}
										companyName={company.companyName}
										companyLogoUrl={company.logoUrl ?? undefined}
										size="md"
									/>
								</td>
								<td class="px-4 py-4 text-surface-600 dark:text-surface-400">
									{company.category}
								</td>
								<td class="px-4 py-4 text-right text-surface-600 dark:text-surface-400">
									{company.h1Apps.toLocaleString()}
								</td>
								<td class="px-4 py-4 text-right font-semibold">
									{company.h2Apps.toLocaleString()}
								</td>
								<td class="px-4 py-4 text-right text-emerald-800 font-semibold">
									+{company.net.toLocaleString()}
								</td>
								<td class="px-4 py-4 text-right">
									<span class={`text-lg font-bold ${getGrowthColor(company.changePercent)}`}>
										{formatPercent(company.changePercent)}
									</span>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	</div>

	<!-- SECTION 2: TOP SHRINKING COMPANIES -->
	<div class={sectionContainerClass}>
		<div
			class={`${sectionHeaderBaseClass} border-red-200 dark:border-red-800 pl-4 border-l-red-500`}
		>
			<h2 class={sectionTitleClass}>📉 Top 10 Shrinking Companies</h2>
			<p class={sectionHeaderSubtitleClass}>
				SDK providers with the largest decline in app integrations from H1 to H2 2025
			</p>
			<h3 class="text-lg font-bold text-primary-900-100 mt-4">What Stands Out:</h3>
			<ul class="list-disc list-inside space-y-1 px-8">
				<li>
					Don't be fooled, though LiftOff saw shrinking trends, it's partnership/parent <a
						href="/companies/vungle.com">Vungle</a
					> saw a healthy increase. This isn't necessarily an issue as their older app clients are absorbed
					into Vungle. A similar situation can be observed for AdColony (Digital Turbine) and MoPub (AppLovin).
				</li>
				<li>
					Flurry saw a decline in integrations that was not reflected in Yahoo!'s flat growth.
				</li>
			</ul>
		</div>

		<div class={cardTableWrapperClass}>
			<div class={tableWrapperClass}>
				<table class="w-full">
					<thead class={tHeadShrinkClass}>
						<tr>
							<th class={tableHeaderLeftClass}>Rank</th>
							<th class={tableHeaderLeftClass}>Company</th>
							<th class={tableHeaderLeftClass}>Category</th>
							<th class={tableHeaderRightClass}>H1 Apps</th>
							<th class={tableHeaderRightClass}>H2 Apps</th>
							<th class={tableHeaderRightClass}>Net Change</th>
							<th class={tableHeaderRightClass}>Change</th>
						</tr>
					</thead>
					<tbody>
						{#each data.topShrinking as company, index}
							<tr class={tableRowClass}>
								<td class="px-4 py-4">
									<span
										class={`${rankPillBaseClass} bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300`}
									>
										{index + 1}
									</span>
								</td>
								<td class="px-4 py-4">
									<CompanyButton
										companyDomain={company.company}
										companyName={company.companyName}
										companyLogoUrl={company.logoUrl ?? undefined}
										size="md"
									/>
								</td>
								<td class="px-4 py-4 text-surface-600 dark:text-surface-400">
									{company.category}
								</td>
								<td class="px-4 py-4 text-right text-surface-600 dark:text-surface-400">
									{company.h1Apps.toLocaleString()}
								</td>
								<td class="px-4 py-4 text-right font-semibold">
									{company.h2Apps.toLocaleString()}
								</td>
								<td class="px-4 py-4 text-right text-red-600 font-semibold">
									{company.net.toLocaleString()}
								</td>
								<td class="px-4 py-4 text-right">
									<span class={`text-lg font-bold ${getGrowthColor(company.changePercent)}`}>
										{formatPercent(company.changePercent)}
									</span>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	</div>

	<!-- SECTION 3: ALL COMPANIES TABLE -->
	<div class={sectionContainerClass}>
		<div
			class={`${sectionHeaderBaseClass} border-primary-200 dark:border-primary-800 pl-4 border-l-primary-500`}
		>
			<h2 class={sectionTitleClass}>📊 All SDK Companies</h2>
			<p class={sectionHeaderSubtitleClass}>
				Complete list of {data.summary.totalCompanies} SDK providers with H1 vs H2 2025 comparison.
			</p>
			<p class={sectionHeaderSubtitleClass}>What Stands Out:</p>
			<ul class="list-disc list-inside space-y-1 px-8">
				<li>
					Revenue boosting companies like <a href="/companies/revenuecat.com">RevenueCat</a> and
					<a href="/companies/superwall.com">SuperWall</a> saw good growth. Though it will take more time
					to tell, they had even more growth in new apps in 2025, which didn't make it into the totals
					for this report.
				</li>
				<li>AirBridge saw a great boost in growth. Their MMP offering is growing rapidly.</li>
				<li>
					<a href="/companies/posthog.com">PostHog</a> and
					<a href="/companies/parse.ly">Parse.ly</a> saw great growth. These more business / developer
					focused analytics platforms are growing rapidly.
				</li>
			</ul>
		</div>

		<!-- Category Filter -->
		<div class="card preset-tonal p-4 mb-6">
			<div class="flex flex-wrap items-center gap-4">
				<span class="font-semibold text-surface-700 dark:text-surface-300">Filter by Category:</span
				>
				<form class="flex flex-wrap gap-3">
					<label class="flex items-center gap-2 cursor-pointer">
						<input
							class="radio"
							type="radio"
							name="category-filter"
							value="all"
							checked={selectedCategory === 'all'}
							onchange={() => (selectedCategory = 'all')}
						/>
						<span class="text-sm">All ({data.allData.length})</span>
					</label>
					{#each data.categories as category}
						<label class="flex items-center gap-2 cursor-pointer">
							<input
								class="radio"
								type="radio"
								name="category-filter"
								value={category}
								checked={selectedCategory === category}
								onchange={() => (selectedCategory = category)}
							/>
							<span class="text-sm"
								>{category} ({data.allData.filter((d) => d.category === category).length})</span
							>
						</label>
					{/each}
				</form>
			</div>
		</div>

		<!-- Search Filter -->
		<div class="card preset-tonal p-4 mb-6">
			<div class="flex items-center gap-4">
				<span class="font-semibold text-surface-700 dark:text-surface-300">Search:</span>
				<input
					type="text"
					placeholder="Filter by company name..."
					bind:value={searchQuery}
					class="input px-3 py-2 rounded-lg max-w-md"
				/>
				<span class="text-sm text-surface-500">
					Showing {filteredData.length} of {data.allData.length} companies
				</span>
			</div>
		</div>

		<div class={cardTableWrapperClass}>
			<div class={tableWrapperClass}>
				<table class="w-full">
					<thead class="bg-gradient-to-r from-primary-200-800 to-primary-100-900 text-white">
						<tr>
							<th class={tableHeaderLeftClass}>
								<button
									class="flex items-center gap-1 hover:text-purple-200 transition-colors"
									onclick={() => handleSort('companyName')}
								>
									Company
									{#if sortColumn === 'companyName'}
										<span>{sortDirection === 'asc' ? '↑' : '↓'}</span>
									{/if}
								</button>
							</th>
							<th class={tableHeaderLeftClass}>
								<button
									class="flex items-center gap-1 hover:text-purple-200 transition-colors"
									onclick={() => handleSort('category')}
								>
									Category
									{#if sortColumn === 'category'}
										<span>{sortDirection === 'asc' ? '↑' : '↓'}</span>
									{/if}
								</button>
							</th>
							<th class={tableHeaderRightClass}>
								<button
									class="flex items-center gap-1 justify-end hover:text-purple-200 transition-colors"
									onclick={() => handleSort('h1Apps')}
								>
									H1 Apps
									{#if sortColumn === 'h1Apps'}
										<span>{sortDirection === 'asc' ? '↑' : '↓'}</span>
									{/if}
								</button>
							</th>
							<th class={tableHeaderRightClass}>
								<button
									class="flex items-center gap-1 justify-end hover:text-purple-200 transition-colors"
									onclick={() => handleSort('h2Apps')}
								>
									H2 Apps
									{#if sortColumn === 'h2Apps'}
										<span>{sortDirection === 'asc' ? '↑' : '↓'}</span>
									{/if}
								</button>
							</th>
							<th class={tableHeaderRightClass}>
								<button
									class="flex items-center gap-1 justify-end hover:text-purple-200 transition-colors"
									onclick={() => handleSort('net')}
								>
									Net Change
									{#if sortColumn === 'net'}
										<span>{sortDirection === 'asc' ? '↑' : '↓'}</span>
									{/if}
								</button>
							</th>
							<th class={tableHeaderRightClass}>
								<button
									class="flex items-center gap-1 justify-end hover:text-purple-200 transition-colors"
									onclick={() => handleSort('changePercent')}
								>
									Change %
									{#if sortColumn === 'changePercent'}
										<span>{sortDirection === 'asc' ? '↑' : '↓'}</span>
									{/if}
								</button>
							</th>
						</tr>
					</thead>
					<tbody>
						{#each paginatedData as company}
							<tr class={tableRowClass}>
								<td class="px-4 py-3">
									<CompanyButton
										companyDomain={company.company}
										companyName={company.companyName}
										companyLogoUrl={company.logoUrl ?? undefined}
										size="md"
									/>
								</td>
								<td class="px-4 py-3 text-surface-600 dark:text-surface-400">
									{company.category}
								</td>
								<td class="px-4 py-3 text-right text-surface-600 dark:text-surface-400">
									{company.h1Apps.toLocaleString()}
								</td>
								<td class="px-4 py-3 text-right font-semibold">
									{company.h2Apps.toLocaleString()}
								</td>
								<td
									class="px-4 py-3 text-right font-semibold {company.net > 0
										? 'text-emerald-800'
										: company.net < 0
											? 'text-red-600'
											: 'text-surface-500'}"
								>
									{company.net > 0 ? '+' : ''}{company.net.toLocaleString()}
								</td>
								<td class="px-4 py-3 text-right">
									<span class={`text-lg font-bold ${getGrowthColor(company.changePercent)}`}>
										{formatPercent(company.changePercent)}
									</span>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<!-- Pagination -->
			<div
				class="flex items-center justify-between p-4 border-t border-surface-200 dark:border-surface-700"
			>
				<div class="text-sm text-surface-600 dark:text-surface-400">
					Page {currentPage} of {totalPages} ({filteredData.length} results)
				</div>
				<div class="flex items-center gap-2">
					<button
						class="btn preset-tonal px-3 py-1"
						disabled={currentPage === 1}
						onclick={() => (currentPage = 1)}
					>
						First
					</button>
					<button
						class="btn preset-tonal px-3 py-1"
						disabled={currentPage === 1}
						onclick={() => (currentPage = Math.max(1, currentPage - 1))}
					>
						Prev
					</button>
					<span class="px-3 py-1 font-semibold">{currentPage}</span>
					<button
						class="btn preset-tonal px-3 py-1"
						disabled={currentPage === totalPages}
						onclick={() => (currentPage = Math.min(totalPages, currentPage + 1))}
					>
						Next
					</button>
					<button
						class="btn preset-tonal px-3 py-1"
						disabled={currentPage === totalPages}
						onclick={() => (currentPage = totalPages)}
					>
						Last
					</button>
				</div>
			</div>
		</div>
	</div>

	<!-- CTA Section -->
	<div class={sectionContainerClass}>
		<div
			class={`${sectionHeaderBaseClass} border-purple-200 dark:border-purple-800 pl-4 border-l-4 border-l-purple-500`}
		>
			<h2 class={sectionTitleClass}>Want deeper SDK insights?</h2>
			<p class={sectionHeaderSubtitleClass}>Contact us for custom SDK intelligence reports</p>
		</div>

		<div class="max-w-none mb-6 text-lg leading-relaxed">
			<p class="mb-4">
				Get detailed analysis on specific SDK categories, competitive intelligence, or custom
				reports tailored to your business needs.
			</p>

			<div class="flex flex-col gap-4 items-start">
				<a
					href="mailto:contact@appgoblin.info"
					class="inline-flex items-center gap-2 px-6 py-3 bg-white rounded-lg hover:scale-105 transition-transform duration-200 shadow-lg"
				>
					<span class="text-black font-bold">Get in Touch</span>
					<span class="text-black font-bold">→</span>
				</a>
				<div class="text-surface-500 text-sm pt-1">
					<p>contact@appgoblin.info</p>
				</div>
			</div>
		</div>
	</div>
</div>

<!-- Footer -->
<div
	class="mt-12 pt-8 border-t-2 border-surface-200 dark:border-surface-700 text-center text-sm text-surface-500 dark:text-surface-400"
>
	<p>
		Data source: AppGoblin SDK Intelligence Platform | Report Period: {data.summary.reportPeriod}
	</p>
	<p class="mt-2">
		For more insights and detailed analytics, visit <a
			href="/"
			class="text-purple-600 hover:underline">AppGoblin.info</a
		>
	</p>
</div>
