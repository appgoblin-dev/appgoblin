<script lang="ts">
	import { page } from '$app/state';
	import type { Snippet } from 'svelte';
	import { formatNumber } from '$lib/utils/formatNumber';
	import WhiteCard from './WhiteCard.svelte';

	let {
		sdkAndroidTotalApps,
		sdkIosTotalApps,
		adstxtAndroidTotalApps,
		adstxtIosTotalApps,
		mainTable
	}: {
		sdkAndroidTotalApps: Snippet;
		sdkIosTotalApps: Snippet;
		adstxtAndroidTotalApps: Snippet;
		adstxtIosTotalApps: Snippet;
		mainTable: Snippet;
	} = $props();

	const typeName = $derived(
		page.params.type
			? (page.data?.companyTypes?.types?.find(
					(t: { url_slug: string }) => t.url_slug === page.params.type
				)?.name ?? 'companies')
			: null
	);
	const categoryName = $derived(
		page.data?.appCats?.categories?.find((c: { id: string }) => c.id === page.params.category)
			?.name ??
			page.params.category ??
			'All'
	);
	const overview = $derived(page.data?.companiesOverview);
	const totals = $derived(
		typeof overview === 'object' && overview?.categories?.categories?.all
			? overview.categories.categories.all
			: null
	);
	const companyCount = $derived(
		typeof overview === 'object' && Array.isArray(overview?.companies_overview)
			? overview.companies_overview.length
			: null
	);
	const showAdstxt = $derived(!page.params.type || page.params.type === 'ad-networks');

	const TYPE_DESCRIPTIONS: Record<string, string> = {
		'ad-networks':
			'Ad Networks includes any company that provides monetization for mobile apps by displaying ads to users. The ad network data comes from api, sdk and app-ads.txt files.',
		'ad-attribution':
			'Ad Attribution / MMP companies track and attribute app installs and user actions to specific marketing campaigns. Attribution is a tightly controlled set of companies by the self attributing ad networks such as Apple, Google and Meta. MMPs collect user data and share with ad networks.',
		'product-analytics':
			'Product Analytics providers offer tools to track user behavior, app performance, and other metrics to help developers optimize their apps and improve user retention.',
		'marketing-automation':
			'Marketing Automation tools help developers automate marketing tasks such as push notifications, email campaigns, and user segmentation to engage and retain users.',
		'development-tools':
			'Development Tools include SDKs, libraries, and platforms that assist developers in building, testing, and deploying mobile applications.',
		'business-tools':
			'A bit of a catch all for companies that provide SDKs for mobile apps. This ranges from cloud services, more traditional CRM tools, revenue management tools, paywall tools etc.',
		mediation:
			'Mediation platforms (which are ad networks) manage the ad bidding to help mobile apps get higher CPMs.'
	};

	const introText = $derived.by(() => {
		const typeSlug = page.params.type;
		const typeLabel = typeName ?? 'companies';
		const categoryLabel = categoryName || 'All';
		const typeDesc =
			typeSlug && TYPE_DESCRIPTIONS[typeSlug]
				? TYPE_DESCRIPTIONS[typeSlug]
				: `This table lists top ${typeLabel}.`;
		if (categoryLabel !== 'All') {
			return `${typeDesc} Shown here for apps in the ${categoryLabel} category.`;
		}
		return `${typeDesc} Shown across all app categories.`;
	});

	const hasSdkTotals = $derived(
		totals && (totals.sdk_android_total_companies > 0 || totals.sdk_ios_total_companies > 0)
	);
	const hasAdstxtTotals = $derived(
		showAdstxt &&
			totals &&
			(totals.adstxt_direct_android_total_companies > 0 ||
				totals.adstxt_direct_ios_total_companies > 0)
	);
</script>

{#if introText}
	<div class="text-sm md:text-base text-surface-600-400 leading-relaxed space-y-2">
		<p class="text-primary-900-100">
			{introText}
		</p>
		<p class="text-primary-900-100">
			{#if totals && (hasSdkTotals || hasAdstxtTotals)}
				{#if hasSdkTotals}
					AppGoblin has mapped and verified {formatNumber(totals.sdk_android_total_companies)} companies
					with Android SDKs and {formatNumber(totals.sdk_ios_total_companies)} with iOS SDKs.
				{/if}
				{#if hasAdstxtTotals}
					In addition to SDK Ad Networks we found {formatNumber(
						totals.adstxt_direct_android_total_companies
					)} advertising domains found in App-ads.txt (DIRECT) for Android and {formatNumber(
						totals.adstxt_direct_ios_total_companies
					)} for iOS. These numbers overlap with the SDK Ad Network totals and also include apps that
					misconfigure advertising domains in app-ads.txt file.
				{/if}
			{/if}
		</p>
	</div>
{/if}

<div class="grid grid-cols-1 gap-8 mt-6">
	<!-- MAIN TABLE -->
	<div class="card preset-tonal">
		<div class="card-content">
			{@render mainTable()}
		</div>
	</div>

	<div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-6">
		<!-- SDK Section -->
		<WhiteCard>
			{#snippet title()}
				SDK
			{/snippet}
			<p class="text-sm md:text-lg mb-2 p-2 md:p-4">
				SDK data is derived by downloading the app's Android APK or iOS IPA file and unzipped. We
				then check the app's data for SDK signatures in paths, AndroidManifest.xml and the
				Info.plist. Many apps are unable to be zipped. Downloading and opening the APK or IPA takes
				time and resources thus the smaller totals.
			</p>
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<!-- Android SDK -->
				<div class="card preset-tonal">
					<div class="card-header">
						<p class="text-sm md:text-lg">
							{@render sdkAndroidTotalApps()}
						</p>
					</div>
					<div class="card-content"></div>
				</div>
				<!-- iOS SDK -->
				<div class="card preset-tonal">
					<div class="card-header">
						<p class="text-sm md:text-lg">
							{@render sdkIosTotalApps()}
						</p>
					</div>
					<div class="card-content"></div>
				</div>
			</div>
		</WhiteCard>

		{#if !page.params.type || page.params.type == 'ad-networks'}
			<!-- App Ads.txt Section -->
			<WhiteCard>
				{#snippet title()}
					App Ads.txt
				{/snippet}
				<p class="text-sm md:text-lg mb-2 p-2 md:p-4">
					App-ads.txt files are an open standard by the IAB to help combat ad fraud. This data was
					crawled from the URLs on the app's developer pages. Not all apps have app-ads.txt, many do
					not. Additionally, below are only apps that have the ad network listed as DIRECT instead
					of RESELLER.
				</p>
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<!-- Android App Ads.txt -->
					<div class="card preset-tonal">
						<div class="card-header">
							<p class="text-sm md:text-lg">
								{@render adstxtAndroidTotalApps()}
							</p>
						</div>
						<div class="card-content"></div>
					</div>
					<!-- iOS App Ads.txt -->
					<div class="card preset-tonal">
						<div class="card-header">
							<p class="text-sm md:text-lg">
								{@render adstxtIosTotalApps()}
							</p>
						</div>
						<div class="card-content"></div>
					</div>
				</div>
			</WhiteCard>
		{/if}
	</div>
</div>
