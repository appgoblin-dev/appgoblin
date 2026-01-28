<script lang="ts">
	import type { AppFullDetail, RankedApps } from '../types';

	import Rating from '$lib/StarsRating.svelte';
	import IconDownload from '$lib/svg/IconDownload.svelte';
	import IconGoogle from './svg/IconGoogle.svelte';
	import IconiOs from './svg/IconiOS.svelte';
	import { formatNumber } from '$lib/utils/formatNumber';
	import TrendingDownIcon from 'lucide-svelte/icons/trending-down';
	import TrendingUpIcon from 'lucide-svelte/icons/trending-up';

	interface Props {
		app: AppFullDetail | RankedApps;
		showHeader: boolean;
	}

	let { app, showHeader = false }: Props = $props();

	function getHeaderImage(app: AppFullDetail | RankedApps) {
		if ('featured_image_url' in app && app.featured_image_url && app.featured_image_url != 'null') {
			return app.featured_image_url;
		} else if (
			'tablet_image_url_1' in app &&
			app.tablet_image_url_1 &&
			app.tablet_image_url_1 != 'null'
		) {
			return app.tablet_image_url_1;
		} else if (
			'phone_image_url_1' in app &&
			app.phone_image_url_1 &&
			app.phone_image_url_1 != 'null'
		) {
			return app.phone_image_url_1;
		}
	}
</script>

<a href={`/apps/${app.store_id}`} class={`card card-hover overflow-hidden col-span-2`}>
	<div>
		<header>
			<div>
				{#if showHeader && getHeaderImage(app)}
					<!-- Show Featured Image (spans 2 cols) -->
					<div class="justify-center">
						<img
							class="h-48 w-full object-top object-none rounded-lg"
							src={getHeaderImage(app)}
							alt={app.name}
							referrerpolicy="no-referrer"
							loading="lazy"
						/>
					</div>
				{:else if showHeader}
					<!-- Show Icon Only (smaller) -->
					<div class="mx-auto block text-center">
						<img
							class="h-48 w-48 rounded-lg mx-auto"
							src={app.app_icon_url}
							alt={app.name}
							referrerpolicy="no-referrer"
							loading="lazy"
						/>
					</div>
				{/if}

				<div class="flex flex-row">
					<div class="flex text-left flex-col">
						<img
							class="w-18 md:w-24 rounded-lg"
							src={app.app_icon_url}
							alt={app.name}
							referrerpolicy="no-referrer"
							loading="lazy"
						/>
						{#if app.rating_count && app.rating_count != 0}
							<div class="md:hidden">
								<Rating total={5} size={14} rating={app.rating} />
								<div class="inline-flex md:hidden gap-2 text-primary-800-200 text-xs">
									{formatNumber(app.rating_count)} ratings
								</div>
							</div>
						{/if}
					</div>
					<div class="grid grid-cols-1 p-2">
						<div class="flex">
							<p class="text-base md:text-xl text-primary-900-100">{app.name}</p>
						</div>

						<div class="flex flex-row justify-start items-center gap-2 text-primary-900-100">
							{#if app.store == 1 || (app.store_link && app.store_link.includes('google.com'))}
								<IconGoogle size="18" />
							{/if}
							{#if app.store == 2 || (app.store_link && app.store_link.includes('apple.com'))}
								<IconiOs size="18" />
							{/if}
							<p class="text-sm md:base text-primary-900-100">{app.developer_name || ''}</p>
						</div>
						<!-- Ratings: STARS (123) -->
						{#if app.rating_count && app.rating_count != 0}
							<div class="hidden md:inline-flex gap-2 text-primary-800-200 text-xs md:text-sm">
								<Rating total={5} size={18} rating={app.rating} />
								{formatNumber(app.rating_count)} ratings
							</div>
						{/if}
						<div class="flex flex-row gap-2 text-primary-900-100 text-xs md:text-sm">
							<!-- Installs DownloadIcon -->
							{#if app.installs && app.installs != 0}
								<div class="block p-0">
									<div class="inline-flex items-center gap-1">
										<IconDownload />
										{formatNumber(app.installs)} installs
									</div>
								</div>
							{/if}
						</div>
						<!-- installs week trend -->
						<div class="flex items-center gap-1 text-primary-800-200 text-xs md:text-sm">
							<span class="inline-flex items-center gap-1">
								{#if app.installs_sum_1w > 0}
									+{formatNumber(app.installs_sum_4w)}
									monthly installs
								{/if}
								{#if !app.installs && app.ratings_sum_4w > 0}
									~{formatNumber(app.ratings_sum_4w * 50)}
									monthly installs
								{/if}
							</span>
						</div>
					</div>
				</div>
			</div>
		</header>
	</div>
</a>
