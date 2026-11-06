<script lang="ts">
	import AdvertiserCountryPie from '#lib/AdvertiserCountryPie.svelte';
	import CompanyButton from '#lib/CompanyButton.svelte';
	import CountryFlag from '#lib/CountryFlag.svelte';
	import CreativeModal from '#lib/CreativeModal.svelte';
	import PopularCreativeCard from '#lib/PopularCreativeCard.svelte';
	import Crown from '@lucide/svelte/icons/crown';
	import Lock from '@lucide/svelte/icons/lock';
	import RankBadge from '#lib/RankBadge.svelte';
	import { createCreativeModal } from '#lib/stores/creativeModal.svelte.js';

	import { formatNumber } from '#lib/utils/formatNumber.js';

	let { data } = $props();

	// Derived splits
	const topGames = $derived(data.apps.filter((a) => a.category?.startsWith('game_')).slice(0, 10));
	const topApps = $derived(data.apps.filter((a) => !a.category?.startsWith('game_')).slice(0, 10));

	// Creative modal state
	const creativeModal = createCreativeModal();
	const reportUrl = 'https://appgoblin.info/reports/ad-user-acquisition-2026-october';
	const reportPublishedDate = '2026-11-06';
	const reportTemporalCoverage = '2026-10-01/2026-10-31';

	function downloadSampleCsv() {
		const sample = data.advertisersSample;
		if (!sample || sample.length === 0) return;

		const columns = [
			'store_id',
			'app_name',
			'category',
			'developer',
			'report_period',
			'weekly_installs',
			'total_estimated_installs',
			'unique_publishers',
			'unique_creatives_count',
			'ad_networks',
			'mmp_providers',
			'estimated_buying_size_score'
		];

		const headerRow = columns.join(',');
		const dataRows = sample.map((row: Record<string, unknown>) =>
			columns
				.map((col) => {
					const val = row[col];
					if (val == null) return '';
					const str = String(val);
					return str.includes(',') || str.includes('"') ? `"${str.replace(/"/g, '""')}"` : str;
				})
				.join(',')
		);

		const csv = '\uFEFF' + [headerRow, ...dataRows].join('\n');
		const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `appgoblin-2026-october-top20-advertisers.csv`;
		a.click();
		URL.revokeObjectURL(url);
	}

	function formatWoWGrowth(num?: number | null): string {
		if (num == null) return '—';
		if (num > 500) {
			const multiplier = Math.round(num / 100);
			return `${multiplier}x`;
		}
		const sign = num > 0 ? '+' : '';
		return `${sign}${num.toFixed(0)}%`;
	}

	function getWoWGrowthColor(value?: number | null): string {
		if (value == null) return 'text-surface-400';
		if (value > 500) return 'text-success-600-400';
		if (value > 0) return 'text-success-800-200';
		if (value < 0) return 'text-rose-400';
		return 'text-surface-500';
	}

	function formatOptional(num?: number | null): string {
		return num == null ? '—' : String(formatNumber(num));
	}

	function formatRoundedOptional(num?: number | null): string {
		return num == null ? '—' : String(formatNumber(Math.round(num)));
	}

	function formatCurrency(num?: number | null): string {
		return num == null ? '—' : '$' + formatNumber(Math.round(num));
	}

	function formatWeekDate(dateStr?: string | null): string {
		if (!dateStr) return '—';
		if (dateStr.includes('T')) return dateStr.split('T')[0];
		return dateStr;
	}

	function getTierClass(tier: string): string {
		if (tier === 'Top') return 'bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300';
		if (tier === 'Big')
			return 'bg-surface-200 dark:bg-surface-700 text-surface-600 dark:text-surface-300';
		return 'bg-transparent text-surface-400';
	}

	const sectionTitleClass = 'text-2xl md:text-3xl font-bold text-surface-900-200';
	const sectionContainerClass = 'mb-20 pt-10 md:pt-12 border-t border-surface-200-800';
	const sectionHeaderSubtitleClass = 'text-sm md:text-base text-surface-600-400';
	const sectionHeaderBaseClass = 'my-4 md:my-6 p-3 md:p-4 border-t border-l-1';
	const sectionDescriptionClass = 'text-base md:text-lg space-y-3 md:space-y-4 mb-4 md:px-4';
	const sectionIntroRowClass = 'flex items-center gap-2 mb-4 md:mb-6';

	const publisherTextColor = 'font-bold text-primary-900-100';
	const creativesTextColor = 'font-bold text-secondary-900-100';
	const advertisersTextColor = 'font-bold text-success-900-100';
	const simpleMetricColor = 'text-base md:text-large text-surface-900-200';
	const sectionBodyClass = 'max-w-none mb-6';
	const paragraphClass = 'text-base md:text-lg leading-relaxed text-surface-800-300';
	const textMutedXsClass = 'text-xs text-surface-500-500';
	const textMutedXsCapClass = `${textMutedXsClass} capitalize`;
	const storeIdClass = `${textMutedXsClass} truncate max-w-[10rem] md:max-w-[16rem]`;
	const appLinkClass =
		'block text-xs md:text-lg font-semibold truncate max-w-[10rem] md:max-w-[16rem] text-surface-900-200';
	const tableRowClass =
		'border-b border-surface-200-800 hover:bg-surface-100-900 transition-colors';
	const tableAppIconClass =
		'w-9 h-9 sm:w-11 sm:h-11 lg:w-14 lg:h-14 rounded-lg shadow-sm flex-shrink-0';
	const cardTableWrapperClass = 'card overflow-hidden';
	const tableWrapperClass = 'report-table-shell report-table-scroll';
	const tableHeaderText = 'text-xs md:text-sm font-bold text-surface-900-200';
	const tableHeaderLeftClass = `px-1 md:px-2 py-2 ${tableHeaderText}`;
	const tableHeaderCenterClass = `px-1 md:px-2 py-2 ${tableHeaderText}`;
	const tableHeaderRightClass = `px-1 md:px-2 py-2 ${tableHeaderText}`;
	const companyButtonListClass = 'flex flex-wrap gap-0.5 md:gap-1';

	const metricGridClass = 'p-4 ';
	const subCardTextClass = 'text-surface-600-400';
	const tHeadClass = 'bg-surface-100-900';
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
	<meta
		property="og:image"
		content="https://appgoblin.info/previews/mobile_app_advertisers_report_july_2026.png"
	/>
	<meta
		property="og:image:alt"
		content="AppGoblin October 2026 mobile UA intelligence report preview"
	/>
	<meta property="article:published_time" content={reportPublishedDate} />
	<meta property="article:modified_time" content={new Date().toISOString().split('T')[0]} />
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content={data.title} />
	<meta name="twitter:description" content={data.description} />
	<meta
		name="twitter:image"
		content="https://appgoblin.info/previews/mobile_app_advertisers_report_july_2026.png"
	/>

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
					url: 'https://appgoblin.info/previews/mobile_app_advertisers_report_july_2026.png'
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
						description: 'Most-distributed video creatives in October 2026'
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
				name: 'October 2026 Mobile App Advertising Intelligence',
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
		<h1 class="text-3xl sm:text-4xl md:text-5xl font-bold mb-4 text-primary-600-400">
			Mobile UA Report - {data.summary.reportPeriod}
		</h1>
		<p class="text-base sm:text-lg md:text-xl max-w-3xl mx-auto text-surface-700-400">
			AppGoblin's free report shares the top mobile apps buying ads in October 2026. See which
			mobile ad networks were most popular for user acquisiton.
		</p>
	</div>

	<!-- Top CSV Download Banner -->
	<div class="mb-10 border border-primary-500 p-4 md:p-5">
		<div class="flex flex-col gap-3">
			<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
				<div class="flex items-center gap-2 min-w-0">
					<Crown class="w-5 h-5 shrink-0 text-primary-600-400" aria-hidden="true" />
					<p class="font-semibold text-surface-900-200 truncate">Full Advertiser CSV</p>
					<p>
						See the top {formatNumber(data.summary.advertisers)} apps that were buying mobile ads and
						running UA campaigns in October 2026.
					</p>
				</div>
				{#if data.hasB2BAccess}
					<a
						href="/reports/ad-user-acquisition-2026-october/advertisers-csv"
						class="btn preset-filled-primary-500 inline-flex items-center gap-2 p-2 text-sm shrink-0"
					>
						<Crown class="w-5 h-5 shrink-0" aria-hidden="true" />
						<span class="text-black">Download CSV</span>
						<span class="text-black">↓</span>
					</a>
				{:else}
					<a
						href="/pricing"
						class="btn preset-outlined-primary-500 inline-flex items-center gap-2 p-2 text-sm shrink-0"
					>
						<Lock class="w-3.5 h-3.5" aria-hidden="true" />
						<span>Full CSV - B2B Only</span>
					</a>
				{/if}
			</div>
			<div
				class="border-t border-primary-500/20 pt-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
			>
				<div class="flex items-center gap-2 min-w-0">
					<p class="text-sm text-surface-600-400">Free sample — top 20 advertisers</p>
				</div>
				<button
					onclick={downloadSampleCsv}
					class="btn preset-outlined-primary-500 inline-flex items-center gap-2 p-2 text-sm shrink-0"
					disabled={!data.advertisersSample || data.advertisersSample.length === 0}
				>
					<span>Download Top 20 Sample</span>
					<span>↓</span>
				</button>
			</div>
		</div>
	</div>

	<div class="mb-12 p-5">
		<div class="grid grid-cols-1 xl:grid-cols-12 gap-5 md:gap-6 xl:items-stretch">
			<div class="space-y-4 xl:col-span-4">
				<div class="rounded-lg preset-outlined-primary-500 p-4">
					<h2 class="text-xl md:text-3xl font-bold leading-tight">October 2026 Top Ad Buyers</h2>
				</div>

				<div class="rounded-lg border border-surface-200-800 p-2 md:px-4">
					<div class="text-base md:text-lg font-semibold mb-3">Top Game Advertisers</div>
					<div
						class="grid grid-cols-5 sm:grid-cols-3 md:grid-cols-10 xl:grid-cols-5 gap-1 md:gap-2"
					>
						{#each topGames as app}
							<a href="/apps/{app.store_id}" class="group" title={app.app_name}>
								<img
									src="https://media.appgoblin.info/app-icons/{app.store_id}/{app.icon_128}"
									alt={app.app_name}
									class="w-12 h-12 sm:w-14 sm:h-14 lg:w-18 lg:h-18 rounded-xl group-hover:scale-105 transition-transform"
									onerror={(e) =>
										((e.currentTarget as HTMLImageElement).src = '/default_company_logo.png')}
								/>
							</a>
						{/each}
					</div>

					<div class="text-base md:text-lg font-semibold mt-3 mb-1">Top App Advertisers</div>
					<div class="grid grid-cols-5 sm:grid-cols-3 xl:grid-cols-5 gap-1 md:gap-2">
						{#each topApps as app}
							<a href="/apps/{app.store_id}" class="group" title={app.app_name}>
								<img
									src="https://media.appgoblin.info/app-icons/{app.store_id}/{app.icon_128}"
									alt={app.app_name}
									class="w-12 h-12 sm:w-14 sm:h-14 md:w-18 md:h-18 rounded-xl group-hover:scale-105 transition-transform"
									onerror={(e) =>
										((e.currentTarget as HTMLImageElement).src = '/default_company_logo.png')}
								/>
							</a>
						{/each}
					</div>

					<div class="text-base md:text-lg font-semibold mt-3 mb-1">Ad Networks</div>
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
					<div class="rounded-lg bg-primary-100-900 p-3 shadow-sm">
						<div class="text-xl md:text-2xl font-bold">
							{formatOptional(data.summary.totalApps)}
						</div>
						<div class="text-sm font-bold">Apps</div>
					</div>
					<div class="rounded-lg bg-secondary-100-900 p-3 shadow-sm">
						<div class="text-xl md:text-2xl font-bold">
							{formatOptional(data.summary.advertisers)}
						</div>
						<div class="text-sm font-bold">Advertisers</div>
					</div>
					<div class="rounded-lg bg-primary-100-900 p-3 shadow-sm">
						<div class="text-xl md:text-2xl font-bold">
							{formatOptional(data.summary.adtechCompanies)}
						</div>
						<div class="text-sm font-bold">Ad Platforms</div>
					</div>
				</div>
			</div>

			<div class="xl:col-span-6">
				<div class="featured-creatives-strip">
					{#each [data.popularCreatives[0], data.popularCreatives[2], data.popularCreatives[3]] as creative, index}
						<div class="featured-creative-slide">
							<PopularCreativeCard
								{creative}
								{index}
								titlePrefix="October Featured Creative"
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
			<div class={`${sectionHeaderBaseClass}`}>
				<h2 class={sectionTitleClass}>Summary</h2>
				<p class={sectionHeaderSubtitleClass}>
					Key findings and performance overview for {data.summary.reportPeriod}
				</p>
			</div>

			<!-- Content -->
			<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-8 px-2 md:px-4">
				{#if data.advertiserCountries && data.advertiserCountries.length > 0}
					<div class="order-2 lg:order-2">
						<p class="text-sm text-surface-500-400 mb-2">Advertiser HQ Countries</p>
						<AdvertiserCountryPie plotData={data.advertiserCountries} plotHeightPx={300} />
					</div>
				{/if}
				<div class="order-1 lg:order-1 max-w-none">
					<p class={paragraphClass}>
						In {data.summary.reportPeriod}, AppGoblin analyzed the advertising creatives and
						campaigns from
						<strong class={publisherTextColor}>
							{formatNumber(data.summary.totalApps)} mobile apps
						</strong>. This report focuses on mobile apps that bought ads via programmatic and SDK
						mobile app ad networks.
					</p>
					<p class={`${paragraphClass} mt-4`}>
						The ad campaigns spanned
						<strong class="">
							{formatNumber(data.summary.adtechCompanies)} AdTech platforms
						</strong>
						with
						<strong class={advertisersTextColor}>
							{formatNumber(data.summary.advertisers)} app advertisers
						</strong>
						using
						<strong class={creativesTextColor}>
							{formatNumber(data.summary.totalCreatives)} creative assets (image and video)
						</strong>
						on ad campaigns that saw some apps with correlated
						<strong class="">{data.summary.avgGrowth}% week on week installs growth </strong>.
					</p>
					<p class={`${paragraphClass} mt-4`}>
						In October the advertising spend tracked by AppGoblin was spent heavily by Vietnam,
						China and US app publishers.
					</p>
				</div>
			</div>
		</div>
	</div>

	<!-- ========================================= -->
	<!-- SECTION 2: AD IMPACT ON INSTALLS -->
	<!-- ========================================= -->
	<div class={sectionContainerClass}>
		<div class={`${sectionHeaderBaseClass}`}>
			<h2 class={sectionTitleClass}>Advertising Apps that saw the Best Weekly Install Growth</h2>
			<p class={sectionHeaderSubtitleClass}>
				These apps saw the best week on week install growth while at the same time running ad
				campaigns.
			</p>
		</div>
		<div class={sectionDescriptionClass}>
			<p>Weather and Makeover games were popping this month with two of each in the top 10.</p>
			<p class="mt-2">
				A Nigeraian developer GLADYS GLOBAL's casual makeover game <span class={publisherTextColor}
					>{data.apps[1].app_name}</span
				> had explosive growth early in October.
			</p>
			<p>
				El Nino news was huge in October 2026 leading to two Weather apps seeing high Week on Week
				growth, lead by <span class={publisherTextColor}>{data.apps[5].app_name}</span>.
			</p>
		</div>
		<div class={cardTableWrapperClass}>
			<div class={tableWrapperClass}>
				<table class="report-table report-table--apps w-full">
					<thead class={tHeadClass}>
						<tr>
							<th class={tableHeaderLeftClass}>Rank</th>
							<th class={tableHeaderLeftClass}>App</th>
							<th class={`${tableHeaderCenterClass} hidden lg:table-cell`}>Country</th>
							<th class={`${tableHeaderLeftClass} hidden md:table-cell`}>Best Week</th>
							<th class={tableHeaderRightClass}>Installs (week)</th>
							<th class={`${tableHeaderRightClass} hidden lg:table-cell`}>WoW Growth</th>
							<th class={`${tableHeaderRightClass} hidden xl:table-cell`}>Rev. Est.</th>
							<th class={`${tableHeaderRightClass} hidden xl:table-cell`}>MAU</th>
							<th class={tableHeaderCenterClass}>Ad Creatives</th>
							<th class={tableHeaderCenterClass}>Ad Networks</th>
							<th class={`${tableHeaderCenterClass} hidden lg:table-cell`}>MMP</th>
						</tr>
					</thead>
					<tbody>
						{#each data.apps as app, index}
							<tr class={tableRowClass}>
								<td class="px-1 md:px-4 py-2 md:py-4 text-center">
									<RankBadge rank={index + 1} />
								</td>
								<td class="px-1 md:px-4 py-2 md:py-4">
									<a href="/apps/{app.store_id}" class="flex items-center gap-2 md:gap-3 min-w-0">
										<img
											src="https://media.appgoblin.info/app-icons/{app.store_id}/{app.icon_128}"
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
								<td class="hidden lg:table-cell px-1 md:px-4 py-2 md:py-4 text-center">
									{#if app.advertiser_country}
										<CountryFlag code={app.advertiser_country} />
									{:else}
										<span class="text-xs text-surface-400">—</span>
									{/if}
								</td>
								<td
									class="hidden md:table-cell px-1 md:px-4 py-2 md:py-4 text-right whitespace-nowrap"
								>
									<div class={`text-xs md:text-lg ${simpleMetricColor}`}>
										{formatWeekDate(app.best_week)}
									</div>
								</td>
								<td class="px-1 md:px-4 py-2 md:py-4 text-right">
									<div class={`text-xs md:text-lg ${simpleMetricColor}`}>
										{formatNumber(app.weekly_installs)}
									</div>
									<div class={textMutedXsClass}>
										Base {formatRoundedOptional(app.baseline_installs)}
									</div>
								</td>
								<td
									class="hidden lg:table-cell px-1 md:px-4 py-2 md:py-4 text-right whitespace-nowrap"
								>
									<div class={`text-xs md:text-lg ${getWoWGrowthColor(app.wow_growth_pct)}`}>
										{formatWoWGrowth(app.wow_growth_pct)}
									</div>
								</td>
								<td
									class="hidden xl:table-cell px-1 md:px-4 py-2 md:py-4 text-right whitespace-nowrap"
								>
									<div class={`text-xs md:text-lg ${simpleMetricColor}`}>
										{formatCurrency(app.weekly_revenue_estimate)}
									</div>
								</td>
								<td
									class="hidden xl:table-cell px-1 md:px-4 py-2 md:py-4 text-right whitespace-nowrap"
								>
									<div class={`text-xs md:text-lg ${simpleMetricColor}`}>
										{formatOptional(app.monthly_active_users)}
									</div>
								</td>
								<td class="px-1 md:px-4 py-2 md:py-4 text-center">
									<div class="flex justify-center items-center gap-1">
										{#each app.creatives.slice(0, 3) as creative}
											<a
												href="/apps/{app.store_id}/ad-placements"
												class="relative group hover:scale-110 transition-transform duration-200"
												title="View ad placements for {app.app_name}"
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
											</a>
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
		<div class={`${sectionHeaderBaseClass}`}>
			<h2 class={sectionTitleClass}>Most Popular Video Creatives</h2>
			<p class={sectionHeaderSubtitleClass}>
				Video ads with the widest mobile app distribution during {data.summary.reportPeriod}
			</p>
		</div>
		<!-- Content -->
		<div class={sectionDescriptionClass}>
			<p>
				The most widely distributed video creatives AppGoblin tracked in October belonged to a a
				dominoes game by Australian developer Savy Soda and seen on
				<strong class="text-pink-600">{data.popularCreatives[0].publisher_count}+ publishers</strong
				>.
			</p>
			<p>
				<strong class="text-pink-600">{data.popularCreatives[1].advertiser_name}</strong> had multiple
				creatives shown across dozens of publishers.
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
		<div class={`${sectionHeaderBaseClass}`}>
			<h2 class={sectionTitleClass}>Ad Network Landscape</h2>
			<p class={sectionHeaderSubtitleClass}>
				The advertising platforms that powered {data.summary.reportPeriod} user acquisition campaigns
			</p>
		</div>
		<!-- Network Metrics Grid -->
		<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
			<div class={metricGridClass}>
				<div class={`mb-1`}>Publishers Apps That Ran Ads</div>
				<div class="text-3xl font-bold">
					{data.networkStats.totalPublishers.toLocaleString()}
				</div>
			</div>
			<div class={metricGridClass}>
				<div class={`${subCardTextClass} mb-1`}>App Advertisers</div>
				<div class="text-3xl font-bold">
					{data.summary.advertisers.toLocaleString()}
				</div>
			</div>
			<div class={metricGridClass}>
				<div class={`${subCardTextClass} mb-1`}>Ad Creatives (video & images)</div>
				<div class="text-3xl font-bold">
					{data.networkStats.totalNetworkCreatives.toLocaleString()}
				</div>
			</div>
		</div>
		<!-- Content -->
		<div class={sectionDescriptionClass}>
			<p>
				<a href="/companies/affle.com">Affle</a> again took a top spot. Looking deeper it looks like
				it's subsidiary <a href="/companies/jampp.com">Jampp</a> and
				<a href="/companies/youappi.com">YouAppi</a> were driving the growth with solid 10% quarterly
				growth each.
			</p>
			<p>
				LiftOff <a href="/companies/liftoff.io">Liftoff</a> was back in the top 10 as well with solid
				growth in observed published app ads.
			</p>
		</div>
		<div class={sectionDescriptionClass}>
			<p>Note on Methodology</p>
			<p class="text-sm">
				When looking at this data its important to keep the context of how it was collected. The
				data is aggregated from API calls made by opening apps and watching the ad network
				connections. As such, this does not include App Store advertising (Apple/Google) or social
				media ads (TikTok/Facebook/Instagram). Facebook Audience Network (FAN) is included, but as
				it is quite small it didn't make the top 10.
			</p>
		</div>
		<br />
		<!-- Top Networks Cards -->
		<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-2 md:gap-6">
			{#each data.adNetworks as network, index}
				<!-- Network Header -->
				<div class="card p-4 border border-surface-200-800 flex flex-col">
					<a
						href="/companies/{network.ad_network_domain}"
						class="hover:border-primary-400-600 transition-all duration-200 hover:shadow-lg"
					>
						<div class="flex items-center gap-3 mb-4">
							<img
								src="https://media.appgoblin.info/{network.company_logo_url}"
								alt={network.ad_network_name}
								class="w-8 h-8 md:w-18 md:h-18 rounded-lg border border-surface-200-800 shadow-sm shrink-0"
								onerror={(e) =>
									((e.currentTarget as HTMLImageElement).src = '/default_company_logo.png')}
							/>
							<div class="min-w-0 flex-1">
								<div class="text-base font-bold truncate text-surface-900-200">
									{network.ad_network_name}
								</div>
								{#if network.domains && network.domains.length > 0}
									<div class="text-xs text-surface-500-500 truncate">
										{network.domains.slice(0, 2).join(', ')}
										{#if network.domains.length > 2}
											<span class="text-surface-400">+{network.domains.length - 2}</span>
										{/if}
									</div>
								{:else}
									<div class="text-xs text-surface-500-500 truncate">
										{network.ad_network_domain}
									</div>
								{/if}
							</div>
							<RankBadge
								rank={index + 1}
								class="shrink-0"
								numberClass="text-sm font-semibold text-surface-500-400"
							/>
						</div>
					</a>

					<!-- Stats Grid -->
					<div class="grid grid-cols-2 gap-3 mb-3">
						<div class="flex flex-col">
							<div class="text-sm mb-1">Publishers</div>
							<div>
								{network.publisher_count.toLocaleString()}
							</div>
						</div>
						<div class="flex flex-col">
							<div class="text-sm mb-1">Advertisers Tracked</div>
							<div>
								{network.advertiser_count.toLocaleString()}
							</div>
						</div>
					</div>

					<!-- Market Share -->
					<div class="pt-3 border-t border-surface-200-800 text-sm">
						<div class="flex items-center justify-between mb-2">
							<span>Market Share</span>
							<span>
								{((network.publisher_count / data.networkStats.totalPublishers) * 100).toFixed(1)}%
							</span>
						</div>

						<!-- Creatives Count -->
						<div class="mt-3 flex items-center justify-between">
							<span class="">Ad Creatives</span>
							<span class="">
								{network.creatives_count.toLocaleString()}
							</span>
						</div>
					</div>
				</div>
			{/each}
		</div>
	</div>

	<!-- ========================================= -->
	<!-- SECTION 5: CAMPAIGN REACH ANALYSIS -->
	<!-- ========================================= -->
	<div class={sectionContainerClass}>
		<!-- Section Header -->
		<div class={`${sectionHeaderBaseClass}`}>
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
				creative across the widest publisher footprint in October 2026.
			</p>
		</div>
		<!-- Top Apps by Publisher Reach -->
		<div class={`mt-6 ${cardTableWrapperClass}`}>
			<div class={tableWrapperClass}>
				<table class="report-table report-table--reach w-full">
					<thead class={tHeadClass}>
						<tr>
							<th class={tableHeaderLeftClass}>Rank</th>
							<th class={tableHeaderLeftClass}>Advertising App</th>
							<th class={tableHeaderRightClass}>Count of Apps with their Ads</th>
							<th class={tableHeaderRightClass}>Ad Creatives</th>
							<th class={`${tableHeaderRightClass} hidden lg:table-cell`}>Buying Power</th>
							<th class={tableHeaderLeftClass}>Ad Networks</th>
							<th class={`${tableHeaderCenterClass} hidden lg:table-cell`}>MMP</th>
						</tr>
					</thead>
					<tbody>
						{#each data.appReachData.slice(0, 10) as app, index}
							<tr class={tableRowClass}>
								<td class="px-1 md:px-2 py-2 md:py-4 text-center">
									<RankBadge rank={index + 1} />
								</td>
								<td class="px-1 md:px-2 py-2 md:py-4">
									<a
										href="/apps/{app.advertiser_store_id}"
										class="flex items-center gap-2 md:gap-3 min-w-0"
									>
										<img
											src="https://media.appgoblin.info/app-icons/{app.advertiser_store_id}/{app.advertiser_icon_128}"
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
								<td
									class="hidden lg:table-cell px-1 md:px-2 py-2 md:py-4 text-center whitespace-nowrap"
								>
									<span
										class="inline-block px-2 py-0.5 rounded text-xs font-bold {getTierClass(
											app.buying_size_tier
										)}"
									>
										{app.buying_size_tier}
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
	<!-- SECTION 6: NEW APPS THIS MONTH -->
	<!-- ========================================= -->
	<div class={sectionContainerClass}>
		<div class={`${sectionHeaderBaseClass}`}>
			<h2 class={sectionTitleClass}>Newly Released Apps that were Buying Ads in October 2026</h2>
			<p class={sectionHeaderSubtitleClass}>
				Brand new apps starting off running ad campaigns during {data.summary.reportPeriod}
			</p>
		</div>
		<div class={sectionDescriptionClass}>
			<p>
				These apps were released recently, not necessarily in October, but at least in the months
				preceeding.
			</p>
		</div>

		<!-- Games Sub-section -->
		{#if data.newGames.length > 0}
			<div class="mb-8">
				<h4 class="text-xl font-bold mb-4 flex items-center gap-2">
					<span class="text-sky-900 dark:text-sky-100">New Games</span>
					<span class="text-sm font-normal text-surface-500 dark:text-surface-400">
						({Math.min(data.newGames.length, 8)} titles)
					</span>
				</h4>
				<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
					{#each data.newGames.slice(0, 8) as app (app.store_id)}
						<div
							class="card p-4 md:p-5 border border-surface-200-800 hover:border-primary-400-600 transition-all duration-200 hover:shadow-lg flex flex-col"
						>
							<!-- Card Header -->
							<a href="/apps/{app.store_id}" class="flex items-center gap-3 mb-3 group">
								{#if app.icon_128}
									<img
										src="https://media.appgoblin.info/app-icons/{app.store_id}/{app.icon_128}"
										alt={app.name}
										class="w-14 h-14 md:w-16 md:h-16 rounded-xl border border-surface-200 dark:border-surface-700 shadow-sm shrink-0"
										onerror={(e) =>
											((e.currentTarget as HTMLImageElement).src = '/default_company_logo.png')}
									/>
								{:else}
									<img
										src="/default_company_logo.png"
										alt={app.name}
										class="w-14 h-14 md:w-16 md:h-16 rounded-xl border border-surface-200 dark:border-surface-700 shadow-sm shrink-0"
									/>
								{/if}
								<div class="min-w-0">
									<div
										class="text-base md:text-lg font-bold truncate group-hover:underline text-surface-800-200"
									>
										{app.name}
									</div>
									<div class="text-xs md:text-sm text-surface-500 dark:text-surface-400 truncate">
										{app.store_id}
									</div>
								</div>
							</a>

							<!-- Stats Row -->
							<div class="flex items-center gap-3 text-sm md:text-lg mb-3">
								{#if app.installs}
									<span class="font-bold text-emerald-400">
										{formatNumber(app.installs)} installs
									</span>
									<span class="text-surface-500">·</span>
								{/if}
								<span class="text-surface-600 dark:text-surface-400 text-sm md:text-base">
									released: {app.release_date ? app.release_date.split('T')[0] : '—'}
								</span>
								{#if app.advertiser_country}
									<span class="text-surface-500">·</span>
									<CountryFlag code={app.advertiser_country} />
								{/if}
							</div>

							<!-- Creatives Thumbnails -->
							{#if app.md5_hashes && app.md5_hashes.length > 0}
								<div class="mt-auto pt-3 border-t border-surface-200 dark:border-surface-700">
									<div class="text-sm font-semibold text-surface-600 dark:text-surface-400 mb-2">
										{app.creative_count} creative{app.creative_count !== 1 ? 's' : ''}
									</div>
									<div class="flex flex-wrap gap-1.5">
										{#each app.md5_hashes.slice(0, 3) as md5_hash, ci}
											{@const fileExt = app.md5_file_extensions?.[ci] ?? 'mp4'}
											<button
												onclick={() =>
													creativeModal.open(
														`https://media.appgoblin.info/creatives/raw/${md5_hash.substring(0, 3)}/${md5_hash}.${fileExt}`,
														app.name
													)}
												class="relative group cursor-pointer hover:scale-110 transition-transform duration-200"
												title="Click to view creative"
											>
												<div
													class="w-16 h-16 md:w-20 md:h-20 rounded-lg border border-surface-300 dark:border-surface-600 overflow-hidden group-hover:border-sky-500"
												>
													<img
														src="https://media.appgoblin.info/creatives/thumbs/{md5_hash}.jpg"
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
										{#if app.md5_hashes.length > 4}
											<button
												onclick={() =>
													creativeModal.open(
														`https://media.appgoblin.info/creatives/raw/${app.md5_hashes[4].substring(0, 3)}/${app.md5_hashes[4]}.${app.md5_file_extensions?.[4] ?? 'mp4'}`,
														app.name
													)}
												class="w-16 h-16 md:w-20 md:h-20 rounded-lg border border-dashed border-surface-300 dark:border-surface-600 flex items-center justify-center text-xs font-semibold text-surface-500 hover:border-sky-500 hover:text-sky-500 transition-colors"
												title="View all creatives"
											>
												+{app.md5_hashes.length - 4}
											</button>
										{/if}
									</div>
								</div>
							{/if}

							<!-- Ad Networks -->
							<div class="mt-3">
								<div class="text-sm font-semibold text-surface-600 dark:text-surface-400 mb-1.5">
									Ad Networks
								</div>
								<div class={companyButtonListClass}>
									{#each app.ad_networks.slice(0, 3) as network}
										<CompanyButton
											companyDomain={network.domain}
											companyLogoUrl={network.logo_url}
											size="logo-only"
										/>
									{/each}
									{#if app.ad_networks.length > 3}
										<span class={`${textMutedXsClass} font-semibold`}
											>+{app.ad_networks.length - 3}</span
										>
									{/if}
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<!-- Apps Sub-section -->
		{#if data.newApps.length > 0}
			<div>
				<h4 class="text-xl font-bold mb-4 flex items-center gap-2">
					<span class="text-sky-900 dark:text-sky-100">New Apps (Not Games)</span>
					<span class="text-sm font-normal text-surface-500 dark:text-surface-400">
						({Math.min(data.newApps.length, 8)} titles)
					</span>
				</h4>
				<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
					{#each data.newApps.slice(0, 8) as app (app.store_id)}
						<div
							class="card p-4 md:p-5 border border-surface-200-800 hover:border-secondary-400-600 transition-all duration-200 hover:shadow-lg flex flex-col"
						>
							<!-- Card Header -->
							<a href="/apps/{app.store_id}" class="flex items-center gap-3 mb-3 group">
								{#if app.icon_128}
									<img
										src="https://media.appgoblin.info/app-icons/{app.store_id}/{app.icon_128}"
										alt={app.name}
										class="w-14 h-14 md:w-16 md:h-16 rounded-xl border border-surface-200 dark:border-surface-700 shadow-sm shrink-0"
										onerror={(e) =>
											((e.currentTarget as HTMLImageElement).src = '/default_company_logo.png')}
									/>
								{:else}
									<img
										src="/default_company_logo.png"
										alt={app.name}
										class="w-14 h-14 md:w-16 md:h-16 rounded-xl border border-surface-200 dark:border-surface-700 shadow-sm shrink-0"
									/>
								{/if}
								<div class="min-w-0">
									<div
										class="text-base md:text-lg font-bold truncate group-hover:underline text-surface-800-200"
									>
										{app.name}
									</div>
									<div class="text-xs md:text-sm text-surface-500 dark:text-surface-400 truncate">
										{app.store_id}
									</div>
								</div>
							</a>

							<!-- Stats Row -->
							<div class="flex items-center gap-3 text-sm md:text-lg mb-3">
								{#if app.installs}
									<span class="font-bold text-purple-400">
										{formatNumber(app.installs)} installs
									</span>
									<span class="text-surface-500">·</span>
								{/if}
								<span class="text-surface-600 dark:text-surface-400 text-sm md:text-base">
									{app.release_date ? app.release_date.split('T')[0] : '—'}
								</span>
								{#if app.advertiser_country}
									<span class="text-surface-500">·</span>
									<CountryFlag code={app.advertiser_country} />
								{/if}
							</div>

							<!-- Ad Networks -->
							<div class="mb-3">
								<div class="text-sm font-semibold text-surface-600 dark:text-surface-400 mb-1.5">
									Ad Networks
								</div>
								<div class={companyButtonListClass}>
									{#each app.ad_networks.slice(0, 3) as network}
										<CompanyButton
											companyDomain={network.domain}
											companyLogoUrl={network.logo_url}
											size="logo-only"
										/>
									{/each}
									{#if app.ad_networks.length > 3}
										<span class={`${textMutedXsClass} font-semibold`}
											>+{app.ad_networks.length - 3}</span
										>
									{/if}
								</div>
							</div>

							<!-- Creatives Thumbnails -->
							{#if app.md5_hashes && app.md5_hashes.length > 0}
								<div class="mt-auto pt-3 border-t border-surface-200 dark:border-surface-700">
									<div class="text-sm font-semibold text-surface-600 dark:text-surface-400 mb-2">
										{app.creative_count} creative{app.creative_count !== 1 ? 's' : ''}
									</div>
									<div class="flex flex-wrap gap-1.5">
										{#each app.md5_hashes.slice(0, 4) as md5_hash, ci}
											{@const fileExt = app.md5_file_extensions?.[ci] ?? 'mp4'}
											<button
												onclick={() =>
													creativeModal.open(
														`https://media.appgoblin.info/creatives/raw/${md5_hash.substring(0, 3)}/${md5_hash}.${fileExt}`,
														app.name
													)}
												class="relative group cursor-pointer hover:scale-110 transition-transform duration-200"
												title="Click to view creative"
											>
												<div
													class="w-16 h-16 md:w-20 md:h-20 rounded-lg border border-surface-300 dark:border-surface-600 overflow-hidden group-hover:border-sky-500"
												>
													<img
														src="https://media.appgoblin.info/creatives/thumbs/{md5_hash}.jpg"
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
										{#if app.md5_hashes.length > 4}
											<button
												onclick={() =>
													creativeModal.open(
														`https://media.appgoblin.info/creatives/raw/${app.md5_hashes[4].substring(0, 3)}/${app.md5_hashes[4]}.${app.md5_file_extensions?.[4] ?? 'mp4'}`,
														app.name
													)}
												class="w-16 h-16 md:w-20 md:h-20 rounded-lg border border-dashed border-surface-300 dark:border-surface-600 flex items-center justify-center text-xs font-semibold text-surface-500 hover:border-sky-500 hover:text-sky-500 transition-colors"
												title="View all creatives"
											>
												+{app.md5_hashes.length - 4}
											</button>
										{/if}
									</div>
								</div>
							{/if}
						</div>
					{/each}
				</div>
			</div>
		{/if}
	</div>

	<!-- CTA Section -->
	<div class={sectionContainerClass}>
		<div class={`${sectionHeaderBaseClass} pl-4 border-l-1`}>
			<h2 class={sectionTitleClass}>Want to leverage AppGoblin's insights?</h2>
			<p class={sectionHeaderSubtitleClass}>AppGoblin B2B app and company intel</p>
		</div>

		<!-- Content -->
		<div class={sectionDescriptionClass}>
			<div
				class="rounded-xl border border-primary-500/30 bg-gradient-to-br from-primary-500/5 to-secondary-500/5 p-5 md:p-6 mt-6"
			>
				<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
					<div>
						<h3 class="text-lg font-bold text-primary-900-100 flex items-center gap-2">
							<Crown class="w-5 h-5 text-primary-900-100" aria-hidden="true" />
							B2B Intelligence — Advertiser CSV
						</h3>
						<p class="text-sm text-surface-600 dark:text-surface-300 mt-1">
							Top {formatNumber(data.summary.advertisers)} advertisers we tracked in {data.summary
								.reportPeriod} with estimated buying size, ad networks, publisher reach, and creative
							counts — one row per advertiser.
						</p>
					</div>
					{#if data.hasB2BAccess}
						<a
							href="/reports/ad-user-acquisition-2026-october/advertisers-csv"
							class="btn preset-filled-primary-500 inline-flex items-center gap-2 p-3 shrink-0"
						>
							<span class="text-black">Download CSV</span>
							<span class="text-black">↓</span>
						</a>
					{:else}
						<a
							href="/pricing"
							class="btn preset-outlined-primary-500 inline-flex items-center gap-2 p-3 shrink-0"
						>
							<Lock class="w-4 h-4" aria-hidden="true" />
							<span>Full CSV - B2B only</span>
						</a>
					{/if}
				</div>

				<div class="border-t border-primary-500/20 pt-4 mt-2">
					<p
						class="text-xs font-semibold text-surface-500 dark:text-surface-400 uppercase tracking-wide mb-3"
					>
						CSV Columns
					</p>
					<div
						class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-1.5 text-xs md:text-sm"
					>
						<div class="flex gap-2">
							<span class="font-mono font-semibold shrink-0">store_id</span><span
								class="text-surface-500 dark:text-surface-400">App store bundle ID</span
							>
						</div>
						<div class="flex gap-2">
							<span class="font-mono font-semibold shrink-0">app_name</span><span
								class="text-surface-500 dark:text-surface-400">App name</span
							>
						</div>
						<div class="flex gap-2">
							<span class="font-mono font-semibold shrink-0">category</span><span
								class="text-surface-500 dark:text-surface-400">App category</span
							>
						</div>
						<div class="flex gap-2">
							<span class="font-mono font-semibold shrink-0">developer</span><span
								class="text-surface-500 dark:text-surface-400">Developer name</span
							>
						</div>
						<div class="flex gap-2">
							<span class="font-mono font-semibold shrink-0">report_period</span><span
								class="text-surface-500 dark:text-surface-400">October 2026</span
							>
						</div>
						<div class="flex gap-2">
							<span class="font-mono font-semibold shrink-0">weekly_installs</span><span
								class="text-surface-500 dark:text-surface-400"
								>Peak weekly installs (max across October)</span
							>
						</div>
						<div class="flex gap-2">
							<span class="font-mono font-semibold shrink-0">total_estimated_installs</span><span
								class="text-surface-500 dark:text-surface-400">Lifetime estimated installs</span
							>
						</div>
						<div class="flex gap-2">
							<span class="font-mono font-semibold shrink-0">unique_publishers</span><span
								class="text-surface-500 dark:text-surface-400"
								>Publisher apps running their ads</span
							>
						</div>
						<div class="flex gap-2">
							<span class="font-mono font-semibold shrink-0">unique_creatives_count</span><span
								class="text-surface-500 dark:text-surface-400">Unique ad creatives tracked</span
							>
						</div>
						<div class="flex gap-2">
							<span class="font-mono font-semibold shrink-0">ad_networks</span><span
								class="text-surface-500 dark:text-surface-400"
								>Ad networks used (semicolon-separated)</span
							>
						</div>
						<div class="flex gap-2">
							<span class="font-mono font-semibold shrink-0">mmp_providers</span><span
								class="text-surface-500 dark:text-surface-400">MMP/attribution providers</span
							>
						</div>
						<div class="flex gap-2">
							<span class="font-mono font-semibold shrink-0">estimated_buying_size_score</span><span
								class="text-surface-500 dark:text-surface-400"
								>Our rough estimate of ad buying scale</span
							>
						</div>
					</div>
				</div>

				<div class="border-t border-primary-500/20 pt-4 mt-2">
					<p
						class="text-xs font-semibold text-surface-500 dark:text-surface-400 uppercase tracking-wide mb-3"
					>
						B2B Premium Advertisers API
					</p>
					<p class="text-sm text-surface-600 dark:text-surface-300">
						All advertisers, creatives, ad networks, and MMP data from this report are also
						available programmatically via the
						<a href="/api-docs" class="font-semibold underline hover:text-primary-500"
							>AppGoblin B2B Premium Advertisers API</a
						>. Query individual advertisers, filter by ad network, category, country, or buying size
						— ideal for integrating UA intelligence into your own dashboards and workflows.
					</p>
				</div>
			</div>

			<div class="flex flex-wrap items-center justify-center gap-3 mt-6">
				<a
					href="/auth/signup"
					class="btn preset-filled-primary-500 inline-flex items-center gap-2 p-3"
				>
					<span class="text-black">Create Free Account</span>
					<span class="text-black">→</span>
				</a>
				<a
					href="/pricing"
					class="btn preset-outlined-primary-500 inline-flex items-center gap-2 p-3"
				>
					<span>View Pricing</span>
					<span>→</span>
				</a>
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

		.report-table--new-apps {
			min-width: 42rem;
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
			height: 80%;
		}
	}
</style>
