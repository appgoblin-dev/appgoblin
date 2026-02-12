<script lang="ts">
	import { page } from '$app/state';
	import AppRankTable from '$lib/AppRankTable.svelte';
	import type { KeywordScore } from '../../../../types';

	type KeywordApps = {
		google?: { ranks: any[] };
		apple?: { ranks: any[] };
	};

	type KeywordPageData = {
		keywordDetails: KeywordScore[] | Record<string, unknown>;
		keywordApps: KeywordApps;
	};

	let { data }: { data: KeywordPageData } = $props();

	const keywordRecords = $derived(Array.isArray(data.keywordDetails) ? data.keywordDetails : []);
	const keywordApps = $derived(data.keywordApps ?? {});

	const storeNames: Record<string | number, string> = {
		1: 'Google Play',
		2: 'Apple App Store',
		android: 'Google Play',
		ios: 'Apple App Store'
	};

	const toNumber = (value: unknown): number | null => {
		if (value === null || value === undefined || value === '' || value === 'NA') {
			return null;
		}

		if (typeof value === 'number') {
			return Number.isFinite(value) ? value : null;
		}

		const parsed = Number(String(value).replace(/,/g, ''));
		return Number.isFinite(parsed) ? parsed : null;
	};

	const average = (values: Array<number | null>) => {
		const filtered = values.filter((value): value is number => value !== null);
		if (!filtered.length) {
			return null;
		}
		return filtered.reduce((sum, value) => sum + value, 0) / filtered.length;
	};

	const formatNumeric = (value: number | null, digits = 1) => {
		if (value === null) {
			return '—';
		}
		return value.toLocaleString(undefined, {
			minimumFractionDigits: digits,
			maximumFractionDigits: digits
		});
	};

	const formatCount = (value: number | null) => {
		if (value === null) {
			return '—';
		}
		return value.toLocaleString();
	};

	const formatRank = (value: number | null) => {
		if (value === null) {
			return '—';
		}
		return value.toLocaleString();
	};

	const pickFirstNumeric = (key: keyof KeywordScore) => {
		for (const record of keywordRecords) {
			const numeric = toNumber(record[key]);
			if (numeric !== null) {
				return numeric;
			}
		}
		return null;
	};

	const keywordDisplay = $derived(keywordRecords[0]?.keyword_text ?? page.params.keyword);

	const opportunityScores = $derived(
		keywordRecords.map((record) => toNumber(record.opportunity_score))
	);
	const difficultyScores = $derived(
		keywordRecords.map((record) => toNumber(record.keyword_difficulty))
	);
	const competitivenessScores = $derived(
		keywordRecords.map((record) => toNumber(record.competitiveness_score))
	);
	const volumeScores = $derived(
		keywordRecords.map((record) => toNumber(record.volume_competition_score))
	);

	const opportunityAvg = $derived(average(opportunityScores));
	const difficultyAvg = $derived(average(difficultyScores));
	const competitivenessAvg = $derived(average(competitivenessScores));
	const volumeAvg = $derived(average(volumeScores));

	const appCountValue = $derived(pickFirstNumeric('app_count'));
	const totalAppsValue = $derived(pickFirstNumeric('total_apps'));
	const majorCompetitors = $derived(pickFirstNumeric('major_competitors'));
	const medianInstalls = $derived(pickFirstNumeric('median_competitor_installs'));
	const avgRating = $derived(pickFirstNumeric('avg_competitor_rating'));

	const rankingRecords = $derived(
		keywordRecords
			.map((record) => {
				const latest = toNumber(record.latest_app_rank);
				const best = toNumber(record.d30_best_rank);
				const rank = latest ?? best;
				if (rank === null) {
					return null;
				}
				return {
					store: record.store,
					rank,
					latest,
					best
				};
			})
			.filter(
				(
					record
				): record is {
					store: KeywordScore['store'];
					rank: number;
					latest: number | null;
					best: number | null;
				} => record !== null
			)
			.sort((a, b) => a.rank - b.rank)
	);

	const topRankRecord = $derived(rankingRecords[0] ?? null);
	const topRankStoreKey = $derived(topRankRecord?.store);
	const topRankStore = $derived(
		topRankStoreKey !== undefined && topRankStoreKey !== null
			? (storeNames[topRankStoreKey] ?? 'the leading store')
			: 'the leading store'
	);
	const topRankValue = $derived(topRankRecord?.rank ?? null);

	const describeOpportunity = (score: number | null) => {
		if (score === null) {
			return null;
		}
		if (score >= 80) {
			return 'high-upside potential';
		}
		if (score >= 60) {
			return 'moderate upside';
		}
		return 'limited upside';
	};

	const describeDifficulty = (score: number | null) => {
		if (score === null) {
			return null;
		}
		if (score <= 55) {
			return 'manageable';
		}
		if (score <= 75) {
			return 'balanced';
		}
		return 'demanding';
	};

	const opportunityDescriptor = $derived(describeOpportunity(opportunityAvg));
	const difficultyDescriptor = $derived(describeDifficulty(difficultyAvg));

	const googleCount = $derived(keywordApps.google?.ranks?.length ?? 0);
	const appleCount = $derived(keywordApps.apple?.ranks?.length ?? 0);

	let summarySentences = $state<string[]>([]);
	$effect(() => {
		const sentences: string[] = [];
		const parts: string[] = [];

		if (opportunityAvg !== null) {
			parts.push(
				`an opportunity score of ${formatNumeric(opportunityAvg, 1)}${
					opportunityDescriptor ? ` (${opportunityDescriptor})` : ''
				}`
			);
		}
		if (difficultyAvg !== null) {
			parts.push(
				`difficulty at ${formatNumeric(difficultyAvg, 1)}${
					difficultyDescriptor ? ` (${difficultyDescriptor})` : ''
				}`
			);
		}

		if (parts.length) {
			sentences.push(
				`“${keywordDisplay}” exhibits ${parts.join(' and ')}, framing the effort required to compete.`
			);
		}

		if (topRankValue !== null) {
			sentences.push(
				`Top-ranked apps are currently holding #${formatRank(topRankValue)} on ${topRankStore}, which sets the benchmark for search visibility.`
			);
		}

		const competitiveNotes: string[] = [];
		if (majorCompetitors !== null) {
			competitiveNotes.push(`${formatCount(majorCompetitors)} major competitors`);
		}
		if (medianInstalls !== null) {
			competitiveNotes.push(`median installs near ${formatCount(medianInstalls)}`);
		}
		if (avgRating !== null) {
			competitiveNotes.push(`average rating around ${formatNumeric(avgRating, 1)}`);
		}
		if (competitiveNotes.length) {
			sentences.push(`Expect ${competitiveNotes.join(', ')} among the current leaders.`);
		}

		if (googleCount || appleCount) {
			sentences.push(
				`We monitor ${googleCount} Android and ${appleCount} iOS apps to track momentum shifts for this keyword.`
			);
		}

		summarySentences = sentences;
	});

	type MetricCard = {
		label: string;
		value: string;
		helper?: string;
	};

	let keywordPerformanceCards = $state<MetricCard[]>([]);
	let keywordBenchmarkCards = $state<MetricCard[]>([]);
	$effect(() => {
		keywordPerformanceCards = [
			{
				label: 'Opportunity Score',
				value: formatNumeric(opportunityAvg, 1),
				helper: opportunityDescriptor
					? `Signals ${opportunityDescriptor} if rankings improve.`
					: 'Signals upside potential if rankings improve.'
			},
			{
				label: 'Keyword Difficulty',
				value: formatNumeric(difficultyAvg, 1),
				helper: difficultyDescriptor
					? `${difficultyDescriptor} level of competition.`
					: 'Indicates how contested this keyword is.'
			},
			{
				label: 'Competitiveness',
				value: formatNumeric(competitivenessAvg, 1),
				helper: 'Blend of rank positions across leading apps.'
			},
			{
				label: 'Volume Score',
				value: formatNumeric(volumeAvg, 1),
				helper: 'Demand proxy for search impressions.'
			}
		];

		keywordBenchmarkCards = [
			{
				label: 'Tracked Apps',
				value: formatCount(appCountValue),
				helper:
					totalAppsValue !== null
						? `Out of ${formatCount(totalAppsValue)} total apps.`
						: 'Coverage within our dataset.'
			},
			{
				label: 'Major Competitors',
				value: formatCount(majorCompetitors),
				helper: 'Consistently ranking apps for this keyword.'
			},
			{
				label: 'Median Competitor Installs',
				value: formatCount(medianInstalls),
				helper: 'Typical install base among the leaders.'
			},
			{
				label: 'Average Competitor Rating',
				value: formatNumeric(avgRating, 1),
				helper: 'Quality benchmark across the top cohort.'
			}
		];
	});

	type StoreSnapshot = {
		title: string;
		appCount: string;
		competitiveness: string;
	};

	let storeSnapshots = $state<StoreSnapshot[]>([]);
	$effect(() => {
		const snapshots: StoreSnapshot[] = [];
		for (const record of keywordRecords) {
			const storeKey = record.store ?? `store-${snapshots.length}`;
			const title = storeNames[storeKey] ?? 'Store';
			const competitiveness = formatNumeric(toNumber(record.competitiveness_score), 1);
			const storeAppCount = formatCount(toNumber(record.app_count));
			snapshots.push({
				title,
				competitiveness,
				appCount: storeAppCount
			});
		}
		storeSnapshots = snapshots;
	});

	const cardBaseClass = 'rounded-xl border border-surface-300-700 bg-surface-100-900 shadow-sm';
	const cardBaseTightClass =
		'rounded-lg border border-surface-300-700 bg-surface-100-900 shadow-sm';
	const cardPaddingLg = `${cardBaseClass} p-6`;
	const cardPaddingTight = `${cardBaseTightClass} p-4`;

	const textMutedSmClass = 'text-sm text-primary-800-200';
	const textMutedXsClass = 'text-xs text-primary-800-200';
	const metricLabelClass = 'text-xs uppercase tracking-wide text-primary-900-100';
	const metricValueClass = 'text-3xl font-semibold text-primary-900-100';
	const summaryParagraphClass = 'mt-4 text-sm text-primary-900-100';
	const sectionSubtitleClass = 'text-xs text-primary-800-200';
	const tagPillClass =
		'rounded-full bg-primary-900-100/10 px-3 py-1 text-xs font-medium text-primary-900-100';
</script>

<div class="space-y-6">
	<section class={cardPaddingLg}>
		<div class="flex flex-col gap-2">
			<h1 class="h4 md:h3">
				Keyword Overview: <span class="text-primary-900-100">“{keywordDisplay}”</span>
			</h1>
			<p class={sectionSubtitleClass}>
				ASO & SEO signals consolidated from keyword scores and store coverage.
			</p>
		</div>
		{#if summarySentences.length}
			<div class="mt-4 space-y-2">
				{#each summarySentences as sentence}
					<p class={summaryParagraphClass}>{sentence}</p>
				{/each}
			</div>
		{:else}
			<p class={summaryParagraphClass}>
				We are gathering more data for this keyword. Check back soon for a richer assessment.
			</p>
		{/if}
	</section>

	<section class={cardPaddingLg}>
		<div class="flex flex-col gap-1">
			<h2 class="h5 md:h4">Keyword Signals</h2>
			<p class={sectionSubtitleClass}>
				Scores distilled from ranking performance and demand indicators.
			</p>
		</div>
		<div class="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
			{#each keywordPerformanceCards as metric}
				<div class={cardPaddingTight}>
					<p class={metricLabelClass}>{metric.label}</p>
					<p class={metricValueClass}>{metric.value}</p>
					{#if metric.helper}
						<p class={`mt-1 ${textMutedXsClass}`}>{metric.helper}</p>
					{/if}
				</div>
			{/each}
		</div>
		<div class="mt-6 flex flex-col gap-1">
			<h3 class="text-sm font-semibold text-primary-900-100">Competitive Benchmarks</h3>
			<p class={sectionSubtitleClass}>
				Gauge the strength of incumbent apps before committing to this keyword.
			</p>
		</div>
		<div class="mt-3 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
			{#each keywordBenchmarkCards as metric}
				<div class={cardPaddingTight}>
					<p class={metricLabelClass}>{metric.label}</p>
					<p class={metricValueClass}>{metric.value}</p>
					{#if metric.helper}
						<p class={`mt-1 ${textMutedXsClass}`}>{metric.helper}</p>
					{/if}
				</div>
			{/each}
		</div>
	</section>

	{#if storeSnapshots.length}
		<section class={cardPaddingLg}>
			<div class="mb-4 flex flex-col gap-1">
				<h2 class="h5 md:h4">Store Snapshot</h2>
				<p class={sectionSubtitleClass}>
					Latest keyword coverage across Android and iOS storefronts.
				</p>
			</div>
			<div class="grid gap-4 md:grid-cols-2">
				{#each storeSnapshots as snapshot}
					<div class={cardPaddingTight}>
						<div class="flex items-center justify-between">
							<p class="text-lg font-semibold text-primary-900-100">{snapshot.title}</p>
						</div>
						<dl class="mt-4 space-y-2 text-xs text-primary-800-200">
							<div class="flex justify-between">
								<dt class="font-medium">Competitiveness</dt>
								<dd>{snapshot.competitiveness}</dd>
							</div>
							<div class="flex justify-between">
								<dt class="font-medium">Tracked Apps</dt>
								<dd>{snapshot.appCount}</dd>
							</div>
						</dl>
					</div>
				{/each}
			</div>
		</section>
	{/if}

	<section class={cardPaddingLg}>
		<div class="mb-4 flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
			<h2 class="h5 md:h4">Store Rankings</h2>
			<p class={sectionSubtitleClass}>
				Benchmark the current leaders on Android and iOS to plan positioning.
			</p>
		</div>
		<div class="grid gap-4 md:grid-cols-2">
			<div class={cardPaddingTight}>
				<div class="mb-3 flex items-center justify-between">
					<h3 class="text-lg font-semibold text-primary-900-100">Google Play</h3>
					<span class={sectionSubtitleClass}>{googleCount} apps tracked</span>
				</div>
				{#if googleCount}
					<AppRankTable data={keywordApps.google?.ranks ?? []} />
				{:else}
					<p class={textMutedSmClass}>No Android apps currently rank for this keyword.</p>
				{/if}
			</div>
			<div class={cardPaddingTight}>
				<div class="mb-3 flex items-center justify-between">
					<h3 class="text-lg font-semibold text-primary-900-100">Apple App Store</h3>
					<span class={sectionSubtitleClass}>{appleCount} apps tracked</span>
				</div>
				{#if appleCount}
					<AppRankTable data={keywordApps.apple?.ranks ?? []} />
				{:else}
					<p class={textMutedSmClass}>No iOS apps currently rank for this keyword.</p>
				{/if}
			</div>
		</div>
	</section>
</div>
