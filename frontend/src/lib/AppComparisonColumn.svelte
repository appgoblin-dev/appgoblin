<script lang="ts">
	import { format, PeriodType } from '@layerstack/utils';
	import { AreaChart, LineChart, BarChart } from 'layerchart';
	import AppSdkOverview from '$lib/AppSDKOverview.svelte';

	export let app: any;
	export let history: any;
	export let histogram: any;
	export let sdks: any;
	export let companyTypes: any;

	// Helper to safely format numbers
	const formatNumber = (num: number | null | undefined): string => {
		if (num == null) return '-';
		if (num >= 1000000) return (num / 1000000).toFixed(2) + 'M';
		if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
		return num.toLocaleString();
	};

	const formatDate = (dateStr: string | null | undefined): string => {
		if (!dateStr) return '-';
		return new Date(dateStr).toLocaleDateString();
	};

	const layer = 'svg';

	// Star rating colors (1-star to 5-star)
	const starColors = ['#E53935', '#FB8C00', '#FDD835', '#7CB342', '#2E7D32'];

	const processHistogram = (histData: any) => {
		if (!histData?.histogram) return [];
		const h = histData.histogram;
		return [
			{ label: '1★', value: h.one_star ?? 0, color: starColors[0] },
			{ label: '2★', value: h.two_star ?? 0, color: starColors[1] },
			{ label: '3★', value: h.three_star ?? 0, color: starColors[2] },
			{ label: '4★', value: h.four_star ?? 0, color: starColors[3] },
			{ label: '5★', value: h.five_star ?? 0, color: starColors[4] }
		];
	};

	$: hist = processHistogram(histogram);
</script>

<div class="space-y-6">
	<!-- Header -->
	<a
		href={`/apps/${app.store_id}`}
		class="block hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors flex flex-col md:flex-row items-center md:items-start gap-2 md:gap-4 rounded-lg border bg-surface-50 p-2 md:p-4 shadow-sm dark:bg-surface-900"
	>
		<img
			src={app.app_icon_url}
			alt={app.name}
			class="h-12 w-12 md:h-20 md:w-20 rounded-xl shadow-md"
		/>
		<div class="text-center md:text-left min-w-0 w-full">
			<h2 class="text-sm md:text-xl font-bold truncate leading-tight">{app.name}</h2>
			<p class="text-[10px] md:text-sm opacity-70 truncate">{app.developer_name}</p>
			<div
				class="mt-1 md:mt-2 flex flex-wrap justify-center md:justify-start gap-1 md:gap-2 text-[10px] md:text-xs font-semibold"
			>
				<span class="rounded px-1 md:px-2 py-0.5 md:py-1 truncate max-w-[80px] md:max-w-none"
					>{app.store}</span
				>
				<span class="rounded px-1 md:px-2 py-0.5 md:py-1 truncate max-w-[80px] md:max-w-none"
					>{app.category}</span
				>
			</div>
		</div>
	</a>

	<!-- Key Metrics Table -->
	<div class="rounded-lg border p-2 md:p-4">
		<h3 class="mb-2 md:mb-4 text-sm md:text-lg font-semibold border-b pb-1 md:pb-2">Key Metrics</h3>
		<dl class="grid grid-cols-1 gap-y-1 md:gap-y-3 text-xs md:text-sm">
			<div class="grid grid-cols-2">
				<dt class="opacity-70">Rating</dt>
				<dd class="font-bold text-sm md:text-lg">{app.rating?.toFixed(2) ?? '-'} ⭐</dd>
			</div>

			<div class="grid grid-cols-2">
				<dt class="opacity-70">Total Ratings</dt>
				<dd class="font-bold">{formatNumber(app.rating_count)}</dd>
			</div>

			<div class="grid grid-cols-2">
				<dt class="opacity-70">Installs</dt>
				<dd class="font-bold">{formatNumber(app.installs)}</dd>
			</div>

			<div class="grid grid-cols-2">
				<dt class="opacity-70">Ad Supported</dt>
				<dd class="font-bold">{app.ad_supported ? 'Yes' : 'No'}</dd>
			</div>

			<div class="grid grid-cols-2">
				<dt class="opacity-70">In-App Purchases</dt>
				<dd class="font-bold">{app.in_app_purchases ? 'Yes' : 'No'}</dd>
			</div>

			<div class="grid grid-cols-2">
				<dt class="opacity-70">Release Date</dt>
				<dd class="font-bold">{formatDate(app.release_date)}</dd>
			</div>

			<div class="grid grid-cols-2">
				<dt class="opacity-70">Last Updated</dt>
				<dd class="font-bold">{formatDate(app.store_last_updated)}</dd>
			</div>

			<div class="grid grid-cols-2">
				<dt class="opacity-70">Version</dt>
				<dd class="font-mono text-[10px] md:text-xs truncate">{app.version_code ?? '-'}</dd>
			</div>
		</dl>
	</div>

	<!-- SDK Overview -->
	<div class="rounded-lg border p-2 md:p-4">
		<h3 class="mb-1 md:mb-2 text-xs md:text-sm font-semibold opacity-70">SDK Overview</h3>
		<div class="h-64 md:h-96 overflow-y-auto text-xs md:text-sm">
			<AppSdkOverview myapp={app} myPackageInfo={sdks} {companyTypes} />
		</div>
	</div>

	<!-- Rating Distribution -->
	<div class="rounded-lg border p-4">
		<h3 class="mb-2 text-sm font-semibold opacity-70">Rating Distribution</h3>
		<div class="h-[200px]">
			{#if hist.length > 0}
				<BarChart
					data={hist}
					x="label"
					y="value"
					c="color"
					{layer}
					props={{
						yAxis: { format: (d: number) => formatNumber(d) }
					}}
				/>
			{:else}
				<div class="flex h-full items-center justify-center text-sm opacity-50">
					No histogram data
				</div>
			{/if}
		</div>
	</div>

	<!-- Charts -->
	<div class="rounded-lg border p-4">
		<h3 class="mb-2 text-sm font-semibold opacity-70">Installs History</h3>
		<div class="h-[200px]">
			{#if history && history.length > 0}
				<AreaChart
					data={history}
					x="week_start"
					y="cumulative_installs"
					{layer}
					props={{
						xAxis: {
							format: (d: any) => format(d, PeriodType.Day, { variant: 'short' }),
							ticks: 4
						},
						yAxis: { format: (d: number) => formatNumber(d) }
					}}
				/>
			{:else}
				<div class="flex h-full items-center justify-center text-sm opacity-50">
					No history data
				</div>
			{/if}
		</div>
	</div>

	<!-- Growth Charts -->
	<div class="rounded-lg border p-2 md:p-4">
		<h3 class="mb-2 text-sm font-semibold opacity-70">Installs Growth Rate</h3>
		<div class="h-[200px]">
			{#if history && history.length > 0 && history.some((d: any) => d.weekly_installs_rate_of_change !== undefined)}
				<LineChart
					data={history}
					x="week_start"
					y="weekly_installs_rate_of_change"
					{layer}
					props={{
						xAxis: {
							format: (d: any) => format(d, PeriodType.Day, { variant: 'short' }),
							ticks: 4
						},
						yAxis: { format: (d: number) => d.toFixed(2) + '%' }
					}}
				/>
			{:else}
				<div class="flex h-full items-center justify-center text-sm opacity-50">No growth data</div>
			{/if}
		</div>
	</div>

	<div class="rounded-lg border p-2 md:p-4">
		<h3 class="mb-2 text-sm font-semibold opacity-70 text-green-700 dark:text-green-400">
			5-Star Growth Rate
		</h3>
		<div class="h-[200px]">
			{#if history && history.length > 0 && history.some((d: any) => d.five_star_rate_of_change !== undefined)}
				<LineChart
					data={history}
					x="week_start"
					y="five_star_rate_of_change"
					series={[{ key: 'five_star_rate_of_change', color: '#2E7D32' }]}
					{layer}
					props={{
						xAxis: {
							format: (d: any) => format(d, PeriodType.Day, { variant: 'short' }),
							ticks: 4
						},
						yAxis: { format: (d: number) => d.toFixed(2) + '%' }
					}}
				/>
			{:else}
				<div class="flex h-full items-center justify-center text-sm opacity-50">No growth data</div>
			{/if}
		</div>
	</div>

	<div class="rounded-lg border p-2 md:p-4">
		<h3 class="mb-2 text-sm font-semibold opacity-70 text-red-700 dark:text-red-400">
			1-Star Growth Rate
		</h3>
		<div class="h-[200px]">
			{#if history && history.length > 0 && history.some((d: any) => d.one_star_rate_of_change !== undefined)}
				<LineChart
					data={history}
					x="week_start"
					y="one_star_rate_of_change"
					series={[{ key: 'one_star_rate_of_change', color: '#E53935' }]}
					{layer}
					props={{
						xAxis: {
							format: (d: any) => format(d, PeriodType.Day, { variant: 'short' }),
							ticks: 4
						},
						yAxis: { format: (d: number) => d.toFixed(2) + '%' }
					}}
				/>
			{:else}
				<div class="flex h-full items-center justify-center text-sm opacity-50">No growth data</div>
			{/if}
		</div>
	</div>
</div>
