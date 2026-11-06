<script lang="ts">
	import { resolve } from '$app/paths';

	let { id }: { id: number } = $props();

	type Stage = { status: string; at: string | null; note: string };
	type Progress = { version_code?: string | null; stages: Record<string, Stage> };
	let progress = $state<Progress | null>(null);
	let loading = $state(false);
	let failed = $state(false);

	const labels: Record<string, string> = {
		request: 'Request submitted',
		download: 'App downloaded',
		sdk_scan: 'App SDKs scanned',
		data_import: 'Data imported to database',
		waydroid: 'Waydroid emulation run'
	};

	async function loadProgress() {
		if (loading) return;
		loading = true;
		failed = false;
		try {
			const response = await fetch(
				resolve('/account/requested-scans/[id]/progress', { id: String(id) })
			);
			if (!response.ok) throw new Error('Could not load progress');
			progress = await response.json();
		} catch {
			failed = true;
		} finally {
			loading = false;
		}
	}

	function handleToggle(event: Event) {
		if ((event.currentTarget as HTMLDetailsElement).open && !progress && !loading) {
			void loadProgress();
		}
	}
</script>

<details class="mt-3" ontoggle={handleToggle}>
	<summary class="cursor-pointer text-sm font-medium">View progress</summary>
	<div class="mt-3 space-y-3 text-sm" aria-live="polite">
		{#if loading}
			<p class="text-surface-500">Loading progress…</p>
		{:else if failed}
			<p class="text-error-600">Unable to load progress.</p>
			<button type="button" class="btn btn-sm preset-tonal" onclick={loadProgress}>Retry</button>
		{:else if progress}
			{#if progress.version_code}<p>Version code: {progress.version_code}</p>{/if}
			<ol class="space-y-3">
				{#each Object.entries(progress.stages) as [key, stage] (key)}
					<li class="border-l-2 border-surface-300-700 pl-3">
						<p class="font-medium">{labels[key] ?? key} · {stage.status.replaceAll('_', ' ')}</p>
						{#if stage.at}<p class="text-xs text-surface-500">
								{new Date(stage.at).toLocaleString()}
							</p>{/if}
						<p class="text-xs text-surface-500">{stage.note}</p>
					</li>
				{/each}
			</ol>
		{/if}
	</div>
</details>
