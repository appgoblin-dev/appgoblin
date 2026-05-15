<script lang="ts">
	import type { CompanyTrendsSummary, CompanyTrendSummary } from '../types';
	import { formatNumber } from '$lib/utils/formatNumber';

	interface Props {
		summary: CompanyTrendsSummary | null | undefined;
		companyDomain: string;
	}

	type SourceCard = {
		key: string;
		label: string;
		platformLabel: string;
		color: string;
		summary: CompanyTrendSummary;
	};

	const palette = ['#6929C4', '#1192E8', '#005D5D', '#9F1853', '#FA4D56'];
	const platformOrder: Record<string, number> = { ios: 0, android: 1 };
	const sourceOrder: Record<string, number> = { sdk_api: 0, app_ads_direct: 1 };
	const sourceColors: Record<string, string> = {
		ios_sdk_api: palette[0],
		ios_app_ads_direct: palette[1],
		android_sdk_api: palette[2],
		android_app_ads_direct: palette[3]
	};
	const sourceLabels: Record<string, string> = {
		sdk_api: 'SDK/API Footprint',
		app_ads_direct: 'App-ads.txt DIRECT'
	};

	let { summary, companyDomain }: Props = $props();

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
		const prefix = value > 0 ? '+' : '';
		return `${prefix}${formatTrimmed(value, 2)}%`;
	};

	const toneClass = (value: number | null | undefined): string => {
		const normalized = Number(value ?? 0);
		if (normalized === 0) return 'text-surface-500';
		return normalized > 0 ? 'text-success-700-300' : 'text-error-700-300';
	};

	const titleCase = (value: string): string =>
		value.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());

	const cards = $derived.by((): SourceCard[] => {
		const entries = Object.entries(summary?.sources ?? {});
		return entries
			.map(([key, sourceSummary]) => ({
				key,
				label:
					sourceLabels[sourceSummary.tag_source ?? ''] ??
					titleCase(sourceSummary.tag_source ?? key),
				platformLabel:
					sourceSummary.platform === 'ios'
						? 'iOS'
						: sourceSummary.platform === 'android'
							? 'Android'
							: titleCase(sourceSummary.platform ?? 'Unknown'),
				color: sourceColors[key] ?? palette[4],
				summary: sourceSummary
			}))
			.sort((a, b) => {
				const platformDelta =
					(platformOrder[a.summary.platform ?? 'unknown'] ?? 99) -
					(platformOrder[b.summary.platform ?? 'unknown'] ?? 99);
				if (platformDelta !== 0) return platformDelta;
				return (
					(sourceOrder[a.summary.tag_source ?? 'unknown'] ?? 99) -
					(sourceOrder[b.summary.tag_source ?? 'unknown'] ?? 99)
				);
			});
	});
</script>

{#if cards.length > 0}
	<div class="p-4 md:p-5">
		<div class="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
			<div>
				<p class="text-xs font-semibold uppercase tracking-[0.2em] text-surface-500">
					Trend Snapshot
				</p>
				<p class="text-sm text-surface-500">
					Latest quarter: {summary?.latest_period}. Platform-specific market share highlights.
				</p>
			</div>
			<a
				href={`/companies/${companyDomain}/trends`}
				class="inline-flex items-center rounded-full border border-surface-300 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-surface-700 transition hover:border-surface-500 hover:text-surface-950"
			>
				View Full Trends
			</a>
		</div>

		<div class="grid grid-cols-1 gap-3 xl:grid-cols-2">
			{#each cards as card}
				<section class="rounded-lg border border-surface-200-800 bg-surface-50-950/40 p-4">
					<div class="mb-3 flex items-start justify-between gap-3">
						<div>
							<p
								class="text-xs font-semibold uppercase tracking-[0.18em]"
								style={`color: ${card.color};`}
							>
								{card.platformLabel}
							</p>
							<h3 class="mt-1 text-base font-semibold">{card.label}</h3>
						</div>
						<div
							class={`text-sm font-semibold ${toneClass(card.summary.latest_pct_market_share_change)}`}
						>
							{formatSharePointChange(card.summary.latest_pct_market_share_change)}
						</div>
					</div>

					<div class="grid grid-cols-3 gap-3 text-sm">
						<div>
							<div class="text-[11px] uppercase tracking-[0.14em] text-surface-500">Share</div>
							<div class="mt-1 font-semibold">
								{formatSharePercent(card.summary.latest_pct_market_share)}
							</div>
						</div>
						<div>
							<div class="text-[11px] uppercase tracking-[0.14em] text-surface-500">Relative</div>
							<div
								class={`mt-1 font-semibold ${toneClass(card.summary.latest_pct_market_share_change_pct)}`}
							>
								{formatRelativeChange(card.summary.latest_pct_market_share_change_pct)}
							</div>
						</div>
						<div>
							<div class="text-[11px] uppercase tracking-[0.14em] text-surface-500">Apps</div>
							<div class="mt-1 font-semibold">{formatNumber(card.summary.latest_total_apps)}</div>
						</div>
					</div>
				</section>
			{/each}
		</div>
	</div>
{/if}
