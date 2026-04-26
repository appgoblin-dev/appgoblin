<script lang="ts">
	import { enhance } from '$app/forms';
	import type { AccountFormResult, TrackedKeyword } from './types';

	let {
		keywords,
		form
	}: {
		keywords: TrackedKeyword[];
		form?: AccountFormResult;
	} = $props();
</script>

<section class="space-y-4">
	<h2 class="text-lg font-semibold">Keyword Watchlist</h2>
	<p class="text-sm text-surface-500">Keywords are private to your account and scoped by app ID.</p>

	<form
		method="POST"
		action="?/addTrackedKeyword"
		use:enhance
		class="grid gap-2 md:grid-cols-[1fr_1fr_auto]"
	>
		<input type="text" name="store_id" class="input" placeholder="App store ID" required />
		<input type="text" name="keyword_text" class="input" placeholder="Keyword" required />
		<button type="submit" class="btn preset-tonal">Add</button>
	</form>

	{#if form?.section === 'tracked-keywords' && form?.message}
		<p class="text-sm {form.success ? 'text-success-600' : 'text-error-600'}">{form.message}</p>
	{/if}

	<div class="space-y-2">
		{#if keywords.length === 0}
			<p class="text-sm text-surface-500">No keywords in your watchlist yet.</p>
		{:else}
			{#each keywords as keyword (keyword.id)}
				<div class="rounded-lg border border-surface-100-900 p-3">
					<div class="flex items-center justify-between gap-3">
						<div>
							<p class="font-medium">{keyword.keyword_text}</p>
							<p class="text-xs text-surface-500">
								{#if keyword.app_name}
									<a href={`/apps/${keyword.store_id}/keywords`} class="hover:underline">
										{keyword.app_name}
									</a>
									(
									<a href={`/apps/${keyword.store_id}/keywords`} class="hover:underline">
										{keyword.store_id}
									</a>
									)
								{:else}
									<a href={`/apps/${keyword.store_id}/keywords`} class="hover:underline">
										{keyword.store_id}
									</a>
								{/if}
							</p>
						</div>

						<form method="POST" action="?/deleteTrackedKeyword" use:enhance>
							<input type="hidden" name="id" value={keyword.id} />
							<button type="submit" class="btn preset-outlined-error-900-100">Remove</button>
						</form>
					</div>
				</div>
			{/each}
		{/if}
	</div>
</section>
