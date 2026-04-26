<script lang="ts">
	import { page } from '$app/state';
	import { Download, Copy, Check, Database, FileText, FlaskConical } from 'lucide-svelte';

	let { data } = $props();

	interface Dataset {
		key: string;
		size_bytes: number;
		last_modified: string;
		download_url: string;
	}

	interface ColumnDef {
		name: string;
		description: string;
	}

	// Static metadata keyed by substring match on S3 object key
	const datasetMeta: Record<
		string,
		{ name: string; description: string; rows: string; icon: any; columns: ColumnDef[] }
	> = {
		'store-apps-metrics': {
			name: 'App Metrics',
			description:
				'All apps in our database with their store metrics and metadata. Covers both Google Play and Apple App Store.',
			rows: '~5 million rows',
			icon: Database,
			columns: [
				{ name: 'store', description: 'App store — "Android" (Google Play) or "iOS" (Apple).' },
				{
					name: 'store_id',
					description: 'Unique store identifier, e.g. com.example.app or 123456789.'
				},
				{ name: 'app_name', description: 'Display name of the app.' },
				{ name: 'app_category', description: 'Store category the app is listed under.' },
				{ name: 'developer_id', description: 'Developer identifier as assigned by the store.' },
				{ name: 'price', description: 'App price in USD (0 for free apps).' },
				{ name: 'ad_supported', description: 'Whether the app shows ads (true/false).' },
				{
					name: 'in_app_purchases',
					description: 'Whether the app offers in-app purchases (true/false).'
				},
				{ name: 'total_installs', description: 'Total install count as reported by the store.' },
				{ name: 'total_ratings', description: 'Total number of user ratings.' },
				{ name: 'rating', description: 'Average user rating (0–5).' },
				{
					name: 'store_last_updated',
					description: 'Date the app was last updated by its developer on the store.'
				},
				{ name: 'release_date', description: 'Original release date of the app.' },
				{ name: 'appgoblin_updated_at', description: 'When AppGoblin last refreshed this record.' },
				{ name: 'last_crawl_result', description: 'Outcome of the most recent AppGoblin crawl.' }
			]
		},
		'store-apps-descriptions': {
			name: 'App Descriptions',
			description:
				'English-language app store descriptions for apps in our database. Useful for NLP, topic modelling, keyword extraction, and market research.',
			rows: 'Millions of apps',
			icon: FileText,
			columns: [
				{ name: 'appstore', description: 'App store — "Android" (Google Play) or "iOS" (Apple).' },
				{
					name: 'store_id',
					description: 'Unique store identifier, e.g. com.example.app or 123456789.'
				},
				{ name: 'category', description: 'Store category the app is listed under.' },
				{
					name: 'description_short',
					description: 'Short tagline or subtitle shown at the top of the store listing.'
				},
				{
					name: 'description',
					description: 'Full long-form description text from the store listing.'
				},
				{
					name: 'description_last_updated',
					description: 'When the description was last updated in the AppGoblin database.'
				}
			]
		},
		descriptions: {
			name: 'App Descriptions',
			description:
				'English-language app store descriptions for apps in our database. Useful for NLP, topic modelling, keyword extraction, and market research.',
			rows: 'Millions of apps',
			icon: FileText,
			columns: [
				{ name: 'appstore', description: 'App store - "Android" (Google Play) or "iOS" (Apple).' },
				{
					name: 'store_id',
					description: 'Unique store identifier, e.g. com.example.app or 123456789.'
				},
				{ name: 'category', description: 'Store category the app is listed under.' },
				{
					name: 'description_short',
					description: 'Short tagline or subtitle shown at the top of the store listing.'
				},
				{
					name: 'description',
					description: 'Full long-form description text from the store listing.'
				},
				{
					name: 'description_last_updated',
					description: 'When the description was last updated in the AppGoblin database.'
				}
			]
		}
	};

	function getMetaForKey(key: string) {
		const lowerKey = key.toLowerCase();
		for (const [pattern, meta] of Object.entries(datasetMeta)) {
			if (lowerKey.includes(pattern)) return meta;
		}
		return {
			name: key,
			description: 'App dataset export.',
			rows: '',
			icon: Database,
			columns: [] as ColumnDef[]
		};
	}

	function formatBytes(bytes: number): string {
		if (bytes >= 1_073_741_824) return (bytes / 1_073_741_824).toFixed(1) + ' GB';
		if (bytes >= 1_048_576) return (bytes / 1_048_576).toFixed(1) + ' MB';
		if (bytes >= 1_024) return (bytes / 1_024).toFixed(1) + ' KB';
		return bytes + ' B';
	}

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}

	function getFileName(path: string): string {
		const parts = path.split('/').filter(Boolean);
		return parts.at(-1) ?? path;
	}

	// Per-card copy state
	let copiedKey = $state<string | null>(null);

	async function copyUrl(url: string, key: string) {
		await navigator.clipboard.writeText(url);
		copiedKey = key;
		setTimeout(() => {
			copiedKey = null;
		}, 2000);
	}

	const datasets: Dataset[] = $derived(data.datasets ?? []);
	const isLoggedIn = $derived(Boolean(page.data.user));
	const signupTooltip = 'Create a free account to download and copy dataset URLs.';
</script>

<svelte:head>
	<title>Free App Dataset Downloads for Researchers & Data Scientists – AppGoblin</title>
	<meta
		name="description"
		content="Free mobile app datasets for researchers, data scientists, and marketers. Browse app metrics and app store descriptions for millions of Android and iOS apps, then download with a free account."
	/>
	<meta
		name="keywords"
		content="free app dataset, app store data download, mobile app research data, app metrics dataset, data science datasets, market research data, app developer data, free data download, app analytics data, app description dataset, android ios dataset, mobile market research"
	/>
	<meta property="og:title" content="Free App Dataset Downloads – AppGoblin" />
	<meta
		property="og:description"
		content="High-quality mobile app datasets for researchers, marketers, and data scientists. Free TSV downloads with app metrics, store data, and descriptions for millions of apps."
	/>
	<meta property="og:image" content="https://appgoblin.info/goblin_purple_hat_250.png" />
	<meta property="og:url" content="https://appgoblin.info/free-app-datasets" />
	<meta property="og:type" content="website" />
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="robots" content="index, follow" />
	<link rel="canonical" href="https://appgoblin.info/free-app-datasets" />
	<!-- Schema.org structured data for SEO -->
	{@html `<script type="application/ld+json">${JSON.stringify({
		'@context': 'https://schema.org',
		'@type': 'DataCatalog',
		name: 'AppGoblin Free App Data Exports',
		description: 'Free mobile app datasets for researchers, data scientists, and marketers',
		url: 'https://appgoblin.info/free-app-datasets',
		imageName: 'AppGoblin Logo',
		imageUrl: 'https://appgoblin.info/goblin_purple_hat_250.png',
		creator: {
			'@type': 'Organization',
			name: 'AppGoblin',
			url: 'https://appgoblin.info'
		},
		dataset: [
			{
				'@type': 'Dataset',
				name: 'App Metrics',
				description:
					'App store metrics and metadata for 5+ million apps covering installs, ratings, categories, pricing, and more',
				keyword: ['app metrics', 'app store data', 'market research'],
				distribution: {
					'@type': 'DataDownload',
					encodingFormat: 'TSV',
					compressionFormat: 'XZ'
				}
			},
			{
				'@type': 'Dataset',
				name: 'App Descriptions',
				description:
					'English-language app store descriptions from Google Play and Apple App Store for NLP, text analysis, and market research',
				keyword: ['app descriptions', 'text data', 'NLP dataset'],
				distribution: {
					'@type': 'DataDownload',
					encodingFormat: 'TSV',
					compressionFormat: 'XZ'
				}
			}
		],
		audience: ['Researchers', 'Data Scientists', 'Marketers']
	})}<\/script>`}
</svelte:head>

<div class="px-2 md:px-8 xl:px-24 grid grid-cols-1 gap-6 md:gap-10 py-4 md:py-8">
	<!-- Hero -->
	<div class="grid gap-2">
		<h1 class="text-3xl md:text-4xl font-black">
			Free App Data Exports for Researchers & Data Scientists
		</h1>
		<p class="text-lg max-w-2xl">
			High-quality, regularly updated app store datasets from Google Play and Apple App Store for
			researchers, data scientists, and marketers. Downloads are free with a free AppGoblin account.
		</p>
	</div>

	<!-- Format callout -->
	<div class="text-base">
		<strong class="">File format:</strong> All files are
		<code class="font-mono text-primary-800-200">.tsv.xz</code> tab-separated values compressed with XZ.
		Files uncompressed are a few gigabytes. Use appropriate tools when opening.
	</div>

	<!-- Dataset cards -->
	{#if datasets.length === 0}
		<div class="preset-filled-surface-100-900 p-8 text-center">
			No datasets available at this time. Please check back soon.
		</div>
	{:else}
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
			{#each datasets as dataset (dataset.key)}
				{@const meta = getMetaForKey(dataset.key)}
				{@const Icon = meta.icon}
				{@const isCopied = copiedKey === dataset.key}
				<div class="preset-outlined-surface-100-900 p-5 flex flex-col gap-4">
					<!-- Card header -->
					<div class="flex items-start gap-3">
						<div class="p-2 rounded-lg bg-primary-500/10 shrink-0">
							<Icon class="h-6 w-6 text-primary-500" />
						</div>
						<div class="flex-1 min-w-0">
							<h2 class="text-xl font-bold">{meta.name}</h2>
							{#if meta.rows}
								<p class="text-xs mt-0.5">{meta.rows}</p>
							{/if}
						</div>
					</div>

					<!-- Description -->
					<p class="text-sm">{meta.description}</p>

					<!-- Column definitions -->
					{#if meta.columns.length > 0}
						<details class="group">
							<summary
								class="cursor-pointer text-xs font-semibold select-none list-none flex items-center gap-1"
							>
								<span class="transition-transform group-open:rotate-90 inline-block">▶</span>
								Column definitions ({meta.columns.length})
							</summary>
							<div class="mt-2 overflow-x-auto">
								<table class="w-full text-xs border-collapse">
									<thead>
										<tr class="border-b border-surface-300-700">
											<th class="text-left py-1 pr-4 font-semibold w-40">Column</th>
											<th class="text-left py-1 font-semibold">Description</th>
										</tr>
									</thead>
									<tbody>
										{#each meta.columns as col}
											<tr class="border-b border-surface-200-800 last:border-0">
												<td class="py-1.5 pr-4 align-top">
													<code class="font-mono">{col.name}</code>
												</td>
												<td class="py-1.5 text-align-top">{col.description}</td>
											</tr>
										{/each}
									</tbody>
								</table>
							</div>
						</details>
					{/if}

					<!-- File info -->
					<div class="flex flex-wrap gap-3 text-xs text-gray-500">
						<span>
							<strong class="text-gray-400">File:</strong>
							<code class="font-mono">{getFileName(dataset.key)}</code>
						</span>
						<span>
							<strong class="text-gray-400">Size:</strong>
							{formatBytes(dataset.size_bytes)}
						</span>
						<span>
							<strong class="text-gray-400">Updated:</strong>
							{formatDate(dataset.last_modified)}
						</span>
					</div>

					<!-- Actions -->
					<div class="flex flex-wrap gap-2 mt-auto pt-1">
						{#if isLoggedIn}
							<a
								href={dataset.download_url}
								download
								class="btn preset-filled-primary-500 flex items-center gap-2 text-sm"
							>
								<Download class="h-4 w-4" />
								Download
							</a>
							<button
								onclick={() => copyUrl(dataset.download_url, dataset.key)}
								class="btn preset-tonal flex items-center gap-2 text-sm"
								aria-label="Copy download URL"
							>
								{#if isCopied}
									<Check class="h-4 w-4 text-green-500" />
									<span class="text-green-500">Copied!</span>
								{:else}
									<Copy class="h-4 w-4" />
									Copy URL
								{/if}
							</button>
						{:else}
							<a
								href="/auth/signup"
								title={signupTooltip}
								class="btn preset-filled-primary-500 flex items-center gap-2 text-sm"
							>
								<Download class="h-4 w-4" />
								Create Free Account
							</a>
							<a
								href="/auth/signup"
								title={signupTooltip}
								class="btn preset-tonal flex items-center gap-2 text-sm"
							>
								<Copy class="h-4 w-4" />
								Login To Copy URL
							</a>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}

	<div class="preset-outlined-surface-100-900 p-5 md:p-6">
		<h2 class="text-xl md:text-2xl font-bold mb-3">Premium Datasets Available</h2>
		<p class="text-sm md:text-base mb-3 max-w-3xl">
			Beyond the free exports on this page, AppGoblin already provides premium datasets for teams
			who need deeper app monetization and company relationship data.
		</p>
		<div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
			<div class="rounded-lg border border-surface-300-700 p-3">
				<p class="font-semibold mb-1">App-ads.txt Datasets</p>
				<p>
					Comprehensive app-ads.txt coverage for supply path analysis, fraud checks, and inventory
					quality workflows.
				</p>
			</div>
			<div class="rounded-lg border border-surface-300-700 p-3">
				<p class="font-semibold mb-1">Company SDK & App Lists</p>
				<p>
					Relationship datasets mapping companies to the apps that use their SDKs, built for market
					mapping, prospecting, and competitive analysis.
				</p>
			</div>
		</div>
		<div class="mt-4">
			<a href="/pricing" class="btn preset-filled-primary-500 text-sm"
				>View Premium Dataset Pricing</a
			>
		</div>
	</div>

	<!-- Footer note -->
	<p class="text-xs text-gray-500 max-w-2xl">
		These datasets are updated periodically. For high-frequency data needs, bulk exports, or custom
		dataset requests, see the <a href="/pricing" class="underline">pricing page</a>
		or <a href="/contact" class="underline">contact us</a>.
	</p>
</div>
