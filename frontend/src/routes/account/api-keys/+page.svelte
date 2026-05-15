<script lang="ts">
	import { enhance } from '$app/forms';
	import type { PageData, ActionData } from './$types';
	import KeyRound from 'lucide-svelte/icons/key-round';
	import Plus from 'lucide-svelte/icons/plus';
	import Trash2 from 'lucide-svelte/icons/trash-2';
	import Copy from 'lucide-svelte/icons/copy';
	import Check from 'lucide-svelte/icons/check';
	import ExternalLink from 'lucide-svelte/icons/external-link';

	let { data, form }: { data: PageData; form?: ActionData | null } = $props();

	let showCreateForm = $state(false);
	let copiedKey = $state(false);
	let newKeyName = $state('');
	let revokingId = $state<number | null>(null);

	function copyKey(key: string) {
		navigator.clipboard.writeText(key);
		copiedKey = true;
		setTimeout(() => (copiedKey = false), 2000);
	}

	function formatDate(date: string | Date): string {
		return new Date(date).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	function formatLastUsed(date: string | Date | null): string {
		if (!date) return 'Never';
		return new Date(date).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function handleCreateSuccess() {
		if (form?.success && form.section === 'create') {
			showCreateForm = false;
			newKeyName = '';
		}
	}
</script>

<svelte:head>
	<title>API Keys - AppGoblin</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="card preset-tonal p-6 md:p-8 space-y-4">
		<div class="flex items-start justify-between gap-4">
			<div>
				<h1 class="text-2xl font-bold flex items-center gap-3">
					<KeyRound size={28} class="text-primary-500" />
					API Keys
				</h1>
				<p class="text-sm text-surface-600-400 mt-1">
					Generate API keys to access the AppGoblin public API programmatically.
				</p>
			</div>
			<a href="/api-docs" class="btn preset-tonal flex items-center gap-2 text-sm">
				<ExternalLink size={16} />
				API Docs
			</a>
		</div>

		<!-- Rate limit info -->
		{#if data.subscription}
			<div class="p-4 rounded-lg bg-surface-100-900 border border-surface-200-800">
				<p class="text-sm">
					<span class="font-semibold">Current Plan:</span>
					<span class="text-primary-500">{data.subscriptionTier ?? 'Free'}</span>
					<span class="text-surface-500 ml-2">|</span>
					<span class="ml-2 font-semibold">Limits:</span>
					<span class="text-surface-600-400">
						{#if data.subscriptionTier === 'Premium B2B'}
							10,000 req/min, 500,000 req/day
						{:else if data.subscriptionTier === 'Business SDK' || data.subscriptionTier === 'App-Ads.txt'}
							2,000 req/min, 100,000 req/day
						{:else if data.subscriptionTier === 'Premium Access'}
							200 req/min, 10,000 req/day
						{:else}
							30 req/min, 1,000 req/day
						{/if}
					</span>
				</p>
			</div>
		{:else}
			<div class="p-4 rounded-lg bg-surface-100-900 border border-surface-200-800">
				<p class="text-sm">
					<span class="font-semibold">Current Plan:</span>
					<span class="text-surface-600-400">Free</span>
					<span class="text-surface-500 ml-2">|</span>
					<span class="ml-2 font-semibold">Limits:</span>
					<span class="text-surface-600-400">30 req/min, 1,000 req/day</span>
				</p>
			</div>
		{/if}
	</div>

	<!-- Messages -->
	{#if form?.message}
		<div
			class="p-4 rounded-lg {form.success
				? 'bg-success-500/10 border border-success-500/30 text-success-600'
				: 'bg-error-500/10 border border-error-500/30 text-error-600'}"
		>
			{form.message}
		</div>
	{/if}

	<!-- New key display (shown once after creation) -->
	{#if form?.rawKey && form.section === 'create'}
		<div class="card preset-tonal p-6 space-y-3 border border-warning-500/30">
			<p class="text-warning-500 font-semibold text-sm">
				Save this key now — it will not be shown again.
			</p>
			<div class="flex items-center gap-2">
				<code
					class="flex-1 p-3 rounded-lg bg-surface-950-50 text-sm font-mono break-all select-all"
				>
					{form.rawKey}
				</code>
				<button
					type="button"
					class="btn preset-tonal shrink-0"
					onclick={() => copyKey(form.rawKey)}
				>
					{#if copiedKey}
						<Check size={16} class="text-success-500" />
					{:else}
						<Copy size={16} />
					{/if}
				</button>
			</div>
		</div>
	{/if}

	<!-- Create new key -->
	<div class="card preset-tonal p-6 md:p-8 space-y-4">
		<p class="text-sm text-surface-600-400">
			Authentication, endpoints, and example requests live in the
			<a href="/api-docs" class="text-primary-500 hover:underline">public API docs</a>.
		</p>
		{#if !showCreateForm}
			<button
				class="btn preset-filled-primary-500 flex items-center gap-2"
				onclick={() => (showCreateForm = true)}
			>
				<Plus size={18} />
				Generate New Key
			</button>
		{:else}
			<form method="post" action="?/create" use:enhance class="space-y-4">
				<div>
					<label for="key-name" class="block text-sm font-medium mb-1">Key Name</label>
					<input
						id="key-name"
						name="name"
						type="text"
						bind:value={newKeyName}
						placeholder="e.g., Production API, CI/CD Pipeline"
						maxlength="100"
						required
						class="input p-3 rounded-lg bg-surface-100-900 border border-surface-300-700 w-full"
					/>
				</div>
				<div class="flex gap-3">
					<button type="submit" class="btn preset-filled-primary-500"> Create Key </button>
					<button
						type="button"
						class="btn preset-tonal"
						onclick={() => {
							showCreateForm = false;
							newKeyName = '';
						}}
					>
						Cancel
					</button>
				</div>
			</form>
		{/if}
	</div>

	<!-- Keys list -->
	<div class="card preset-tonal p-6 md:p-8">
		{#if data.apiKeys.length === 0}
			<p class="text-surface-500 text-center py-8">No API keys yet. Generate one to get started.</p>
		{:else}
			<div class="overflow-x-auto">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b border-surface-300-700 text-left">
							<th class="pb-3 font-semibold">Name</th>
							<th class="pb-3 font-semibold">Key</th>
							<th class="pb-3 font-semibold">Created</th>
							<th class="pb-3 font-semibold">Last Used</th>
							<th class="pb-3 font-semibold">Status</th>
							<th class="pb-3 font-semibold"></th>
						</tr>
					</thead>
					<tbody>
						{#each data.apiKeys as key (key.id)}
							<tr class="border-b border-surface-300-700/50">
								<td class="py-4 font-medium">{key.name}</td>
								<td class="py-4">
									<code class="text-xs bg-surface-200-800 px-2 py-1 rounded">
										{key.key_prefix}•••
									</code>
								</td>
								<td class="py-4 text-surface-500">{formatDate(key.created_at)}</td>
								<td class="py-4 text-surface-500">{formatLastUsed(key.last_used_at)}</td>
								<td class="py-4">
									{#if key.is_active}
										<span class="badge preset-filled-success-900-100 text-xs">Active</span>
									{:else}
										<span class="badge preset-filled-surface-500 text-xs">Revoked</span>
									{/if}
								</td>
								<td class="py-4 text-right">
									{#if key.is_active}
										<form
											method="post"
											action="?/revoke"
											use:enhance={() => {
												revokingId = key.id;
												return async ({ update }) => {
													revokingId = null;
													await update();
												};
											}}
										>
											<input type="hidden" name="id" value={key.id} />
											<button
												type="submit"
												class="btn btn-sm preset-tonal text-error-500 flex items-center gap-1"
												disabled={revokingId === key.id}
											>
												<Trash2 size={14} />
												{revokingId === key.id ? 'Revoking...' : 'Revoke'}
											</button>
										</form>
									{/if}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
</div>
