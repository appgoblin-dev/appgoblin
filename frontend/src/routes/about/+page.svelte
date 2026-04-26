<script>
	import discordIcon from '$lib/svg/discord-mark-black.svg?raw';
	let titlePadding = 'p-2 md:p-4';
	let contentPadding = 'p-2 md:p-4';
	let cardPadding = 'p-2 md:p-4';
</script>

<svelte:head>
	<title>About AppGoblin: Competitor Analysis and App Marketing Tools</title>
	<meta
		name="description"
		content="Free ASO tools, competitor analysis, lead generation and ad analytics platform for apps. Includes free app datasets for researchers, marketers, and data scientists."
	/>
	<meta
		name="keywords"
		content="AppGoblin, aso, app marketing, lead generation, competitor analysis, app advertising, in-app advertising, app monetization, open source, app analytics, app market intelligence, mobile app insights, app advertising, app marketing"
	/>
	<meta property="og:title" content="About AppGoblin: App Advertising and Marketing Tools" />
	<meta
		property="og:description"
		content="AppGoblin is a free app marketing and advertising analytics platform."
	/>
	<meta property="og:image" content="https://appgoblin.info/goblin_purple_hat_250.png" />
	<meta property="og:url" content="https://appgoblin.info/about" />
	<meta property="og:type" content="website" />
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content="About AppGoblin: App Marketing and Ad Analytics" />
	<meta
		name="twitter:description"
		content="AppGoblin is a free app marketing and advertising analytics platform."
	/>
	<meta name="twitter:image" content="https://appgoblin.info/goblin_purple_hat_250.png" />
	<meta name="robots" content="index, follow" />
	<link rel="canonical" href="https://appgoblin.info/about" />
</svelte:head>

<div class="p-2 px-2 md:px-16 xl:px-32 grid grid-cols-1 gap-4 md:gap-8">
	<h1 class="text-3xl font-bold">Welcome to AppGoblin</h1>
	<p>
		AppGoblin has marketing and advertising tools to help illuminate the world of in app advertising
		and marketing. AppGoblin has many <strong class="">free mobile app marketing resources</strong> as
		well as some paid datasets like competitor analysis and SDK client lists. The goal is to provide as
		much free and reproducible open source app analytics for the community as possible.
	</p>
	<p>
		See the <a
			href="/pricing"
			class="underline decoration-primary-500/60 hover:decoration-primary-500">pricing page</a
		>
		for plan details. We offer Free access for exploration, Premium Access for exports, and B2B tiers
		for SDK intelligence, app-ads.txt datasets, and combined access.
	</p>
	<p>
		Looking for open app data? Browse our
		<a
			href="/free-app-datasets"
			class="underline decoration-primary-500/60 hover:decoration-primary-500"
			>free app datasets page</a
		>
		for app metrics and app descriptions available with a free account.
	</p>

	<div class="items-center">
		<div class="flex flex-col gap-4 items-center">
			<div class="flex flex-wrap gap-3 justify-center">
				<a
					href="/account"
					class="btn preset-filled-primary-500 inline-flex items-center gap-2 px-6 py-3"
				>
					<span class="text-black font-bold">Create Free Account</span>
				</a>
				<a
					href="/pricing"
					class="btn preset-filled-primary-100-900 inline-flex items-center gap-2 px-6 py-3 rounded-lg"
				>
					Get premium data access →
				</a>
			</div>
			<a
				href="mailto:contact@appgoblin.info"
				class="btn preset-outlined inline-flex items-center gap-2 px-6 py-3"
			>
				<span>Get in Touch</span>
			</a>

			<div class="text-primary-900-100 text-sm pt-1">
				<p>contact@appgoblin.info</p>
			</div>
		</div>
	</div>

	<div class="card preset-filled-surface-100-900 {cardPadding}">
		<h2 class="h2 {titlePadding}">Features</h2>
		<div class={contentPadding}>
			<ul class="space-y-4">
				<li>
					<strong>App Intelligence</strong> — Data on 4M+ iOS and Android apps (updated daily): keywords,
					trends, rankings, new apps discovery, and growth metrics
				</li>
				<li>
					<strong>SDK Analysis</strong> — Detailed breakdown of SDKs in decompiled Android and iOS apps,
					including advertising, analytics, and open-source libraries
				</li>
				<li>
					<strong>Companies Directory</strong> — Rankings of mobile app companies based on SDK integration
					frequency, filterable by category
				</li>
				<li>
					<strong>Company Intelligence</strong> — See the top client apps for any mobile SDK or services
					company
				</li>
				<li>
					<strong>Ad Tech Insights</strong> — Tracks live ad campaigns and the ad tech domains apps communicate
					with
				</li>
				<li>
					<strong>ASO Tools</strong> — Free keyword research tools and data dumps to optimize app store
					visibility
				</li>
				<li>
					<strong>App-Ads.txt</strong> — Daily-updated files tying apps to their DIRECT and RESELLER ad
					networks and SSPs
				</li>
			</ul>
		</div>
	</div>

	<div class="card preset-filled-surface-100-900 {cardPadding}">
		<h2 class="h2 {titlePadding}">Who It's For</h2>
		<div class={contentPadding}>
			<ul class="space-y-3">
				<li>
					<strong>App & Game Developers</strong> — Grow your app with free ASO tools, keyword tracking,
					rankings data, and competitor SDK analysis
				</li>
				<li>
					<strong>Ad Sales Teams</strong> — Prospect clients by analyzing which apps use your target ad
					networks, mediation platforms, and analytics providers
				</li>
				<li>
					<strong>Ad Networks & DSPs</strong> — Perform fraud detection by auditing SDK integrations and
					validating app-ads.txt supply-path data
				</li>
				<li>
					<strong>DSPs — App-Ads.txt Verification</strong> — Map app-ads.txt DIRECT and RESELLER entries
					to real app store IDs rather than just domain names
				</li>
				<li>
					<strong>Researchers & Journalists</strong> — Deep technical analysis across millions of apps
					— SDKs, API calls, and data security patterns at scale
				</li>
				<li>
					<strong>Competitor Researchers</strong> — Track which SDKs competitors are adopting and how
					fast they're growing
				</li>
				<li>
					<strong>Privacy Advocates</strong> — Identify hidden trackers, ad-tech domains, and SDK networks
					embedded in popular apps
				</li>
			</ul>
		</div>
	</div>

	<div class="card preset-filled-surface-100-900 p-2 md:p-8">
		<h2 class="h2 p-2 md:p-4">Community & Feedback</h2>
		<div class="p-2 space-y-4">
			<div class="flex flex-wrap gap-2">
				<a
					class="btn preset-tonal"
					href="https://github.com/appgoblin-dev/appgoblin"
					target="_blank"
					rel="noreferrer"
				>
					<p class="text-base">GitHub</p>
				</a>
				<a class="btn preset-tonal" href="mailto:contact@appgoblin.info">
					<p class="text-base">Email</p>
				</a>
				<a
					class="btn preset-tonal"
					href="https://linkedin.com/companies/AppGoblin"
					target="_blank"
					rel="noreferrer"
				>
					<p class="text-base">LinkedIn</p>
				</a>
			</div>
			<a
				class="btn preset-tonal"
				href="https://discord.gg/7jpWEhkXRW"
				target="_blank"
				rel="noreferrer"
			>
				<div class="inline-flex items-center gap-2">
					{@html discordIcon}
					<p class="text-base">Join AppGoblin Discord</p>
				</div>
			</a>
			<p>
				Join AppGoblin's Discord for a quick way to contact me or discuss ASO, app marketing and in
				app advertisements. Feel free to give feedback or request new features.
			</p>
		</div>
	</div>
	<div class="card preset-filled-surface-100-900 {cardPadding}">
		<h2 class="h2 {titlePadding}">Free Resources</h2>
		<div class={contentPadding}>
			<p>
				The majority of AppGoblin's marketing data and ASO features are free to browse. You can also
				access free exports from our
				<a
					href="/free-app-datasets"
					class="underline decoration-primary-500/60 hover:decoration-primary-500"
					>free app datasets page</a
				>. Some open source data sets are available for free download on
				<strong
					><a href="https://github.com/appgoblin-dev/appgoblin-data"
						>github.com/appgoblin-dev/appgoblin-data</a
					></strong
				>. Feel free to reach out if there are other parts of data you'd like to see exported.
			</p>
			<br />
			<p>
				The code is maintained open source for transparency. The data is collected with
				<strong
					><a href="https://github.com/appgoblin-dev/adscrawler"
						>github.com/appgoblin-dev/adscrawler</a
					></strong
				>
				and the website code can be found at
				<strong
					><a href="https://github.com/appgoblin-dev/appgoblin"
						>github.com/appgoblin-dev/appgoblin</a
					></strong
				>.
			</p>
		</div>
	</div>
	<br />
	<div class="card preset-filled-surface-100-900 {cardPadding}">
		<h2 class="h2 {titlePadding}">Check the Trackers on Your Android Device</h2>
		<div class={contentPadding}>
			<p>AppGoblin has an Android app which can be used to check the trackers on your device.</p>
			<br />
			<p>You can download it from the Google Play Store.</p>
			<a
				href="https://app.thirdgate.dev/appgoblin-android-site"
				target="_blank"
				class="anchor inline-flex items-baseline"
			>
				<img class="w-40 md:w-60" src="/gp_en_badge_web_generic.png" alt="AppGoblin Android App" />
			</a>
		</div>
	</div>
</div>
