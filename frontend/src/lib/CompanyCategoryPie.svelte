<script lang="ts">
	import { PieChart, Text, Tooltip } from 'layerchart';

	type CompanyCategoryDatum = {
		group?: string;
		key?: string;
		label?: string;
		value?: number;
	};

	let { plotData, plotHeightPx = 250 } = $props();

	const palette = ['#6929C4', '#1192E8', '#005D5D', '#9F1853', '#FA4D56', '#FF832B', '#198038'];

	const normalizedPlotData = $derived.by(() => {
		return ((plotData ?? []) as CompanyCategoryDatum[])
			.map((item) => {
				const label =
					typeof item.group === 'string'
						? item.group
						: typeof item.label === 'string'
							? item.label
							: typeof item.key === 'string'
								? item.key
								: null;
				const value = typeof item.value === 'number' ? item.value : 0;

				if (!label || value <= 0) return null;

				return {
					key: label,
					label,
					value
				};
			})
			.filter((item): item is { key: string; label: string; value: number } => item !== null)
			.sort((a, b) => b.value - a.value);
	});

	const totalApps = $derived(normalizedPlotData.reduce((sum, item) => sum + item.value, 0));

	const labeledPlotData = $derived(
		normalizedPlotData.map((item, index) => ({
			...item,
			color: palette[index % palette.length],
			percentage: totalApps > 0 ? (item.value / totalApps) * 100 : 0
		}))
	);

	const formatCount = (value: number): string => {
		if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
		if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
		return value.toLocaleString();
	};

	const formatPercent = (value: number): string => `${value.toFixed(1)}%`;
</script>

<div class="p-1 md:p-2">
	<PieChart
		data={labeledPlotData}
		key="key"
		value="value"
		cRange={palette}
		innerRadius={-22}
		cornerRadius={4}
		padAngle={0.03}
		padding={{ left: 80 }}
		height={plotHeightPx}
		legend={{
			orientation: 'vertical',
			placement: 'left'
		}}
	>
		{#snippet aboveMarks()}
			<Text
				value={formatCount(totalApps)}
				textAnchor="middle"
				verticalAnchor="middle"
				class="text-xl font-semibold fill-surface-50"
				dy={-4}
			/>
			<Text
				value="Apps (all sources)"
				textAnchor="middle"
				verticalAnchor="middle"
				class="text-base"
				dy={16}
			/>
		{/snippet}

		{#snippet tooltip()}
			<Tooltip.Root>
				{#snippet children({ data })}
					<Tooltip.Header>{data.label}</Tooltip.Header>
					<Tooltip.List>
						<Tooltip.Item label="Share" value={formatPercent(data.percentage)} />
						<Tooltip.Item label="Apps" value={formatCount(data.value)} />
					</Tooltip.List>
				{/snippet}
			</Tooltip.Root>
		{/snippet}
	</PieChart>

	<!-- <div class="mt-2 grid grid-cols-1 gap-1 text-xs md:grid-cols-2">
		{#each labeledPlotData as item}
			<div
				class="flex items-center justify-between gap-3 rounded-md bg-surface-100-900/60 px-2 py-1"
			>
				<div class="flex min-w-0 items-center gap-2">
					<span class="h-2.5 w-2.5 shrink-0 rounded-full" style={`background-color: ${item.color};`}
					></span>
					<span class="truncate">{item.label}</span>
				</div>
				<span class="shrink-0 font-medium">{formatPercent(item.percentage)}</span>
			</div>
		{/each}
	</div> -->
</div>
