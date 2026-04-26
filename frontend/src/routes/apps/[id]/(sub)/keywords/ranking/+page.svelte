<script lang="ts">
	import type { AppFullDetail, KeywordScore } from '../../../../../../types';
	import AppKeywordsTable from '$lib/AppKeywordsTable.svelte';
	import AppKeywordsNav from '$lib/AppKeywordsNav.svelte';

	type KeywordData = {
		keywords: string[];
		keyword_scores: KeywordScore[];
	};

	type RankingPageData = {
		myKeywords: KeywordData | string;
		myapp: Promise<AppFullDetail> | AppFullDetail;
	};

	let { data }: { data: RankingPageData } = $props();

	const isKeywordData = (value: unknown): value is KeywordData => {
		return (
			typeof value === 'object' &&
			value !== null &&
			Array.isArray((value as KeywordData).keyword_scores)
		);
	};

	const normalizeKeyword = (value: string) => value.trim().toLowerCase();

	const dedupeByKeywordText = (scores: KeywordScore[]) => {
		const seen = new Set<string>();
		const unique: KeywordScore[] = [];
		for (const score of scores) {
			const key = normalizeKeyword(score.keyword_text);
			if (seen.has(key)) {
				continue;
			}
			seen.add(key);
			unique.push(score);
		}
		return unique;
	};

	const keywordData = $derived(isKeywordData(data.myKeywords) ? data.myKeywords : null);
	const keywordScores = $derived(keywordData?.keyword_scores ?? []);
	const rankingKeywords = $derived.by(() =>
		dedupeByKeywordText(keywordScores.filter((score) => score.is_keyword_ranking === true))
	);

	const cardBase = 'rounded-xl border border-surface-300-700 bg-surface-100-900 shadow-sm';
</script>

{#await data.myapp}
	<div class={`${cardBase} p-6 text-center`}>Loading app details...</div>
{:then myapp}
	<div class="space-y-6">
		<AppKeywordsNav storeId={myapp.store_id} />

		<section class={`${cardBase} p-6`}>
			<h1 class="h4 md:h3 mb-2">Top / Ranking Keywords</h1>
			<p class="text-sm -200">
				Keywords with current-month ranking signals for {myapp.name}.
			</p>
			<p class="mt-2 text-sm -200">
				Use this view to protect high-performing terms, identify drops quickly, and open app-level
				comparison for terms you want to investigate.
			</p>
			<p class="mt-3 text-xs -200">
				{rankingKeywords.length.toLocaleString()} ranking keywords
			</p>
		</section>

		<section class={`${cardBase} p-6`}>
			<h2 class="h6 md:h5 mb-2">Mobile Workflow Tip</h2>
			<p class="text-sm -200">
				On small screens, start with the table action button to jump directly into compare for a
				single keyword, then add related terms in compare view.
			</p>
		</section>

		<section class={`${cardBase} p-6`}>
			{#if rankingKeywords.length > 0}
				<AppKeywordsTable data={rankingKeywords} storeId={myapp.store_id} linkMode="app" />
			{:else}
				<p class="text-sm -200">No ranking keywords available yet.</p>
			{/if}
		</section>
	</div>
{/await}
