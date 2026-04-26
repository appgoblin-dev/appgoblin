<script lang="ts">
	import WhiteCard from '$lib/WhiteCard.svelte';
	import SDKOverview from '$lib/utils/SDKOverview.svelte';
	import { formatNumberLocale } from '$lib/utils/formatNumber';
	let { data } = $props();
</script>

<div class="grid grid-cols-1 gap-4 md:gap-8 px-2 md:px-20 lg:px-48">
	<br />
	<h1 class="h1">AppGoblin Data Review</h1>

	<div class="space-y-2">
		<div class="preset-filled-surface-100-900 p-2 md:p-8 space-y-4">
			<p>
				Live stats for AppGoblin's current app ecosystem and the live crawling. Green number
				represent success and grey is the total.
			</p>
			<p>
				Green represents apps that are currently live on the app stores while the grey numbers are
				older apps that are no longer active on the app stores. For example AppGoblin is currently
				tracking <span class="font-bold text-success-900-100"
					>{formatNumberLocale(data.appsOverview.success_android_apps)}</span
				>
				Android Apps on Google Play out of a total of
				<span class="font-bold">{formatNumberLocale(data.appsOverview.android_apps)}</span>
				Android Apps that we have in our database. We also scan
				<span class="font-bold text-success-900-100"
					>{formatNumberLocale(data.appsOverview.weekly_scanned_android_apps)}</span
				>
				Android Apps every week and successfully scan
				<span class="font-bold">{formatNumberLocale(data.appsOverview.android_apps)}</span> of them.
			</p>
			<WhiteCard>
				{#snippet title()}
					App Store Scanned Apps
				{/snippet}
				{#if data.appsOverview}
					<div class="table-wrap">
						<table class="table w-full">
							<thead>
								<tr class="border-b">
									<th>Android Apps</th>
									<th>iOS Apps</th>
									<th>Android Weekly Scans</th>
									<th>iOS Weekly Scans</th>
								</tr>
							</thead>
							<tbody>
								<tr class="text-xs md:text-base">
									<td>
										<span class="text-success-900-100">
											{formatNumberLocale(data.appsOverview.success_android_apps)}
										</span>
										/ {formatNumberLocale(data.appsOverview.android_apps)}
									</td>
									<td>
										<span class="text-success-900-100">
											{formatNumberLocale(data.appsOverview.success_ios_apps)}
										</span>
										/ {formatNumberLocale(data.appsOverview.ios_apps)}
									</td>
									<td>
										<span class="text-success-900-100">
											{formatNumberLocale(data.appsOverview.weekly_success_scanned_android_apps)}
										</span>
										/ {formatNumberLocale(data.appsOverview.weekly_scanned_android_apps)}
									</td>
									<td>
										<span class="text-success-900-100">
											{formatNumberLocale(data.appsOverview.weekly_success_scanned_ios_apps)}
										</span>
										/ {formatNumberLocale(data.appsOverview.weekly_scanned_ios_apps)}
									</td>
								</tr>
							</tbody>
						</table>
					</div>
				{/if}
			</WhiteCard>

			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<SDKOverview {data} />
				<WhiteCard>
					{#snippet title()}
						App Ads.txt URLs
					{/snippet}
					<p class="text-xs mb-2">
						Note that many apps do not host app-ads.txt files on their web domains.
					</p>
					<table class="table mt-4">
						<thead>
							<tr class="border-b">
								<th>Total URLs</th>
								<th>URLs Scanned This Week</th>
							</tr>
						</thead>
						<tbody>
							<tr>
								<td>
									<span class="text-success-900-100">
										{formatNumberLocale(data.appsOverview.appads_success_urls)}
									</span>
									/ {formatNumberLocale(data.appsOverview.appads_urls)}
								</td>

								<td>
									<span class="text-success-900-100">
										{formatNumberLocale(data.appsOverview.appads_weekly_success_urls)}
									</span>
									/ {formatNumberLocale(data.appsOverview.appads_weekly_urls)}
								</td>
							</tr>
						</tbody>
					</table>
				</WhiteCard>
			</div>
		</div>
	</div>
</div>
