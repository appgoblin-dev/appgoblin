<script lang="ts">
	import { BarChart, Tooltip } from 'layerchart';

	type TopCompanyPoint = {
		group: string;
		value: number;
		company_domain?: string | null;
		company_logo_url?: string | null;
	};

	interface Props {
		plotData: TopCompanyPoint[];
		plotTitle?: string;
		plotHeightPx?: number;
	}

	let { plotData, plotTitle, plotHeightPx }: Props = $props();

	const sortedPlotData = $derived([...plotData].sort((a, b) => b.value - a.value));

	const palette = ['#6929C4', '#1192E8', '#005D5D', '#9F1853', '#FA4D56'];
	const logoSize = 36;
	const logoOffset = 10;

	const chartHeight = $derived(plotHeightPx ?? Math.max(220, sortedPlotData.length * 40 + 40));

	const hasLogoData = $derived(
		sortedPlotData.some((d) =>
			Boolean(d.company_logo_url && String(d.company_logo_url).trim().length > 0)
		)
	);

	const chartPadding = $derived({
		top: 4,
		right: 6,
		bottom: 8,
		left: hasLogoData ? 74 : 4
	});

	const formatCount = (value: number): string => {
		if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
		if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
		return value.toLocaleString();
	};

	const getLogoHref = (companyLogoUrl?: string | null): string | null => {
		if (!companyLogoUrl) return null;
		const trimmed = companyLogoUrl.trim();
		if (!trimmed) return null;
		if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) return trimmed;
		return `https://media.appgoblin.info/${trimmed}`;
	};
</script>

<div class="p-1 md:p-2">
	{#if plotTitle}
		<h3 class="mb-1 text-sm font-semibold">{plotTitle}</h3>
	{/if}

	<BarChart
		data={sortedPlotData}
		x="value"
		y="group"
		c="group"
		cRange={palette}
		bandPadding={0.22}
		orientation="horizontal"
		axis="y"
		rule={false}
		height={chartHeight}
		padding={chartPadding}
		props={{
			xAxis: { format: 'metric', ticks: 4 },
			yAxis: {
				tickLabelProps: {
					textAnchor: 'start',
					dx: 8,
					dy: 2,
					class: 'text-[11px] font-semibold fill-white stroke-none'
				},
				tickLength: 0
			}
		}}
	>
		{#snippet aboveMarks({ context })}
			{#if hasLogoData}
				{#each sortedPlotData as d}
					{@const logoHref = getLogoHref(d.company_logo_url)}
					{#if logoHref}
						<image
							href={logoHref}
							x={-logoSize - logoOffset}
							y={(context.yScale?.(d.group) ?? 0) +
								(context.yScale?.bandwidth?.() ?? 0) / 2 -
								logoSize / 2}
							width={logoSize}
							height={logoSize}
							clip-path="circle(45%)"
							preserveAspectRatio="xMidYMid slice"
						/>
					{/if}
				{/each}
			{/if}
		{/snippet}

		{#snippet tooltip()}
			<Tooltip.Root>
				{#snippet children({ data })}
					<Tooltip.Header>{data.group}</Tooltip.Header>
					<Tooltip.List>
						<Tooltip.Item label="Apps" value={formatCount(data.value)} />
					</Tooltip.List>
				{/snippet}
			</Tooltip.Root>
		{/snippet}
	</BarChart>
</div>
