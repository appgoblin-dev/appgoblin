<script lang="ts">
	import type { AppFullDetail, KeywordScore } from '../../../../../types';
	import AppKeywordsTable from '$lib/AppKeywordsTable.svelte';

	type KeywordData = {
		keywords: string[];
		keyword_scores: KeywordScore[];
	};

	type KeywordsPageData = {
		myKeywords: KeywordData | string;
		myapp: Promise<AppFullDetail> | AppFullDetail;
		[key: string]: unknown;
	};

	let { data }: { data: KeywordsPageData } = $props();

	const isKeywordData = (value: unknown): value is KeywordData => {
		return (
			typeof value === 'object' &&
			value !== null &&
			Array.isArray((value as KeywordData).keyword_scores)
		);
	};

	const toNumber = (value: number | string | null | undefined) => {
		if (value === null || value === undefined) {
			return null;
		}

		if (typeof value === 'number') {
			return Number.isFinite(value) ? value : null;
		}

		const trimmed = value.trim();
		if (trimmed === '' || trimmed.toLowerCase() === 'na') {
			return null;
		}

		const numeric = Number(trimmed);
		return Number.isFinite(numeric) ? numeric : null;
	};

	const average = (values: number[]) => {
		if (!values.length) {
			return null;
		}

		const total = values.reduce((sum, value) => sum + value, 0);
		return total / values.length;
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

	const formatPercent = (value: number | null) => {
		if (value === null) {
			return '—';
		}

		return `${Math.round(value)}%`;
	};

	const formatRankDisplay = (value: number | null) => {
		if (value === null) {
			return '—';
		}

		return value.toLocaleString();
	};

	const formatCount = (value: number | string | null | undefined) => {
		if (value === null || value === undefined || value === '') {
			return '—';
		}

		if (typeof value === 'number') {
			return Number.isFinite(value) ? value.toLocaleString() : '—';
		}

		const cleaned = value.toString().replace(/,/g, '');
		const parsed = Number(cleaned);
		if (Number.isNaN(parsed)) {
			return value.toString();
		}

		return parsed.toLocaleString();
	};

	const getNumericValues = (
		scores: KeywordScore[],
		accessor: (score: KeywordScore) => number | string | null | undefined
	) =>
		scores
			.map((score) => toNumber(accessor(score)))
			.filter((value): value is number => value !== null);

	const keywordData = $derived(isKeywordData(data.myKeywords) ? data.myKeywords : null);

	const keywordScores = $derived(keywordData?.keyword_scores ?? []);

	const trackedKeywords = $derived(keywordScores.length);

	const rankedKeywordCount = $derived.by(() => {
		return keywordScores.filter((score) => {
			const latest = toNumber(score.latest_app_rank);
			const best = toNumber(score.d30_best_rank);
			return latest !== null || best !== null;
		}).length;
	});

	const unrankedKeywords = $derived.by(() => {
		return keywordScores.filter((score) => {
			const latest = toNumber(score.latest_app_rank);
			const best = toNumber(score.d30_best_rank);
			return latest === null && best === null;
		});
	});

	const averageOpportunity = $derived(
		average(getNumericValues(keywordScores, (score) => score.opportunity_score))
	);

	const averageDifficulty = $derived(
		average(getNumericValues(keywordScores, (score) => score.keyword_difficulty))
	);

	const top10Coverage = $derived.by(() => {
		if (rankedKeywordCount <= 0) {
			return null;
		}

		const top10Count = keywordScores.filter((score) => {
			const rank = toNumber(score.latest_app_rank) ?? toNumber(score.d30_best_rank);
			return rank !== null && rank <= 10;
		}).length;

		return (top10Count / rankedKeywordCount) * 100;
	});

	const bestRank = $derived.by(() => {
		const ranks: number[] = [];
		for (const score of keywordScores) {
			const latest = toNumber(score.latest_app_rank);
			const best = toNumber(score.d30_best_rank);
			if (latest !== null) {
				ranks.push(latest);
			}
			if (best !== null) {
				ranks.push(best);
			}
		}
		if (!ranks.length) {
			return null;
		}
		return Math.min(...ranks);
	});

	const topOpportunityKeywords = $derived.by(() => {
		return [...keywordScores]
			.filter((score) => toNumber(score.opportunity_score) !== null)
			.sort(
				(a, b) =>
					(toNumber(b.opportunity_score) ?? Number.NEGATIVE_INFINITY) -
					(toNumber(a.opportunity_score) ?? Number.NEGATIVE_INFINITY)
			)
			.slice(0, 5);
	});

	const unrankedOpportunityKeywords = $derived.by(() => {
		return [...unrankedKeywords]
			.filter(
				(score) =>
					toNumber(score.opportunity_score) !== null || toNumber(score.keyword_difficulty) !== null
			)
			.sort(
				(a, b) =>
					(toNumber(b.opportunity_score) ?? Number.NEGATIVE_INFINITY) -
					(toNumber(a.opportunity_score) ?? Number.NEGATIVE_INFINITY)
			)
			.slice(0, 5);
	});

	const defensiveKeywords = $derived.by(() => {
		return [...keywordScores]
			.filter((score) => {
				const rank = toNumber(score.latest_app_rank) ?? toNumber(score.d30_best_rank);
				return rank !== null && rank <= 5;
			})
			.sort((a, b) => {
				const aRank =
					toNumber(a.latest_app_rank) ?? toNumber(a.d30_best_rank) ?? Number.POSITIVE_INFINITY;
				const bRank =
					toNumber(b.latest_app_rank) ?? toNumber(b.d30_best_rank) ?? Number.POSITIVE_INFINITY;
				return aRank - bRank;
			})
			.slice(0, 5);
	});

	const highCompetitionKeywords = $derived.by(() => {
		return [...keywordScores]
			.sort(
				(a, b) =>
					(toNumber(b.app_count) ?? Number.NEGATIVE_INFINITY) -
					(toNumber(a.app_count) ?? Number.NEGATIVE_INFINITY)
			)
			.slice(0, 5);
	});

	const hasKeywordData = $derived(keywordScores.length > 0);

	const buildSummary = (app: AppFullDetail) => {
		if (!hasKeywordData) {
			return `${app.name} doesn't have tracked keywords yet.`;
		}

		const keywordLabel = trackedKeywords === 1 ? 'keyword' : 'keywords';
		const rankedLabel =
			rankedKeywordCount === 0
				? 'no keywords rank yet'
				: `${rankedKeywordCount.toLocaleString()} ${
						rankedKeywordCount === 1 ? 'keyword ranks' : 'keywords rank'
					}`;

		const tractionLabel =
			unrankedKeywords.length > 0
				? `${unrankedKeywords.length.toLocaleString()} ${
						unrankedKeywords.length === 1 ? 'needs' : 'need'
					} traction`
				: 'full coverage across the tracked set';

		const headline = `${app.name} tracks ${trackedKeywords.toLocaleString()} ${keywordLabel} (${rankedLabel}; ${tractionLabel}).`;

		const parts: string[] = [];

		if (top10Coverage !== null) {
			parts.push(`${formatPercent(top10Coverage)} top-10 coverage`);
		}

		if (averageOpportunity !== null) {
			parts.push(`opportunity ${formatNumeric(averageOpportunity, 1)}`);
		}

		if (averageDifficulty !== null) {
			parts.push(`difficulty ${formatNumeric(averageDifficulty, 1)}`);
		}

		if (bestRank !== null) {
			parts.push(`best rank ${formatRankDisplay(bestRank)}`);
		}

		const metricsSummary = parts.length ? ` Key metrics: ${parts.join(', ')}.` : '';

		return `${headline}${metricsSummary}`;
	};

	const cardBaseClass = 'rounded-xl border border-surface-300-700 bg-surface-100-900 shadow-sm';
	const cardBaseTightClass =
		'rounded-lg border border-surface-300-700 bg-surface-100-900 shadow-sm';
	const cardPaddingLg = `${cardBaseClass} p-6`;
	const cardPaddingTight = `${cardBaseTightClass} p-4`;
	const cardPaddingList = `${cardBaseClass} p-6`;

	const textMutedSmClass = 'text-sm text-primary-800-200';
	const textMutedXsClass = 'text-xs text-primary-800-200';
	const metricLabelClass = 'text-xs uppercase tracking-wide text-primary-900-100';
	const metricValueClass = 'text-3xl font-semibold text-primary-900-100';
	const metricListItemClass = 'rounded-lg border border-surface-300-700 p-3';
	const metricListItemDashedClass = 'rounded-lg border border-dashed border-surface-300-700 p-3';
	const headingListClass = 'h5 md:h4 mb-3';
	const summaryParagraphClass = 'mt-4 text-sm text-primary-900-100';
	const descriptionSnippetClass = 'mt-2 text-xs text-primary-800-200';
</script>

{#await data.myapp}
	<div class={`${cardBaseClass} p-6 text-center`}>Loading app details…</div>
{:then myapp}
	<div class="space-y-6">
		<section class={cardPaddingLg}>
			<div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
				<div class="flex items-center gap-4">
					{#if myapp.app_icon_url}
						<img
							src={myapp.app_icon_url}
							alt={`${myapp.name} icon`}
							class="h-16 w-16 rounded-xl border border-surface-300-700 object-cover"
							loading="lazy"
						/>
					{/if}
					<div class="space-y-2">
						<h1 class="h4 md:h3">ASO Keyword Dashboard</h1>
						<p class={textMutedSmClass}>
							Tracking {trackedKeywords.toLocaleString()} keywords for {myapp.name} in {myapp.store}
						</p>
						<div class="flex flex-wrap gap-x-4 gap-y-1 text-xs text-primary-700-300">
							<span>Developer: {myapp.developer_name}</span>
							{#if myapp.category}
								<span>Category: {myapp.category}</span>
							{/if}
							{#if myapp.rating}
								<span>Rating: {myapp.rating}</span>
							{/if}
						</div>
					</div>
				</div>
			</div>
			<p class={summaryParagraphClass}>{buildSummary(myapp)}</p>
			{#if myapp.description_short}
				<p class={descriptionSnippetClass}>{myapp.description_short}</p>
			{/if}
		</section>

		{#if hasKeywordData}
			<section class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
				<div class={cardPaddingTight}>
					<p class={metricLabelClass}>Tracked keywords</p>
					<p class={metricValueClass}>
						{trackedKeywords.toLocaleString()}
					</p>
					<p class={textMutedSmClass}>
						<span class="font-medium text-primary-100-900"
							>{rankedKeywordCount.toLocaleString()}</span
						>
						&nbsp;ranked •&nbsp;
						<span class="font-medium text-primary-100-900"
							>{unrankedKeywords.length.toLocaleString()}</span
						>
						&nbsp;not ranking yet
					</p>
				</div>
				<div class={cardPaddingTight}>
					<p class={metricLabelClass}>Top 10 coverage</p>
					<p class={metricValueClass}>
						{top10Coverage !== null ? formatPercent(top10Coverage) : '—'}
					</p>
					<p class={textMutedSmClass}>
						Best rank {formatRankDisplay(bestRank)} • Latest leader{' '}
						{formatRankDisplay(toNumber(topOpportunityKeywords[0]?.latest_app_rank ?? null))}
					</p>
				</div>
				<div class={cardPaddingTight}>
					<p class={metricLabelClass}>Avg opportunity</p>
					<p class={metricValueClass}>
						{formatNumeric(averageOpportunity, 1)}
					</p>
					<p class={textMutedSmClass}>
						Top keyword: {topOpportunityKeywords[0]?.keyword_text ?? '—'}
					</p>
				</div>
				<div class={cardPaddingTight}>
					<p class={metricLabelClass}>Avg difficulty</p>
					<p class={metricValueClass}>
						{formatNumeric(averageDifficulty, 1)}
					</p>
					<p class={textMutedSmClass}>Lower scores indicate easier wins</p>
				</div>
			</section>

			<section class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
				<div class={cardPaddingList}>
					<h4 class={headingListClass}>Opportunity leaders</h4>
					{#if topOpportunityKeywords.length}
						<ul class="space-y-3">
							{#each topOpportunityKeywords as keyword}
								<li
									class="flex items-start justify-between gap-4 rounded-lg border border-surface-300-700 bg-surface-100-900 p-3"
								>
									<div class="space-y-1">
										<p class="font-medium">{keyword.keyword_text}</p>
										<p class={textMutedXsClass}>
											Opportunity: {formatNumeric(toNumber(keyword.opportunity_score), 1)} • Difficulty:
											{formatNumeric(toNumber(keyword.keyword_difficulty), 1)} • Rank
											{formatRankDisplay(
												toNumber(keyword.latest_app_rank) ?? toNumber(keyword.d30_best_rank)
											)}
										</p>
										<p class={textMutedXsClass}>
											Competitors: {formatCount(keyword.major_competitors)}
										</p>
									</div>
									<span class="text-sm font-semibold">
										{formatNumeric(toNumber(keyword.competitiveness_score), 1)}
									</span>
								</li>
							{/each}
						</ul>
					{:else}
						<p class={textMutedSmClass}>No opportunity data available yet.</p>
					{/if}
				</div>

				<div class={cardPaddingList}>
					<h4 class={headingListClass}>Unranked opportunities</h4>
					{#if unrankedOpportunityKeywords.length}
						<ul class="space-y-3">
							{#each unrankedOpportunityKeywords as keyword}
								<li class={metricListItemDashedClass}>
									<p class="font-medium">{keyword.keyword_text}</p>
									<p class={`mt-1 ${textMutedXsClass}`}>
										Opportunity: {formatNumeric(toNumber(keyword.opportunity_score), 1)} • Difficulty:
										{formatNumeric(toNumber(keyword.keyword_difficulty), 1)} • Competitors:
										{formatCount(keyword.major_competitors)}
									</p>
								</li>
							{/each}
						</ul>
					{:else}
						<p class={textMutedSmClass}>Every tracked keyword currently has some ranking data.</p>
					{/if}
				</div>

				<div class={cardPaddingList}>
					<h4 class={headingListClass}>High competition keywords</h4>
					{#if highCompetitionKeywords.length}
						<ul class="space-y-3">
							{#each highCompetitionKeywords as keyword}
								<li class={metricListItemClass}>
									<p class="font-medium">{keyword.keyword_text}</p>
									<p class={`mt-1 ${textMutedXsClass}`}>
										Total apps: {formatCount(keyword.app_count)} • Major competitors:
										{formatCount(keyword.major_competitors)}
									</p>
									<p class={textMutedXsClass}>
										Latest rank: {formatRankDisplay(toNumber(keyword.latest_app_rank))} • Difficulty:
										{formatNumeric(toNumber(keyword.keyword_difficulty), 1)}
									</p>
								</li>
							{/each}
						</ul>
					{:else}
						<p class={textMutedSmClass}>
							No competitive benchmarks available for this keyword set yet.
						</p>
					{/if}
				</div>
			</section>

			<section class={cardPaddingLg}>
				<div class="mb-4 flex items-center justify-between">
					<h4 class="h5 md:h4">All tracked keywords</h4>
					<p class={textMutedXsClass}>
						Includes opportunity, difficulty, rankings and competitor benchmarks
					</p>
				</div>
				<AppKeywordsTable data={keywordScores} />
			</section>
		{:else}
			<section class={`${cardPaddingLg} text-center`}>
				<h4 class="h5 md:h4 mb-2">No keywords tracked yet</h4>
				<p class={textMutedSmClass}>
					We could not generate keyword insights for this app. Add more metadata or refresh the
					crawl to populate ASO keywords.
				</p>
			</section>
		{/if}

		<section class={cardPaddingLg}>
			<h4 class="h4 md:h3 mb-4">App Description</h4>
			<div class="space-y-2">
				{#if myapp.description_short}
					<p class="text-strong">{myapp.description_short}</p>
				{/if}
				{#if myapp.description}
					<div class="prose prose-sm max-w-none text-primary-900-100">
						{@html myapp.description.replace(/\r?\n/g, '<br>')}
					</div>
				{/if}
			</div>
		</section>
	</div>
{/await}
