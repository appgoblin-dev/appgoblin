<script lang="ts">
	import { enhance } from '$app/forms';

	import type { ActionData, PageData } from './$types';

	export let data: PageData;
	export let form: ActionData;
</script>

<svelte:head>
	<title>Sign In - AppGoblin</title>
</svelte:head>

<div class="max-w-5xl mx-auto py-8 px-4 md:px-8">
	<div class="grid md:grid-cols-2 gap-6 md:gap-12 lg:gap-16 items-start">
		<!-- Dynamic Sign Up CTA / SEO Callouts -->
		<div
			class="card border border-surface-100-900 p-6 md:p-8 flex flex-col justify-center space-y-4"
		>
			{#if data.redirectTo?.includes('/sdks/')}
				<h3 class="text-xl md:text-2xl font-bold">Unlock Mobile SDK Data for Free</h3>
				<p class="text-sm md:text-base leading-relaxed">
					You've requested access to deep technical SDK tracking data. Good news—it's <strong
						>completely free</strong
					>! Simply create an account to start analyzing app architecture, performing critical
					competitor research, and tracking the latest mobile trends with AppGoblin's high-quality
					technical intelligence.
				</p>
				<div class="pt-4 mt-4 border-t border-surface-100-900">
					<p class="text-sm">
						<span class="font-semibold">Looking for business intelligence?</span>
						Our paid
						<a href="/pricing" class="underline font-medium hover:text-primary-500"
							>Business SDK subscription</a
						> allows you to see exactly which apps use this SDK, perfect for sales prospecting and ad
						tech teams.
					</p>
				</div>
			{:else if data.redirectTo?.includes('/app-adstxt')}
				<h3 class="text-xl md:text-2xl font-bold">Access Technical App-Ads.txt Data</h3>
				<p class="text-sm md:text-base leading-relaxed">
					You're trying to view publisher App-Ads.txt details. Good news—it's <strong
						>completely free</strong
					>! Create an account to browse AppGoblin's high-quality technical data. Use our tools to
					map programmatic supply chains, fight ad fraud, and conduct rigorous ad network research.
				</p>
				<div class="pt-4 mt-4 border-t border-surface-100-900">
					<p class="text-sm">
						<span class="font-semibold">Need bulk ad-tech data?</span>
						Our paid
						<a href="/pricing" class="underline font-medium hover:text-primary-500"
							>B2B App-Ads.txt subscription</a
						> provides full, daily updated datasets for DSPs and SSPs.
					</p>
				</div>
			{:else}
				<h2 class="text-xl md:text-2xl font-bold">Create a free account</h2>
				<p class=" text-sm md:text-base leading-relaxed">
					New to AppGoblin? Create a free account to get started and unlock deeper technical
					insights.
				</p>
				<ul class="text-sm md:text-base list-disc list-inside space-y-1 mb-4">
					<li>Advanced App SDK breakdowns</li>
					<li>App Comparisons & Trending Growth Apps</li>
					<li>Keyword tracking and rankings</li>
				</ul>
			{/if}

			<div class="mt-auto pt-4">
				<a class="btn preset-filled w-full" href="/auth/signup"> Create AppGoblin Account </a>
			</div>
		</div>

		<!-- Sign In Form -->
		<div class="border border-surface-100-900 rounded-lg p-6 md:p-8 space-y-6">
			<div>
				<h2 class="text-2xl font-bold">Sign In</h2>
				<p class=" text-sm mt-1">Welcome back to AppGoblin</p>
			</div>

			<form class="space-y-4" method="post" use:enhance>
				{#if data.redirectTo}
					<input type="hidden" name="redirectTo" value={data.redirectTo} />
				{/if}

				<div class="space-y-1">
					<label class="label font-medium text-sm" for="form-login.email">Email</label>
					<input
						class="input"
						type="email"
						id="form-login.email"
						name="email"
						autocomplete="username"
						required
						value={form?.email ?? ''}
					/>
				</div>

				<div class="space-y-1">
					<div class="flex items-center justify-between">
						<label class="label font-medium text-sm" for="form-login.password">Password</label>
						<a
							class="text-xs text-primary-600-400 hover:text-primary-500 underline"
							href="/auth/forgot-password">Forgot password?</a
						>
					</div>
					<input
						class="input"
						type="password"
						id="form-login.password"
						name="password"
						autocomplete="current-password"
						required
					/>
				</div>

				<div class="pt-2">
					<button class="btn preset-filled w-full">Sign In</button>
				</div>

				{#if form?.message}
					<div
						class="p-3 rounded bg-error-500/10 border border-error-500/30 text-error-600 text-center text-sm font-medium mt-4"
					>
						{form.message}
					</div>
				{/if}
			</form>
		</div>
	</div>
</div>
