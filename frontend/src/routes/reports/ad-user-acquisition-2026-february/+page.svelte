<script lang="ts">
	import CompanyButton from '$lib/CompanyButton.svelte';
	import CreativeModal from '$lib/CreativeModal.svelte';
	import PopularCreativeCard from '$lib/PopularCreativeCard.svelte';
	import { createCreativeModal } from '$lib/stores/creativeModal.svelte';

	import { formatNumber } from '$lib/utils/formatNumber.js';

	let { data } = $props();

	// Creative modal state
	const creativeModal = createCreativeModal();
	const reportUrl = 'https://appgoblin.info/reports/ad-user-acquisition-2026-february';
	const reportPublishedDate = '2026-03-20';
	const reportTemporalCoverage = '2026-02-01/2026-02-28';

	function formatPercent(num: number): string {
		return num.toFixed(1) + '%';
	}

	function formatSignedPercent(num?: number | null, digits = 1): string {
		if (num == null) return '—';
		const sign = num > 0 ? '+' : '';
		return `${sign}${num.toFixed(digits)}%`;
	}

	function formatDecimal(num?: number | null, digits = 2): string {
		return num == null ? '—' : num.toFixed(digits);
	}

	function getGrowthColor(growth: number): string {
		if (growth > 100) return 'text-pink-600';
		if (growth > 50) return 'text-pink-400';
		if (growth > 30) return 'text-rose-400';
		if (growth > 15) return 'text-orange-600';
		return 'text-yellow-600';
	}

	function getTrendColor(value?: number | null): string {
		if (value == null) return 'text-surface-400';
		if (value > 0) return 'text-emerald-400';
		if (value < 0) return 'text-rose-400';
		return 'text-surface-500';
	}

	function getLongTermTrendLabel(z4?: number | null): string {
		if (z4 == null) return '';
		if (z4 >= 4) return 'Strong Uptrend';
		if (z4 >= 2.5) return 'Uptrend';
		return '';
	}

	function getShortTermMomentumLabel(z2?: number | null, wowGrowthPct?: number | null): string {
		if (z2 == null) return '';
		if (z2 >= 5 || (wowGrowthPct ?? 0) >= 35) return 'Breakout';
		if (z2 >= 3) return 'Building';
		return '';
	}

	function formatOptional(num?: number | null): string {
		return num == null ? '—' : String(formatNumber(num));
	}

	function formatRoundedOptional(num?: number | null): string {
		return num == null ? '—' : String(formatNumber(Math.round(num)));
	}

	function formatWeekDate(dateStr?: string | null): string {
		if (!dateStr) return '—';
		if (dateStr.includes('T')) return dateStr.split('T')[0];
		return dateStr;
	}

	const sectionTitleClass =
		'p-3 md:p-4 text-2xl md:text-3xl font-bold bg-gradient-to-r from-primary-900-100 to-secondary-900-100 bg-clip-text text-transparent';
	const sectionContainerClass = 'mb-20 pt-10 md:pt-12 border-t-2 border-surface-200-800';
	const sectionHeaderSubtitleClass =
		'text-sm md:text-base ml-3 md:ml-4 text-surface-600 dark:text-surface-300';
	const sectionHeaderBaseClass = 'my-6 md:my-8 p-3 md:p-4 border-t-2 border-l-1';
	const sectionDescriptionClass = 'text-base md:text-lg space-y-3 md:space-y-4 mb-6';
	const sectionIntroRowClass = 'flex items-center gap-2 mb-4 md:mb-6';

	const publisherTextColor = 'text-sm md:text-xl text-bold text-emerald-400';
	const creativesTextColor = 'text-sm md:text-xl text-bold text-pink-600';
	const advertisersTextColor = 'text-sm md:text-xl text-bold text-purple-400';
	const simpleMetricColor = 'text-sm md:text-xl text-bold text-surface-800-200';
	const sectionBodyClass = 'max-w-none mb-6';
	const paragraphClass = 'text-base md:text-lg leading-relaxed ';
	const textMutedXsClass = 'text-xs text-surface-500 dark:text-surface-400';
	const textMutedXsCapClass = `${textMutedXsClass} capitalize`;
	const storeIdClass = `${textMutedXsClass} truncate max-w-[10rem] md:max-w-[16rem]`;
	const appLinkClass =
		'block text-sm md:text-base font-semibold truncate max-w-[10rem] md:max-w-[16rem]';
	const tableRowClass =
		'border-b border-surface-200 dark:border-surface-700 hover:bg-surface-100-900 transition-colors';
	const tableAppIconClass =
		'w-9 h-9 sm:w-11 sm:h-11 lg:w-14 lg:h-14 rounded-lg shadow-sm flex-shrink-0';
	const cardTableWrapperClass = 'card overflow-hidden';
	const tableWrapperClass = 'report-table-shell report-table-scroll';
	const tableHeaderText = 'text-xs md:text-sm font-bold ';
	const tableHeaderLeftClass = `px-1 md:px-2 py-2 text-left ${tableHeaderText}`;
	const tableHeaderCenterClass = `px-1 md:px-2 py-2 text-center ${tableHeaderText}`;
	const tableHeaderRightClass = `px-1 md:px-2 py-2 text-right ${tableHeaderText}`;
	const companyButtonListClass = 'flex flex-wrap gap-0.5 md:gap-1';
	const rankPillBaseClass =
		'inline-flex items-center justify-center w-6 h-6 md:w-8 md:h-8 rounded-full font-bold text-xs md:text-sm';

	const kpiCardBaseClass = 'card md:p-6 bg-gradient-to-br text-white shadow-lg';
	const kpiLabelClass = 'text-center text-lg md:text-3xl text-bold mb-4';
	const kpiValueClass = 'text-center text-xl md:text-4xl font-bold mb-1';
	const metricGridClass =
		'p-4 bg-white dark:bg-surface-900 rounded-lg border border-surface-200 dark:border-surface-700';
	const subCardTextClass = '';
	const insightCardBaseClass = 'card p-6 bg-gradient-to-br border-2';
	const insightIconClass =
		'flex-shrink-0 w-12 h-12 bg-gradient-to-br rounded-full flex items-center justify-center text-2xl';
	const ctaPrimaryClass =
		'btn-primary inline-flex w-full justify-center items-center gap-2 px-6 py-3 bg-white rounded-lg hover:scale-105 transition-transform duration-200 shadow-lg md:w-auto';
	const ctaSecondaryClass =
		'btn preset-outlined-primary-100-900 inline-flex w-full justify-center items-center gap-2 px-6 py-3 rounded-lg md:w-auto';

	const tHeadClass = 'bg-gradient-to-r from-purple-600 to-pink-600 text-white';
</script>

<svelte:head>
	<title>{data.title}</title>
	<meta name="description" content={data.description} />
	<link rel="canonical" href={reportUrl} />
	<meta property="og:type" content="article" />
	<meta property="og:site_name" content="AppGoblin" />
	<meta property="og:title" content={data.title} />
	<meta property="og:description" content={data.description} />
	<meta property="og:url" content={reportUrl} />
	<meta property="og:image" content="https://appgoblin.info/appgoblin_screenshot.png" />
	<meta property="og:image:alt" content="AppGoblin mobile UA intelligence report dashboard" />
	<meta property="article:published_time" content={reportPublishedDate} />
	<meta property="article:modified_time" content={new Date().toISOString().split('T')[0]} />
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content={data.title} />
	<meta name="twitter:description" content={data.description} />
	<meta name="twitter:image" content="https://appgoblin.info/appgoblin_screenshot.png" />

	<!-- Structured Data for Report and NewsArticle -->
	{@html `<script type="application/ld+json">${JSON.stringify({
		'@context': 'https://schema.org',
		'@graph': [
			{
				'@type': ['Report', 'NewsArticle'],
				'@id': `${reportUrl}#report`,
				url: reportUrl,
				mainEntityOfPage: {
					'@type': 'WebPage',
					'@id': reportUrl
				},
				name: data.title,
				headline: data.title,
				alternativeHeadline: `${data.summary.reportPeriod} mobile user acquisition report for ad buyers and growth teams`,
				description: data.description,
				inLanguage: 'en',
				datePublished: reportPublishedDate,
				dateModified: new Date().toISOString().split('T')[0],
				isAccessibleForFree: true,
				publisher: {
					'@id': `${reportUrl}#publisher`
				},
				author: {
					'@type': 'Organization',
					name: 'AppGoblin Mobile UA Intelligence'
				},
				image: {
					'@type': 'ImageObject',
					url: 'https://appgoblin.info/appgoblin_screenshot.png'
				},
				audience: [
					{
						'@type': 'Audience',
						audienceType: 'Mobile user acquisition buyers'
					},
					{
						'@type': 'Audience',
						audienceType: 'Ad sales and growth teams'
					}
				],
				about: [
					{
						'@type': 'Thing',
						name: 'Mobile User Acquisition',
						description: 'Performance signals for paid app growth and campaign distribution'
					},
					{
						'@type': 'Thing',
						name: 'Ad Networks and DSPs',
						description: 'Network reach, advertiser overlap, and creative volume'
					},
					{
						'@type': 'Thing',
						name: 'Creative Performance',
						description: 'Most-distributed video creatives in February 2026'
					}
				],
				mentions: [
					data.apps?.[0]
						? {
								'@type': 'MobileApplication',
								name: data.apps[0].app_name,
								identifier: data.apps[0].store_id,
								url: `https://appgoblin.info/apps/${data.apps[0].store_id}`
							}
						: null,
					data.adNetworks?.[0]
						? {
								'@type': 'Organization',
								name: data.adNetworks[0].ad_network_name,
								url: `https://appgoblin.info/companies/${data.adNetworks[0].ad_network_domain}`
							}
						: null
				].filter(Boolean),
				articleSection: ['Mobile Advertising', 'User Acquisition', 'AdTech'],
				keywords: Array.isArray(data.keywords) ? data.keywords.join(', ') : data.keywords,
				mainEntity: {
					'@id': `${reportUrl}#dataset`
				}
			},
			{
				'@type': 'Dataset',
				'@id': `${reportUrl}#dataset`,
				name: 'February 2026 Mobile App Advertising Intelligence',
				description:
					'Comprehensive dataset of app performance, ad networks, and creative strategies',
				publisher: {
					'@id': `${reportUrl}#publisher`
				},
				url: reportUrl,
				license: 'https://appgoblin.info/terms',
				spatialCoverage: {
					'@type': 'Place',
					name: 'Global'
				},
				temporalCoverage: reportTemporalCoverage,
				measurementTechnique: [
					'Mobile app network request telemetry',
					'Weekly installs trend analysis',
					'Creative distribution mapping'
				],
				distribution: [
					{
						'@type': 'DataDownload',
						encodingFormat: 'application/json'
					}
				],
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
			},
			{
				'@type': 'Organization',
				'@id': `${reportUrl}#publisher`,
				name: 'AppGoblin',
				url: 'https://appgoblin.info/',
				logo: {
					'@type': 'ImageObject',
					url: 'https://appgoblin.info/AppGoblin_Large_Logo.png'
				}
			},
			{
				'@type': 'WebPage',
				'@id': reportUrl,
				url: reportUrl,
				name: data.title,
				description: data.description,
				isPartOf: {
					'@id': 'https://appgoblin.info/#website'
				},
				about: {
					'@id': `${reportUrl}#report`
				}
			},
			{
				'@type': 'WebSite',
				'@id': 'https://appgoblin.info/#website',
				url: 'https://appgoblin.info/',
				name: 'AppGoblin'
			},
			{
				'@type': 'BreadcrumbList',
				'@id': `${reportUrl}#breadcrumbs`,
				itemListElement: [
					{
						'@type': 'ListItem',
						position: 1,
						name: 'Home',
						item: 'https://appgoblin.info/'
					},
					{
						'@type': 'ListItem',
						position: 2,
						name: 'Reports',
						item: 'https://appgoblin.info/reports'
					},
					{
						'@type': 'ListItem',
						position: 3,
						name: data.title,
						item: reportUrl
					}
				]
			}
		]
	})}<\/script>`}
</svelte:head>

<div class="container mx-auto px-3 md:px-8 xl:px-16 py-6 md:py-8">
	<!-- Header Section -->
	<div class="mb-10 md:mb-12 text-center max-w-4xl mx-auto">
		<h1
			class="text-3xl sm:text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-primary-900-100 to-secondary-900-100 bg-clip-text text-transparent"
		>
			Mobile UA Report - {data.summary.reportPeriod}
		</h1>
		<p
			class="text-base sm:text-lg md:text-xl max-w-3xl mx-auto text-surface-700 dark:text-surface-200"
		>
			The ad campaigns behind February's fastest growing mobile apps. AppGoblin breaks the best
			creatives we tracked in app ad campaigns.
		</p>
	</div>

	<!-- February Snapshot -->
	<div
		class="mb-12 rounded-2xl border border-surface-200 dark:border-surface-700 bg-gradient-to-br from-surface-50 to-white dark:from-surface-900 dark:to-surface-800 p-5 md:p-7 shadow-md"
	>
		<div class="flex flex-col md:flex-row md:items-center md:justify-between gap-2 md:gap-3 mb-5">
			<h2 class="text-2xl md:text-3xl font-bold">App advertising overview - Feb 2026</h2>
			<div class="text-sm md:text-base text-surface-600 dark:text-surface-300">
				What stood out this month
			</div>
		</div>

		<div class="grid grid-cols-1 xl:grid-cols-12 gap-5 md:gap-6 xl:items-stretch">
			<div class="space-y-4 xl:col-span-4">
				<div class="rounded-xl bg-gradient-to-r from-pink-600 to-rose-500 text-white p-5">
					<div class="text-xl md:text-2xl font-bold leading-tight">
						Familiar advertisers from January and new apps with big growth spikes
					</div>
				</div>

				<div
					class="rounded-xl border border-surface-200 dark:border-surface-700 p-4 md:p-5 bg-white/80 dark:bg-surface-900/80"
				>
					<div class="text-base md:text-lg font-semibold mb-3">Top Advertising Apps</div>
					<div class="grid grid-cols-5 sm:grid-cols-10 xl:grid-cols-5 gap-2 md:gap-3 mb-4">
						{#each data.apps.slice(0, 10) as app}
							<a href="/apps/{app.store_id}" class="group" title={app.app_name}>
								<img
									src="https://media.appgoblin.info/app-icons/{app.store_id}/{app.icon_url_100}"
									alt={app.app_name}
									class="w-12 h-12 sm:w-14 sm:h-14 md:w-16 md:h-16 rounded-xl border border-surface-200 dark:border-surface-700 shadow-sm group-hover:scale-105 transition-transform"
									onerror={(e) =>
										((e.currentTarget as HTMLImageElement).src = '/default_company_logo.png')}
								/>
							</a>
						{/each}
					</div>

					<div class="text-base md:text-lg font-semibold mb-3">Ad Networks</div>
					<div class="flex flex-wrap gap-2 md:gap-3">
						{#each data.adNetworks.slice(0, 6) as network}
							<CompanyButton
								companyDomain={network.ad_network_domain}
								companyName={network.ad_network_name}
								companyLogoUrl={network.company_logo_url}
								size="logo-only"
							/>
						{/each}
					</div>
				</div>

				<div class="grid grid-cols-3 gap-3 text-center">
					<div class="rounded-lg bg-emerald-700 dark:bg-emerald-800 p-3 shadow-sm">
						<div class="text-xl md:text-2xl font-bold text-white">
							{formatOptional(data.summary.totalApps)}
						</div>
						<div class="text-sm font-bold text-white">Apps</div>
					</div>
					<div class="rounded-lg bg-purple-700 dark:bg-purple-800 p-3 shadow-sm">
						<div class="text-xl md:text-2xl font-bold text-white">
							{formatOptional(data.summary.advertisers)}
						</div>
						<div class="text-sm font-bold text-white">Advertisers</div>
					</div>
					<div class="rounded-lg bg-pink-700 dark:bg-pink-800 p-3 shadow-sm">
						<div class="text-xl md:text-2xl font-bold text-white">
							{formatOptional(data.summary.adtechCompanies)}
						</div>
						<div class="text-sm font-bold text-white">Platforms</div>
					</div>
				</div>
			</div>

			<div class="xl:col-span-8 xl:h-full xl:flex xl:flex-col">
				<div class="featured-creatives-strip xl:flex-1">
					{#each data.popularCreatives.slice(0, 3) as creative, index}
						<div class="featured-creative-slide">
							<PopularCreativeCard
								{creative}
								{index}
								titlePrefix="February Featured Creative"
								badgeLabel="Popular Creative"
								compact={true}
								dense={true}
								onOpen={(rawUrl, title) => creativeModal.open(rawUrl, title)}
							/>
						</div>
					{/each}
				</div>
			</div>
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
						<strong class="">
							{formatNumber(data.summary.httpsTracked)} HTTPS events
						</strong>
						across
						<strong class="">
							{formatNumber(data.summary.apiDomains)} unique API domains
						</strong>, providing a comprehensive view of acquisition activity.
					</p>
					<p class={`${paragraphClass} mt-4`}>
						This activity spanned
						<strong class="">
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
						<strong class="">{data.summary.avgGrowth}% week on week installs growth </strong>.
					</p>

					<div class="mt-6 p-4 rounded-lg border border-surface-200">
						<p class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">
							AppGoblin collected millions of data points to show you how mobile app user
							acquisition works.
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
								<strong class=" text-lg font-bold"
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
			<p class={sectionHeaderSubtitleClass}>New titles and returning old games</p>
		</div>
		<div class={sectionDescriptionClass}>
			<p class="mt-2">
				Remember January's 2026 top app that saw high impact from it's ads? Well <span
					class={publisherTextColor}>{data.apps[0].app_name}</span
				>
				is back! What happened here is it looks like the ad campaign was in full force last week of January
				and first week of February. This led this ranking with
				<strong class={publisherTextColor}>{formatNumber(data.apps[0].weekly_installs)}</strong>
				installs that were higher, but a big decrease from the the huge numbers it got last week of January.
			</p>
			<p class="mt-2">
				Another returning app, <span class={publisherTextColor}>{data.apps[1].app_name}</span>, but
				this time it saw an even bigger install growth in the first week of February, which then
				went down a bit in the second week, but still had a very strong growth compared to January.
				This shows that the ad campaign for this app was also very effective in driving installs,
				and it seems like they are maintaining a strong presence in the market.
			</p>
		</div>
		<div class={cardTableWrapperClass}>
			<div class={tableWrapperClass}>
				<table class="report-table report-table--apps w-full">
					<thead class={tHeadClass}>
						<tr>
							<th class={tableHeaderLeftClass}>Rank</th>
							<th class={tableHeaderLeftClass}>App</th>
							<th class={`${tableHeaderLeftClass} hidden md:table-cell`}>Best Week</th>
							<th class={tableHeaderRightClass}>Installs (week)</th>
							<th class={`${tableHeaderRightClass} hidden xl:table-cell`}>Long-Term Trend</th>
							<th class={`${tableHeaderRightClass} hidden lg:table-cell`}>Short-Term Momentum</th>
							<th class={tableHeaderCenterClass}>Ad Creatives</th>
							<th class={tableHeaderCenterClass}>Ad Networks</th>
							<th class={`${tableHeaderCenterClass} hidden lg:table-cell`}>MMP</th>
						</tr>
					</thead>
					<tbody>
						{#each data.apps as app, index}
							<tr class={tableRowClass}>
								<td class="px-1 md:px-4 py-2 md:py-4">
									<span
										class={`${rankPillBaseClass} bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300`}
									>
										{index + 1}
									</span>
								</td>
								<td class="px-1 md:px-4 py-2 md:py-4">
									<a href="/apps/{app.store_id}" class="flex items-center gap-2 md:gap-3 min-w-0">
										<img
											src="https://media.appgoblin.info/app-icons/{app.store_id}/{app.icon_url_100}"
											alt={app.app_name}
											class={tableAppIconClass}
											onerror={(e) =>
												((e.currentTarget as HTMLImageElement).src = '/default_company_logo.png')}
										/>
										<div class="min-w-0">
											<div class={appLinkClass}>
												{app.app_name}
											</div>
											<div class={storeIdClass} title={app.store_id}>
												{app.store_id}
											</div>
										</div>
									</a>
								</td>
								<td
									class="hidden md:table-cell px-1 md:px-4 py-2 md:py-4 text-right whitespace-nowrap"
								>
									<div class="text-xs md:text-lg font-semibold">
										{formatWeekDate(app.best_week)}
									</div>
									{#if app.installs_acceleration > 0}
										<div class={`${textMutedXsClass} ${getTrendColor(app.installs_acceleration)}`}>
											Accel {formatDecimal(app.installs_acceleration)}
										</div>
									{/if}
								</td>
								<td class="px-1 md:px-4 py-2 md:py-4 text-right">
									<div class={`text-xs md:text-lg font-bold ${simpleMetricColor}`}>
										{formatNumber(app.weekly_installs)}
									</div>
									<div class={textMutedXsClass}>
										Base {formatRoundedOptional(app.baseline_installs)}
									</div>
								</td>
								<td class="hidden xl:table-cell px-2 text-right whitespace-nowrap">
									{#if getLongTermTrendLabel(app.installs_z_score_4w)}
										<div
											class={`text-xs md:text-base font-bold ${getTrendColor(app.installs_z_score_4w)}`}
										>
											{getLongTermTrendLabel(app.installs_z_score_4w)}
										</div>
									{/if}
								</td>
								<td
									class="hidden lg:table-cell px-1 md:px-4 py-2 md:py-4 text-right whitespace-nowrap"
								>
									{#if getShortTermMomentumLabel(app.installs_z_score_2w, app.wow_growth_pct)}
										<div
											class={`text-xs md:text-base font-bold ${getTrendColor(app.installs_z_score_2w)}`}
										>
											{getShortTermMomentumLabel(app.installs_z_score_2w, app.wow_growth_pct)}
										</div>
									{/if}
									{#if getShortTermMomentumLabel(app.installs_z_score_2w, app.wow_growth_pct)}
										<div class={`${textMutedXsClass} ${getTrendColor(app.wow_growth_pct)}`}>
											WoW {formatSignedPercent(app.wow_growth_pct)}
										</div>
									{/if}
								</td>
								<td class="px-1 md:px-4 py-2 md:py-4 text-center">
									<div class="flex justify-center items-center gap-1">
										{#each app.creatives.slice(0, 3) as creative}
											<button
												onclick={() =>
													creativeModal.open(
														`https://media.appgoblin.info/creatives/raw/${creative.md5_hash.substring(0, 3)}/${creative.md5_hash}.${creative.file_extension}`,
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
								<td class="px-1 md:px-4 py-2 md:py-4 min-w-[8rem]">
									<div class={companyButtonListClass}>
										{#each app.ad_networks as network}
											<CompanyButton
												companyDomain={network.domain}
												companyLogoUrl={network.logo_url}
												size="logo-only"
											/>
										{/each}
									</div>
								</td>
								<td class="hidden lg:table-cell px-1 md:px-4 py-2 md:py-4 min-w-[6rem]">
									{#if app.mmps && app.mmps.length > 0}
										<div class={companyButtonListClass}>
											{#each app.mmps as mmp}
												<CompanyButton
													companyDomain={mmp.domain}
													companyLogoUrl={mmp.logo_url}
													size="logo-only"
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
				demonstrating its popularity and success as a mobile app ad creative.
			</p>
			<p>
				The leading creative in this sample belongs to
				<a href="/apps/{data.popularCreatives[0].advertiser_store_id}">
					{data.popularCreatives[0].advertiser_store_id}
				</a>
				and gives a concrete example of the kind of asset that managed to travel broadly across publisher
				inventory.
			</p>
			<p>
				Because the top five are still based on relatively small publisher counts, changes from
				month to month are best treated as directional signals rather than absolute market-share
				conclusions.
			</p>
		</div>
		<!-- Creatives Grid -->
		<div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3 md:gap-4 xl:gap-6">
			{#each data.popularCreatives as creative, index}
				<PopularCreativeCard
					{creative}
					{index}
					titlePrefix="Popular Creative"
					badgeLabel="Most Popular"
					dense={true}
					onOpen={(rawUrl, title) => creativeModal.open(rawUrl, title)}
				/>
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
				The advertising platforms that powered {data.summary.reportPeriod} user acquisition campaigns
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
				February 2026 shows a mix of SDK inventory and programmatic distribution. In this sample,
				<a href="/companies/{data.adNetworks[0].ad_network_domain}"
					>{data.adNetworks[0].ad_network_name}</a
				>
				led the network table with {data.adNetworks[0].publisher_count.toLocaleString()} publisher apps
				and
				{data.adNetworks[0].advertiser_count.toLocaleString()} advertisers.
			</p>
			<div class="list-disc list-inside space-y-1 px-8">
				<li>
					Publisher coverage and advertiser coverage do not move in lockstep, so broad reach does
					not always mean the widest advertiser base.
				</li>
			</div>
		</div>
		<h4 class="text-large font-bold text-indigo-900 dark:text-indigo-100">Note on Methodology</h4>
		<div class={sectionDescriptionClass}>
			<p class="text-sm">
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
				<table class="report-table report-table--network w-full">
					<thead class={tHeadClass}>
						<tr>
							<th class={tableHeaderLeftClass}>Rank</th>
							<th class={tableHeaderLeftClass}>Ad Network</th>
							<th class={tableHeaderRightClass}>Publishers</th>
							<th class={tableHeaderRightClass}>Advertisers</th>
							<th class={`${tableHeaderRightClass} hidden sm:table-cell`}>Creatives</th>
							<th class={`${tableHeaderRightClass} hidden md:table-cell`}>Market Share</th>
						</tr>
					</thead>
					<tbody>
						{#each data.adNetworks as network, index}
							<tr class={tableRowClass}>
								<td class="px-1 md:px-4 py-2 md:py-4">
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
								<td class="px-1 md:px-4 py-2 md:py-4 min-w-[13rem]">
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
								<td class="px-1 md:px-4 py-2 md:py-4 text-right">
									<span class={publisherTextColor}>
										{network.publisher_count.toLocaleString()}
									</span>
								</td>
								<td class="px-1 md:px-4 py-2 md:py-4 text-right">
									<span class={advertisersTextColor}>
										{network.advertiser_count.toLocaleString()}
									</span>
								</td>
								<td
									class="hidden sm:table-cell px-1 md:px-4 py-2 md:py-4 text-right whitespace-nowrap"
								>
									<span class={creativesTextColor}>
										{network.creatives_count.toLocaleString()}
									</span>
								</td>
								<td
									class="hidden md:table-cell px-1 md:px-4 py-2 md:py-4 text-right whitespace-nowrap"
								>
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
				These are the advertisers that appeared in the most unique publisher apps during {data
					.summary.reportPeriod}.
				{data.appReachData[0].advertiser_name} led the reach table with {data.appReachData[0]
					.unique_publishers}
				publishers and {data.appReachData[0].unique_creatives} creatives.
			</p>
			<p class={paragraphClass}>
				This is a useful set of apps for understanding which advertisers were able to spread
				creative across the widest publisher footprint in February 2026.
			</p>
		</div>
		<!-- Top Apps by Publisher Reach -->
		<div class={`mt-6 ${cardTableWrapperClass}`}>
			<div class={tableWrapperClass}>
				<table class="report-table report-table--reach table table-compact">
					<thead class={tHeadClass}>
						<tr>
							<th class={tableHeaderLeftClass}>Rank</th>
							<th class={tableHeaderLeftClass}>App</th>
							<th class={tableHeaderRightClass}>Publishers</th>
							<th class={tableHeaderRightClass}>Creatives</th>
							<th class={tableHeaderLeftClass}>Ad Networks</th>
							<th class={`${tableHeaderCenterClass} hidden lg:table-cell`}>MMP</th>
						</tr>
					</thead>
					<tbody>
						{#each data.appReachData.slice(0, 10) as app, index}
							<tr class={tableRowClass}>
								<td class="px-1 md:px-2 py-2 md:py-4">
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
								<td class="px-1 md:px-2 py-2 md:py-4">
									<a
										href="/apps/{app.advertiser_store_id}"
										class="flex items-center gap-2 md:gap-3 min-w-0"
									>
										<img
											src="https://media.appgoblin.info/app-icons/{app.advertiser_store_id}/{app.advertiser_icon_url_100}"
											alt={app.advertiser_name}
											class={tableAppIconClass}
											onerror={(e) =>
												((e.currentTarget as HTMLImageElement).src = '/default_company_logo.png')}
										/>
										<div class="min-w-0">
											<div class={appLinkClass}>
												{app.advertiser_name}
											</div>
											<div class={textMutedXsCapClass}>
												{app.advertiser_category?.replace(/_/g, ' ')}
											</div>
										</div>
									</a>
								</td>
								<td class="px-1 md:px-2 py-2 md:py-4 text-right">
									<span class={publisherTextColor}>
										{app.unique_publishers}
									</span>
								</td>
								<td class="px-1 md:px-2 py-2 md:py-4 text-right">
									<span class={creativesTextColor}>
										{app.unique_creatives}
									</span>
								</td>
								<td class="px-1 md:px-2 py-2 md:py-4 min-w-[8rem]">
									{#if app.ad_networks && app.ad_networks.length > 0}
										<div class={companyButtonListClass}>
											{#each app.ad_networks.slice(0, 4) as network}
												<CompanyButton
													companyDomain={network.domain}
													companyLogoUrl={network.logo_url}
													size="logo-only"
												/>
											{/each}
											{#if app.ad_networks.length > 4}
												<span class={`${textMutedXsClass} font-semibold`}
													>+{app.ad_networks.length - 4}</span
												>
											{/if}
										</div>
									{:else}
										<span class="text-xs text-surface-400">—</span>
									{/if}
								</td>
								<td class="hidden lg:table-cell px-1 md:px-2 py-2 md:py-4 text-right min-w-[6rem]">
									{#if app.mmps && app.mmps.length > 0}
										<div class={companyButtonListClass}>
											{#each app.mmps as mmp}
												<CompanyButton
													companyDomain={mmp.domain}
													companyLogoUrl={mmp.logo_url}
													size="logo-only"
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
						<h3 class="text-lg font-bold text-blue-900 dark:text-blue-100 mb-2">Creative Cycles</h3>
						<p>
							Month-to-month changes in the ad ecosystem are not just the result of updates in your
							own campaigns, but also the decisions of every competing advertiser. Keep an eye on
							creative and buying trends so you understand what your competition is doing.
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
							Apps that ran February 2026 campaigns averaged {data.summary.avgGrowth}%
							week-over-week growth on this ranking, which reinforces how quickly paid acquisition
							can change install trajectories when creative and distribution line up.
						</p>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- CTA Section -->
	<div class={sectionContainerClass}>
		<div
			class={`${sectionHeaderBaseClass} border-purple-200 dark:border-purple-800 pl-4 border-l-4 border-l-purple-500`}
		>
			<h2 class={sectionTitleClass}>Want to leverage AppGoblin's insights?</h2>
			<p class={sectionHeaderSubtitleClass}>Choose the next step that fits your team</p>
		</div>

		<!-- Content -->
		<div class={sectionDescriptionClass}>
			<p>
				Use pricing to unlock AppGoblin data, or create a free account to explore the platform
				today.
			</p>

			<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
				<div
					class="card p-6 border border-purple-200 dark:border-purple-800 hover:border-purple-500 transition-colors"
				>
					<div class="text-sm uppercase tracking-wide text-surface-500 dark:text-surface-400">
						Pricing
					</div>
					<h3 class="text-xl font-bold mt-2 mb-2">Get Access to AppGoblin Data</h3>
					<p class="text-sm text-surface-600 dark:text-surface-300 mb-4">
						See plans and unlock broader AppGoblin datasets, exports, and deeper coverage.
					</p>
					<a href="/pricing" class={ctaSecondaryClass}>
						<span class="font-bold">View Pricing</span>
						<span class="font-bold">→</span>
					</a>
				</div>

				<div
					class="card p-6 border border-emerald-200 dark:border-emerald-800 hover:border-emerald-500 transition-colors"
				>
					<div class="text-sm uppercase tracking-wide text-surface-500 dark:text-surface-400">
						Free Account
					</div>
					<h3 class="text-xl font-bold mt-2 mb-2">Create Free Account</h3>
					<p class="text-sm text-surface-600 dark:text-surface-300 mb-4">
						Start exploring the platform immediately and see what AppGoblin already makes available
						for free.
					</p>
					<a href="/auth/signup" class={ctaPrimaryClass}>
						<span class="text-black font-bold">Sign Up Free</span>
						<span class="text-black font-bold">→</span>
					</a>
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

<style>
	.featured-creatives-strip {
		display: flex;
		gap: 1rem;
		overflow-x: auto;
		padding-bottom: 0.25rem;
		scroll-snap-type: x proximity;
		overscroll-behavior-x: contain;
		-webkit-overflow-scrolling: touch;
	}

	.featured-creative-slide {
		min-width: min(18rem, 82vw);
		flex: 0 0 auto;
		scroll-snap-align: start;
	}

	.report-table-shell {
		max-width: 100%;
	}

	.report-table-scroll {
		overflow-x: auto;
		overflow-y: hidden;
		overscroll-behavior-x: contain;
		-webkit-overflow-scrolling: touch;
		padding-bottom: 0.25rem;
	}

	.report-table {
		min-width: 100%;
	}

	@media (max-width: 767px) {
		.report-table--apps {
			min-width: 45rem;
		}

		.report-table--network {
			min-width: 34rem;
		}

		.report-table--reach {
			min-width: 38rem;
		}
	}

	@media (min-width: 768px) {
		.featured-creatives-strip {
			display: grid;
			grid-template-columns: repeat(3, minmax(0, 1fr));
			align-items: stretch;
			height: 100%;
			overflow: visible;
			padding-bottom: 0;
		}

		.featured-creative-slide {
			min-width: 0;
			height: 100%;
		}
	}
</style>
