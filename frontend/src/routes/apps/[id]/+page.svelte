<script lang="ts">
	import ExternalLinkSvg from '$lib/svg/ExternalLinkSVG.svelte';
	import RequestSDKScanButton from '$lib/RequestSDKScanButton.svelte';
	import type { AppFullDetails } from '../../../types';
	import WhiteCard from '$lib/WhiteCard.svelte';
	import AppSDKOverview from '$lib/AppSDKOverview.svelte';
	import AppOverviewSummary from '$lib/AppOverviewSummary.svelte';
	import { formatNumber } from '$lib/utils/formatNumber';

	interface Props {
		data: AppFullDetails;
	}
	let { data }: Props = $props();

	function isProbablyValidHTML(str: string): boolean {
		if (!str) return false;

		// Catch invalid tags like <.b>
		if (/<\.[^>]+>/.test(str)) return false;

		// Check that all <tag> have matching </tag>
		const tagPattern = /<([a-zA-Z0-9]+)(\s[^>]*)?>/g;
		const stack: string[] = [];
		let match;

		while ((match = tagPattern.exec(str))) {
			const tag = match[1].toLowerCase();
			if (str.includes(`</${tag}>`)) continue;
			if (!['br', 'img', 'hr', 'input'].includes(tag)) {
				stack.push(tag);
			}
		}

		return stack.length === 0;
	}
</script>

<section class="grid grid-flow-cols-1 md:grid-cols-2 md:gap-4 p-2">
	<!-- App Overview Summary - Full Width -->
	<div class="col-span-full mb-4">
		<div class="card preset-filled-surface-100-900 p-4 lg:p-6">
			<AppOverviewSummary app={data.myapp} />
		</div>
	</div>

	<div class="card preset-filled-surface-100-900 p-0 lg:p-8">
		<div class="card-footer md:flex">
			<!-- SDKs, Trackers & Permissions Overview -->
			<div class="grid grid-cols-1 gap-2 md:gap-4">
				<WhiteCard>
					{#snippet title()}
						SDKs, Trackers & Permissions
					{/snippet}
					<AppSDKOverview
						myPackageInfo={data.appSDKsOverview}
						companyTypes={data.companyTypes}
						myapp={data.myapp}
					/>
				</WhiteCard>
				<!-- App Details Section -->
				<div class="grid grid-cols-2 gap-2 md:gap-4 text-xs md:text-base">
					<WhiteCard>
						{#snippet title()}
							App Details
						{/snippet}
						<div class="space-y-2 p-2">
							<div class="flex items-center gap-2">
								<span class="font-medium">Store ID:</span>
								<span class="text-primary-900-100">{data.myapp.store_id}</span>
							</div>
							<div class="flex items-center gap-2">
								<span class="font-medium">First Released:</span>
								<span class="text-primary-900-100">{data.myapp.release_date}</span>
							</div>
							<div class="flex items-center gap-2">
								<span class="font-medium">Store Last Updated:</span>
								<span class="text-primary-900-100">{data.myapp.store_last_updated}</span>
							</div>
							<div class="flex items-center gap-2">
								<span class="font-medium">In-App Purchases:</span>
								<span class="text-primary-900-100"
									>{data.myapp.in_app_purchases ? 'Yes' : 'No'}</span
								>
							</div>
							<div class="flex items-center gap-2">
								<span class="font-medium">Ads:</span>
								<span class="text-primary-900-100">{data.myapp.ad_supported ? 'Yes' : 'No'}</span>
							</div>

							{#if data.myapp.developer_url}
								<div class="flex items-center gap-2">
									<span class="font-medium">Website:</span>
									<a
										href="https://{data.myapp.developer_url}"
										target="_blank"
										class="anchor inline-flex"
									>
										{data.myapp.developer_url}
										<ExternalLinkSvg />
									</a>
								</div>
							{/if}
							<hr class="opacity-50" />
						</div>
					</WhiteCard>

					<!-- App Information Section -->
					<WhiteCard>
						{#snippet title()}
							App Store
						{/snippet}
						<div class="space-y-2 p-2">
							<div class="flex items-center gap-2">
								<span class="font-medium">Crawl Status:</span>
								<span
									class={data.myapp.crawl_result == 1
										? 'text-success-900-100'
										: 'text-error-900-100'}
								>
									{data.myapp.crawl_result == 1 ? 'Success' : 'Failed'}
								</span>
							</div>
							<div class="flex items-center gap-2">
								<span class="font-medium">AppGoblin First Crawled:</span>
								<span class="text-primary-900-100">{data.myapp.created_at}</span>
							</div>
							<div class="flex items-center gap-2">
								<span class="font-medium">AppGoblin Last Crawled:</span>
								<span class="text-primary-900-100">{data.myapp.updated_at}</span>
							</div>
						</div>
					</WhiteCard>

					<!-- Tracking Information Section -->
					<WhiteCard>
						{#snippet title()}
							Ads & App-Ads.txt
						{/snippet}
						{#if data.myapp.ad_supported || data.myapp.adstxt_crawl_result == 1}
							{#if data.myapp.adstxt_last_crawled}
								<div class="space-y-2 p-2">
									<div class="flex items-center gap-2">
										<span class="font-medium">Ads.txt Last Crawled:</span>
										<span class="text-primary-900-100">{data.myapp.adstxt_last_crawled}</span>
									</div>
									<div class="flex items-center gap-2">
										<span class="font-medium">Ads.txt Crawl Status:</span>
										<span
											class={data.myapp.adstxt_crawl_result == 1
												? 'text-success-900-100'
												: 'text-error-900-100'}
										>
											{data.myapp.adstxt_crawl_result == 1 ? 'Success' : 'Failed'}
										</span>
									</div>
								</div>
							{:else}
								App not yet analyzed for ads.
							{/if}
						{:else}
							App does not have ads.
						{/if}
					</WhiteCard>
					<WhiteCard>
						{#snippet title()}
							AppGoblin SDK Scans
						{/snippet}
						<div class="space-y-2 p-2">
							{#if data.myapp.sdk_last_crawled}
								<div class="flex items-center gap-2">
									<span class="font-medium">Successful Last Crawled:</span>
									<span class="text-primary-900-100">{data.myapp.sdk_successful_last_crawled}</span>
								</div>
								<div class="flex items-center gap-2">
									<span class="font-medium">Last Crawled:</span>
									<span class="text-primary-900-100">{data.myapp.sdk_last_crawled}</span>
								</div>
								<div class="flex items-center gap-2">
									<span class="font-medium">Last Crawl Status:</span>
									<span
										class={data.myapp.sdk_last_crawl_result == 1
											? 'text-success-900-100'
											: 'text-error-900-100'}
									>
										{data.myapp.sdk_last_crawl_result == 1 ? 'Success' : 'Failed'}
									</span>
								</div>
							{:else}
								App not yet analyzed for SDKs.
								<RequestSDKScanButton />
							{/if}
						</div>
					</WhiteCard>
				</div>
			</div>
		</div>
		<br />
		<div class="p-2 md:flex">
			<div class="self-center text-center">
				<p class="text-4xl p-2 text-primary-800-200">{data.myapp.rating}★</p>
				<p class="text-primary-900-100">Ratings: {formatNumber(data.myapp.rating_count)}</p>
			</div>
			<div class="flex-1">
				{#await data.myhistory}
					Loading rating details...
				{:then histdata}
					{#if histdata.histogram}
						{@const histogram = histdata.histogram}
						{@const stars = [
							{ label: '5★', count: histogram.five_star },
							{ label: '4★', count: histogram.four_star },
							{ label: '3★', count: histogram.three_star },
							{ label: '2★', count: histogram.two_star },
							{ label: '1★', count: histogram.one_star }
						]}
						{@const total =
							histogram.one_star +
							histogram.two_star +
							histogram.three_star +
							histogram.four_star +
							histogram.five_star}
						{#each stars as star}
							<div class="flex bar-spacer">
								<span class="label">{star.label}</span>
								<div class="bar-container bg-surface-100-900 grow">
									<div
										class="bar bg-primary-100-900"
										style="width: {total > 0 ? (star.count / total) * 100 : 0}%"
										title="{star.label}: {star.count} ratings"
									></div>
								</div>
							</div>
						{/each}
					{:else}
						<p>No rating data available for this app.</p>
					{/if}
				{/await}
			</div>
		</div>
	</div>

	<!-- Column2: App Pictures -->
	<div class="card preset-filled-surface-100-900 p-2 md:p-8">
		<div class="card preset-tonal p-2 md:p-8 mt-2 md:mt-4">
			<h4 class="h4 md:h3 p-2">Screenshots</h4>
			{#if data.myapp.featured_image_url}
				<div>
					<img
						class="h-auto max-w-full rounded-lg p-4 mx-auto"
						src={data.myapp.featured_image_url}
						alt="App screenshot"
						loading="lazy"
					/>
				</div>
			{/if}
			<section class="grid grid-cols-2 md:grid-cols-3 gap-4">
				{#each [data.myapp.phone_image_url_1, data.myapp.phone_image_url_2, data.myapp.phone_image_url_3, data.myapp.tablet_image_url_1, data.myapp.tablet_image_url_2, data.myapp.tablet_image_url_3] as imageUrl}
					{#if imageUrl && imageUrl != 'null'}
						<div>
							<img
								class="h-auto max-w-full rounded-lg"
								src={imageUrl}
								alt="App screenshot"
								loading="lazy"
							/>
						</div>
					{/if}
				{/each}
			</section>
			<section class="">
				<h4 class="h4 md:h3 p-2">App Description</h4>
				<div>
					<p class="text-strong">{data.myapp.description_short}</p>
				</div>
				<div>
					{#if data.myapp.description}
						{#if isProbablyValidHTML(data.myapp.description)}
							<p>
								{@html data.myapp.description?.replace(/\r?\n/g, '<br>')}
							</p>
						{:else}
							{data.myapp.description}
						{/if}
					{/if}
				</div>
			</section>
		</div>
	</div>
</section>

<style>
	.bar-spacer {
		margin: 10px;
	}

	.label {
		max-width: 20px;
	}

	.bar-container {
		align-self: center;
		align-items: center;
		border-radius: 5px; /* Rounded corners */
		margin-left: 5px;
		padding: 0px;
	}

	.bar {
		height: 20px; /* Fixed height for each bar */
		border-radius: 5px; /* Rounded corners */
	}
</style>
