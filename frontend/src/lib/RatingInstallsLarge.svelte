<script lang="ts">
	import TrendingUpIcon from 'lucide-svelte/icons/trending-up';
	import TrendingDownIcon from 'lucide-svelte/icons/trending-down';

	import IconDownload from '$lib/svg/IconDownload.svelte';
	import Star from './Star.svelte';
	import { formatNumber } from '$lib/utils/formatNumber';

	import type { AppFullDetail } from '../types';
	interface Props {
		app: AppFullDetail;
	}

	let { app }: Props = $props();

	let app_install_estimate_min = $derived(app.rating_count * 50);
	let app_install_estimate_max = $derived(app.rating_count * 100);
</script>

<div class="inline-block">
	<div
		class="grid grid-cols-2 md:grid-cols-1 p-0 md:p-2 text-primary-900-100 text-xl gap-0 md:gap-4"
	>
		<div class="items-center">
			{#if app.installs && app.installs != 0}
				<div class="flex items-center gap-2">
					<IconDownload />
					<span class="font-medium">{formatNumber(app.installs)}</span> installs
				</div>
			{:else if app.rating_count != 0}
				<div class="flex items-center">
					<IconDownload />
					<span class="font-medium">
						~{formatNumber(app_install_estimate_min)}
						- {formatNumber(app_install_estimate_max)}</span
					>
				</div>
			{:else}
				<span class="text-primary-600-400">Installs not yet available</span>
			{/if}
		</div>

		{#if app.rating_count != 0}
			<div class="flex items-center gap-2">
				<Star />
				<span class="font-medium"> {formatNumber(app.rating_count)}</span> ratings
			</div>
		{:else}
			<span class="text-primary-600-400">Ratings not yet available</span>
		{/if}

		<!-- installs week trend -->
		{#if app.installs_sum_1w > 0}
			<div class="flex items-center gap-1 text-primary-800-200">
				<span class="text-primary-600-400 text-xs md:text-base">
					+{formatNumber(app.installs_sum_1w)}
					weekly installs
					{#if app.installs_z_score_2w > 1}
						<div class="flex items-center gap-1 text-success-900-100">
							<TrendingUpIcon />
						</div>
					{:else if app.installs_z_score_2w < -1}
						<div class="flex items-center gap-1 text-danger-900-100">
							<TrendingDownIcon />
						</div>
					{:else}
						<div class="flex items-center gap-0 text-primary-600-400 text-xs">
							<span>trend steady</span>
						</div>
					{/if}
				</span>
			</div>
		{/if}
		<!-- installs month trend -->
		{#if app.installs_sum_4w > 0}
			<div class="flex items-center gap-1 text-primary-800-200">
				<span class="text-primary-600-400 text-xs md:text-base">
					+{formatNumber(app.installs_sum_4w)}
					monthly installs
					{#if app.installs_z_score_4w > 1}
						<div class="flex items-center gap-1 text-success-900-100">
							<TrendingUpIcon />
						</div>
					{:else if app.installs_z_score_4w < -1}
						<div class="flex items-center gap-1 text-danger-900-100">
							<TrendingDownIcon />
						</div>
					{:else}
						<div class="flex items-center gap-1 text-primary-600-400 text-xs">
							<span>trend steady</span>
						</div>
					{/if}
				</span>
			</div>
		{/if}
	</div>
</div>
