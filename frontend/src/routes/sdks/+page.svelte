<script lang="ts">
	import SDKsLatestAppsTable from '$lib/SDKsLatestAppsTable.svelte';
	import SDKsUserRequestAppsTable from '$lib/SDKsUserRequestAppsTable.svelte';
	import WhiteCard from '$lib/WhiteCard.svelte';
	import SDKOverview from '$lib/utils/SDKOverview.svelte';
	import { Tabs } from '@skeletonlabs/skeleton-svelte';

	let { data } = $props();
</script>

<div class="mx-2 md:mx-16">
	<h1 class="text-2xl font-bold">Free Mobile App SDK Scanning</h1>

	<div class="grid grid-cols-1 md:grid-cols-2 gap-4 my-6">
		<WhiteCard>
			{#snippet title()}
				SDKs Overview
			{/snippet}
			<p class="text-sm md:text-base p-2 md:p-4">
				AppGoblin provides free SDK and API scanning to detect mobile app SDKs, trackers and
				permissions. Users can request apps to be SDK and API scanned for free on AppGoblin.
			</p>
		</WhiteCard>
		<SDKOverview {data} />
	</div>

	<div>
		<Tabs defaultValue="user_requested">
			<Tabs.List>
				<Tabs.Trigger value="user_requested" class="p-0 md:p-8"
					><p class="text-xs md:text-base">User Requests</p></Tabs.Trigger
				>
				<Tabs.Trigger value="latest_success" class="p-0 md:p-8"
					><p class="text-xs md:text-base">Latest Success</p></Tabs.Trigger
				>
				<Tabs.Trigger value="latest_failed" class="p-0 md:p-8"
					><p class="text-xs md:text-base">Latest Failed</p></Tabs.Trigger
				>
				<Tabs.Indicator />
			</Tabs.List>

			<Tabs.Content value="user_requested">
				<h2 class="text-2xl font-bold">User Requested App Scans</h2>
				<p class="text-sm md:text-base p-2 md:p-4">
					Users can request apps to be SDK and API scanned for free on AppGoblin. User requested app
					SDK scans are automated and usually happen quickly (~1hr). The results will aggregate to
					the dashboard in about a day. If you see that your request failed, please reach out on
					Discord/Email as manual processing may be needed.
				</p>
				{#await data.sdksUserRequested}
					loading
				{:then mySdksUserRequested}
					<WhiteCard>
						{#snippet title()}
							User Requests
						{/snippet}

						{#if mySdksUserRequested.user_requested_latest_apps && mySdksUserRequested.user_requested_latest_apps.length > 0}
							<SDKsUserRequestAppsTable
								entries_table={mySdksUserRequested.user_requested_latest_apps}
							/>
						{/if}
					</WhiteCard>
				{/await}
			</Tabs.Content>
			<Tabs.Content value="latest_success">
				<h2 class="text-2xl font-bold">Latest Successfully Crawled Apps</h2>

				<div class="grid grid-cols-1 md:grid-cols-2 gap-2 md:gap-6">
					{#await data.sdksOverview}
						loading
					{:then mySdksOverview}
						<WhiteCard>
							{#snippet title()}
								Android Successfully Crawled Apps
							{/snippet}

							{#if mySdksOverview.android_success_latest_apps && mySdksOverview.android_success_latest_apps.length > 0}
								<SDKsLatestAppsTable entries_table={mySdksOverview.android_success_latest_apps} />
							{/if}
						</WhiteCard>

						<WhiteCard>
							{#snippet title()}
								iOS Apps SDKs
							{/snippet}

							{#if mySdksOverview.ios_success_latest_apps && mySdksOverview.ios_success_latest_apps.length > 0}
								<SDKsLatestAppsTable entries_table={mySdksOverview.ios_success_latest_apps} />
							{/if}
						</WhiteCard>
					{/await}
				</div></Tabs.Content
			>
			<Tabs.Content value="latest_failed">
				<h2 class="text-2xl font-bold">Latest Failed to Crawled Apps</h2>

				<div class="grid grid-cols-1 md:grid-cols-2 gap-2 md:gap-6">
					{#await data.sdksOverview}
						loading
					{:then mySdksOverview}
						<WhiteCard>
							{#snippet title()}
								Android Failed to Crawled Apps
							{/snippet}

							{#if mySdksOverview.android_failed_latest_apps && mySdksOverview.android_failed_latest_apps.length > 0}
								<SDKsLatestAppsTable entries_table={mySdksOverview.android_failed_latest_apps} />
							{/if}
						</WhiteCard>

						<WhiteCard>
							{#snippet title()}
								iOS Failed to Crawled Apps
							{/snippet}

							{#if mySdksOverview.ios_failed_latest_apps && mySdksOverview.ios_failed_latest_apps.length > 0}
								<SDKsLatestAppsTable entries_table={mySdksOverview.ios_failed_latest_apps} />
							{/if}
						</WhiteCard>
					{/await}
				</div>
			</Tabs.Content>
		</Tabs>
	</div>
</div>
