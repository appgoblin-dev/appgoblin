<script lang="ts">
	type ReportEntry = {
		slug: string;
		url: string;
		title: string;
		period: string | null;
		sortValue: number;
	};

	const monthNames = [
		'january',
		'february',
		'march',
		'april',
		'may',
		'june',
		'july',
		'august',
		'september',
		'october',
		'november',
		'december'
	];

	const reportsPageUrl = 'https://appgoblin.info/reports';
	const reportsPageTitle = 'Mobile App Marketing Reports for Ad Buyers and Publishers | AppGoblin';
	const reportsPageDescription =
		'Browse AppGoblin mobile app marketing reports for ad buyers and mobile app publishers. Compare ad network reach, creatives, UA trends, and advertiser strategies.';

	// Class constants
	const tagClass =
		'inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-surface-200 dark:bg-surface-700 text-surface-900 dark:text-surface-50';
	const reportCardClass =
		'group block h-full rounded-lg border border-surface-200 dark:border-surface-700 bg-white dark:bg-surface-900 p-6 shadow-sm hover:shadow-lg transition-all hover:-translate-y-1 hover:border-purple-400 dark:hover:border-purple-500';
	const reportTitleClass =
		'text-2xl font-bold text-surface-900 dark:text-surface-100 group-hover:text-purple-600 dark:group-hover:text-purple-400 transition';
	const reportPeriodClass = 'text-xl font-semibold  mt-2';
	const ctaLinkClass =
		'flex items-center gap-2 text-sm font-semibold text-purple-600 dark:text-purple-400 group-hover:gap-3 transition-all';

	function toTitleCase(value: string): string {
		return value
			.split('-')
			.filter(Boolean)
			.map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
			.join(' ');
	}

	function getDateFromSlug(slug: string): string | null {
		const segments = slug.split('-');
		const yearIndex = segments.findIndex((segment) => /^\d{4}$/.test(segment));

		if (yearIndex !== -1) {
			const year = segments[yearIndex];
			const monthSegment = segments[yearIndex + 1];
			const monthIndex = monthNames.indexOf(monthSegment?.toLowerCase() ?? '');

			if (monthIndex >= 0) {
				const monthNum = String(monthIndex + 1).padStart(2, '0');
				return `${year}-${monthNum}-01`;
			}
		}
		return null;
	}

	function generateJsonLdArticles(): Array<{
		'@type': string;
		position: number;
		item: {
			'@type': string[];
			'@id': string;
			name: string;
			headline: string;
			description: string;
			url: string;
			datePublished?: string;
			inLanguage: string;
			audience: { '@type': string; audienceType: string }[];
			keywords: string[];
		};
	}> {
		return reports.map((report, index) => {
			const datePublished = getDateFromSlug(report.slug);
			const absoluteReportUrl = `https://appgoblin.info${report.url}`;
			return {
				'@type': 'ListItem',
				position: index + 1,
				item: {
					'@type': ['Report', 'NewsArticle'],
					'@id': `${absoluteReportUrl}#report`,
					name: report.title,
					headline: report.title,
					description:
						'Mobile app marketing report covering user acquisition trends, ad network distribution, creative performance, and publisher-relevant insights.',
					url: absoluteReportUrl,
					...(datePublished && { datePublished }),
					inLanguage: 'en',
					audience: [
						{ '@type': 'Audience', audienceType: 'Mobile ad buyers' },
						{ '@type': 'Audience', audienceType: 'Mobile app publishers' }
					],
					keywords: [
						'mobile app marketing report',
						'user acquisition',
						'ad network analytics',
						'mobile advertising creatives',
						'mobile app publishers'
					]
				}
			};
		});
	}

	const reportModules = import.meta.glob('./*/+page.svelte');

	const reports: ReportEntry[] = Object.keys(reportModules)
		.map((path) => {
			const match = path.match(/\.\/([^/]+)\/\+page\.svelte$/);
			const slug = match ? match[1] : path;
			const segments = slug.split('-');
			const yearIndex = segments.findIndex((segment) => /^\d{4}$/.test(segment));

			let title = toTitleCase(slug);
			let period: string | null = null;
			let sortValue = 0;

			if (yearIndex !== -1) {
				const nameParts = segments.slice(0, yearIndex);
				const periodParts = segments.slice(yearIndex);
				const year = Number(periodParts[0]);
				const monthSegment = periodParts[1] ?? '';
				const monthIndex = monthNames.indexOf(monthSegment.toLowerCase());

				title = nameParts.length > 0 ? toTitleCase(nameParts.join('-')) : toTitleCase(slug);

				if (!Number.isNaN(year)) {
					sortValue = year * 100 + (monthIndex >= 0 ? monthIndex + 1 : 0);
					if (monthIndex >= 0) {
						const monthName = monthSegment.charAt(0).toUpperCase() + monthSegment.slice(1);
						period = `${monthName} ${year}`;
					} else {
						const additional = periodParts.slice(1).map(toTitleCase).join(' ');
						period = [additional, year].filter(Boolean).join(' ').trim() || `${year}`;
					}
				}
			}

			return {
				slug,
				url: `/reports/${slug}`,
				title,
				period,
				sortValue
			};
		})
		.sort((a, b) => {
			if (b.sortValue !== a.sortValue) return b.sortValue - a.sortValue;
			return a.title.localeCompare(b.title);
		});
</script>

<svelte:head>
	<title>{reportsPageTitle}</title>
	<meta name="description" content={reportsPageDescription} />
	<link rel="canonical" href={reportsPageUrl} />
	<meta property="og:type" content="website" />
	<meta property="og:site_name" content="AppGoblin" />
	<meta property="og:title" content={reportsPageTitle} />
	<meta property="og:description" content={reportsPageDescription} />
	<meta property="og:url" content={reportsPageUrl} />
	<meta property="og:image" content="https://appgoblin.info/appgoblin_screenshot.png" />
	<meta
		property="og:image:alt"
		content="AppGoblin reports hub for mobile app marketing and user acquisition intelligence"
	/>
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content={reportsPageTitle} />
	<meta name="twitter:description" content={reportsPageDescription} />
	<meta name="twitter:image" content="https://appgoblin.info/appgoblin_screenshot.png" />

	<!-- Structured Data for CollectionPage and Articles -->
	{@html `<script type="application/ld+json">${JSON.stringify({
		'@context': 'https://schema.org',
		'@graph': [
			{
				'@type': 'CollectionPage',
				'@id': `${reportsPageUrl}#collection`,
				url: reportsPageUrl,
				name: 'Mobile App Marketing Reports',
				description: reportsPageDescription,
				inLanguage: 'en',
				isPartOf: {
					'@id': 'https://appgoblin.info/#website'
				},
				about: [
					{ '@type': 'Thing', name: 'Mobile App Marketing' },
					{ '@type': 'Thing', name: 'User Acquisition' },
					{ '@type': 'Thing', name: 'Mobile Ad Networks' }
				],
				audience: [
					{ '@type': 'Audience', audienceType: 'Mobile ad buyers' },
					{ '@type': 'Audience', audienceType: 'Mobile app publishers' }
				],
				mainEntity: {
					'@id': `${reportsPageUrl}#itemlist`
				},
				publisher: {
					'@id': 'https://appgoblin.info/#organization'
				}
			},
			{
				'@type': 'ItemList',
				'@id': `${reportsPageUrl}#itemlist`,
				name: 'AppGoblin Report Index',
				numberOfItems: reports.length,
				itemListOrder: 'https://schema.org/ItemListOrderDescending',
				itemListElement: generateJsonLdArticles()
			},
			{
				'@type': 'BreadcrumbList',
				'@id': `${reportsPageUrl}#breadcrumbs`,
				itemListElement: [
					{
						'@type': 'ListItem',
						position: 1,
						name: 'Home',
						item: 'https://appgoblin.info/'
					},
					{
						'@type': 'ListItem',
						position: 2,
						name: 'Reports',
						item: reportsPageUrl
					}
				]
			},
			{
				'@type': 'Organization',
				'@id': 'https://appgoblin.info/#organization',
				name: 'AppGoblin',
				url: 'https://appgoblin.info/',
				logo: {
					'@type': 'ImageObject',
					url: 'https://appgoblin.info/AppGoblin_Large_Logo.png'
				}
			},
			{
				'@type': 'WebSite',
				'@id': 'https://appgoblin.info/#website',
				url: 'https://appgoblin.info/',
				name: 'AppGoblin',
				publisher: {
					'@id': 'https://appgoblin.info/#organization'
				}
			}
		]
	})}<\/script>`}
</svelte:head>

<div class="container mx-auto max-w-6xl px-4 py-12">
	<!-- Enhanced Header Section -->
	<header class="mb-16">
		<div class="text-center mb-12">
			<h1 class="mt-6 text-5xl md:text-6xl font-bold text-surface-900 dark:text-surface-50">
				Mobile App Marketing Reports
			</h1>
			<p class="mt-4 text-xl text-surface-600 dark:text-surface-400 max-w-3xl mx-auto">
				Research-grade report library for mobile ad buyers and app publishers. Compare UA trends, ad
				network coverage, creative distribution, and advertiser strategy shifts.
			</p>
		</div>
	</header>

	<section>
		<h2 class="text-2xl font-bold text-surface-900 dark:text-surface-50 mb-8">Available Reports</h2>
		<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
			{#each reports as report}
				<a href={report.url} class={reportCardClass}>
					<!-- Report Header -->
					<div class="flex items-start justify-between mb-4">
						<div class="flex-1">
							<h3 class={reportTitleClass}>{report.title}</h3>
							{#if report.period}
								<p class={reportPeriodClass}>{report.period}</p>
							{/if}
						</div>
					</div>

					<!-- Report Features -->
					<div class="flex flex-wrap gap-2 mb-6">
						<span class={tagClass}>Creatives</span>
						<span class={tagClass}>Top Advertisers</span>
						<span class={tagClass}>Ad Network Analytics</span>
					</div>

					<!-- CTA -->
					<div class={ctaLinkClass}>
						<span>View Report</span>
						<svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
							<path
								d="M12.293 3.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 11-1.414-1.414L14.586 9H4a1 1 0 110-2h10.586l-2.293-2.293a1 1 0 010-1.414z"
							/>
						</svg>
					</div>
				</a>
			{/each}
		</div>
	</section>
</div>
