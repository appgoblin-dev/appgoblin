<script lang="ts">
	import { BarChart, AreaChart, LineChart } from 'layerchart';
	import type { AppGlobalMetrics, AppCountryMetrics } from '../types';
	import { format, PeriodType } from '@layerstack/utils';
	import { countryCodeToEmoji } from './utils/countryCodeToEmoji';
	import { Switch } from '@skeletonlabs/skeleton-svelte';

	// Star rating colors (1-star to 5-star order)
	const red = '#E53935';
	const orange = '#FB8C00';
	const yellow = '#FDD835';
	const lightgreen = '#7CB342';
	const darkgreen = '#2E7D32';
	const starColors = [red, orange, yellow, lightgreen, darkgreen]; // 1-star to 5-star
	const keyColors = starColors;

	interface SeriesEntry {
		key: string;
		label: string;
		color: string;
	}

	function generateSeriesKeys(
		data: (AppGlobalMetrics | AppCountryMetrics)[],
		keyColors: string[],
		titleMetric: string
	): SeriesEntry[] {
		// Keys ordered from 1-star to 5-star to match color array
		const isNew = titleMetric.startsWith('new_');
		const uniqueKeys = isNew
			? ['new_one_star', 'new_two_star', 'new_three_star', 'new_four_star', 'new_five_star']
			: ['one_star', 'two_star', 'three_star', 'four_star', 'five_star'];

		// Calculate total value for each key
		const keyTotals = uniqueKeys.map((key) => ({
			key,
			total: data.reduce((sum, row) => sum + (Number(row[key as keyof typeof row]) || 0), 0)
		}));

		// Map to final format with proper color matching
		const seriesKeys = keyTotals.slice(0, keyColors.length).map((entry, index) => ({
			key: entry.key,
			label: entry.key
				? String(entry.key).charAt(0).toUpperCase() + String(entry.key).slice(1).replace('_', ' ')
				: titleMetric,
			color: keyColors[index]
		}));

		return seriesKeys;
	}

	interface Props {
		data: (AppGlobalMetrics | AppCountryMetrics)[];
		isIOS: boolean;
	}
	let { data, isIOS }: Props = $props();

	const layer = 'svg';

	// State for toggles
	let starsExpanded = $state(false);
	let showNewStars = $state(false);

	// Extract unique countries from data, or use default
	const availableCountries = $derived.by(() => {
		if (!data || data.length === 0) {
			return ['global'];
		}
		if (isIOS && 'country' in data[0]) {
			const countries = [...new Set((data as AppCountryMetrics[]).map((d) => d.country))];
			return countries.sort();
		}
		return ['global'];
	});

	// Set default selected country
	let selectedCountry = $state('global');
	let countryInitialized = $state(false);
	$effect(() => {
		if (!countryInitialized) {
			selectedCountry = isIOS ? 'US' : 'global';
			countryInitialized = true;
		}
	});

	// Filter data by selected country
	const filteredData = $derived.by(() => {
		if (!data || data.length === 0) {
			return [];
		}
		if (selectedCountry === 'global') {
			return data;
		}
		return (data as AppCountryMetrics[]).filter((d) => d.country === selectedCountry);
	});

	// Metric keys differ: AppGlobalMetrics uses week_start, cumulative_*, weekly_*; AppCountryMetrics uses snapshot_date, rating_count, new_*
	const xAxisKey = $derived(isIOS ? 'snapshot_date' : 'week_start');
	const getDate = (d: (AppGlobalMetrics | AppCountryMetrics) | undefined) =>
		d ? ((d as AppGlobalMetrics).week_start ?? (d as AppCountryMetrics).snapshot_date ?? '') : '';
	const ratingCountKey = $derived(isIOS ? 'rating_count' : 'cumulative_ratings');
	const newRatingCountKey = $derived(isIOS ? 'new_rating_count' : 'weekly_ratings');
	const newReviewCountKey = $derived(isIOS ? 'new_review_count' : 'weekly_reviews');
	const getRatingCount = (d: (AppGlobalMetrics | AppCountryMetrics) | undefined) =>
		(d ? Number((d as unknown as Record<string, unknown>)[ratingCountKey]) : 0) || 0;
	const getReviewCount = (d: (AppGlobalMetrics | AppCountryMetrics) | undefined) =>
		d && 'review_count' in d ? (d as AppCountryMetrics).review_count : 0;

	// Generate series keys based on whether we're showing new or cumulative
	let seriesKeysBar = $derived(
		showNewStars
			? generateSeriesKeys(filteredData, keyColors, 'new_one_star')
			: generateSeriesKeys(filteredData, keyColors, 'one_star')
	);

	// Format helpers
	const formatNumber = (num: number): string => {
		if (num >= 1000000) return (num / 1000000).toFixed(2) + 'M';
		if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
		return num.toFixed(0);
	};

	const formatPercent = (num: number): string => {
		return num.toFixed(2) + '%';
	};

	// Calculate summary stats from filtered data
	const latestData = $derived(filteredData[filteredData.length - 1]);
	const earliestData = $derived(filteredData[0]);

	// Calculate overall trend from earliest to latest
	const calculateOverallChange = (latest: number, earliest: number): number => {
		if (!earliest || earliest === 0) return 0;
		return ((latest - earliest) / earliest) * 100;
	};

	// Calculate 1-star to 5-star ratio
	const calculateStarRatio = (data: typeof latestData): number => {
		const oneStars = data?.one_star ?? 0;
		const fiveStars = data?.five_star ?? 0;
		if (fiveStars === 0) return 0;
		return oneStars / fiveStars;
	};

	// Calculate trend direction
	const getTrendIcon = (value: number) => (value >= 0 ? '↑' : '↓');
	const getTrendColor = (value: number) => (value >= 0 ? 'text-green-600' : 'text-red-600');
	// Inverted color for star ratio (lower is better)
	const getStarRatioColor = (value: number) => (value <= 0 ? 'text-green-600' : 'text-red-600');
</script>

<!-- Header with Summary Cards -->
<div class="mb-8">
	<div class="mb-6 flex items-center justify-between">
		<h1 class="text-2xl font-bold">App Trends</h1>

		<!-- Country Selector (visible when countries available) -->
		{#if availableCountries.length > 1 || (availableCountries.length === 1 && availableCountries[0] !== 'global')}
			<div class="flex items-center gap-3">
				<label for="country-select" class="text-sm font-medium">Country:</label>
				<select
					id="country-select"
					bind:value={selectedCountry}
					class="rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
				>
					{#each availableCountries as country}
						<option value={country}>{countryCodeToEmoji(country)} {country.toUpperCase()}</option>
					{/each}
				</select>
			</div>
		{/if}
	</div>

	<!-- Summary Cards -->
	<div
		class="grid grid-cols-1 gap-4 md:grid-cols-2"
		class:lg:grid-cols-5={!isIOS}
		class:lg:grid-cols-4={isIOS}
	>
		<!-- Date Range Card -->
		<div class="rounded-lg border p-5">
			<div class="mb-2 text-sm font-medium opacity-70">Tracking Period</div>
			<div class="mb-1 text-lg font-bold">
				{format(getDate(earliestData), PeriodType.Day, { variant: 'short' })}
			</div>
			<div class="mb-2 text-center text-xs opacity-50">to</div>
			<div class="text-lg font-bold">
				{format(getDate(latestData), PeriodType.Day, { variant: 'short' })}
			</div>
			<div class="mt-3 text-xs opacity-70">
				{filteredData.length} data points
			</div>
		</div>

		{#if !isIOS && 'cumulative_installs' in (latestData ?? {})}
			<div class="rounded-lg border p-5 shadow-sm">
				<div class="text-sm font-medium opacity-70">Total Installs</div>
				<div class="my-3 text-3xl font-bold">
					{formatNumber((latestData as AppGlobalMetrics)?.cumulative_installs ?? 0)}
				</div>
				<div class="flex items-center justify-between text-xs">
					<div class="opacity-70">
						From: <span class="font-semibold"
							>{formatNumber((earliestData as AppGlobalMetrics)?.cumulative_installs ?? 0)}</span
						>
					</div>
					<div
						class="font-semibold {getTrendColor(
							calculateOverallChange(
								(latestData as AppGlobalMetrics)?.cumulative_installs ?? 0,
								(earliestData as AppGlobalMetrics)?.cumulative_installs ?? 0
							)
						)}"
					>
						{getTrendIcon(
							calculateOverallChange(
								(latestData as AppGlobalMetrics)?.cumulative_installs ?? 0,
								(earliestData as AppGlobalMetrics)?.cumulative_installs ?? 0
							)
						)}
						{formatPercent(
							Math.abs(
								calculateOverallChange(
									(latestData as AppGlobalMetrics)?.cumulative_installs ?? 0,
									(earliestData as AppGlobalMetrics)?.cumulative_installs ?? 0
								)
							)
						)}
					</div>
				</div>
			</div>
		{/if}

		<div class="rounded-lg border p-5 shadow-sm">
			<div class="text-sm font-medium opacity-70">Average Rating</div>
			<div class="my-3 text-3xl font-bold">{(latestData?.rating ?? 0).toFixed(2)} ⭐</div>
			<div class="flex items-center justify-between text-xs">
				<div class="opacity-70">
					From: <span class="font-semibold">{(earliestData?.rating ?? 0).toFixed(2)} ⭐</span>
				</div>
				<div
					class="font-semibold {getTrendColor(
						calculateOverallChange(latestData?.rating ?? 0, earliestData?.rating ?? 0)
					)}"
				>
					{getTrendIcon(calculateOverallChange(latestData?.rating ?? 0, earliestData?.rating ?? 0))}
					{formatPercent(
						Math.abs(calculateOverallChange(latestData?.rating ?? 0, earliestData?.rating ?? 0))
					)}
				</div>
			</div>
		</div>

		<div class="rounded-lg border p-5 shadow-sm">
			<div class="text-sm font-medium opacity-70">Total Ratings</div>
			<div class="my-3 text-3xl font-bold">{formatNumber(getRatingCount(latestData))}</div>
			<div class="flex items-center justify-between text-xs">
				<div class="opacity-70">
					From: <span class="font-semibold">{formatNumber(getRatingCount(earliestData))}</span>
				</div>
				<div
					class="font-semibold {getTrendColor(
						calculateOverallChange(getRatingCount(latestData), getRatingCount(earliestData))
					)}"
				>
					{getTrendIcon(
						calculateOverallChange(getRatingCount(latestData), getRatingCount(earliestData))
					)}
					{formatPercent(
						Math.abs(
							calculateOverallChange(getRatingCount(latestData), getRatingCount(earliestData))
						)
					)}
				</div>
			</div>
		</div>

		<div class="rounded-lg border p-5 shadow-sm">
			<div class="text-sm font-medium opacity-70">Total Reviews</div>
			<div class="my-3 text-3xl font-bold">{formatNumber(getReviewCount(latestData))}</div>
			<div class="flex items-center justify-between text-xs">
				<div class="opacity-70">
					From: <span class="font-semibold">{formatNumber(getReviewCount(earliestData))}</span>
				</div>
				<div
					class="font-semibold {getTrendColor(
						calculateOverallChange(getReviewCount(latestData), getReviewCount(earliestData))
					)}"
				>
					{getTrendIcon(
						calculateOverallChange(getReviewCount(latestData), getReviewCount(earliestData))
					)}
					{formatPercent(
						Math.abs(
							calculateOverallChange(getReviewCount(latestData), getReviewCount(earliestData))
						)
					)}
				</div>
			</div>
		</div>

		<!-- Star Ratio Card (1-star / 5-star) -->
		<div class="rounded-lg border p-5 shadow-sm">
			<div class="text-sm font-medium opacity-70">1★ / 5★ Ratio</div>
			<div class="my-3 text-3xl font-bold">{calculateStarRatio(latestData).toFixed(3)}</div>
			<div class="flex items-center justify-between text-xs">
				<div class="opacity-70">
					From: <span class="font-semibold">{calculateStarRatio(earliestData).toFixed(3)}</span>
				</div>
				<div
					class="font-semibold {getStarRatioColor(
						calculateOverallChange(calculateStarRatio(latestData), calculateStarRatio(earliestData))
					)}"
				>
					{getTrendIcon(
						calculateOverallChange(calculateStarRatio(latestData), calculateStarRatio(earliestData))
					)}
					{formatPercent(
						Math.abs(
							calculateOverallChange(
								calculateStarRatio(latestData),
								calculateStarRatio(earliestData)
							)
						)
					)}
				</div>
			</div>
		</div>
	</div>
</div>

<!-- Main Content -->
<div class="space-y-8">
	<!-- Installs Section -->
	{#if !isIOS}
		<div class="rounded-lg border p-6">
			<h2 class="mb-6 text-xl font-bold">Install Analytics</h2>
			<div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
				<div>
					<h3 class="mb-3 text-sm font-semibold">Cumulative Installs</h3>
					<div class="h-[300px]">
						<AreaChart
							data={filteredData}
							x={xAxisKey}
							y="cumulative_installs"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 5 },
								yAxis: { format: (d) => formatNumber(d) }
							}}
						/>
					</div>
				</div>

				<div>
					<h3 class="mb-3 text-sm font-semibold">Weekly Installs</h3>
					<div class="h-[300px]">
						<BarChart
							data={filteredData}
							x={xAxisKey}
							y="weekly_installs"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 5 },
								yAxis: { format: (d) => formatNumber(d) }
							}}
						/>
					</div>
				</div>

				<div>
					<h3 class="mb-3 text-sm font-semibold">Install Growth Rate (%)</h3>
					<div class="h-[300px]">
						<LineChart
							data={filteredData}
							x={xAxisKey}
							y="weekly_installs_rate_of_change"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 5 },
								yAxis: { format: (d) => d.toFixed(2) + '%' }
							}}
						/>
					</div>
				</div>
			</div>
		</div>

		<!-- Engagement & Revenue Section -->
		<div class="rounded-lg border p-6">
			<h2 class="mb-6 text-xl font-bold">Engagement & Revenue</h2>
			<div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
				<div>
					<h3 class="mb-3 text-sm font-semibold">Weekly Active Users</h3>
					<div class="h-[300px]">
						<BarChart
							data={filteredData}
							x={xAxisKey}
							y="weekly_active_users"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 5 },
								yAxis: { format: (d) => formatNumber(d) }
							}}
						/>
					</div>
				</div>

				<div>
					<h3 class="mb-3 text-sm font-semibold">Weekly Ad Revenue</h3>
					<div class="h-[300px]">
						<BarChart
							data={filteredData}
							x={xAxisKey}
							y="weekly_ad_revenue"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 5 },
								yAxis: { format: (d) => formatNumber(d) }
							}}
						/>
					</div>
				</div>

				<div>
					<h3 class="mb-3 text-sm font-semibold">Weekly IAP Revenue</h3>
					<div class="h-[300px]">
						<BarChart
							data={filteredData}
							x={xAxisKey}
							y="weekly_iap_revenue"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 5 },
								yAxis: { format: (d) => formatNumber(d) }
							}}
						/>
					</div>
				</div>
			</div>
		</div>
	{/if}

	<!-- Ratings Section -->
	<div class="rounded-lg border p-6">
		<h2 class="mb-6 text-xl font-bold">Rating Analytics</h2>
		<div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
			<div>
				<h3 class="mb-3 text-sm font-semibold">Average Rating</h3>
				<div class="h-[300px]">
					<LineChart
						data={filteredData}
						x={xAxisKey}
						y="rating"
						{layer}
						props={{
							xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 5 },
							yAxis: { format: (d) => d.toFixed(2) }
						}}
					/>
				</div>
			</div>

			<div>
				<h3 class="mb-3 text-sm font-semibold">Total Rating Count</h3>
				<div class="h-[300px]">
					<AreaChart
						data={filteredData}
						x={xAxisKey}
						y={ratingCountKey}
						{layer}
						props={{
							xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 5 },
							yAxis: { format: (d) => formatNumber(d) }
						}}
					/>
				</div>
			</div>

			<div>
				<h3 class="mb-3 text-sm font-semibold">Weekly Ratings</h3>
				<div class="h-[300px]">
					<BarChart
						data={filteredData}
						x={xAxisKey}
						y={newRatingCountKey}
						{layer}
						props={{
							xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 5 },
							yAxis: { format: (d) => formatNumber(d) }
						}}
					/>
				</div>
			</div>
		</div>
	</div>

	<!-- Reviews Section -->
	{#if !isIOS}
		<div class="rounded-lg border p-6">
			<h2 class="mb-6 text-xl font-bold">Review Analytics</h2>
			<div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
				<div>
					<h3 class="mb-3 text-sm font-semibold">Total Reviews</h3>
					<div class="h-[300px]">
						<AreaChart
							data={filteredData}
							x={xAxisKey}
							y="review_count"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 5 },
								yAxis: { format: (d) => formatNumber(d) }
							}}
						/>
					</div>
				</div>

				<div>
					<h3 class="mb-3 text-sm font-semibold">Weekly Reviews</h3>
					<div class="h-[300px]">
						<BarChart
							data={filteredData}
							x={xAxisKey}
							y={newReviewCountKey}
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 5 },
								yAxis: { format: (d) => formatNumber(d) }
							}}
						/>
					</div>
				</div>

				<div>
					<h3 class="mb-3 text-sm font-semibold">Review Growth Rate (%)</h3>
					<div class="h-[300px]">
						<LineChart
							data={filteredData}
							x={xAxisKey}
							y="weekly_reviews_rate_of_change"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 5 },
								yAxis: { format: (d) => d.toFixed(2) + '%' }
							}}
						/>
					</div>
				</div>
			</div>
		</div>
	{/if}

	<!-- Sentiment Analysis Section -->
	<div class="rounded-lg border p-6">
		<div class="mb-6">
			<div class="flex items-center justify-between">
				<h2 class="text-xl font-bold">Star Rating Sentiment Analysis</h2>

				<!-- Toggle Switches -->
				<div class="flex items-center gap-6">
					<!-- Cumulative vs New Toggle -->
					<div class="flex items-center gap-3">
						<Switch onCheckedChange={() => (showNewStars = !showNewStars)}>
							<Switch.Control>
								<Switch.Thumb />
							</Switch.Control>
							<Switch.Label>Daily Ratings</Switch.Label>
							<Switch.HiddenInput />
						</Switch>
					</div>

					<!-- Count vs Percentage Toggle -->
					<div class="flex items-center gap-3">
						<Switch onCheckedChange={() => (starsExpanded = !starsExpanded)}>
							<Switch.Control>
								<Switch.Thumb />
							</Switch.Control>
							<Switch.Label>Percentage</Switch.Label>
							<Switch.HiddenInput />
						</Switch>
					</div>
				</div>
			</div>
		</div>

		<!-- Stacked Bar Chart -->
		<div class="mb-6">
			<h3 class="mb-3 text-sm font-semibold">
				{showNewStars ? 'New Star Ratings per Period' : 'Cumulative Star Rating Distribution'} Over Time
			</h3>
			<div class="h-[350px]">
				<BarChart
					data={filteredData}
					x={xAxisKey}
					series={seriesKeysBar}
					seriesLayout={starsExpanded ? 'stackExpand' : 'stack'}
					{layer}
					props={{
						xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 5 },
						yAxis: { format: (d) => (starsExpanded ? d.toFixed(0) + '%' : formatNumber(d)) }
					}}
				/>
			</div>
		</div>

		<!-- Star Distribution Overview -->
		<div class="mb-8 grid grid-cols-2 gap-4 md:grid-cols-5">
			<div class="rounded border p-4" style="border-color: {darkgreen};">
				<div class="text-xs font-medium">5 Stars ⭐⭐⭐⭐⭐</div>
				<div class="mt-2 text-xl font-bold">
					{formatNumber(latestData?.five_star ?? 0)}
				</div>
				<div class="mt-1 text-xs">
					+{formatNumber(latestData?.new_five_star ?? 0)}
				</div>
			</div>
			<div class="rounded border p-4" style="border-color: {lightgreen};">
				<div class="text-xs font-medium">4 Stars ⭐⭐⭐⭐</div>
				<div class="mt-2 text-xl font-bold">
					{formatNumber(latestData?.four_star ?? 0)}
				</div>
				<div class="mt-1 text-xs">
					+{formatNumber(latestData?.new_four_star ?? 0)}
				</div>
			</div>
			<div class="rounded border p-4" style="border-color: {yellow};">
				<div class="text-xs font-medium">3 Stars ⭐⭐⭐</div>
				<div class="mt-2 text-xl font-bold">
					{formatNumber(latestData?.three_star ?? 0)}
				</div>
				<div class="mt-1 text-xs">
					+{formatNumber(latestData?.new_three_star ?? 0)}
				</div>
			</div>
			<div class="rounded border p-4" style="border-color: {orange};">
				<div class="text-xs font-medium">2 Stars ⭐⭐</div>
				<div class="mt-2 text-xl font-bold">
					{formatNumber(latestData?.two_star ?? 0)}
				</div>
				<div class="mt-1 text-xs">
					+{formatNumber(latestData?.new_two_star ?? 0)}
				</div>
			</div>
			<div class="rounded border p-4" style="border-color: {red};">
				<div class="text-xs font-medium">1 Star ⭐</div>
				<div class="mt-2 text-xl font-bold">
					{formatNumber(latestData?.one_star ?? 0)}
				</div>
				<div class="mt-1 text-xs">
					+{formatNumber(latestData?.new_one_star ?? 0)}
				</div>
			</div>
		</div>

		<!-- 5 Star Charts -->
		<div class="mb-6">
			<h3 class="mb-4 text-lg font-semibold" style="color: {darkgreen};">5-Star Ratings</h3>
			<div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
				<div>
					<h4 class="mb-3 text-xs font-semibold opacity-70">Total 5-Star Ratings</h4>
					<div class="h-[250px]">
						<AreaChart
							data={filteredData}
							x={xAxisKey}
							y="five_star"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 4 },
								yAxis: { format: (d) => formatNumber(d) }
							}}
						/>
					</div>
				</div>
				<div>
					<h4 class="mb-3 text-xs font-semibold opacity-70">New 5-Star Ratings</h4>
					<div class="h-[250px]">
						<BarChart
							data={filteredData}
							x={xAxisKey}
							y="new_five_star"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 4 },
								yAxis: { format: (d) => formatNumber(d) }
							}}
						/>
					</div>
				</div>
				<div>
					<h4 class="mb-3 text-xs font-semibold opacity-70">5-Star Growth Rate (%)</h4>
					<div class="h-[250px]">
						<LineChart
							data={filteredData}
							x={xAxisKey}
							y="five_star_rate_of_change"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 4 },
								yAxis: { format: (d) => d.toFixed(2) + '%' }
							}}
						/>
					</div>
				</div>
			</div>
		</div>

		<!-- 4 Star Charts -->
		<div class="mb-6">
			<h3 class="mb-4 text-lg font-semibold" style="color: {lightgreen};">4-Star Ratings</h3>
			<div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
				<div>
					<h4 class="mb-3 text-xs font-semibold opacity-70">Total 4-Star Ratings</h4>
					<div class="h-[250px]">
						<AreaChart
							data={filteredData}
							x={xAxisKey}
							y="four_star"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 4 },
								yAxis: { format: (d) => formatNumber(d) }
							}}
						/>
					</div>
				</div>
				<div>
					<h4 class="mb-3 text-xs font-semibold opacity-70">New 4-Star Ratings</h4>
					<div class="h-[250px]">
						<BarChart
							data={filteredData}
							x={xAxisKey}
							y="new_four_star"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 4 },
								yAxis: { format: (d) => formatNumber(d) }
							}}
						/>
					</div>
				</div>
				<div>
					<h4 class="mb-3 text-xs font-semibold opacity-70">4-Star Growth Rate (%)</h4>
					<div class="h-[250px]">
						<LineChart
							data={filteredData}
							x={xAxisKey}
							y="four_star_rate_of_change"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 4 },
								yAxis: { format: (d) => d.toFixed(2) + '%' }
							}}
						/>
					</div>
				</div>
			</div>
		</div>

		<!-- 3 Star Charts -->
		<div class="mb-6">
			<h3 class="mb-4 text-lg font-semibold" style="color: {yellow};">3-Star Ratings</h3>
			<div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
				<div>
					<h4 class="mb-3 text-xs font-semibold opacity-70">Total 3-Star Ratings</h4>
					<div class="h-[250px]">
						<AreaChart
							data={filteredData}
							x={xAxisKey}
							y="three_star"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 4 },
								yAxis: { format: (d) => formatNumber(d) }
							}}
						/>
					</div>
				</div>
				<div>
					<h4 class="mb-3 text-xs font-semibold opacity-70">New 3-Star Ratings</h4>
					<div class="h-[250px]">
						<BarChart
							data={filteredData}
							x={xAxisKey}
							y="new_three_star"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 4 },
								yAxis: { format: (d) => formatNumber(d) }
							}}
						/>
					</div>
				</div>
				<div>
					<h4 class="mb-3 text-xs font-semibold opacity-70">3-Star Growth Rate (%)</h4>
					<div class="h-[250px]">
						<LineChart
							data={filteredData}
							x={xAxisKey}
							y="three_star_rate_of_change"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 4 },
								yAxis: { format: (d) => d.toFixed(2) + '%' }
							}}
						/>
					</div>
				</div>
			</div>
		</div>

		<!-- 2 Star Charts -->
		<div class="mb-6">
			<h3 class="mb-4 text-lg font-semibold" style="color: {orange};">2-Star Ratings</h3>
			<div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
				<div>
					<h4 class="mb-3 text-xs font-semibold opacity-70">Total 2-Star Ratings</h4>
					<div class="h-[250px]">
						<AreaChart
							data={filteredData}
							x={xAxisKey}
							y="two_star"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 4 },
								yAxis: { format: (d) => formatNumber(d) }
							}}
						/>
					</div>
				</div>
				<div>
					<h4 class="mb-3 text-xs font-semibold opacity-70">New 2-Star Ratings</h4>
					<div class="h-[250px]">
						<BarChart
							data={filteredData}
							x={xAxisKey}
							y="new_two_star"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 4 },
								yAxis: { format: (d) => formatNumber(d) }
							}}
						/>
					</div>
				</div>
				<div>
					<h4 class="mb-3 text-xs font-semibold opacity-70">2-Star Growth Rate (%)</h4>
					<div class="h-[250px]">
						<LineChart
							data={filteredData}
							x={xAxisKey}
							y="two_star_rate_of_change"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 4 },
								yAxis: { format: (d) => d.toFixed(2) + '%' }
							}}
						/>
					</div>
				</div>
			</div>
		</div>

		<!-- 1 Star Charts -->
		<div class="mb-6">
			<h3 class="mb-4 text-lg font-semibold" style="color: {red};">1-Star Ratings</h3>
			<div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
				<div>
					<h4 class="mb-3 text-xs font-semibold opacity-70">Total 1-Star Ratings</h4>
					<div class="h-[250px]">
						<AreaChart
							data={filteredData}
							x={xAxisKey}
							y="one_star"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 4 },
								yAxis: { format: (d) => formatNumber(d) }
							}}
						/>
					</div>
				</div>
				<div>
					<h4 class="mb-3 text-xs font-semibold opacity-70">New 1-Star Ratings</h4>
					<div class="h-[250px]">
						<BarChart
							data={filteredData}
							x={xAxisKey}
							y="new_one_star"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 4 },
								yAxis: { format: (d) => formatNumber(d) }
							}}
						/>
					</div>
				</div>
				<div>
					<h4 class="mb-3 text-xs font-semibold opacity-70">1-Star Growth Rate (%)</h4>
					<div class="h-[250px]">
						<LineChart
							data={filteredData}
							x={xAxisKey}
							y="one_star_rate_of_change"
							{layer}
							props={{
								xAxis: { format: (d) => format(d, PeriodType.Day, { variant: 'short' }), ticks: 4 },
								yAxis: { format: (d) => d.toFixed(2) + '%' }
							}}
						/>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>
