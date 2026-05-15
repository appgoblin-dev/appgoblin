<script lang="ts">
	import { LineChart } from 'layerchart';
	import { formatNumber } from '$lib/utils/formatNumber';
	import type { CompanyTrendPoint, CompanyTrendSummary, CompanyTrends } from '../types';

	interface Props {
		trends: CompanyTrends | null | undefined;
		companyName: string;
	}

	type SourceMeta = {
		label: string;
		primary: string;
		secondary: string;
	};

	type IndexedTrendPoint = CompanyTrendPoint & {
		period_index: number;
	};

	type SourceCard = {
		key: string;
		platform: string;
		platformLabel: string;
		label: string;
		colors: SourceMeta;
		summary: CompanyTrendSummary;
		history: IndexedTrendPoint[];
		pastYear: IndexedTrendPoint[];
		trailingYearShareChange: number | null;
	};

	type PlatformSection = {
		platform: string;
		platformLabel: string;
		cards: SourceCard[];
	};

	const palette = ['#6929C4', '#1192E8', '#005D5D', '#9F1853', '#FA4D56'];
	const platformOrder: Record<string, number> = { ios: 0, android: 1 };
	const sourceOrder: Record<string, number> = { sdk_api: 0, app_ads_direct: 1 };
	const sourceLabels: Record<string, string> = {
		sdk_api: 'SDK/API Footprint',
		app_ads_direct: 'App-ads.txt DIRECT'
	};
	const sourceMeta: Record<string, SourceMeta> = {
		ios_sdk_api: {
			label: 'SDK/API Footprint',
			primary: palette[0],
			secondary: palette[1]
		},
		ios_app_ads_direct: {
			label: 'App-ads.txt DIRECT',
			primary: palette[1],
			secondary: palette[0]
		},
		android_sdk_api: {
			label: 'SDK/API Footprint',
			primary: palette[2],
			secondary: palette[3]
		},
		android_app_ads_direct: {
			label: 'App-ads.txt DIRECT',
			primary: palette[3],
			secondary: palette[2]
		}
	};
	const defaultSourceMeta: SourceMeta = {
		label: 'Quarterly Signal',
		primary: palette[4],
		secondary: palette[1]
	};

	let { trends, companyName }: Props = $props();

	const titleCase = (value: string): string =>
		value.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());

	const formatTrimmed = (value: number, digits: number): string =>
		value.toFixed(digits).replace(/\.0+$|(?<=\.[0-9]*[1-9])0+$/, '');

	const getShareDigits = (value: number): number => {
		const absolute = Math.abs(value);
		if (absolute >= 10) return 2;
		if (absolute >= 1) return 3;
		if (absolute >= 0.1) return 4;
		if (absolute >= 0.01) return 5;
		return 6;
	};

	const formatSharePercent = (value: number | null | undefined): string => {
		if (typeof value !== 'number' || Number.isNaN(value)) return 'n/a';
		return `${formatTrimmed(value, getShareDigits(value))}%`;
	};

	const formatSharePointChange = (value: number | null | undefined): string => {
		if (typeof value !== 'number' || Number.isNaN(value)) return 'n/a';
		const prefix = value > 0 ? '+' : '';
		return `${prefix}${formatTrimmed(value, getShareDigits(value))} pts`;
	};

	const formatRelativeChange = (value: number | null | undefined): string => {
		if (typeof value !== 'number' || Number.isNaN(value)) return 'n/a';
		const absolute = Math.abs(value);
		const digits = absolute >= 100 ? 1 : absolute >= 10 ? 2 : 3;
		const prefix = value > 0 ? '+' : '';
		return `${prefix}${formatTrimmed(value, digits)}%`;
	};

	const toneClass = (value: number | null | undefined): string => {
		const normalized = Number(value ?? 0);
		if (normalized === 0) return 'text-surface-500';
		return normalized > 0 ? 'text-success-700-300' : 'text-error-700-300';
	};

	const withIndex = (points: CompanyTrendPoint[] | undefined): IndexedTrendPoint[] =>
		(points ?? []).map((point, index) => ({
			...point,
			period_index: index + 1
		}));

	const getSourceMeta = (sourceKey: string, tagSource?: string | null): SourceMeta => {
		const known = sourceMeta[sourceKey];
		if (known) return known;
		return {
			...defaultSourceMeta,
			label: sourceLabels[tagSource ?? ''] ?? titleCase(tagSource ?? sourceKey)
		};
	};

	const getPeriodLabel = (points: IndexedTrendPoint[], rawValue: unknown): string => {
		const targetIndex = Math.round(Number(rawValue));
		return points.find((point) => point.period_index === targetIndex)?.period ?? '';
	};

	const sourceCards = $derived.by((): SourceCard[] => {
		const entries = Object.entries(trends?.sources ?? {});
		return entries
			.map(([sourceKey, summary]) => {
				const history = withIndex(trends?.history?.[sourceKey]);
				const pastYear = history.slice(-4);
				const startShare = pastYear[0]?.pct_market_share;
				const endShare = pastYear[pastYear.length - 1]?.pct_market_share;
				const platform = summary.platform ?? 'unknown';
				const tagSource = summary.tag_source ?? sourceKey;
				const meta = getSourceMeta(sourceKey, tagSource);

				return {
					key: sourceKey,
					platform,
					platformLabel:
						platform === 'ios' ? 'iOS' : platform === 'android' ? 'Android' : titleCase(platform),
					label: meta.label,
					colors: meta,
					summary,
					history,
					pastYear,
					trailingYearShareChange:
						typeof startShare === 'number' && typeof endShare === 'number'
							? endShare - startShare
							: null
				};
			})
			.sort((a, b) => {
				const platformDelta = (platformOrder[a.platform] ?? 99) - (platformOrder[b.platform] ?? 99);
				if (platformDelta !== 0) return platformDelta;
				return (
					(sourceOrder[a.summary.tag_source ?? 'unknown'] ?? 99) -
					(sourceOrder[b.summary.tag_source ?? 'unknown'] ?? 99)
				);
			});
	});

	const platformSections = $derived.by((): PlatformSection[] => {
		const sections = new Map<string, PlatformSection>();
		for (const card of sourceCards) {
			const existing = sections.get(card.platform);
			if (existing) {
				existing.cards.push(card);
				continue;
			}

			sections.set(card.platform, {
				platform: card.platform,
				platformLabel: card.platformLabel,
				cards: [card]
			});
		}

		return Array.from(sections.values()).sort(
			(a, b) => (platformOrder[a.platform] ?? 99) - (platformOrder[b.platform] ?? 99)
		);
	});
</script>

{#if platformSections.length > 0}
	<div class="p-3 md:p-5">
		<div class="mb-5 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
			<div>
				<p class="text-xs font-semibold uppercase tracking-[0.22em] text-surface-500">
					Quarterly Trends
				</p>
				<h2 class="text-xl font-semibold">{companyName} platform momentum</h2>
				<p class="text-sm text-surface-500">
					Latest quarter: {trends?.latest_period}. iOS and Android market share are split into
					separate source histories so the underlying scan pools stay comparable.
				</p>
			</div>
			<div
				class="rounded-full border border-surface-200-800 px-3 py-1 text-xs font-medium text-surface-600"
			>
				{sourceCards.length} tracked source{sourceCards.length === 1 ? '' : 's'}
			</div>
		</div>

		<div class="space-y-6">
			{#each platformSections as section}
				<section class="rounded-xl border border-surface-200-800 bg-surface-50-950/30 p-4 md:p-5">
					<div class="mb-4">
						<p class="text-xs font-semibold uppercase tracking-[0.2em] text-surface-500">
							{section.platformLabel}
						</p>
						<h3 class="mt-1 text-lg font-semibold">
							{section.platformLabel} quarterly share trends
						</h3>
					</div>

					<div class="grid grid-cols-1 gap-4 2xl:grid-cols-2">
						{#each section.cards as card}
							<section class="rounded-lg border border-surface-200-800 bg-surface-50-950/40 p-4">
								<div class="mb-4 flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
									<div>
										<p
											class="text-xs font-semibold uppercase tracking-[0.18em]"
											style={`color: ${card.colors.primary};`}
										>
											{card.label}
										</p>
										<h4 class="mt-1 text-lg font-semibold">
											{formatSharePercent(card.summary.latest_pct_market_share)} market share
										</h4>
										<p class="text-sm text-surface-500">{card.summary.latest_period} snapshot</p>
									</div>
									<div
										class="rounded-full border border-surface-200-800 px-3 py-1 text-xs font-medium text-surface-600"
									>
										QoQ share {formatSharePointChange(card.summary.latest_pct_market_share_change)}
									</div>
								</div>

								<div class="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
									<div class="rounded-lg border border-surface-200-800 bg-surface-100-900/60 p-3">
										<div class="text-[11px] uppercase tracking-[0.16em] text-surface-500">
											Share Now
										</div>
										<div class="mt-2 text-xl font-semibold">
											{formatSharePercent(card.summary.latest_pct_market_share)}
										</div>
										<div class="text-xs text-surface-500">
											Prev. {formatSharePercent(card.summary.previous_pct_market_share)}
										</div>
									</div>

									<div class="rounded-lg border border-surface-200-800 bg-surface-100-900/60 p-3">
										<div class="text-[11px] uppercase tracking-[0.16em] text-surface-500">
											QoQ Delta
										</div>
										<div
											class={`mt-2 text-xl font-semibold ${toneClass(card.summary.latest_pct_market_share_change)}`}
										>
											{formatSharePointChange(card.summary.latest_pct_market_share_change)}
										</div>
										<div
											class={`text-xs ${toneClass(card.summary.latest_pct_market_share_change_pct)}`}
										>
											Relative {formatRelativeChange(
												card.summary.latest_pct_market_share_change_pct
											)}
										</div>
									</div>

									<div class="rounded-lg border border-surface-200-800 bg-surface-100-900/60 p-3">
										<div class="text-[11px] uppercase tracking-[0.16em] text-surface-500">
											Trailing Year
										</div>
										<div
											class={`mt-2 text-xl font-semibold ${toneClass(card.trailingYearShareChange)}`}
										>
											{formatSharePointChange(card.trailingYearShareChange)}
										</div>
										<div class="text-xs text-surface-500">
											{formatSharePercent(card.pastYear[0]?.pct_market_share)} to {formatSharePercent(
												card.pastYear[card.pastYear.length - 1]?.pct_market_share
											)}
										</div>
									</div>

									<div class="rounded-lg border border-surface-200-800 bg-surface-100-900/60 p-3">
										<div class="text-[11px] uppercase tracking-[0.16em] text-surface-500">
											Tracked Apps
										</div>
										<div class="mt-2 text-xl font-semibold">
											{formatNumber(card.summary.latest_total_apps)}
										</div>
										<div class="text-xs text-surface-500">
											+{formatNumber(card.summary.latest_apps_added)} / -{formatNumber(
												card.summary.latest_apps_lost
											)}
										</div>
									</div>
								</div>

								<div class="grid grid-cols-1 gap-4 xl:grid-cols-2">
									<div class="rounded-lg border border-surface-200-800 p-3">
										<h5 class="mb-2 text-sm font-semibold">Raw Market Share by Quarter</h5>
										<div class="h-[220px]">
											{#if card.history.length > 0}
												<LineChart
													data={card.history}
													x="period_index"
													series={[{ key: 'pct_market_share', color: card.colors.primary }]}
													props={{
														xAxis: {
															format: (value: unknown) => getPeriodLabel(card.history, value),
															ticks: Math.min(card.history.length, 6)
														},
														yAxis: {
															format: (value: number) => formatSharePercent(Number(value))
														}
													}}
												/>
											{:else}
												<div
													class="flex h-full items-center justify-center text-sm text-surface-500"
												>
													No quarterly history yet
												</div>
											{/if}
										</div>
									</div>

									<div class="rounded-lg border border-surface-200-800 p-3">
										<h5 class="mb-2 text-sm font-semibold">Quarter-over-Quarter Share Change</h5>
										<div class="h-[220px]">
											{#if card.pastYear.some((point) => typeof point.pct_market_share_change === 'number')}
												<LineChart
													data={card.pastYear}
													x="period_index"
													series={[
														{ key: 'pct_market_share_change', color: card.colors.secondary }
													]}
													props={{
														xAxis: {
															format: (value: unknown) => getPeriodLabel(card.pastYear, value),
															ticks: Math.min(card.pastYear.length, 4)
														},
														yAxis: {
															format: (value: number) => formatSharePointChange(Number(value))
														}
													}}
												/>
											{:else}
												<div
													class="flex h-full items-center justify-center text-sm text-surface-500"
												>
													No recent share-change data yet
												</div>
											{/if}
										</div>
									</div>
								</div>
							</section>
						{/each}
					</div>
				</section>
			{/each}
		</div>
	</div>
{:else}
	<div class="p-6 text-sm text-surface-500">
		No quarterly trend history is available for this company yet.
	</div>
{/if}
