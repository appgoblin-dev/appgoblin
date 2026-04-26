<script lang="ts">
	import { enhance } from '$app/forms';
	import type { SubmitFunction } from '@sveltejs/kit';
	import type { AccountFormResult, FollowedApp } from './types';

	let {
		apps,
		form
	}: {
		apps: FollowedApp[];
		form?: AccountFormResult;
	} = $props();

	let editingId = $state<number | null>(null);

	const syncFormAndCloseEditor: SubmitFunction = () => {
		return async ({ result, update }) => {
			await update();

			if (result.type === 'success') {
				editingId = null;
			}
		};
	};
</script>

<section class="space-y-4">
	<h2 class="text-lg font-semibold">App Watchlist</h2>
	<p class="text-sm text-surface-500">Add apps you want in your quick access menu.</p>

	<form method="POST" action="?/addFollowedApp" use:enhance class="flex gap-2">
		<input
			type="text"
			name="store_id"
			class="input flex-1"
			placeholder="App store ID (example: com.example.app)"
			required
		/>
		<button type="submit" class="btn preset-tonal">Add</button>
	</form>

	{#if form?.section === 'tracked-apps' && form?.message}
		<p class="text-sm {form.success ? 'text-success-600' : 'text-error-600'}">{form.message}</p>
	{/if}

	<div class="space-y-2">
		{#if apps.length === 0}
			<p class="text-sm text-surface-500">No apps in your watchlist yet.</p>
		{:else}
			{#each apps as app (app.id)}
				<div class="rounded-lg border border-surface-100-900 p-3">
					{#if editingId === app.id}
						<form
							method="POST"
							action="?/updateFollowedApp"
							use:enhance={syncFormAndCloseEditor}
							class="flex flex-col gap-3 md:flex-row md:items-center"
						>
							<input type="hidden" name="id" value={app.id} />
							<input
								type="text"
								name="store_id"
								class="input flex-1"
								value={app.store_id}
								required
							/>
							<div class="flex gap-2">
								<button type="submit" class="btn preset-tonal">Save</button>
								<button
									type="button"
									class="btn preset-outlined"
									onclick={() => (editingId = null)}
								>
									Cancel
								</button>
							</div>
						</form>
					{:else}
						<div class="flex items-center justify-between gap-3">
							<div>
								<p class="font-medium">
									{#if app.app_name}
										<a class="hover:underline" href={`/apps/${app.store_id}`}>{app.app_name}</a>
									{:else}
										<a class="hover:underline" href={`/apps/${app.store_id}`}>{app.store_id}</a>
									{/if}
								</p>
								<p class="text-xs text-surface-500">{app.store_id}</p>
							</div>

							<div class="flex gap-2">
								<button
									type="button"
									class="btn preset-outlined"
									onclick={() => (editingId = app.id)}
								>
									Edit
								</button>
								<form
									method="POST"
									action="?/deleteFollowedApp"
									use:enhance={syncFormAndCloseEditor}
								>
									<input type="hidden" name="id" value={app.id} />
									<button type="submit" class="btn preset-outlined-error-500">Remove</button>
								</form>
							</div>
						</div>
					{/if}
				</div>
			{/each}
		{/if}
	</div>
</section>
