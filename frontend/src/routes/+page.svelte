<script lang="ts">
	import { onMount } from 'svelte';
	import AppRankTableShort from '$lib/AppRankTableShort.svelte';
	import CompaniesBarChart from '$lib/CompaniesBarChart.svelte';
	import AdvertiserCreativeRankingsTableTop from '$lib/AdvertiserCreativeRankingsTableTop.svelte';
	import { formatNumber } from '$lib/utils/formatNumber.js';
	import {
		ClipboardList,
		TrendingUp,
		Layers,
		ChartNoAxesColumnIncreasing,
		Smartphone,
		Gamepad2,
		Sparkles,
		Zap,
		Calendar,
		Star
	} from 'lucide-svelte';

	let { data } = $props();

	const description =
		'Mobile app and ad intelligence platform with free ASO tools, SDK and API analysis, app-ads.txt intelligence, and paid data exports for growth, sales prospecting, and fraud detection teams.';

	const title = 'AppGoblin Free App Marketing Tools';

	const featureBulletClass = 'text-sm md:text-lg font-medium';
	const sectionTitleClass = 'text-2xl transition-colors';
	const sectionSubtitleClass = 'text-primary-800-200 font-medium';
	const sectionDescriptionClass = 'mb-6';
	const subSectionClass = 'p-4';
	const cardTitleClass = 'text-lg font-bold transition-colors';
	const cardDescriptionClass = 'text-sm text-gray-400 mb-4';
	const coreFeatureBulletSpanClass = 'text-primary-900-100/80 font-medium';
	const featureCtaClass = 'btn px-3 py-1.5 bg-primary-300-700 font-medium';
	const exampleAnchorClass =
		'text-xs md:text-md px-2 py-1 rounded-md bg-secondary-900-100/10 hover:bg-secondary-50-950/50';
	const mainSectionClass =
		'card p-4 md:p-8 rounded-2xl shadow-xl border border-secondary-900-100/20';

	// Get current month and year for display
	const now = new Date();
	const monthYear = now.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

	type DashboardHighlight = {
		kicker: string;
		title: string;
		description: string;
		points: string[];
		href: string;
		cta: string;
		imageLight: string;
		imageDark: string;
		imageAlt: string;
	};

	const dashboardHighlights: DashboardHighlight[] = [
		{
			kicker: 'Competitor app intelligence',
			title: 'Analyze Competitor Apps',
			description: 'See growth, monetization, creatives, and store performance in one place.',
			points: [
				'Track installs and ratings',
				'Review monetization signals',
				'Scan creatives and rankings'
			],
			href: '/apps/com.rovio.baba',
			cta: 'View App Intelligence',
			imageLight: '/frontpage/app_page_light.png',
			imageDark: '/frontpage/app_page_dark.png',
			imageAlt:
				'App intelligence dashboard preview showing app overview, installs, ratings, and monetization data.'
		},
		{
			kicker: 'Creative market visibility',
			title: 'Browse the Creatives Top Advertisers Use',
			description: 'Browse live creative libraries to see what advertisers are running right now.',
			points: [
				'Browse live creative feeds',
				'Filter by network and format',
				'Spot active campaign patterns'
			],
			href: '/ad-creatives',
			cta: 'Browse Creatives',
			imageLight: '/frontpage/creative_explorer_light.png',
			imageDark: '/frontpage/creative_explorer_dark.png',
			imageAlt:
				'Ad creative explorer preview showing network filters and a feed of advertiser creatives.'
		},
		{
			kicker: 'Company and SDK intelligence',
			title: "See Who's Actually Using Mobile Adtech Products",
			description: 'See which apps, categories, and related entities are tied to each company.',
			points: ['Find top apps by company', 'Compare category adoption', 'Follow related entities'],
			href: '/companies/google.com',
			cta: 'View Companies',
			imageLight: '/frontpage/app_intelligence_company_overview_light.png',
			imageDark: '/frontpage/app_intelligence_company_overview_dark.png',
			imageAlt:
				'Company intelligence dashboard preview showing category breakdowns, related entities, and top customer apps.'
		}
	];

	const dashboardAutoplayMs = 7000;
	let activeDashboardIndex = $state(0);
	let dashboardInterval: number | undefined;

	function showDashboard(index: number) {
		activeDashboardIndex = index;
		restartDashboardAutoplay();
	}

	function showPreviousDashboard() {
		activeDashboardIndex =
			(activeDashboardIndex - 1 + dashboardHighlights.length) % dashboardHighlights.length;
		restartDashboardAutoplay();
	}

	function showNextDashboard() {
		advanceDashboard();
		restartDashboardAutoplay();
	}

	function advanceDashboard() {
		activeDashboardIndex = (activeDashboardIndex + 1) % dashboardHighlights.length;
	}

	function restartDashboardAutoplay() {
		if (dashboardInterval) {
			clearInterval(dashboardInterval);
		}

		dashboardInterval = window.setInterval(() => {
			advanceDashboard();
		}, dashboardAutoplayMs);
	}

	onMount(() => {
		restartDashboardAutoplay();

		return () => {
			if (dashboardInterval) {
				clearInterval(dashboardInterval);
			}
		};
	});
</script>

<svelte:head>
	<!-- Title -->
	<title>{title}</title>

	<!-- Standard meta tags -->
	<meta name="description" content={description} />
	<meta
		name="keywords"
		content="app, aso, app competitor analysis, ad creatives, ios, android, marketing, advertising, analytics, keyword analytics,  Google Play data, app data, app rankings, download statistics, competitor analysis, mobile app insights, app store intelligence"
	/>

	<!-- Open Graph meta tags -->
	<meta property="og:title" content={title} />
	<meta property="og:description" content={description} />
	<meta property="og:image" content="https://appgoblin.info/goblin_purple_hat_250.png" />
	<meta property="og:url" content="https://appgoblin.info" />
	<meta property="og:type" content="website" />

	<!-- Twitter Card meta tags -->
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content={title} />
	<meta name="twitter:description" content={description} />
	<meta name="twitter:image" content="https://appgoblin.info/goblin_purple_hat_250.png" />

	<!-- Additional meta tags -->
	<meta name="robots" content="index, follow" />
	<link rel="canonical" href="https://appgoblin.info" />
</svelte:head>

<div class="flex flex-col gap-8 px-2 md:px-20 lg:px-48">
	<!-- Hero Header Section -->
	<section class="text-center mt-8 mb-8 space-y-4">
		<h1 class="text-xl md:text-3xl font-bold mb-4">App Marketing Tools and Mobile Intelligence</h1>
		<div class="flex flex-wrap justify-center gap-4 text-sm mb-6">
			<span class="px-3 py-1 bg-secondary-100-900/20 rounded-full">🚀 Free ASO Tools</span>
			<span class="px-3 py-1 bg-warning-100-900/20 rounded-full"
				>⚡ Find High Growth Apps and Advertisers</span
			>
			<span class="px-3 py-1 bg-success-100-900/20 rounded-full"
				>✨ Mobile Ad and Creative Insights</span
			>
		</div>
		<p class="text-base md:text-lg max-w-2xl mx-auto">
			Analyze your competitors' growth and marketing tools.
		</p>
		<p>
			Browse
			<span class="font-bold text-success-900-100"
				>{formatNumber(data.appsOverview.android_apps)}</span
			>
			Android and
			<span class="font-bold text-success-900-100">{formatNumber(data.appsOverview.ios_apps)}</span>
			iOS apps.
		</p>

		<div class="items-center">
			<div class="flex flex-col gap-4 items-center">
				<div class="flex flex-wrap items-center justify-center gap-3">
					<a
						href="/auth/signup"
						class="btn preset-filled-primary-500 inline-flex items-center gap-2 p-3"
					>
						<span class="text-black">Create Free Account</span>
					</a>
					<a
						href="/contact"
						class="btn preset-outlined-primary-500 inline-flex items-center gap-2 p-3"
					>
						<span>Get in Touch</span>
					</a>
				</div>
			</div>
		</div>
	</section>

	<section
		class="relative overflow-hidden rounded-[2rem] border border-secondary-900-100/20 bg-surface-100-900/40 px-4 py-6 shadow-2xl md:px-8 md:py-10"
	>
		<div
			class="pointer-events-none absolute -right-16 top-0 h-48 w-48 rounded-full bg-secondary-500/10 blur-3xl"
		></div>
		<div
			class="pointer-events-none absolute -left-12 bottom-0 h-40 w-40 rounded-full bg-primary-500/10 blur-3xl"
		></div>

		<div class="relative">
			<div class="mb-8 max-w-3xl">
				<p class="mb-3 text-xs font-bold uppercase tracking-[0.32em] text-secondary-700-300">
					See how the dashboards work
				</p>
				<h2 class="mb-3 text-3xl font-bold leading-tight md:text-4xl">
					See the workflows teams use most
				</h2>
				<p class="text-base md:text-lg">
					Research apps, monitor creatives, and find the companies behind the mobile stack.
				</p>
			</div>

			<article
				class="overflow-hidden rounded-[1.75rem] border border-surface-100-900/70 bg-surface-100-900/55 shadow-lg"
			>
				<div class="grid gap-6 p-4 md:grid-cols-[minmax(0,0.78fr)_minmax(0,1.22fr)] md:p-6">
					<div class="flex flex-col justify-between gap-6">
						<div>
							<p class="mb-3 text-xs font-bold uppercase tracking-[0.28em] text-primary-800-200">
								{dashboardHighlights[activeDashboardIndex].kicker}
							</p>
							<h3 class="mb-3 text-2xl font-bold leading-tight md:text-3xl">
								{dashboardHighlights[activeDashboardIndex].title}
							</h3>
							<p class="mb-5 text-sm leading-7 md:text-base">
								{dashboardHighlights[activeDashboardIndex].description}
							</p>

							<ul class="mb-6 space-y-2 text-sm md:text-base">
								{#each dashboardHighlights[activeDashboardIndex].points as point}
									<li class="flex items-start gap-3">
										<span class="mt-1 h-2.5 w-2.5 shrink-0 rounded-full bg-success-500"></span>
										<span>{point}</span>
									</li>
								{/each}
							</ul>

							<div class="flex flex-wrap items-center gap-3">
								<a
									href={dashboardHighlights[activeDashboardIndex].href}
									class="btn preset-filled-primary-500 px-4 py-2 font-medium"
								>
									{dashboardHighlights[activeDashboardIndex].cta}
								</a>
							</div>
						</div>

						<div class="flex items-center gap-3">
							<button
								type="button"
								class="flex h-10 w-10 items-center justify-center rounded-full border border-surface-100-900/60 bg-surface-50-950/35 text-lg font-bold transition-colors hover:border-secondary-600/60 hover:bg-surface-50-950/55"
								onclick={showPreviousDashboard}
								aria-label="Show previous dashboard"
							>
								&lt;
							</button>

							<div class="flex items-center gap-2">
								{#each dashboardHighlights as _, index}
									<button
										type="button"
										class={[
											'h-3 w-3 rounded-full transition-all',
											activeDashboardIndex === index
												? 'bg-primary-500 shadow-[0_0_0_4px_rgba(125,211,252,0.12)]'
												: 'bg-surface-500/40 hover:bg-surface-500/70'
										].join(' ')}
										onclick={() => showDashboard(index)}
										aria-label={`Show dashboard ${index + 1}`}
										aria-pressed={activeDashboardIndex === index}
									></button>
								{/each}
							</div>

							<button
								type="button"
								class="flex h-10 w-10 items-center justify-center rounded-full border border-surface-100-900/60 bg-surface-50-950/35 text-lg font-bold transition-colors hover:border-secondary-600/60 hover:bg-surface-50-950/55"
								onclick={showNextDashboard}
								aria-label="Show next dashboard"
							>
								&gt;
							</button>
						</div>
					</div>

					<a
						href={dashboardHighlights[activeDashboardIndex].href}
						class="group relative block overflow-hidden rounded-[1.5rem] border border-secondary-900-100/20 bg-surface-50-950/70 p-2 shadow-xl"
					>
						<div
							class="absolute inset-0 z-10 bg-gradient-to-tr from-surface-950/35 via-transparent to-primary-500/15"
						></div>
						<div
							class="absolute inset-x-0 bottom-0 z-10 h-28 bg-gradient-to-t from-surface-950/45 to-transparent"
						></div>
						<div
							class="absolute inset-y-0 left-0 z-10 hidden w-24 bg-gradient-to-r from-surface-950/25 to-transparent md:block"
						></div>
						<div
							class="absolute right-4 top-4 z-20 rounded-full border border-white/20 bg-surface-950/55 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.2em] text-white/90 backdrop-blur-sm"
						>
							Live Preview
						</div>
						<div class="aspect-[16/11] overflow-hidden rounded-[1rem]">
							<img
								src={dashboardHighlights[activeDashboardIndex].imageLight}
								alt={dashboardHighlights[activeDashboardIndex].imageAlt}
								class="block h-full w-full object-cover object-top-left opacity-90 saturate-[0.92] transition-transform duration-500 group-hover:scale-[1.015] dark:hidden"
								loading="eager"
							/>
							<img
								src={dashboardHighlights[activeDashboardIndex].imageDark}
								alt={dashboardHighlights[activeDashboardIndex].imageAlt}
								class="hidden h-full w-full object-cover object-top-left opacity-90 saturate-[0.92] transition-transform duration-500 group-hover:scale-[1.015] dark:block"
								loading="eager"
							/>
						</div>
					</a>
				</div>
			</article>
		</div>
	</section>

	<section class={mainSectionClass}>
		<div class="flex items-center mb-6">
			<div
				class="bg-gradient-to-br from-secondary-900-100 to-secondary-600 p-1 rounded-2xl shadow-lg mr-4"
			>
				<ClipboardList class="h-8 w-8 text-white" />
			</div>
			<div>
				<h2 class={sectionTitleClass}>Core App Growth Intelligence</h2>
				<p class={sectionSubtitleClass}>Free tools with export-ready datasets</p>
			</div>
		</div>

		<p class={sectionDescriptionClass}>
			Free tools to analyze app performance, competitive landscape, and ad-tech activity across 4M+
			Android and iOS apps.
		</p>

		<h3 class="text-lg font-bold mb-3">AppGoblin Tools</h3>
		<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
			<div class="rounded-md border border-surface-100-900 p-4 bg-surface-100-900/50">
				<h4 class="font-bold mb-2">
					<a href="/rankings/store/1/collection/1/category/1/US" class="hover:text-primary-600-400"
						>App Intelligence (Free)</a
					>
				</h4>
				<p class="text-sm mb-3">Daily intelligence on 4M+ Android and iOS apps.</p>
				<ul class="text-sm space-y-1.5">
					<li>
						<span class={coreFeatureBulletSpanClass}>Keyword Tracking</span> — Monitor target terms and
						top ranking apps
					</li>
					<li>
						<span class={coreFeatureBulletSpanClass}>Growth Trends</span> — Follow install and rating
						changes over time
					</li>
					<li>
						<span class={coreFeatureBulletSpanClass}>Store Rankings</span> — Track Google Play and App
						Store positions daily
					</li>
					<li>
						<span class={coreFeatureBulletSpanClass}>New App Discovery</span> — Surface new releases early
						across categories
					</li>
					<li>
						<span class={coreFeatureBulletSpanClass}>SDK Footprints</span> — See which SDKs each app is
						using
					</li>
				</ul>
				<p class="text-xs text-surface-500/60 mt-3 mb-1">Who it's for:</p>
				<p class="text-sm">App marketers, ASO teams, and competitor researchers.</p>
				<p class="text-xs text-surface-500/60 mt-3 mb-2">Examples:</p>
				<div class="flex justify-between items-end gap-2 mb-0">
					<div class="flex flex-wrap gap-2">
						<a href="/apps/com.rovio.baba" class={exampleAnchorClass}>Angry Birds 2 App</a>
					</div>
					<a href="/rankings/store/1/collection/1/category/1/US" class={featureCtaClass}
						>Track Rankings →</a
					>
				</div>
			</div>

			<div class="rounded-md border border-surface-100-900 p-4 bg-surface-100-900/50">
				<h4 class="font-bold mb-2">
					<a href="/sdks" class="hover:text-primary-600-400">SDK Analysis</a>
				</h4>
				<p class="text-sm">
					Inspect SDK footprints from decompiled Android and iOS apps, including ad, analytics, and
					open-source libraries.
				</p>
				<ul class="text-sm space-y-1.5 mt-3">
					<li>
						<span class={coreFeatureBulletSpanClass}>Library Detection</span> — Identify ad, analytics,
						and open-source packages in each app
					</li>
					<li>
						<span class={coreFeatureBulletSpanClass}>On-Demand Scans</span> — Request app analysis and
						review newly processed results
					</li>
				</ul>
				<p class="text-xs text-white/60 mt-3 mb-1">Who it's for:</p>
				<p class="text-sm">Developers, technical researchers, and security analysts.</p>
				<p class="text-sm mt-3 mb-3">Free: request any app for analysis.</p>
				<p class="text-xs text-white/60 mb-2">Examples:</p>
				<div class="flex justify-between items-end gap-2 mb-0">
					<div class="flex flex-wrap gap-2">
						<a href="/sdks" class={exampleAnchorClass}>Recently Requested SDK Scans</a>
					</div>
					<a href="/sdks" class={featureCtaClass}>Request Scan →</a>
				</div>
			</div>

			<div class="rounded-md border border-surface-100-900 p-4 bg-surface-100-900/50">
				<h4 class="font-bold mb-2">
					<a href="/companies" class="hover:text-primary-600-400">Company Intelligence</a>
				</h4>
				<p class="text-sm mb-3">
					Rank and filter companies by SDK adoption, then drill into the top apps using each SDK,
					API, or mobile services provider.
				</p>
				<ul class="text-sm space-y-1.5 mb-3">
					<li>
						<span class={coreFeatureBulletSpanClass}>Category Filters</span> — Slice company adoption
						by app vertical and use case
					</li>
					<li>
						<span class={coreFeatureBulletSpanClass}>Client App Visibility</span> — See leading apps tied
						to each provider
					</li>
				</ul>
				<p class="text-xs text-white/60 mb-1">Who it's for:</p>
				<p class="text-sm mb-3">Ad sales teams, partner teams, and market intelligence analysts.</p>
				<p class="text-xs text-white/60 mb-2">Examples:</p>
				<div class="flex justify-between items-end gap-2 mb-0">
					<div class="flex flex-wrap gap-2">
						<a href="/companies/types/ad-networks/game_casino" class={exampleAnchorClass}
							>Ad Networks for Casino Games</a
						>
						<a href="/companies/types/product-analytics/business" class={exampleAnchorClass}
							>Product Analytics for Business Apps →</a
						>
						<a href="/companies/salesforce.com" class={exampleAnchorClass}>Salesforce Clients →</a>
						<a href="/companies/appsflyer.com" class={exampleAnchorClass}>AppsFlyer Top Apps →</a>
					</div>
					<a href="/companies" class={featureCtaClass}>Browse Companies →</a>
				</div>
			</div>

			<div class="rounded-md border border-surface-100-900 p-4 bg-surface-100-900/50">
				<h4 class="font-bold mb-2">Ad Tech Insights</h4>
				<p class="text-sm">
					Track active ad campaigns, ad-tech domains apps contact in production traffic, and
					app-ads.txt mappings of DIRECT and RESELLER entries to real app IDs.
				</p>
				<ul class="text-sm space-y-1.5 mt-3">
					<li>
						<span class={coreFeatureBulletSpanClass}>Live Campaign Tracking</span> — Monitor active advertisers
						and creatives in market
					</li>
					<li>
						<span class={coreFeatureBulletSpanClass}>Supply Path Validation</span> — Map app-ads.txt entries
						to real app IDs for verification
					</li>
				</ul>
				<p class="text-xs text-surface-500/60 mt-3 mb-1">Who it's for:</p>
				<p class="text-sm">Ad networks, DSP teams, and fraud detection analysts.</p>
				<p class="text-xs text-surface-500/60 mt-3 mb-2">Examples:</p>
				<div class="flex justify-between items-end gap-2 mb-0">
					<div class="flex flex-wrap gap-2">
						<a href="/top-mobile-advertisers" class={exampleAnchorClass}>Top Mobile Advertisers</a>
						<a href="/ad-creatives" class={exampleAnchorClass}>Browse Thousands of Ad-Creatives</a>
						<a href="/companies/applovin.com/app-adstxt" class={exampleAnchorClass}
							>AppLovin App-Ads.txt Entries</a
						>
						<a href="/apps/com.rovio.baba/ads-txt" class={exampleAnchorClass}
							>Angry Birds 2 App Example</a
						>
					</div>
					<a href="/top-mobile-advertisers" class={featureCtaClass}>View Campaigns →</a>
				</div>
			</div>
		</div>
	</section>

	<!-- Top Advertiser Section -->
	<section class={mainSectionClass}>
		<div class="flex items-center mb-6">
			<div
				class="bg-gradient-to-br from-success-900-100 to-success-600 p-1 rounded-2xl shadow-lg mr-4"
			>
				<TrendingUp class="h-8 w-8 text-white" />
			</div>
			<div>
				<h2 class={sectionTitleClass}>{monthYear} Top Android Advertiser</h2>
				<p class={sectionSubtitleClass}>Live advertising intelligence</p>
			</div>
		</div>

		<p class={sectionDescriptionClass}>
			AppGoblin tracks who is currently spending on mobile ads. See the biggest mobile ad buyers
			this month, their creatives, and the ad networks they use. Data is collected from live ad
			requests sent from apps.
		</p>

		{#if data.topAdvertisers && data.topAdvertisers.length > 0}
			<div class="mb-6 md:p-4">
				<AdvertiserCreativeRankingsTableTop data={data.topAdvertisers.slice(0, 1)} />
			</div>
		{/if}

		<div class="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
			<div class="flex gap-4">
				<span class={featureBulletClass}>📱 Mobile ad tracking</span>
				<span class={featureBulletClass}>🎨 Creative analysis</span>
				<span class={featureBulletClass}>📊 Network insights</span>
			</div>
			<a href="/top-mobile-advertisers" class="btn preset-filled-success-200-800">
				Browse All Ad Buyers
			</a>
		</div>
	</section>

	<!-- Popular Companies/SDKs Section -->
	<section class={mainSectionClass}>
		<div class="flex items-center mb-6">
			<div
				class="bg-gradient-to-br from-primary-900-100 to-primary-600 rounded-2xl p-1 shadow-lg mr-4"
			>
				<Layers class="h-8 w-8 text-white" />
			</div>
			<div>
				<h2 class={sectionTitleClass}>Most Popular SDKs & Analytics</h2>
				<p class={sectionSubtitleClass}>Mobile SDK intelligence</p>
			</div>
		</div>

		<p class={sectionDescriptionClass}>
			Explore top ad networks, MMPs, analytics, and developer tools used in mobile apps, then drill
			down into company pages for SDK footprint, API behavior, app-ads.txt links, and category-level
			adoption trends.
		</p>

		<div class="grid grid-cols-1 md:grid-cols-2 md:gap-8 mb-6">
			<div class={subSectionClass}>
				<div class="flex items-center mb-3">
					<a href="/companies/types/ad-attribution">
						<h4 class="{cardTitleClass} ">MMPs</h4>
					</a>
				</div>
				<p class={cardDescriptionClass}>
					Top MMPs and mobile app tracking companies in Android and iOS apps.
				</p>
				{#if data.topCompanies.attribution}
					<CompaniesBarChart plotData={data.topCompanies.attribution.sdk_ios} />
				{/if}
			</div>
			<div class={subSectionClass}>
				<div class="flex items-center mb-3">
					<a href="/companies/types/product-analytics">
						<h4 class="{cardTitleClass} hover:text-green-400">Product Analytics</h4>
					</a>
				</div>
				<p class={cardDescriptionClass}>
					Most popular product analytics companies and open source libraries based on SDKs in iOS
					and Android apps.
				</p>
				{#if data.topCompanies.analytics}
					<CompaniesBarChart plotData={data.topCompanies.analytics.sdk_ios} />
				{/if}
			</div>
		</div>

		<div class="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
			<div class="flex gap-4">
				<span class={featureBulletClass}>🔍 SDK detection</span>
				<span class={featureBulletClass}>📈 Market share analytics</span>
				<span class={featureBulletClass}>🏢 Company profiles</span>
			</div>
			<a href="/companies" class="btn preset-filled-primary-200-800"> Browse 500+ Companies</a>
		</div>
	</section>

	<!-- App Store Rankings Section -->
	<section class={mainSectionClass}>
		<div class="flex items-center mb-6">
			<div
				class="bg-gradient-to-br from-warning-900-100 to-warning-600 p-1 rounded-2xl shadow-lg mr-4"
			>
				<ChartNoAxesColumnIncreasing class="h-8 w-8 text-white" />
			</div>
			<div>
				<h2 class={sectionTitleClass}>Today's App Store Rankings</h2>
				<p class={sectionSubtitleClass}>Live app store data</p>
			</div>
		</div>

		<p class={sectionDescriptionClass}>
			See the latest app store rankings for Android and iOS. Click through for full categories and
			details.
		</p>

		<div class="grid grid-cols-1 grid-cols-2 gap-6 mb-6">
			<div class={subSectionClass}>
				<a href="/rankings/store/1/collection/1/category/1/US">
					<span
						class="text-base md:text-lg inline-flex gap-2 items-center font-bold hover:text-green-400"
					>
						<Smartphone class="h-4 w-4" />
						Today's Top 5 Android Apps
					</span>
				</a>
				{#if data.androidAppRanks}
					<AppRankTableShort myTable={data.androidAppRanks} />
				{/if}
			</div>
			<div class={subSectionClass}>
				<a href="/rankings/store/1/collection/1/category/36/US">
					<span
						class="text-base md:text-lg inline-flex gap-2 items-center font-bold hover:text-green-400"
					>
						<Gamepad2 class="h-4 w-4" />
						Today's Top 5 Android Games
					</span>
				</a>
				{#if data.androidGameRanks}
					<AppRankTableShort myTable={data.androidGameRanks} />
				{/if}
			</div>
			<div class={subSectionClass}>
				<a href="/rankings/store/2/collection/4/category/120/US">
					<span
						class="text-base md:text-lg inline-flex gap-2 items-center font-bold hover:text-gray-400"
					>
						<Smartphone class="h-4 w-4" />
						Today's Top 5 iOS Apps
					</span>
				</a>
				{#if data.iOSAppRanks}
					<AppRankTableShort myTable={data.iOSAppRanks} />
				{/if}
			</div>
			<div class={subSectionClass}>
				<a href="/rankings/store/2/collection/4/category/62/US">
					<span
						class="text-base md:text-lg inline-flex gap-2 items-center font-bold hover:text-gray-400"
					>
						<Gamepad2 class="h-4 w-4" />
						Today's Top 5 iOS Games
					</span>
				</a>
				{#if data.iOSGameRanks}
					<AppRankTableShort myTable={data.iOSGameRanks} />
				{/if}
			</div>
		</div>

		<div class="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
			<div class="flex gap-4">
				<span class={featureBulletClass}>📱 Real-time rankings</span>
				<span class={featureBulletClass}>🌍 Global + country data</span>
				<span class={featureBulletClass}>📈 Historical tracking</span>
			</div>
			<a
				href="/rankings/store/1/collection/1/category/1/US"
				class="btn preset-filled-secondary-200-800"
			>
				See All Rankings
			</a>
		</div>
	</section>

	<!-- New Apps Section -->
	<section class={mainSectionClass}>
		<div class="flex items-center mb-6">
			<div class="bg-gradient-to-br from-info-900-100 to-info-600 p-1 rounded-2xl shadow-lg mr-4">
				<Sparkles class="h-8 w-8 text-white" />
			</div>
			<div>
				<h2 class={sectionTitleClass}>Discover New Apps</h2>
				<p class={sectionSubtitleClass}>Latest releases & trending apps</p>
			</div>
		</div>

		<p class="{sectionDescriptionClass} mb-8">
			Discover trending new apps across Google Play and the App Store. Track the latest releases and
			find emerging apps before they become mainstream.
		</p>

		<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
			<a href="/collections/new_weekly/google/overall" class="group/card">
				<div
					class="p-6 bg-white/5 rounded-xl border border-white/10 hover:border-info-900-100/50 hover:bg-white/10 transition-all duration-300"
				>
					<div class="flex items-center mb-4">
						<div class="bg-gradient-to-br from-cyan-500 to-cyan-600 p-3 rounded-lg mr-4 shrink-0">
							<Zap class="h-5 w-5 text-white" />
						</div>
						<div>
							<h3 class="text-lg font-bold group-hover/card:text-cyan-400 transition-colors">
								This Week
							</h3>
							<p class="text-sm text-gray-500">Newest releases</p>
						</div>
					</div>
				</div>
			</a>
			<a href="/collections/new_monthly/google/overall" class="group/card">
				<div
					class="p-6 bg-white/5 rounded-xl border border-white/10 hover:border-info-900-100/50 hover:bg-white/10 transition-all duration-300"
				>
					<div class="flex items-center mb-4">
						<div
							class="bg-gradient-to-br from-info-900-100 to-info-600 p-3 rounded-lg mr-4 shrink-0"
						>
							<Calendar class="h-5 w-5 text-white" />
						</div>
						<div>
							<h3 class="text-lg font-bold group-hover/card:text-info-900-100 transition-colors">
								This Month
							</h3>
							<p class="text-sm text-gray-500">Popular releases</p>
						</div>
					</div>
				</div>
			</a>
			<a href="/collections/new_yearly/google/overall" class="group/card">
				<div
					class="p-6 bg-white/5 rounded-xl border border-white/10 hover:border-info-900-100/50 hover:bg-white/10 transition-all duration-300"
				>
					<div class="flex items-center mb-4">
						<div
							class="bg-gradient-to-br from-yellow-500 to-yellow-600 p-3 rounded-lg mr-4 shrink-0"
						>
							<Star class="h-5 w-5 text-white" />
						</div>
						<div>
							<h3 class="text-lg font-bold group-hover/card:text-yellow-400 transition-colors">
								2025 Best
							</h3>
							<p class="text-sm text-gray-500">Top of the year</p>
						</div>
					</div>
				</div>
			</a>
		</div>

		<div class="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
			<div class="flex gap-4">
				<span class={featureBulletClass}>📱 Cross-platform tracking</span>
				<span class={featureBulletClass}>📈 Trending analysis</span>
				<span class={featureBulletClass}>🎯 Category insights</span>
			</div>
			<a href="/collections/new_monthly/google/overall" class="btn preset-filled-primary-200-800">
				Explore New Apps
			</a>
		</div>
	</section>
</div>
