<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { LineChart } from 'layerchart';
	import { format, PeriodType } from '@layerstack/utils';
	import { plotColors } from '$lib/constants';
	import AppKeywordsNav from '$lib/AppKeywordsNav.svelte';
	import type { AppFullDetail } from '../../../../../../types';

	type ComparePageData = {
		myapp: AppFullDetail;
		requestedKeywords: string[];
		resolvedKeywords: { keyword_id: number; keyword_text: string }[];
		keywordHistory: any[];
		availableKeywords: string[];
		trackedKeywords: string[];
	};

	let { data }: { data: ComparePageData } = $props();

	// ── Active keyword set (drives the URL) ───────────────────────────────────
	// Start from the server-resolved set so the chip list is always in sync.
	let activeKeywords = $state<string[]>([]);

	$effect(() => {
		activeKeywords = data.resolvedKeywords.map((keyword) => keyword.keyword_text);
	});

	// Search / picker state
	let searchQuery = $state('');
	let pickerOpen = $state(false);

	// Deduplicated pool: tracked keywords first (they're personal), then app keywords
	const allCandidates = $derived.by(() => {
		const tracked = data.trackedKeywords.map((k) => k.toLowerCase());
		const app = data.availableKeywords.map((k) => k.toLowerCase());
		// union, tracked first
		const seen = new Set<string>();
		const result: { text: string; isTracked: boolean }[] = [];
		for (const t of data.trackedKeywords) {
			const lower = t.toLowerCase();
			if (!seen.has(lower)) {
				seen.add(lower);
				result.push({ text: t, isTracked: true });
			}
		}
		for (const a of data.availableKeywords) {
			const lower = a.toLowerCase();
			if (!seen.has(lower)) {
				seen.add(lower);
				result.push({ text: a, isTracked: false });
			}
		}
		return result;
	});

	const filteredCandidates = $derived.by(() => {
		const q = searchQuery.trim().toLowerCase();
		const active = new Set(activeKeywords.map((k) => k.toLowerCase()));
		return allCandidates
			.filter((c) => !active.has(c.text.toLowerCase()))
			.filter((c) => !q || c.text.toLowerCase().includes(q))
			.slice(0, 30);
	});

	function addKeyword(text: string) {
		if (activeKeywords.length >= 10) return;
		const lower = text.toLowerCase();
		if (!activeKeywords.some((k) => k.toLowerCase() === lower)) {
			activeKeywords = [...activeKeywords, text];
		}
		searchQuery = '';
		applyKeywords();
	}

	function removeKeyword(text: string) {
		activeKeywords = activeKeywords.filter((k) => k.toLowerCase() !== text.toLowerCase());
		applyKeywords();
	}

	function applyKeywords() {
		const kParam = activeKeywords.map(encodeURIComponent).join(',');
		const url = kParam
			? `/apps/${data.myapp.store_id}/keywords/compare?k=${kParam}`
			: `/apps/${data.myapp.store_id}/keywords/compare`;
		goto(url, { replaceState: true, keepFocus: true, noScroll: true });
	}

	// ── Chart data ─────────────────────────────────────────────────────────────
	const chartData = $derived.by(() => {
		const history = data.keywordHistory;
		if (!history || history.length === 0) return [];

		const keywordTextById = new Map<string, string>(
			data.resolvedKeywords.map((keyword) => [String(keyword.keyword_id), keyword.keyword_text])
		);

		const rows = history.map((row) => {
			const entry: Record<string, string | number | null> = {
				crawled_date: String(row.crawled_date)
			};

			for (const [key, rawValue] of Object.entries(row)) {
				if (key === 'crawled_date') continue;
				const keywordText = keywordTextById.get(key);
				if (!keywordText) continue;
				entry[keywordText] =
					typeof rawValue === 'number'
						? Number.isFinite(rawValue)
							? rawValue
							: null
						: rawValue === null
							? null
							: Number.isFinite(Number(rawValue))
								? Number(rawValue)
								: null;
			}

			return entry;
		});

		return rows.sort(
			(a, b) =>
				new Date(String(a.crawled_date)).getTime() - new Date(String(b.crawled_date)).getTime()
		);
	});

	const seriesKeys = $derived(
		data.resolvedKeywords.map((kw, i) => ({
			key: kw.keyword_text,
			label: kw.keyword_text,
			color: plotColors[i % plotColors.length]
		}))
	);

	const yDomain = $derived.by((): [number, number] => {
		if (chartData.length === 0) return [10, 1];
		const rankValues = chartData.flatMap((row) =>
			Object.entries(row)
				.filter(([key]) => key !== 'crawled_date')
				.map(([, value]) => (typeof value === 'number' ? value : null))
				.filter((value): value is number => value !== null)
		);
		if (rankValues.length === 0) return [10, 1];
		const maxRank = Math.max(...rankValues);
		return [Math.max(maxRank + 5, 10), 1];
	});

	$effect(() => {
		console.debug('[keywords-compare] raw keywordHistory', data.keywordHistory);
		console.debug('[keywords-compare] resolvedKeywords', data.resolvedKeywords);
		console.debug('[keywords-compare] chartData', chartData);
		console.debug('[keywords-compare] seriesKeys', seriesKeys);
		console.debug('[keywords-compare] yDomain', yDomain);
	});

	// ── Styles ─────────────────────────────────────────────────────────────────
	const cardBase = 'rounded-xl border border-surface-300-700 bg-surface-100-900 shadow-sm';
	const cardPadding = `${cardBase} p-6`;
	const textMuted = 'text-sm -200';
</script>

<div class="space-y-6">
	<AppKeywordsNav storeId={data.myapp.store_id} />

	<!-- Breadcrumb -->
	<nav class="flex items-center gap-2 text-sm">
		<a href={`/apps/${data.myapp.store_id}`} class="text-primary-500 hover:underline">
			{data.myapp.name}
		</a>
		<span class="-200">/</span>
		<a href={`/apps/${data.myapp.store_id}/keywords`} class="text-primary-500 hover:underline">
			Keywords
		</a>
		<span class="-200">/</span>
		<span class="font-medium">Compare</span>
	</nav>

	<!-- Header -->
	<section class={cardPadding}>
		<h1 class="h4 md:h3 mb-1">Keyword Rank Comparison</h1>
		<p class={textMuted}>
			Compare rank history for <strong>{data.myapp.name}</strong> across multiple keywords.
		</p>
		<p class="mt-2 text-sm -200">
			This view helps you measure momentum, spot ranking drops, and evaluate whether tracked terms
			are improving after metadata changes.
		</p>
		<p class="mt-2 text-xs -200">Tip: Add more keywords for comparison.</p>
	</section>

	<!-- Keyword Picker ───────────────────────────────────────────────────────── -->
	<section class={cardPadding}>
		<h2 class="h5 md:h4 mb-4">Keywords in Comparison</h2>

		<!-- Active keyword chips -->
		<div class="mb-4 flex min-h-[2.5rem] flex-wrap gap-2">
			{#if activeKeywords.length === 0}
				<p class="text-sm -200 italic">No keywords selected yet.</p>
			{/if}
			{#each activeKeywords as kw, i (kw)}
				<span
					class="flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm font-medium"
					style="border-color: {plotColors[i % plotColors.length]}; background-color: {plotColors[
						i % plotColors.length
					]}22"
				>
					<span
						class="h-2.5 w-2.5 rounded-full"
						style="background-color: {plotColors[i % plotColors.length]}"
					></span>
					{kw}
					<button
						type="button"
						onclick={() => removeKeyword(kw)}
						class="ml-0.5 rounded-full p-0.5 opacity-60 hover:opacity-100 focus:outline-none"
						aria-label="Remove {kw}"
					>
						✕
					</button>
				</span>
			{/each}
		</div>

		<!-- Search / add picker -->
		{#if activeKeywords.length <= 5}
			<div class="relative">
				<div class="flex gap-2">
					<div class="relative flex-1">
						<input
							type="text"
							class="input w-full pr-8"
							placeholder="Search keywords to add…"
							bind:value={searchQuery}
							onfocus={() => (pickerOpen = true)}
							onblur={() => setTimeout(() => (pickerOpen = false), 150)}
							onkeydown={(e) => {
								if (e.key === 'Escape') {
									pickerOpen = false;
									searchQuery = '';
								}
								if (e.key === 'Enter' && filteredCandidates.length > 0) {
									addKeyword(filteredCandidates[0].text);
								}
							}}
						/>
						{#if searchQuery}
							<button
								type="button"
								class="absolute right-2 top-1/2 -translate-y-1/2 text-primary-500 hover:text-primary-900"
								onclick={() => {
									searchQuery = '';
									pickerOpen = false;
								}}
							>
								✕
							</button>
						{/if}
					</div>
				</div>

				<!-- Dropdown list -->
				{#if pickerOpen && (filteredCandidates.length > 0 || searchQuery)}
					<div
						class="absolute z-50 mt-1 w-full rounded-lg border border-surface-300-700 bg-surface-50-950 shadow-xl"
					>
						{#if filteredCandidates.length === 0}
							<p class="px-4 py-3 text-sm -200">No matching keywords found.</p>
						{:else}
							<!-- Tracked section header (if any tracked appear) -->
							{@const trackedVisible = filteredCandidates.filter((c) => c.isTracked)}
							{@const appVisible = filteredCandidates.filter((c) => !c.isTracked)}

							{#if trackedVisible.length > 0}
								<div
									class="border-b border-surface-200-800 px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-primary-700-300"
								>
									Your tracked keywords
								</div>
								{#each trackedVisible as candidate}
									<button
										type="button"
										class="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm hover:bg-surface-100-900 focus:outline-none"
										onmousedown={() => addKeyword(candidate.text)}
									>
										<span class="text-xs">⭐</span>
										{candidate.text}
									</button>
								{/each}
							{/if}

							{#if appVisible.length > 0}
								{#if trackedVisible.length > 0}
									<div
										class="border-b border-surface-200-800 px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-primary-700-300"
									>
										App keywords
									</div>
								{/if}
								{#each appVisible as candidate}
									<button
										type="button"
										class="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm hover:bg-surface-100-900 focus:outline-none"
										onmousedown={() => addKeyword(candidate.text)}
									>
										{candidate.text}
									</button>
								{/each}
							{/if}
						{/if}
					</div>
				{/if}
			</div>

			<p class="mt-2 text-xs -200">
				{activeKeywords.length}/10 keywords selected
				{#if data.trackedKeywords.length > 0}
					• ⭐ = your personally tracked keywords
				{/if}
			</p>
		{:else}
			<p class="text-xs text-warning-600">
				Maximum of 10 keywords reached. Remove one to add another.
			</p>
		{/if}
	</section>

	<!-- Chart ────────────────────────────────────────────────────────────────── -->
	{#if chartData.length > 0}
		<section class={cardPadding}>
			<div class="mb-4 flex flex-wrap items-center gap-3">
				<h2 class="h5 md:h4">Rank History (Last 90 Days)</h2>
				<p class="text-xs -200">Lower = better position</p>
			</div>

			{#if data.requestedKeywords.length > data.resolvedKeywords.length}
				{@const missing = data.requestedKeywords.filter(
					(k) => !data.resolvedKeywords.find((r) => r.keyword_text.toLowerCase() === k)
				)}
				<p class="mb-3 text-xs text-warning-600">
					No rank data for: {missing.join(', ')}
				</p>
			{/if}

			<div class="h-[450px]">
				<LineChart
					data={chartData}
					x="crawled_date"
					series={seriesKeys}
					layer="svg"
					props={{
						xAxis: {
							format: (d) => format(d, PeriodType.Day, { variant: 'short' }),
							ticks: 7
						},
						yAxis: { format: (d) => `#${d}` }
					}}
					{yDomain}
				/>
			</div>
		</section>
	{:else if activeKeywords.length > 0}
		<section class={`${cardPadding} text-center`}>
			<p class={textMuted}>
				{#if data.resolvedKeywords.length === 0}
					None of the selected keywords have rank history data for this app yet.
				{:else}
					Loading rank history…
				{/if}
			</p>
		</section>
	{:else}
		<section class={`${cardPadding} text-center`}>
			<h2 class="h5 mb-2">No keywords selected</h2>
			<p class={textMuted}>Use the picker above to add keywords to compare.</p>
		</section>
	{/if}
</div>
