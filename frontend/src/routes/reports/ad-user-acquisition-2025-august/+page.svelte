<script lang="ts">
	import CompanyButton from '$lib/CompanyButton.svelte';
	import CreativeModal from '$lib/CreativeModal.svelte';
	import { createCreativeModal } from '$lib/stores/creativeModal.svelte';

	import { formatNumber } from '$lib/utils/formatNumber.js';

	let { data } = $props();

	// Creative modal state
	const creativeModal = createCreativeModal();

	function formatPercent(num: number): string {
		return num.toFixed(1) + '%';
	}

	function getGrowthColor(growth: number): string {
		if (growth > 100) return 'text-pink-600';
		if (growth > 50) return 'text-pink-400';
		if (growth > 30) return 'text-rose-400';
		if (growth > 15) return 'text-orange-600';
		return 'text-yellow-600';
	}

	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}

	function formatOptional(num?: number | null): string {
		return num == null ? '—' : String(formatNumber(num));
	}

	const sectionTitleClass =
		'p-4 text-3xl font-bold bg-gradient-to-r from-primary-900-100 to-secondary-900-100 bg-clip-text text-transparent';
	const sectionContainerClass = 'mb-24 pt-12 border-t-2 border-surface-200-800';
	const sectionHeaderSubtitleClass = 'text-sm ml-4';
	const sectionHeaderBaseClass = 'my-8 p-4 border-t-2 border-l-1';
	const sectionDescriptionClass = 'text-lg space-y-4 mb-6';
	const sectionIntroRowClass = 'flex items-center gap-2 mb-6';

	const publisherTextColor = 'text-xl text-bold text-emerald-400';
	const creativesTextColor = 'text-xl text-bold text-pink-600';
	const advertisersTextColor = 'text-xl text-bold text-purple-400';
	const simpleMetricColor = 'text-xl text-bold text-surface-800-200';
	const sectionBodyClass = 'max-w-none mb-6';
	const paragraphClass = 'text-lg leading-relaxed text-primary-900-100';
	const textMutedXsClass = 'text-xs text-surface-500 dark:text-surface-400';
	const textMutedXsCapClass = `${textMutedXsClass} capitalize`;
	const appLinkClass = `text-base flex`;
	const tableRowClass =
		'border-b border-surface-200 dark:border-surface-700 hover:bg-surface-100-900 transition-colors';
	const tableAppIconClass = 'w-20 h-20 rounded-lg shadow-sm';
	const creativeAppLinkClass = 'flex items-center gap-2 mb-3 hover:opacity-80 transition-opacity';
	const creativeAppIconClass = 'w-14 h-14 rounded-lg shadow-sm';
	const cardTableWrapperClass = 'card overflow-hidden';
	const tableWrapperClass = 'table-container overflow-x-auto';
	const tableHeaderText = 'text-lg font-bold text-primary-900-100';
	const tableHeaderLeftClass = `px-1 py-2 text-left ${tableHeaderText}`;
	const tableHeaderCenterClass = `px-2 py-3 text-center ${tableHeaderText}`;
	const tableHeaderRightClass = `px-2 py-3 text-right ${tableHeaderText}`;
	const companyButtonListClass = 'flex flex-wrap gap-1';
	const rankPillBaseClass =
		'inline-flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm';

	const kpiCardBaseClass = 'card p-6 bg-gradient-to-br text-white shadow-lg';
	const kpiLabelClass = 'text-center text-3xl text-bold mb-4';
	const kpiValueClass = 'text-center text-4xl font-bold mb-1';
	const metricGridClass =
		'p-4 bg-white dark:bg-surface-900 rounded-lg border border-surface-200 dark:border-surface-700';
	const subCardTextClass = '';
	const insightCardBaseClass = 'card p-6 bg-gradient-to-br border-2';
	const insightIconClass =
		'flex-shrink-0 w-12 h-12 bg-gradient-to-br rounded-full flex items-center justify-center text-2xl';

	const tHeadClass = 'bg-gradient-to-r from-purple-600 to-pink-600 text-white';
</script>

<svelte:head>
	<title>{data.title}</title>
	<meta name="description" content={data.description} />
	<meta name="keywords" content={data.keywords} />

	<!-- Structured Data for Report and NewsArticle -->
	{@html `<script type="application/ld+json">${JSON.stringify({
		'@context': 'https://schema.org',
		'@type': 'Report',
		name: data.title,
		headline: data.title,
		description: data.description,
		url: 'https://appgoblin.info/reports/ad-user-acquisition-2025-august',
		datePublished: '2025-09-01',
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
		about: [
			{
				'@type': 'Thing',
				name: 'Mobile App Marketing',
				description: 'Analysis of user acquisition strategies in mobile apps'
			},
			{
				'@type': 'Thing',
				name: 'Digital Advertising',
				description: 'Ad networks and creative performance data'
			},
			{
				'@type': 'Thing',
				name: 'App Install Growth',
				description: 'Weekly install trends and growth percentages'
			}
		],
		keywords: data.keywords,
		articleSection: 'Technology',
		image: {
			'@type': 'ImageObject',
			url: 'https://appgoblin.info/appgoblin_screenshot.png'
		},
		mainEntity: {
			'@type': 'DataSet',
			name: 'August 2025 Mobile App Advertising Intelligence',
			description: 'Comprehensive dataset of app performance, ad networks, and creative strategies',
			distribution: {
				'@type': 'DataDownload',
				encodingFormat: 'application/json'
			},
			spatialCoverage: {
				'@type': 'Place',
				name: 'Global'
			},
			temporalCoverage: '2025-08-01/2025-08-31',
			variableMeasured: [
				{
					'@type': 'PropertyValue',
					name: 'Apps Analyzed',
					value: '${data.summary.totalApps}'
				},
				{
					'@type': 'PropertyValue',
					name: 'Total Weekly Installs',
					value: '${data.summary.totalInstalls}'
				},
				{
					'@type': 'PropertyValue',
					name: 'Unique Creatives',
					value: '${data.summary.totalCreatives}'
				},
				{
					'@type': 'PropertyValue',
					name: 'Ad Networks Identified',
					value: '${data.summary.uniqueNetworks}'
				},
				{
					'@type': 'PropertyValue',
					name: 'Advertiser Count',
					value: '${data.summary.advertisers}'
				},
				{
					'@type': 'PropertyValue',
					name: 'AdTech Companies',
					value: '${data.summary.adtechCompanies}'
				},
				{
					'@type': 'PropertyValue',
					name: 'HTTPS Tracked Requests',
					value: '${data.summary.httpsTracked}'
				},
				{
					'@type': 'PropertyValue',
					name: 'API Domains',
					value: '${data.summary.apiDomains}'
				}
			]
		}
	})}<\/script>`}
</svelte:head>

<div class="container mx-auto px-4 py-8 max-w-7xl">
	<!-- Header Section -->
	<div class="mb-12 text-center">
		<div
			class="inline-block px-4 py-2 bg-surface-100-900 text-white rounded-full text-sm font-semibold mb-4"
		>
			User Acquisition Intelligence Report
		</div>
		<h1
			class="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-primary-900-100 to-secondary-900-100 bg-clip-text text-transparent"
		>
			{data.summary.reportPeriod} Ad Growth Analysis
		</h1>
		<p class="text-xl max-w-3xl mx-auto">
			Discover the fastest-growing mobile apps and the advertising strategies powering their user
			acquisition campaigns in August 2025.
		</p>
	</div>

	<!-- Key Metrics Dashboard -->
	<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
		<div class={`${kpiCardBaseClass} bg-gradient-to-r from-primary-100-900 to-primary-400-600`}>
			<div class={kpiValueClass}>{formatOptional(data.summary.totalApps)}</div>
			<div class={`${kpiLabelClass}`}>Apps Analyzed</div>
		</div>

		<div class={`${kpiCardBaseClass} bg-gradient-to-b to-purple-800 from-purple-400`}>
			<div class={kpiValueClass}>{formatOptional(data.summary.advertisers)}</div>
			<div class={`${kpiLabelClass}`}>Advertisers</div>
		</div>

		<div class={`${kpiCardBaseClass} bg-gradient-to-l from-primary-100-900 to-primary-400-600`}>
			<div class={kpiValueClass}>{formatOptional(data.summary.adtechCompanies)}</div>
			<div class={`${kpiLabelClass}`}>AdTech Platforms</div>
		</div>

		<div class={`${kpiCardBaseClass} bg-gradient-to-t from-error-200-800 to-pink-600`}>
			<div class={kpiValueClass}>{formatOptional(data.summary.totalCreatives)}</div>
			<div class={`${kpiLabelClass}`}>Creative Assets</div>
		</div>

		<div class={`${kpiCardBaseClass} bg-gradient-to-t from-primary-100-900 to-primary-400-600`}>
			<div class={kpiValueClass}>{formatOptional(data.summary.httpsTracked)}</div>
			<div class={`${kpiLabelClass}`}>Events Captured</div>
		</div>

		<div class={`${kpiCardBaseClass} bg-gradient-to-t from-emerald-800 to-emerald-400`}>
			<div class={kpiValueClass}>{formatOptional(data.summary.apiDomains)}</div>
			<div class={`${kpiLabelClass}`}>Unique API Domains</div>
		</div>
	</div>
	<div class="flex flex-col gap-4 items-center mb-16">
		<a
			href="mailto:contact@appgoblin.info"
			class="btn-primary inline-flex items-center gap-2 px-6 py-3 bg-white rounded-lg hover:scale-105 transition-transform duration-200 shadow-lg"
		>
			<span class="text-black font-bold">Get in Touch or Schedule Free Walkthrough</span>
			<span class="text-black font-bold">→</span>
		</a>
		<div class="text-white/80 text-sm pt-1">
			<p>contact@appgoblin.info</p>
		</div>
	</div>

	<!-- ========================================= -->
	<!-- SECTION 1: EXECUTIVE SUMMARY -->
	<!-- ========================================= -->
	<div class={sectionContainerClass}>
		<div class="mb-16">
			<!-- Section Header -->
			<div
				class={`${sectionHeaderBaseClass} border-purple-200 dark:border-purple-800 pl-4 border-l-purple-500`}
			>
				<h2 class={sectionTitleClass}>Executive Summary</h2>
				<p class={sectionHeaderSubtitleClass}>
					Key findings and performance overview for {data.summary.reportPeriod}
				</p>
			</div>

			<!-- Content -->
			<div>
				<div class={sectionIntroRowClass}>
					<h3 class="text-xl font-bold text-purple-900 dark:text-purple-100">Overview</h3>
				</div>
				<div class="max-w-none">
					<p class={paragraphClass}>
						In {data.summary.reportPeriod}, AppGoblin analyzed
						<strong class={publisherTextColor}>
							{formatNumber(data.summary.totalApps)} mobile apps
						</strong>
						and captured
						<strong class="text-primary-900-100">
							{formatNumber(data.summary.httpsTracked)} HTTPS events
						</strong>
						across
						<strong class="text-primary-900-100">
							{formatNumber(data.summary.apiDomains)} unique API domains
						</strong>, providing a comprehensive view of acquisition activity.
					</p>
					<p class={`${paragraphClass} mt-4`}>
						This activity spanned
						<strong class="text-primary-900-100">
							{formatNumber(data.summary.adtechCompanies)} AdTech platforms
						</strong>
						supporting
						<strong class={advertisersTextColor}>
							{formatNumber(data.summary.advertisers)} advertisers
						</strong>
						and
						<strong class={creativesTextColor}>
							{formatNumber(data.summary.totalCreatives)} creative assets
						</strong>
						driving some ad campaigns to
						<strong class="text-primary-900-100"
							>{data.summary.avgGrowth}% week on week installs growth
						</strong>.
					</p>

					<div class="mt-6 p-4 rounded-lg border border-surface-200">
						<p class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">
							This is a behind-the-scenes look at mobile app advertising based on data collected by
							AppGoblin.
						</p>
						<ul class="text-sm leading-6 list-disc pl-5 space-y-1">
							<li>
								<strong class={advertisersTextColor}
									>Which apps were advertising the most —
									{formatNumber(data.summary.advertisers)}</strong
								>
								apps were actively running ads
							</li>
							<li>
								<strong class={creativesTextColor}>
									What their ads looked like — nearly
									{formatNumber(data.summary.totalCreatives)}</strong
								>
								different commercials, banners, and videos
							</li>
							<li>
								<strong class={publisherTextColor}>
									Where they were advertising —
									{formatNumber(data.summary.adtechCompanies)}</strong
								>
								different advertising platforms and services
							</li>
							<li>
								<strong class="text-primary-900-100 text-lg font-bold"
									>How the whole system works — over
									{formatNumber(data.summary.httpsTracked)}</strong
								>
								technical interactions captured (clicks, loads, redirects)
							</li>
						</ul>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- ========================================= -->
	<!-- SECTION 2: AD IMPACT ON INSTALLS -->
	<!-- ========================================= -->
	<div class={sectionContainerClass}>
		<div
			class={`${sectionHeaderBaseClass} border-orange-200 dark:border-orange-800 pl-4 border-l-orange-500`}
		>
			<h2 class={sectionTitleClass}>Ad Impacts on Weekly Install Growth</h2>
			<p class={sectionHeaderSubtitleClass}>App discoverability in the app stores is dead.</p>
		</div>
		<div class={sectionDescriptionClass}>
			<p class="mt-2">
				Organic app discoverability is the myth that the ad monopolies on the Apple and Google use
				to juice their store ad campaigns. Few people search for new apps.
			</p>
			<p>
				Meanwhile, in-app ads are a direct way for apps to reach new audiences (you're still not
				getting away from the ad monopolies). The Ad Impact section shows the correlations between
				apps that were seen running ad campaigns and their increased installs during the following
				week.
			</p>
			<p>
				These are the August 2025 ad mobile app ad campaigns (US) that drove the highest increases
				in week on week (W/W) install growth.
			</p>
		</div>
		<div class={cardTableWrapperClass}>
			<div class={tableWrapperClass}>
				<table class="w-full">
					<thead class={tHeadClass}>
						<tr>
							<th class={tableHeaderLeftClass}>Rank</th>
							<th class={tableHeaderLeftClass}>App</th>
							<th class={tableHeaderLeftClass}>Best Week</th>
							<th class={tableHeaderRightClass}>W/W Growth</th>
							<th class={tableHeaderRightClass}>Installs (week)</th>
							<th class={tableHeaderCenterClass}>Ad Creatives</th>
							<th class={tableHeaderCenterClass}>Ad Networks</th>
							<th class={tableHeaderCenterClass}>MMP</th>
						</tr>
					</thead>
					<tbody>
						{#each data.apps as app, index}
							<tr class={tableRowClass}>
								<td class="px-4 py-4">
									<span
										class={`${rankPillBaseClass} bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300`}
									>
										{index + 1}
									</span>
								</td>
								<td class="px-4 py-4">
									<a href="/apps/{app.store_id}">
										<img
											src="https://media.appgoblin.info/app-icons/{app.store_id}/{app.icon_url_100}"
											alt={app.app_name}
											class={tableAppIconClass}
											onerror={(e) =>
												((e.currentTarget as HTMLImageElement).src = '/default_company_logo.png')}
										/>
										<div>
											<div class={appLinkClass}>
												{app.app_name}
											</div>
											<div class={textMutedXsClass}>
												{app.store_id}
											</div>
										</div>
									</a>
								</td>
								<td class="px-4 py-4 text-right">
									<span class="text-lg">
										{app.best_week}
									</span>
								</td>
								<td class="px-4 py-4 text-right">
									<span class="text-lg font-bold {getGrowthColor(app.weekly_percent_increase)}">
										+{formatPercent(app.weekly_percent_increase)}
									</span>
								</td>
								<td class={`px-2 text-right ${simpleMetricColor}`}>
									{formatNumber(app.weekly_installs)}
								</td>
								<td class="px-4 py-4 text-center">
									<div class="flex justify-center items-center gap-1">
										{#each app.creatives.slice(0, 3) as creative}
											<button
												onclick={() =>
													creativeModal.open(
														creative.md5_hash,
														creative.file_extension,
														app.app_name
													)}
												class="relative group cursor-pointer hover:scale-110 transition-transform duration-200"
												title="Click to view"
											>
												<div
													class="w-10 h-10 rounded border border-surface-300 dark:border-surface-600 overflow-hidden group-hover:border-purple-500"
												>
													<img
														src="https://media.appgoblin.info/creatives/thumbs/{creative.md5_hash}.jpg"
														alt="Creative"
														class="w-full h-full object-cover"
														onerror={(e) => {
															const target = e.currentTarget as HTMLImageElement;
															const parent = target.parentElement;
															if (parent) {
																parent.innerHTML =
																	'<div class="w-full h-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-xs">N/A</div>';
															}
														}}
													/>
												</div>
											</button>
										{/each}
										{#if app.creative_count > 3}
											<span class={`${textMutedXsClass} font-semibold ml-1`}>
												+{app.creative_count - 3}
											</span>
										{/if}
									</div>
								</td>
								<td class="px-4 py-4">
									<div class={companyButtonListClass}>
										{#each app.ad_networks as network}
											<CompanyButton
												companyDomain={network.domain}
												companyLogoUrl={network.logo_url}
												size="md"
											/>
										{/each}
									</div>
								</td>
								<td class="px-4 py-4">
									{#if app.mmps && app.mmps.length > 0}
										<div class={companyButtonListClass}>
											{#each app.mmps as mmp}
												<CompanyButton
													companyDomain={mmp.domain}
													companyLogoUrl={mmp.logo_url}
													size="md"
												/>
											{/each}
										</div>
									{:else}
										<span class="text-xs text-surface-400">—</span>
									{/if}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	</div>

	<!-- ========================================= -->
	<!-- SECTION 3: MOST POPULAR VIDEO CREATIVES -->
	<!-- ========================================= -->
	<div class={sectionContainerClass}>
		<!-- Section Header -->
		<div
			class={`${sectionHeaderBaseClass} border-pink-200 dark:border-pink-800 pl-4 border-l-pink-500`}
		>
			<h2 class={sectionTitleClass}>Most Popular Video Creatives</h2>
			<p class={sectionHeaderSubtitleClass}>
				Video ads with the widest mobile app distribution during {data.summary.reportPeriod}
			</p>
		</div>
		<!-- Content -->
		<div class={sectionIntroRowClass}>
			<span class="text-3xl">🎬</span>
			<h3 class="text-xl font-bold text-pink-900 dark:text-pink-100">Creative Performance</h3>
		</div>
		<div class={sectionDescriptionClass}>
			<p>
				These mobile app ad video creatives achieved the widest distribution among mobile publishers
				in {data.summary.reportPeriod}. The top performer was showing across
				<strong class="text-pink-600">{data.popularCreatives[0].publisher_count} publishers</strong>
				demonstrating it's popularity and success as a mobile app ad creative.
			</p>
			<p>
				TikTok was the leading advertiser and its creatives were preloaded the most. Interestingly
				there were several ecommerce product apps that were also seeing wide distribution. And of
				course at least one AI app, Microsoft's Copilot also saw one of the highest ad reach.
			</p>
		</div>
		<!-- Creatives Grid -->
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
			{#each data.popularCreatives as creative, index}
				<div
					class="bg-white dark:bg-surface-900 rounded-lg border-2 border-pink-200 dark:border-pink-800 overflow-hidden hover:shadow-xl transition-shadow duration-300"
				>
					<!-- Rank Badge -->
					<div
						class="bg-gradient-to-r from-pink-500 to-rose-500 text-white px-3 py-1 text-sm font-bold"
					>
						#{index + 1} Most Popular
					</div>
					<!-- Thumbnail with Play Button -->
					<button
						onclick={() =>
							creativeModal.open(
								creative.md5_hash,
								creative.file_extension,
								`Popular Creative #${index + 1}`
							)}
						class="relative w-full aspect-video bg-gradient-to-br from-purple-200 to-pink-200 dark:from-purple-900 dark:to-pink-900 cursor-pointer group overflow-hidden"
						title="Click to play video"
					>
						<img
							src="https://media.appgoblin.info/creatives/thumbs/{creative.md5_hash}.jpg"
							alt={`Popular creative ${index + 1}`}
							class="w-full h-full object-cover"
							onerror={(e) => {
								const target = e.currentTarget as HTMLImageElement;
								target.style.display = 'none';
							}}
						/>
						<!-- Play Button Overlay -->
						<div
							class="absolute inset-0 flex items-center justify-center bg-surface-100-900/20 group-hover:bg-surface-100-900/10 transition-all duration-200"
						>
							<div
								class="w-12 h-12 bg-white rounded-full flex items-center justify-center group-hover:scale-110 transition-transform duration-200 shadow-lg"
							>
								<svg class="w-8 h-8 text-pink-600 ml-1" fill="currentColor" viewBox="0 0 20 20">
									<path
										d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z"
									/>
								</svg>
							</div>
						</div>
					</button>
					<!-- Stats -->
					<div class="p-4 space-y-2">
						<!-- Advertiser Info -->
						<a href="/apps/{creative.advertiser_store_id}" class={creativeAppLinkClass}>
							<img
								src="https://media.appgoblin.info/app-icons/{creative.advertiser_store_id}/{creative.advertiser_icon_url_100}"
								alt="App icon"
								class={creativeAppIconClass}
								onerror={(e) =>
									((e.currentTarget as HTMLImageElement).src = '/default_company_logo.png')}
							/>
							<span class={`${textMutedXsClass} truncate hover:underline`}
								>{creative.advertiser_store_id}</span
							>
						</a>
						<!-- Publisher Count -->
						<div class="flex justify-between items-center">
							<span class="text-sm text-surface-600 dark:text-surface-400">Publishers</span>
							<span class={publisherTextColor}>{creative.publisher_count}</span>
						</div>
						<!-- Date Range -->
						<div
							class="text-xs text-surface-500 dark:text-surface-500 pt-2 border-t border-surface-200 dark:border-surface-700"
						>
							<div class="flex justify-between">
								<span>First seen:</span>
								<span class="font-semibold">{formatDate(creative.first_seen)}</span>
							</div>
							<div class="flex justify-between">
								<span>Last seen:</span>
								<span class="font-semibold">{formatDate(creative.last_seen)}</span>
							</div>
						</div>
					</div>
				</div>
			{/each}
		</div>
	</div>

	<!-- ========================================= -->
	<!-- SECTION 4: AD NETWORK LANDSCAPE -->
	<!-- ========================================= -->
	<div class={sectionContainerClass}>
		<!-- Section Header -->
		<div
			class={`${sectionHeaderBaseClass} border-indigo-200 dark:border-indigo-800 pl-4 border-l-indigo-500`}
		>
			<h2 class={sectionTitleClass}>Ad Network Landscape</h2>
			<p class={sectionHeaderSubtitleClass}>
				The advertising platforms that powered August 2025 user acquisition campaigns
			</p>
		</div>
		<!-- Network Metrics Grid -->
		<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
			<div class={metricGridClass}>
				<div class={`${subCardTextClass} mb-1`}>Publishers Apps That Ran Ads</div>
				<div class="text-3xl font-bold text-emerald-400">
					{data.networkStats.totalPublishers.toLocaleString()}
				</div>
			</div>
			<div class={metricGridClass}>
				<div class={`${subCardTextClass} mb-1`}>App Advertisers</div>
				<div class="text-3xl font-bold text-purple-400">
					{data.summary.advertisers.toLocaleString()}
				</div>
			</div>
			<div class={metricGridClass}>
				<div class={`${subCardTextClass} mb-1`}>Ad Creatives (video & images)</div>
				<div class="text-3xl font-bold text-pink-600">
					{data.networkStats.totalNetworkCreatives.toLocaleString()}
				</div>
			</div>
		</div>
		<!-- Content -->
		<div class={sectionIntroRowClass}>
			<span class="text-3xl">🌐</span>
			<h3 class="text-xl font-bold text-indigo-900 dark:text-indigo-100">Network Distribution</h3>
		</div>
		<div class={sectionDescriptionClass}>
			<p>
				The mobile advertising Android ecosystem is monopolized by Google due to it's control of the
				Android OS. However, there are several other ad networks that provide valuable reach and
				targeting options for app advertisers. Overall we saw
				<strong class="text-emerald-400">{data.networkStats.totalPublishers} publishers</strong>,
				delivering
				<strong class="text-pink-600"
					>{data.networkStats.totalNetworkCreatives} unique creatives</strong
				> across the top ad networks in August 2025.
			</p>
			<p>
				The other ad networks fighting for the leftover market share are split into two overlapping
				groups: SDK direct ad networks and programmatic networks.
			</p>
			<div class="list-disc list-inside space-y-1 px-8">
				<li>
					SDK networks like Unity Ads and AppLovin can leverage their direct SDK integrations to
					control the ad delivery environment.
				</li>
				<li>
					Programmatic networks like RTB House rely on these SDK networks to deliver their ads.
				</li>
			</div>
		</div>
		<h4 class="text-xl font-bold text-indigo-900 dark:text-indigo-100">Note on Methodology</h4>
		<div class={sectionDescriptionClass}>
			<p>
				When looking at this data its important to keep the context of how it was collected. The
				data is aggregated from API calls made by opening apps and watching the ad network
				connections. As such, this does not include App Store advertising (Apple/Google) or social
				media ads (TikTok/Facebook/Instagram). Facebook Audience Network (FAN) is included, but as
				it is quite small it didn't make the top 10.
			</p>
		</div>
		<!-- Top Networks Table -->
		<div class={cardTableWrapperClass}>
			<div class={tableWrapperClass}>
				<table class="w-full">
					<thead class={tHeadClass}>
						<tr>
							<th class={tableHeaderLeftClass}>Rank</th>
							<th class={tableHeaderLeftClass}>Ad Network</th>
							<th class={tableHeaderRightClass}>Publishers</th>
							<th class={tableHeaderRightClass}>Advertisers</th>
							<th class={tableHeaderRightClass}>Creatives</th>
							<th class={tableHeaderRightClass}>Market Share</th>
						</tr>
					</thead>
					<tbody>
						{#each data.adNetworks as network, index}
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
														: 'bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300'
										}`}
									>
										{index + 1}
									</span>
								</td>
								<td class="px-4 py-4">
									<CompanyButton
										companyDomain={network.ad_network_domain}
										companyName={network.ad_network_name}
										companyLogoUrl={network.company_logo_url}
										size="lg"
									/>
									{#if network.domains && network.domains.length > 0}
										<div class={textMutedXsClass}>
											{network.domains.join(', ')}
										</div>
									{:else}
										<span class="text-xs text-surface-400">—</span>
									{/if}
								</td>
								<td class="px-4 py-4 text-right">
									<span class={publisherTextColor}>
										{network.publisher_count.toLocaleString()}
									</span>
								</td>
								<td class="px-4 py-4 text-right">
									<span class={advertisersTextColor}>
										{network.advertiser_count.toLocaleString()}
									</span>
								</td>
								<td class="px-4 py-4 text-right">
									<span class={creativesTextColor}>
										{network.creatives_count.toLocaleString()}
									</span>
								</td>
								<td class="px-4 py-4 text-right">
									<div class="flex items-center justify-end gap-2">
										<div
											class="w-24 h-2 bg-surface-200 dark:bg-surface-700 rounded-full overflow-hidden"
										>
											<div
												class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
												style="width: {(
													(network.publisher_count / data.networkStats.totalPublishers) *
													100
												).toFixed(1)}%"
											></div>
										</div>
										<span class={simpleMetricColor}>
											{(
												(network.publisher_count / data.networkStats.totalPublishers) *
												100
											).toFixed(1)}%
										</span>
									</div>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	</div>

	<!-- ========================================= -->
	<!-- SECTION 5: CAMPAIGN REACH ANALYSIS -->
	<!-- ========================================= -->
	<div class={sectionContainerClass}>
		<!-- Section Header -->
		<div
			class={`${sectionHeaderBaseClass} border-emerald-200 dark:border-emerald-800 pl-4 border-l-emerald-500`}
		>
			<h2 class={sectionTitleClass}>Campaign Reach Analysis</h2>
			<p class={sectionHeaderSubtitleClass}>
				Publisher distribution strategies and market penetration insights
			</p>
		</div>
		<!-- Content -->
		<div class={sectionIntroRowClass}>
			<h3 class="text-xl font-bold text-emerald-900 dark:text-emerald-100">
				Reach Tiers & Distribution
			</h3>
		</div>
		<div class={sectionBodyClass}>
			<p class={paragraphClass}>
				These are the advertisers that appeared in the most unique publisher apps during this
				period. TikTok dominated with it's ads being shown in the vast majority of Google's
				preloaded ads.
			</p>
			<p class={paragraphClass}>
				This is a useful set of apps for those looking to understand who is likely running larger
				mobile ad campaigns in August 2025.
			</p>
		</div>
		<!-- Top Apps by Publisher Reach -->
		<div class={`mt-6 ${cardTableWrapperClass}`}>
			<div class={tableWrapperClass}>
				<table class="table table-compact">
					<thead class={tHeadClass}>
						<tr>
							<th class={tableHeaderLeftClass}>Rank</th>
							<th class={tableHeaderLeftClass}>App</th>
							<th class={tableHeaderRightClass}>Publishers</th>
							<th class={tableHeaderRightClass}>Creatives</th>
							<th class={tableHeaderRightClass}>Installs</th>
							<th class={tableHeaderLeftClass}>Ad Networks</th>
							<th class={tableHeaderCenterClass}>MMP</th>
						</tr>
					</thead>
					<tbody>
						{#each data.appReachData.slice(0, 10) as app, index}
							<tr class={tableRowClass}>
								<td class="px-2 py-4">
									<span
										class={`${rankPillBaseClass} ${
											index === 0
												? 'bg-gradient-to-br from-yellow-400 to-yellow-600 text-white'
												: index === 1
													? 'bg-gradient-to-br from-gray-300 to-gray-500 text-white'
													: index === 2
														? 'bg-gradient-to-br from-orange-400 to-orange-600 text-white'
														: 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300'
										}`}
									>
										{index + 1}
									</span>
								</td>
								<td class="px-2 py-4 flex items-center gap-3">
									<a href="/apps/{app.advertiser_store_id}">
										<img
											src="https://media.appgoblin.info/app-icons/{app.advertiser_store_id}/{app.advertiser_icon_url_100}"
											alt={app.advertiser_name}
											class={tableAppIconClass}
											onerror={(e) =>
												((e.currentTarget as HTMLImageElement).src = '/default_company_logo.png')}
										/>
										<div>
											<div class={appLinkClass}>
												{app.advertiser_name}
											</div>
											<div class={textMutedXsCapClass}>
												{app.advertiser_category.replace(/_/g, ' ')}
											</div>
										</div>
									</a>
								</td>
								<td class="px-2 py-4 text-right">
									<span class={publisherTextColor}>
										{app.unique_publishers}
									</span>
								</td>
								<td class="px-2 py-4 text-right">
									<span class={creativesTextColor}>
										{app.unique_creatives}
									</span>
								</td>
								<td class={`px-2 py-4 ${simpleMetricColor} text-right`}>
									{formatNumber(app.advertiser_installs)}
								</td>
								<td class="px-2 py-4">
									{#if app.ad_networks && app.ad_networks.length > 0}
										<div class={companyButtonListClass}>
											{#each app.ad_networks as network}
												<CompanyButton
													companyDomain={network.domain}
													companyLogoUrl={network.logo_url}
													size="md"
												/>
											{/each}
										</div>
									{:else}
										<span class="text-xs text-surface-400">—</span>
									{/if}
								</td>
								<td class="px-1 py-4 text-right">
									{#if app.mmps && app.mmps.length > 0}
										<div class={companyButtonListClass}>
											{#each app.mmps as mmp}
												<CompanyButton
													companyDomain={mmp.domain}
													companyLogoUrl={mmp.logo_url}
													size="md"
												/>
											{/each}
										</div>
									{:else}
										<span class="text-xs text-surface-400">—</span>
									{/if}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	</div>

	<!-- ========================================= -->
	<!-- SECTION 6: KEY INSIGHTS & RECOMMENDATIONS -->
	<!-- ========================================= -->
	<div class={sectionContainerClass}>
		<div
			class={`${sectionHeaderBaseClass} border-blue-200 dark:border-warning-800-200 pl-4 border-l-warning-800-200`}
		>
			<h2 class={sectionTitleClass}>Final Insights</h2>
			<p class={sectionHeaderSubtitleClass}>
				Actionable takeaways and strategic recommendations for user acquisition
			</p>
		</div>
		<!-- Content -->
		<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
			<!-- Insight Card 1 -->
			<div
				class={`${insightCardBaseClass} from-blue-50 to-cyan-50 dark:from-surface-800 dark:to-surface-700 border-blue-200 dark:border-blue-800`}
			>
				<div class="flex items-start gap-3 mb-4">
					<div class={`${insightIconClass} from-blue-500 to-cyan-500`}>💡</div>
					<div>
						<h3 class="text-lg font-bold text-blue-900 dark:text-blue-100 mb-2">
							Diversification is Key
						</h3>
						<p>
							Google holds <strong class="text-emerald-400"
								>{(
									(data.adNetworks[0].publisher_count / data.networkStats.totalPublishers) *
									100
								).toFixed(1)}% market share</strong
							>. Concentrated monoplization of ad networks hurts app developers. Diversifying beyond
							Google Ads reduces platform risk and increases audience reach. This is currently only
							available for large app publishers.
						</p>
					</div>
				</div>
			</div>

			<div
				class={`${insightCardBaseClass} from-rose-50 to-pink-50 dark:from-surface-800 dark:to-surface-700 border-rose-200 dark:border-rose-800`}
			>
				<div class="flex items-start gap-3 mb-4">
					<div class={`${insightIconClass} from-rose-500 to-pink-500`}>🚀</div>
					<div>
						<h3 class="text-lg font-bold text-rose-900 dark:text-rose-100 mb-2">
							High Growth Opportunities
						</h3>
						<p class="text-surface-700 dark:text-surface-300">
							Average growth rate of {data.summary.avgGrowth}% demonstrates significant opportunity
							in the mobile app market. Strategic ad campaigns can rapidly scale user acquisition
							for those that can afford it.
						</p>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- ========================================= -->
	<!-- ABOUT APPGOBLIN -->
	<!-- ========================================= -->
	<div class={sectionContainerClass}>
		<div
			class={`${sectionHeaderBaseClass} border-blue-200 dark:border-primary-800-200 pl-4 border-l-primary-800-200`}
		>
			<h2 class={sectionTitleClass}>About AppGoblin</h2>
			<p class={sectionHeaderSubtitleClass}>Free mobile ad intelligence</p>
		</div>
		<!-- Content -->
		<div class={sectionDescriptionClass}>
			<p>
				AppGoblin is a free mobile ad intelligence platform that provides insights into the mobile
				app ecosystem. Our mission is to democratize access to mobile ad data, enabling developers,
				marketers, and analysts to make informed decisions.
			</p>
			<p>
				AppGoblin has many free tools for researchers, journalists and mobile app developers. Feel
				free to explore and contact us.
			</p>
		</div>
	</div>

	<!-- CTA Section -->
	<div class={sectionContainerClass}>
		<div
			class={`${sectionHeaderBaseClass} border-purple-200 dark:border-purple-800 pl-4 border-l-4 border-l-purple-500`}
		>
			<h2 class={sectionTitleClass}>Want to learn more?</h2>
			<p class={sectionHeaderSubtitleClass}>Schedule a free demo or walkthrough</p>
		</div>

		<!-- Content -->
		<div class={sectionDescriptionClass}>
			<p>
				Get deeper insights into mobile ad strategies, explore custom reports for your business, or
				schedule a free demo and walkthrough of the AppGoblin platform to discover how we can help
				you understand the mobile ad ecosystem.
			</p>

			<div class="flex flex-col gap-4 items-start">
				<a
					href="mailto:contact@appgoblin.info"
					class="btn-primary inline-flex items-center gap-2 px-6 py-3 bg-white rounded-lg hover:scale-105 transition-transform duration-200 shadow-lg"
				>
					<span class="text-black font-bold">Get in Touch or Schedule Free Walkthrough</span>
					<span class="text-black font-bold">→</span>
				</a>
				<div class="text-white/80 text-sm pt-1">
					<p>contact@appgoblin.info</p>
				</div>
			</div>
		</div>
	</div>
</div>

<!-- Footer -->
<div
	class="mt-20 pt-12 border-t-2 border-surface-200 dark:border-surface-700 text-center text-sm text-surface-500 dark:text-surface-400"
>
	<p>
		Data source: AppGoblin Ad Intelligence Platform | Report Period: {data.summary.reportPeriod}
	</p>
	<p class="mt-2">
		For more insights and detailed analytics, visit <a
			href="/"
			class="text-purple-600 hover:underline">AppGoblin.info</a
		>
	</p>
	<p class="text-sm text-surface-500 mt-4">Report Generated: {data.summary.generatedDate}</p>
</div>

<!-- Creative Modal -->
<CreativeModal
	bind:isOpen={creativeModal.isOpen}
	creativeUrl={creativeModal.creativeUrl}
	title={creativeModal.title}
/>
