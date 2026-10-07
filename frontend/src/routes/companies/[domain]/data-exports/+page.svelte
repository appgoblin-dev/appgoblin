<script lang="ts">
	import DataExportColumnDocs from '$lib/components/docs/DataExportColumnDocs.svelte';

	interface Props {
		data: {
			companyName: string;
			canDownload: boolean;
			userId: number | null;
			reports: Array<{
				file_key: string;
				report_name: string;
				row_count: number | null;
				last_modified: string;
				url?: string | null;
			}>;
		};
	}

	let { data }: Props = $props();

	let hasAnyExports = $derived(data.reports.length > 0);
	let hasAppAdsTxtExport = $derived(
		data.reports.some((report) => report.report_name.toLowerCase().includes('app-ads'))
	);
	let hasVerifiedAppsExport = $derived(
		data.reports.some((report) => !report.report_name.toLowerCase().includes('app-ads'))
	);

	const getDatasetMetadata = (report: Props['data']['reports'][number]) => {
		const name = `${report.report_name} ${report.file_key}`.toLowerCase();
		const isAppAdsTxt = name.includes('app-ads') || name.includes('ads_txt');
		const isIos = name.includes('ios') || name.includes('apple');

		return {
			label: isAppAdsTxt
				? 'App-Ads.txt Data'
				: `SDK & API Verified Apps (${isIos ? 'iOS' : 'Android'})`,
			platform: isAppAdsTxt ? 'Cross-Platform' : isIos ? 'iOS' : 'Android',
			signalDepth: isAppAdsTxt
				? 'Apps with app-ads.txt records for the company domain.'
				: 'Apps verified by matched SDKs or API HTTP requests.'
		};
	};
</script>

<svelte:head>
	<title>{data.companyName} Data Exports — AppGoblin</title>
	<meta
		name="description"
		content="Download the complete {data.companyName} app list by SDK adoption, API signals, and app-ads.txt records. Analysis-ready data for B2B prospecting, compliance, and competitive intelligence."
	/>
	<meta name="robots" content="index, nofollow" />
</svelte:head>

<section class="mx-2 md:mx-auto md:max-w-4xl space-y-8">
	<h1 class="h1">{data.companyName} Client App Downloads</h1>

	<p class="text-base md:text-lg max-w-3xl">
		Download all client apps data for {data.companyName}. Data comes in two styles: App-Ads.txt and
		SDK/API Verified. App-Ads.txt data is fuzzier and covers all known apps and domains, this is
		useful for fraud tracking. SDK/API verified apps are a smaller subset of the apps among the top
		200k apps that were verified to be using {data.companyName} via the presence of their SDK or via API
		calls to domains they own. SDK/API data is much more deterministic though it by it's nature covers
		a smaller portion of the whole. Please feel free to reach out if you have questions.
	</p>

	<!-- Value Propositions -->
	<section class="space-y-6">
		<h2 class="text-xl font-bold">What this data does for you</h2>

		<div class="space-y-5">
			<div>
				<h3 class="font-semibold">Sales Prospecting</h3>
				<p class="text-sm opacity-80">
					Stop guessing who uses {data.companyName}. Get a clean list of iOS and Android apps with
					active {data.companyName} SDK integrations or API signals. Target accounts that are already
					monetizing heavily and prime for a competitive pitch.
				</p>
			</div>

			<div>
				<h3 class="font-semibold">Audit Supply-Side Relationships via App-Ads.txt</h3>
				<p class="text-sm opacity-80">
					Map out {data.companyName}'s direct and reseller supply path configurations to identify
					programmatic arbitrage opportunities or compliance risks.
				</p>
			</div>
		</div>
	</section>

	<!-- How Teams Deploy -->
	<section class="space-y-4">
		<h2 class="text-xl font-bold">How teams deploy this data</h2>
		<ul class="space-y-3">
			<li class="pl-2">
				<p class="font-semibold">Competitor Analysis</p>
				<p class="text-sm opacity-80">
					Pinpoint publishers reliant on {data.companyName}.
				</p>
			</li>
			<li class="pl-2">
				<p class="font-semibold">Corporate Development, VC and Hedge Funds</p>
				<p class="text-sm opacity-80">
					Run tracking on {data.companyName}'s market share growth or contraction across specific
					app categories to validate investment theses.
				</p>
			</li>
			<li class="pl-2">
				<p class="font-semibold">Data Products & Analytics Platforms</p>
				<p class="text-sm opacity-80">
					Feed this into your own proprietary enterprise dashboards or enrichment engines via the <a
						href="/api-docs"
						class="underline hover:text-primary-600-400">AppGoblin API</a
					>.
				</p>
			</li>
		</ul>
	</section>

	<!-- Available Datasets -->
	{#if !hasAnyExports}
		<section class="rounded-lg border border-surface-200-800/70 p-6 text-center">
			<p class="text-base opacity-70">No exports are currently available for this domain.</p>
		</section>
	{:else}
		<section class="space-y-4">
			<h2 class="text-xl font-bold">Available Datasets</h2>
			<div class="overflow-x-auto rounded-lg border border-surface-200-800/70">
				<table class="table w-full">
					<thead>
						<tr class="border-b border-surface-200-800/50">
							<th class="text-left py-3 px-4 text-sm font-semibold">Dataset</th>
							<th class="text-left py-3 px-4 text-sm font-semibold">Platform</th>
							<th class="text-left py-3 px-4 text-sm font-semibold">Description</th>
							<th class="text-right py-3 px-4 text-sm font-semibold">Rows</th>
							<th class="text-right py-3 px-4 text-sm font-semibold">Updated</th>
							<th class="text-center py-3 px-4 text-sm font-semibold">Format</th>
							<th class="text-right py-3 px-4"></th>
						</tr>
					</thead>
					<tbody>
						{#each data.reports as row}
							{@const metadata = getDatasetMetadata(row)}
							<tr class="border-b border-surface-200-800/30 last:border-b-0">
								<td class="py-3 px-4 text-sm font-medium">{metadata.label}</td>
								<td class="py-3 px-4 text-sm opacity-70">{metadata.platform}</td>
								<td class="py-3 px-4 text-sm opacity-70">{metadata.signalDepth}</td>
								<td class="py-3 px-4 text-right text-sm opacity-70">
									{row.row_count?.toLocaleString() ?? '—'}
								</td>
								<td class="py-3 px-4 text-right text-sm opacity-70">
									{new Date(row.last_modified).toLocaleDateString()}
								</td>
								<td class="py-3 px-4 text-center text-sm opacity-70">CSV</td>

								<td class="py-3 px-4 text-right">
									{#if data.canDownload && row.url}
										<a
											href={row.url}
											target="_blank"
											rel="noopener noreferrer"
											class="btn preset-filled-primary-500 p-3 text-sm"
										>
											Signed Download
										</a>
									{:else}
										<a href="/pricing" class="btn preset-filled-primary-500 p-3 text-sm"
											>Get B2B Premium</a
										>
									{/if}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</section>
	{/if}

	<!-- Column reference documentation -->
	<section class="space-y-8">
		<h2 class="text-xl font-bold">CSV Column References</h2>

		{#if hasVerifiedAppsExport}
			<DataExportColumnDocs variant="verified-apps" companyName={data.companyName} />
		{/if}

		{#if hasAppAdsTxtExport}
			<DataExportColumnDocs variant="app-ads-txt" companyName={data.companyName} />
		{/if}
	</section>
</section>
