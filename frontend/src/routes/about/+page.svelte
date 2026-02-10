<script>
	import discordIcon from '$lib/svg/discord-mark-black.svg?raw';
	let titlePadding = 'p-2 md:p-4';
	let contentPadding = 'p-2 md:p-4';
	let cardPadding = 'p-2 md:p-4';
	let pricingText = 'mt-2 text-sm opacity-80';
</script>

<svelte:head>
	<title>About AppGoblin: Competitor Analysis and App Marketing Tools</title>
	<meta
		name="description"
		content="Free ASO tools, competitor analysis, lead generation and ad analytics platform for apps. Tools for competitor analysis, app-ads.txt analysis, and more."
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

<div class="p-2 px-2 md:px-16 lg:px-32 grid grid-cols-1 gap-4 md:gap-8">
	<h1 class="text-3xl font-bold text-primary-900-100">Welcome to AppGoblin</h1>
	<p>
		AppGoblin has marketing and advertising tools to help illuminate the world of in app advertising
		and marketing. AppGoblin has many <strong class="text-primary-900-100"
			>free mobile app marketing resources</strong
		> as well as some paid datasets like competitor analysis and SDK client lists. The goal is to provide
		as much free and reproducible open source app analytics for the community as possible.
	</p>
	<p class="text-sm text-surface-600-400">
		See the <a
			href="/pricing"
			class="underline decoration-primary-500/60 hover:decoration-primary-500">pricing page</a
		>
		for plan details. We offer Free access for exploration, Premium Supporter for exports, and B2B tiers
		for SDK intelligence, app-ads.txt datasets, and combined access.
	</p>

	<div class="items-center">
		<div class="flex flex-col gap-4 items-center">
			<a
				href="mailto:contact@appgoblin.info"
				class="btn-primary inline-flex items-center gap-2 px-6 py-3 bg-white rounded-lg hover:scale-105 transition-transform duration-200 shadow-lg"
			>
				<span class="text-black font-bold">Get in Touch or Schedule Free Walkthrough</span>
				<span class="text-black font-bold">→</span>
			</a>
			<div class="text-white/80 text-sm pt-1">
				<p>contact@appgoblin.info</p>
			</div>
		</div>
	</div>

	<div class="card preset-filled-surface-100-900 p-2 md:p-8">
		<h2 class="h2 p-2 md:p-4">Community & Feedback</h2>
		<div class="p-2 space-y-4">
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
				The majority of AppGoblin's marketing data and ASO features are free to browse. Some open
				source data sets are available for free download. They can be found on
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
		<h2 class="h2 {titlePadding}">Background</h2>
		<div class={contentPadding}>
			<p>
				Originally this came out of a curiosity I had about the IAB app-ads.txt standard in 2022. In
				order to scrape app-ads.txt files I had to first get 4,000,000+ iOS and Android apps + their
				respective publisher URLs. While that project, like app-ads.txt itself, went unused, I
				remained interested in letting the database of apps keep growing. Then in the fall of 2023
				while on haitus from real work, I started working on an API and UI.
			</p>
			<br />
			<p>
				Now, App Goblin is the combination of several open source projects I built. Yes, there are a
				large number of similar companies like data.ai and sensortower.com which have many more
				features. But it was a great project for me to learn more frontend and javascript.
			</p>
			<br />
			<p>If you have questions or suggestions please feel free to reach out.</p>
			<br />
			<a href="mailto:contact@appgoblin.info">contact@appgoblin.info</a>
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
