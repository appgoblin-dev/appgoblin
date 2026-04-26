<script lang="ts">
	import { page } from '$app/state';
	import type { AppFullDetail, KeywordScore } from '../../../../../../types';
	import AppKeywordsNav from '$lib/AppKeywordsNav.svelte';
	import AppKeywordsTable from '$lib/AppKeywordsTable.svelte';

	type KeywordData = {
		keywords: string[];
		keyword_scores: KeywordScore[];
	};

	type TrackedPageData = {
		myKeywords: KeywordData | string;
		myapp: Promise<AppFullDetail> | AppFullDetail;
		userTrackedKeywordsForApp?: Array<{
			id: number;
			keyword_text: string;
			created_at: string | Date;
		}>;
	};

	let { data }: { data: TrackedPageData } = $props();

	let trackedKeywordRows = $state<
		Array<{ id: number; keyword_text: string; created_at: string | Date }>
	>([]);
	let newKeywordText = $state('');
	let keywordTrackerMessage = $state('');
	let keywordTrackerLoading = $state(false);

	const isKeywordData = (value: unknown): value is KeywordData => {
		return (
			typeof value === 'object' &&
			value !== null &&
			Array.isArray((value as KeywordData).keyword_scores)
		);
	};

	const normalizeKeywordForDedupe = (value: string) => value.trim().toLowerCase();

	const dedupeByKeywordText = (scores: KeywordScore[]) => {
		const seen = new Set<string>();
		const unique: KeywordScore[] = [];
		for (const score of scores) {
			const key = normalizeKeywordForDedupe(score.keyword_text);
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
	const userAddedKeywordScores = $derived.by(() =>
		dedupeByKeywordText(
			keywordScores.filter(
				(score) => score.is_keyword_user_added === true || score.is_user_added === true
			)
		)
	);

	$effect(() => {
		trackedKeywordRows = data.userTrackedKeywordsForApp ?? [];
	});

	function normalizeKeyword(value: string): string {
		return value.trim().toLowerCase();
	}

	async function addTrackedKeywordForApp() {
		const keywordText = newKeywordText.trim();
		if (!keywordText) {
			keywordTrackerMessage = 'Keyword cannot be empty.';
			return;
		}

		const normalized = normalizeKeyword(keywordText);
		if (trackedKeywordRows.some((row) => normalizeKeyword(row.keyword_text) === normalized)) {
			keywordTrackerMessage = 'Keyword is already in your tracked list for this app.';
			return;
		}

		keywordTrackerLoading = true;
		keywordTrackerMessage = '';
		try {
			const response = await fetch('/api/follows', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					entity: 'keyword',
					follow: true,
					storeId: page.params.id,
					keywordText
				})
			});

			if (!response.ok) {
				keywordTrackerMessage =
					response.status === 401
						? 'Sign in to save tracked keywords.'
						: 'Could not add keyword right now.';
				return;
			}

			trackedKeywordRows = [
				{ id: Date.now(), keyword_text: keywordText, created_at: new Date().toISOString() },
				...trackedKeywordRows
			];
			newKeywordText = '';
			keywordTrackerMessage = 'Keyword added to your tracked list.';
		} catch {
			keywordTrackerMessage = 'Could not add keyword right now.';
		} finally {
			keywordTrackerLoading = false;
		}
	}

	async function removeTrackedKeywordForApp(keywordText: string) {
		keywordTrackerLoading = true;
		keywordTrackerMessage = '';
		try {
			const response = await fetch('/api/follows', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					entity: 'keyword',
					follow: false,
					storeId: page.params.id,
					keywordText
				})
			});

			if (!response.ok) {
				keywordTrackerMessage =
					response.status === 401
						? 'Sign in to manage tracked keywords.'
						: 'Could not remove keyword right now.';
				return;
			}

			const normalized = normalizeKeyword(keywordText);
			trackedKeywordRows = trackedKeywordRows.filter(
				(row) => normalizeKeyword(row.keyword_text) !== normalized
			);
			keywordTrackerMessage = 'Keyword removed from your tracked list.';
		} catch {
			keywordTrackerMessage = 'Could not remove keyword right now.';
		} finally {
			keywordTrackerLoading = false;
		}
	}

	const cardBase = 'rounded-xl border border-surface-300-700 bg-surface-100-900 shadow-sm';
</script>

{#await data.myapp}
	<div class={`${cardBase} p-6 text-center`}>Loading app details...</div>
{:then myapp}
	<div class="space-y-6 px-2 md:px-8">
		<AppKeywordsNav storeId={myapp.store_id} />
		<div class="grid grid-cols-2 gap-2 md:gap-8">
			<section class={`${cardBase} p-6`}>
				<h1 class="h4 md:h3 mb-3">My Keywords</h1>
				<p class="text-sm -200 mb-4">
					Manage your personal watchlist for {myapp.name}.
				</p>
				<p class="text-sm -200 mb-4">
					Tracked keywords are your priority ASO set for this app. Use this list to build focused
					compare views and monitor movement over time.
				</p>
				<form
					onsubmit={(event) => {
						event.preventDefault();
						addTrackedKeywordForApp();
					}}
					class="flex flex-col gap-2 md:flex-row"
				>
					<input
						type="text"
						class="input flex-1"
						placeholder="Add a keyword to track"
						bind:value={newKeywordText}
						disabled={keywordTrackerLoading}
					/>
					<button
						type="submit"
						class="btn preset-tonal w-full md:w-auto"
						disabled={keywordTrackerLoading}
					>
						{keywordTrackerLoading ? 'Saving...' : 'Add Keyword'}
					</button>
				</form>

				{#if keywordTrackerMessage}
					<p class="mt-2 text-sm -200">{keywordTrackerMessage}</p>
				{/if}
			</section>

			<section class={`${cardBase} p-6`}>
				<h2 class="h5 md:h4 mb-3">Current List</h2>
				<p class="mb-3 text-xs -200">
					Keep this list tight: remove low-value terms so compare stays focused on strategic
					keywords.
				</p>
				{#if trackedKeywordRows.length === 0}
					<p class="text-sm -200">No personal tracked keywords for this app yet.</p>
				{:else}
					<div class="space-y-2">
						{#each trackedKeywordRows as row (row.id)}
							<div
								class="flex flex-col gap-3 rounded-lg border border-surface-300-700 p-3 md:flex-row md:items-center md:justify-between"
							>
								<div>
									<p class="font-medium">{row.keyword_text}</p>
									<p class="text-xs -200">
										Added {new Date(row.created_at).toLocaleString()}
									</p>
								</div>
								<button
									type="button"
									class="btn preset-outlined-error-500 btn-sm w-full md:w-auto"
									onclick={() => removeTrackedKeywordForApp(row.keyword_text)}
									disabled={keywordTrackerLoading}
								>
									Remove
								</button>
							</div>
						{/each}
					</div>
				{/if}
			</section>
		</div>

		<section class={`${cardBase} p-6`}>
			<h2 class="h5 md:h4 mb-3">My Keyword Performance Table</h2>
			<p class="mb-3 text-sm -200">
				Shows keyword metrics for keywords you've added to this app's tracked list that also have
				ranking signals. Note if you added a new keyword recently, it may take some time for ranking
				data to populate and show up in this
			</p>
			{#if userAddedKeywordScores.length > 0}
				<AppKeywordsTable data={userAddedKeywordScores} storeId={myapp.store_id} linkMode="app" />
			{:else}
				<p class="text-sm -200">
					No keyword score rows are currently flagged as user-added for this app.
				</p>
			{/if}
		</section>
	</div>
{/await}
