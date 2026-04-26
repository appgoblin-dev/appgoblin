<script lang="ts">
	import WhiteCard from '$lib/WhiteCard.svelte';

	type ExportRow = {
		key: 'appAdsTxt' | 'companyVerifiedAndroid' | 'companyVerifiedIos';
		name: string;
		available: boolean;
		url: string | null;
	};

	interface Props {
		data: {
			canDownload: boolean;
			companyName: string;
			downloadUrls: {
				appAdsTxt: string | null;
				companyVerifiedAndroid: string | null;
				companyVerifiedIos: string | null;
			} | null;
			exportStats: {
				appAdsTxt: { estimatedRows: number; available: boolean };
				companyVerifiedAndroid: { estimatedRows: number; available: boolean };
				companyVerifiedIos: { estimatedRows: number; available: boolean };
			};
		};
	}

	let { data }: Props = $props();

	let exportRows = $derived.by<ExportRow[]>(() => {
		const rows: ExportRow[] = [
			{
				key: 'appAdsTxt',
				name: 'App-ads.txt publishers (iOS + Android)',
				available: data.exportStats.appAdsTxt.available,
				url: data.downloadUrls?.appAdsTxt ?? null
			},
			{
				key: 'companyVerifiedAndroid',
				name: 'SDK/API traffic apps (Android)',
				available: data.exportStats.companyVerifiedAndroid.available,
				url: data.downloadUrls?.companyVerifiedAndroid ?? null
			},
			{
				key: 'companyVerifiedIos',
				name: 'SDK/API traffic apps (iOS)',
				available: data.exportStats.companyVerifiedIos.available,
				url: data.downloadUrls?.companyVerifiedIos ?? null
			}
		];

		return rows.filter((row) => row.available);
	});
</script>

<h1 class="h1 mx-2 md:mx-auto md:max-w-4xl">Data Exports</h1>

<div class="p-4 grid gap-4 mx-2 md:mx-auto md:max-w-4xl">
	<p class="text-base">
		Exports provide raw, analysis-ready datasets tied to this company so teams can run custom
		modeling, compliance checks, and longitudinal market tracking outside the dashboard.
	</p>

	{#if exportRows.length === 0}
		<p class="text-base">No exports are currently available for this domain.</p>
	{:else}
		<div class="rounded-md border border-surface-200-800">
			<ul class="divide-y divide-surface-200-800">
				{#each exportRows as row}
					<li class="p-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
						<div class="min-w-0">
							<p class="text-base font-medium leading-snug">{row.name}</p>
							<p class="text-xs opacity-70">CSV export</p>
						</div>
						<div class="shrink-0">
							{#if data.canDownload && row.url}
								<a
									href={row.url}
									class="btn btn-sm preset-outlined-primary-100-900"
									target="_blank"
									rel="noopener noreferrer"
								>
									Download CSV
								</a>
							{:else}
								<a href="/pricing" class="btn btn-sm preset-filled-primary-50-950">
									Get Premium Data
								</a>
							{/if}
						</div>
					</li>
				{/each}
			</ul>
		</div>

		{#if !data.canDownload}
			<p class=" text-sm">
				Data exports are included with a paid subscription.
				<a href="/pricing" class="underline hover:text-primary-600-400">View pricing</a> to unlock.
			</p>
		{/if}
	{/if}
</div>
