<script lang="ts">
	import TrendingUpIcon from 'lucide-svelte/icons/trending-up';
	import TrendingDownIcon from 'lucide-svelte/icons/trending-down';
	import UsersIcon from 'lucide-svelte/icons/users';
	import DollarSignIcon from 'lucide-svelte/icons/dollar-sign';

	import IconDownload from '$lib/svg/IconDownload.svelte';
	import Star from './Star.svelte';
	import { formatNumber, getRevenueBucket } from '$lib/utils/formatNumber';

	import type { AppFullDetail } from '../types';
	interface Props {
		app: AppFullDetail;
	}

	let { app }: Props = $props();

	let app_install_estimate_min = $derived(app.rating_count * 50);
	let app_install_estimate_max = $derived(app.rating_count * 100);

	let monthlyActiveUsers = $derived(Number(app.monthly_active_users) || 0);
	let monthlyAdRevenue = $derived(Number(app.monthly_ad_revenue) || 0);
	let monthlyIapRevenue = $derived(Number(app.monthly_iap_revenue) || 0);
	let monthlyTotalRevenue = $derived(monthlyAdRevenue + monthlyIapRevenue);

	let monthlyAdRevenueShare = $derived(
		monthlyTotalRevenue > 0 ? Math.round((monthlyAdRevenue / monthlyTotalRevenue) * 100) : 0
	);
	let monthlyIapRevenueShare = $derived(monthlyTotalRevenue > 0 ? 100 - monthlyAdRevenueShare : 0);
</script>

<div class="inline-block w-full">
	<div class="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4 p-3 md:p-4 text-primary-900-100">
		<!-- Primary Metrics -->
		<div class="space-y-3">
			<!-- Installs -->
			<div class="flex items-start sm:items-center gap-2">
				{#if app.installs && app.installs != 0}
					<div class="text-primary-600-400">
						<IconDownload />
					</div>
					<div class="leading-tight">
						<span class="font-semibold text-base md:text-lg">{formatNumber(app.installs)}</span>
						<span class="text-primary-600-400 text-sm ml-1">installs</span>
					</div>
				{:else if app.rating_count != 0}
					<div class="text-primary-600-400">
						<IconDownload />
					</div>
					<div class="leading-tight">
						<span class="font-semibold text-base md:text-lg">
							~{formatNumber(app_install_estimate_min)} - {formatNumber(app_install_estimate_max)}
						</span>
						<span class="text-primary-600-400 text-sm ml-1">est. installs</span>
					</div>
				{:else}
					<div class="text-primary-600-400">
						<IconDownload />
					</div>
					<span class="text-primary-600-400 text-sm">Installs not yet available</span>
				{/if}
			</div>

			<!-- Ratings -->
			<div class="flex items-start sm:items-center gap-2">
				{#if app.rating_count != 0}
					<Star class="w-5 h-5" />
					<div class="leading-tight">
						<span class="font-semibold text-base md:text-lg">{formatNumber(app.rating_count)}</span>
						<span class="text-primary-600-400 text-sm ml-1">ratings</span>
					</div>
				{:else}
					<Star class="w-5 h-5 text-primary-600-400" />
					<span class="text-primary-600-400 text-sm">Ratings not yet available</span>
				{/if}
			</div>
		</div>

		<!-- Engagement & Revenue Metrics -->
		<div class="space-y-3">
			<!-- Monthly Active Users -->
			<div class="flex items-start sm:items-center gap-2">
				{#if monthlyActiveUsers > 0}
					<UsersIcon class="w-5 h-5 text-primary-600-400" />
					<div class="leading-tight">
						<span class="font-semibold text-base md:text-lg"
							>{formatNumber(monthlyActiveUsers)}</span
						>
						<span class="text-primary-600-400 text-sm ml-1">monthly active users</span>
					</div>
				{:else}
					<UsersIcon class="w-5 h-5 text-primary-600-400" />
					<span class="text-primary-600-400 text-sm">MAU not available</span>
				{/if}
			</div>

			<!-- Monthly Revenue -->
			<div class="flex items-start sm:items-center gap-2">
				{#if monthlyTotalRevenue > 0}
					<DollarSignIcon class="w-5 h-5 text-success-900-100" />
					<div class="flex-1 min-w-0 flex flex-col">
						<div>
							<span class="font-semibold text-base md:text-lg text-success-900-100"
								>{getRevenueBucket(monthlyTotalRevenue)}</span
							>
							<span class="text-primary-600-400 text-sm ml-1">monthly revenue est.</span>
						</div>
						<!-- Revenue split visualization -->
						<div class="flex items-center gap-2 mt-1">
							<div class="flex-1 flex h-2 rounded-full overflow-hidden bg-primary-200-800">
								<div
									class="bg-success-800-200"
									style="width: {monthlyIapRevenueShare}%"
									title="IAP {monthlyIapRevenueShare}%"
								></div>
								<div
									class="bg-primary-800-200"
									style="width: {monthlyAdRevenueShare}%"
									title="Ad {monthlyAdRevenueShare}%"
								></div>
							</div>
						</div>
						<div class="text-xs ml-0.5 flex flex-wrap items-center gap-x-2 gap-y-1 mt-0.5">
							<span class="flex items-center gap-1">
								<span class="w-2 h-2 rounded-full bg-success-800-200"></span>
								<span class="text-success-800-200">IAP {monthlyIapRevenueShare}%</span>
							</span>
							<span class="text-primary-600-400">·</span>
							<span class="flex items-center gap-1">
								<span class="w-2 h-2 rounded-full bg-primary-800-200"></span>
								<span class="text-primary-800-200">Ad {monthlyAdRevenueShare}%</span>
							</span>
						</div>
					</div>
				{:else}
					<DollarSignIcon class="w-5 h-5 text-primary-600-400" />
					<span class="text-primary-600-400 text-sm">Revenue not available</span>
				{/if}
			</div>
		</div>

		<!-- Install Trends -->
		{#if app.installs_sum_1w > 0 || app.installs_sum_4w > 0}
			<div class="col-span-1 md:col-span-2 border-t border-primary-200-800 pt-3 space-y-2">
				<div class="text-xs font-medium text-primary-600-400 uppercase tracking-wide">
					Install Trends
				</div>
				<div class="grid grid-cols-1 md:grid-cols-2 gap-2">
					{#if app.installs_sum_1w > 0}
						<div
							class="flex items-start sm:items-center justify-between gap-2 bg-primary-50-900/20 rounded px-3 py-2"
						>
							<div class="flex items-center gap-2 min-w-0">
								<span class="text-sm text-primary-600-400">Weekly</span>
								<span class="font-medium text-sm">+{formatNumber(app.installs_sum_1w)}</span>
							</div>
							{#if app.installs_z_score_2w > 1}
								<div class="flex items-center gap-1 text-success-600">
									<TrendingUpIcon class="w-4 h-4" />
									<span class="text-xs font-medium">Trending</span>
								</div>
							{:else if app.installs_z_score_2w < -1}
								<div class="flex items-center gap-1 text-danger-600">
									<TrendingDownIcon class="w-4 h-4" />
									<span class="text-xs font-medium">Declining</span>
								</div>
							{:else}
								<span class="text-xs text-primary-600-400">Steady</span>
							{/if}
						</div>
					{/if}
					{#if app.installs_sum_4w > 0}
						<div
							class="flex items-start sm:items-center justify-between gap-2 bg-primary-50-900/20 rounded px-3 py-2"
						>
							<div class="flex items-center gap-2 min-w-0">
								<span class="text-sm text-primary-600-400">Monthly</span>
								<span class="font-medium text-sm">+{formatNumber(app.installs_sum_4w)}</span>
							</div>
							{#if app.installs_z_score_4w > 1}
								<div class="flex items-center gap-1 text-success-600">
									<TrendingUpIcon class="w-4 h-4" />
									<span class="text-xs font-medium">Trending</span>
								</div>
							{:else if app.installs_z_score_4w < -1}
								<div class="flex items-center gap-1 text-danger-600">
									<TrendingDownIcon class="w-4 h-4" />
									<span class="text-xs font-medium">Declining</span>
								</div>
							{:else}
								<span class="text-xs text-primary-600-400">Steady</span>
							{/if}
						</div>
					{/if}
				</div>
			</div>
		{/if}
	</div>
</div>
