<script lang="ts">
	import type { AppFullDetail, KeywordScore } from '../../../../../../types';
	import AppKeywordsTable from '$lib/AppKeywordsTable.svelte';
	import AppKeywordsNav from '$lib/AppKeywordsNav.svelte';

	type KeywordData = {
		keywords: string[];
		keyword_scores: KeywordScore[];
	};

	type DiscoveryPageData = {
		myKeywords: KeywordData | string;
		myapp: Promise<AppFullDetail> | AppFullDetail;
	};

	let { data }: { data: DiscoveryPageData } = $props();

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
	const discoveryKeywords = $derived.by(() =>
		dedupeByKeywordText(
			keywordScores.filter(
				(score) => score.is_keyword_ranking !== true && score.is_keyword_generated === true
			)
		)
	);

	const cardBase = 'rounded-xl border border-surface-300-700 bg-surface-100-900 shadow-sm';
</script>

{#await data.myapp}
	<div class={`${cardBase} p-6 text-center`}>Loading app details...</div>
{:then myapp}
	<div class="space-y-6">
		<AppKeywordsNav storeId={myapp.store_id} />

		<section class={`${cardBase} p-6`}>
			<h1 class="h4 md:h3 mb-2">Keywords Found In Description</h1>
			<p class="text-sm -200">
				These are suggestion keywords extracted from metadata and may not rank for this app.
			</p>
			<p class="mt-2 text-sm -200">
				Treat these as expansion ideas: validate opportunity and difficulty before adding terms to
				your tracked list.
			</p>
			<p class="mt-3 text-xs -200">
				Use the action button to open the global keyword page outside this app dashboard.
			</p>
		</section>
		<section class={`${cardBase} p-6`}>
			{#if discoveryKeywords.length > 0}
				<AppKeywordsTable data={discoveryKeywords} linkMode="global" />
			{:else}
				<p class="text-sm -200">No discovery keywords available yet.</p>
			{/if}
		</section>
	</div>
{/await}
