<script>
	import { enhance } from '$app/forms';
	let titlePadding = 'p-2 md:p-4';
	let contentPadding = 'p-2 md:p-4';
	let cardPadding = 'p-2 md:p-4';

	let loading = false;
	/** @type {string | null} */
	let activePriceKey = null;

	/** @param {{ result: import('@sveltejs/kit').ActionResult }} param0 */
	const handleSubscribeResult = async ({ result }) => {
		console.log('Form result:', result);

		if (result.type === 'redirect') {
			console.log('Redirecting to:', result.location);
			window.location.href = result.location;
			return;
		}

		if (result.type === 'failure') {
			console.error('Form failed:', result.data);
		}

		loading = false;
		activePriceKey = null;
	};

	/** @param {{ formElement: HTMLFormElement }} param0 */
	const subscribeEnhance = ({ formElement }) => {
		activePriceKey = formElement.dataset.priceKey ?? null;
		loading = true;

		return handleSubscribeResult;
	};
</script>

<svelte:head>
	<title>Pricing - AppGoblin</title>
</svelte:head>

<div class="p-2 px-2 md:px-16 lg:px-32 grid grid-cols-1 gap-4 md:gap-8">
	<h1 class="text-3xl font-bold text-primary-900-100">Pricing</h1>

	<div class="card preset-filled-surface-100-900 {cardPadding}">
		<h2 class="h2 {titlePadding}">Plans & Pricing</h2>
		<div class={contentPadding}>
			<p>Simple pricing for teams that need clear data access.</p>

			<br />

			<div class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
				<div class="card preset-filled-surface-50-950 p-4 flex flex-col gap-3">
					<div>
						<p class="text-xs uppercase tracking-wide opacity-60">Free</p>
						<p class="text-2xl font-semibold">$0</p>
						<p class="text-xs opacity-70">Indie devs, researchers, casual users</p>
					</div>
					<ul class="text-xs list-disc list-inside space-y-1 opacity-90">
						<li>Advanced per-SDK results</li>
						<li>Keyword tools, comparisons, rankings</li>
						<li>Ad intelligence, trending apps</li>
						<li>Email alerts/saved searches</li>
					</ul>
					<p class="text-xs opacity-60">Included with every account</p>
				</div>

				<div class="card preset-filled-surface-50-950 p-4 flex flex-col gap-3">
					<div>
						<p class="text-xs uppercase tracking-wide opacity-60">Premium Supporter</p>
						<p class="text-2xl font-semibold">$49</p>
						<p class="text-xs opacity-70">Freelance ASO, small teams, power users</p>
					</div>
					<ul class="text-xs list-disc list-inside space-y-1 opacity-90">
						<li>Everything in Free</li>
						<li>App exports (CSV/Excel/JSON)</li>
					</ul>
					<form
						method="POST"
						action="?/subscribe"
						use:enhance={subscribeEnhance}
						data-price-key="app_dev"
						class="mt-auto"
					>
						<input type="hidden" name="priceKey" value="app_dev" />
						<button type="submit" disabled={loading} class="btn preset-filled-primary-500 w-full">
							{loading && activePriceKey === 'app_dev' ? 'Redirecting to checkout...' : 'Subscribe'}
						</button>
					</form>
				</div>

				<div class="card preset-filled-surface-50-950 p-4 flex flex-col gap-3">
					<div>
						<p class="text-xs uppercase tracking-wide opacity-60">Business SDK</p>
						<p class="text-2xl font-semibold">$299</p>
						<p class="text-xs opacity-70">Ad tech, SDK vendors, competitive intel teams</p>
					</div>
					<ul class="text-xs list-disc list-inside space-y-1 opacity-90">
						<li>Everything in Premium</li>
						<li>SDK exports and usage lists</li>
						<li>Bulk company reports</li>
					</ul>
					<form
						method="POST"
						action="?/subscribe"
						use:enhance={subscribeEnhance}
						data-price-key="b2b_sdk"
						class="mt-auto"
					>
						<input type="hidden" name="priceKey" value="b2b_sdk" />
						<button type="submit" disabled={loading} class="btn preset-filled-primary-500 w-full">
							{loading && activePriceKey === 'b2b_sdk' ? 'Redirecting to checkout...' : 'Subscribe'}
						</button>
					</form>
				</div>

				<div class="card preset-filled-surface-50-950 p-4 flex flex-col gap-3">
					<div>
						<p class="text-xs uppercase tracking-wide opacity-60">App-Ads.txt</p>
						<p class="text-2xl font-semibold">$299</p>
						<p class="text-xs opacity-70">Ad networks, publishers, ad ops teams</p>
					</div>
					<ul class="text-xs list-disc list-inside space-y-1 opacity-90">
						<li>Everything in Premium</li>
						<li>Daily app-ads.txt downloads</li>
						<li>Historical snapshots</li>
					</ul>
					<form
						method="POST"
						action="?/subscribe"
						use:enhance={subscribeEnhance}
						data-price-key="b2b_appads"
						class="mt-auto"
					>
						<input type="hidden" name="priceKey" value="b2b_appads" />
						<button type="submit" disabled={loading} class="btn preset-filled-primary-500 w-full">
							{loading && activePriceKey === 'b2b_appads'
								? 'Redirecting to checkout...'
								: 'Subscribe'}
						</button>
					</form>
				</div>

				<div
					class="card preset-filled-surface-50-950 p-4 flex flex-col gap-3 border border-primary-500/40"
				>
					<div>
						<p class="text-xs uppercase tracking-wide opacity-60">Premium B2B</p>
						<p class="text-2xl font-semibold">$499</p>
						<p class="text-xs opacity-70">Agencies and larger companies</p>
					</div>
					<ul class="text-xs list-disc list-inside space-y-1 opacity-90">
						<li>Business SDK + App-Ads.txt</li>
						<li>Combined access + higher limits</li>
					</ul>
					<form
						method="POST"
						action="?/subscribe"
						use:enhance={subscribeEnhance}
						data-price-key="b2b_premium"
						class="mt-auto"
					>
						<input type="hidden" name="priceKey" value="b2b_premium" />
						<button type="submit" disabled={loading} class="btn preset-filled-primary-500 w-full">
							{loading && activePriceKey === 'b2b_premium'
								? 'Redirecting to checkout...'
								: 'Subscribe'}
						</button>
					</form>
				</div>
			</div>

			<div class="mt-8 grid grid-cols-1 gap-4 lg:grid-cols-2">
				<div class="card preset-filled-surface-50-950 p-5 space-y-3">
					<h3 class="text-lg font-semibold">For Researchers, Journalists, and Academics</h3>
					<p class="text-sm text-surface-600-400">
						AppGoblin supports independent research and journalism. If you're a student, academic
						researcher, or investigative journalist working on mobile advertising, privacy, or app
						ecosystems, you're welcome to reach out for collaboration.
					</p>
				</div>

				<div class="card preset-filled-surface-50-950 p-5 space-y-3">
					<h3 class="text-lg font-semibold">Free Resources</h3>
					<p class="text-sm text-surface-600-400">
						The majority of AppGoblin's marketing data and ASO features are free to browse. Some
						open source data sets are available for free download at
						<a
							href="https://github.com/appgoblin-dev/appgoblin-data"
							class="underline decoration-primary-500/60 hover:decoration-primary-500"
						>
							github.com/appgoblin-dev/appgoblin-data
						</a>
						. Feel free to reach out if there are other parts of data you'd like to see exported.
					</p>
					<p class="text-sm text-surface-600-400">
						The code is maintained open source for transparency. The data is collected with
						<a
							href="https://github.com/appgoblin-dev/adscrawler"
							class="underline decoration-primary-500/60 hover:decoration-primary-500"
						>
							github.com/appgoblin-dev/adscrawler
						</a>
						and the website code can be found at
						<a
							href="https://github.com/appgoblin-dev/appgoblin"
							class="underline decoration-primary-500/60 hover:decoration-primary-500"
						>
							github.com/appgoblin-dev/appgoblin
						</a>
						.
					</p>
				</div>
			</div>
		</div>
	</div>
</div>
