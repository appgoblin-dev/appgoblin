<script lang="ts">
	import { enhance } from '$app/forms';
	import type { SubmitFunction } from '@sveltejs/kit';
	import type { AccountFormResult, FollowedCompany } from './types';

	let {
		companies,
		form
	}: {
		companies: FollowedCompany[];
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
	<h2 class="text-lg font-semibold">Company Watchlist</h2>
	<p class="text-sm text-surface-500">Add companies for quick access in your account menu.</p>

	<form method="POST" action="?/addFollowedCompany" use:enhance class="flex gap-2">
		<input
			type="number"
			name="company_id"
			class="input flex-1"
			placeholder="Company ID"
			min="1"
			required
		/>
		<button type="submit" class="btn preset-tonal">Add</button>
	</form>

	{#if form?.section === 'tracked-companies' && form?.message}
		<p class="text-sm {form.success ? 'text-success-600' : 'text-error-600'}">{form.message}</p>
	{/if}

	<div class="space-y-2">
		{#if companies.length === 0}
			<p class="text-sm text-surface-500">No companies in your watchlist yet.</p>
		{:else}
			{#each companies as company (company.id)}
				<div class="rounded-lg border border-surface-100-900 p-3">
					{#if editingId === company.id}
						<form
							method="POST"
							action="?/updateFollowedCompany"
							use:enhance={syncFormAndCloseEditor}
							class="flex flex-col gap-3 md:flex-row md:items-center"
						>
							<input type="hidden" name="id" value={company.id} />
							<input
								type="number"
								name="company_id"
								class="input flex-1"
								value={company.company_id}
								min="1"
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
									{#if company.company_domain}
										<a class="hover:underline" href={`/companies/${company.company_domain}`}>
											{company.company_name ?? company.company_domain}
										</a>
									{:else}
										{company.company_name ?? `Company #${company.company_id}`}
									{/if}
								</p>
								<p class="text-xs text-surface-500">ID: {company.company_id}</p>
							</div>

							<div class="flex gap-2">
								<button
									type="button"
									class="btn preset-outlined"
									onclick={() => (editingId = company.id)}
								>
									Edit
								</button>
								<form
									method="POST"
									action="?/deleteFollowedCompany"
									use:enhance={syncFormAndCloseEditor}
								>
									<input type="hidden" name="id" value={company.id} />
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
