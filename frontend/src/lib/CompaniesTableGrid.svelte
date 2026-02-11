<script lang="ts">
	import { page } from '$app/state';
	import type { Snippet } from 'svelte';
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

	import WhiteCard from './WhiteCard.svelte';
</script>

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
			SDK data is derived by downloading the app's Android APK or iOS IPA file and unzipped. We then
			check the app's data for SDK signatures in paths, AndroidManifest.xml and the Info.plist. Many
			apps are unable to be zipped. Downloading and opening the APK or IPA takes time and resources
			thus the smaller totals.
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
				not. Additionally, below are only apps that have the ad network listed as DIRECT instead of
				RESELLER.
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
