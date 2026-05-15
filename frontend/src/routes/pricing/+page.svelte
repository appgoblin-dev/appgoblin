<script lang="ts">
	import { enhance } from '$app/forms';
	import { Check, X } from 'lucide-svelte';

	/** @type {import('./$types').PageData} */
	export let data;

	let titlePadding = 'p-2 md:p-4';
	let contentPadding = 'p-2 md:p-4';

	let loading = false;
	let activePriceKey: string | null = null;

	const plans = [
		{
			key: 'free',
			name: 'Deeper App Insights',
			price: '$0',
			description: 'Indie devs, researchers, casual users',
			included: true
		},
		{
			key: 'b2b_sdk',
			name: 'B2B SDK Intelligence',
			price: '$299',
			period: '/mo',
			description: 'Sales teams, ad networks, agencies'
		},
		{
			key: 'b2b_appads',
			name: 'App-Ads.txt',
			price: '$299',
			period: '/mo',
			description: 'Ad networks, DSPs, SSPs'
		},
		{
			key: 'b2b_premium',
			name: 'Premium B2B',
			price: '$499',
			period: '/mo',
			description: 'Larger companies, security teams, ad networks, hedge funds',
			featured: true
		}
	];

	const features = [
		{
			category: 'Core Features',
			name: 'Advanced SDK app data',
			free: true,
			sdk: true,
			appads: true,
			b2b: true
		},
		{
			category: 'Core Features',
			name: 'Request free SDK/API scans',
			free: true,
			sdk: true,
			appads: true,
			b2b: true
		},
		{
			category: 'Core Features',
			name: 'App Comparisons',
			free: true,
			sdk: true,
			appads: true,
			b2b: true
		},
		{
			category: 'Core Features',
			name: 'ASO keyword dash',
			free: true,
			sdk: true,
			appads: true,
			b2b: true
		},
		{
			category: 'Core Features',
			name: 'Ad intelligence',
			free: true,
			sdk: true,
			appads: true,
			b2b: true
		},
		{
			category: 'Premium Tools',
			name: 'App Explorer dash + SDK filters',
			free: false,
			sdk: true,
			appads: true,
			b2b: true
		},
		{
			category: 'Data Export',
			name: 'Export Company / SDK apps',
			free: false,
			premium: false,
			sdk: true,
			appads: false,
			b2b: true
		},
		{
			category: 'Data Export',
			name: 'Bulk app-ads.txt datasets',
			free: false,
			premium: false,
			sdk: false,
			appads: true,
			b2b: true
		},
		{
			category: 'Enterprise',
			name: 'Compliance & security requests',
			free: false,
			premium: false,
			sdk: false,
			appads: false,
			b2b: true
		},
		{
			category: 'Enterprise',
			name: 'Custom reports & integration',
			free: false,
			premium: false,
			sdk: false,
			appads: false,
			b2b: true
		}
	];

	/** @param {{ result: import('@sveltejs/kit').ActionResult }} param0 */
	const handleSubscribeResult = async ({
		result
	}: {
		result: import('@sveltejs/kit').ActionResult;
	}) => {
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
	const subscribeEnhance = ({ formElement }: { formElement: HTMLFormElement }) => {
		activePriceKey = formElement.dataset.priceKey ?? null;
		loading = true;

		return handleSubscribeResult;
	};

	const getFeatureValue = (feature: (typeof features)[0], planKey: string): boolean => {
		if (planKey === 'free') return feature.free;
		if (planKey === 'b2b_sdk') return feature.sdk;
		if (planKey === 'b2b_appads') return feature.appads;
		if (planKey === 'b2b_premium') return feature.b2b;
		return false;
	};
</script>

<svelte:head>
	<title>Pricing - AppGoblin</title>
</svelte:head>

<div class="px-2 lg:px-4 xl:px-16 grid grid-cols-1 gap-4 md:gap-4 lg:gap-8">
	<h1 class="h1 {titlePadding}">Plans & Pricing</h1>
	<div class={contentPadding}>
		<p>
			For alternative payment options (Invoice, PayPal, etc.), please reach out to us at <a
				href="mailto:contact@appgoblin.info">contact@appgoblin.info</a
			>.
		</p>

		<p class="text-sm opacity-80 mt-3 max-w-3xl">
			Paid plans are billed monthly. You can cancel anytime, and your access will remain active
			through the end of your current billing period. Payments already made are non-refundable.
		</p>

		<br />

		<!-- Features Table -->
		<div class="overflow-x-auto">
			<div
				class="grid gap-px border border-surface-500/20"
				style={`grid-template-columns: 300px repeat(${plans.length}, 1fr); min-width: 780px;`}
			>
				<!-- Plan header row -->
				<div class="p-2 bg-surface-50-950 font-semibold text-xs">Feature</div>
				{#each plans as plan (plan.key)}
					<div
						class="p-2 border-l border-surface-500/20 bg-surface-50-950 text-center {plan.featured
							? 'bg-primary-500/5'
							: ''}"
					>
						<p class="text-xs uppercase tracking-wide opacity-60">{plan.name}</p>
						<p class="text-base font-semibold leading-tight mt-1">
							{plan.price}<span class="text-xs opacity-60 ml-1">{plan.period || ''}</span>
						</p>
						<p class="text-xs opacity-70 mt-1 leading-snug">{plan.description}</p>
					</div>
				{/each}

				<!-- Feature rows -->
				{#each features as feature}
					<!-- Feature name cell -->
					<div class="p-2 bg-surface-50-950 text-xs md:text-sm">{feature.name}</div>

					<!-- Feature checkmark cells -->
					{#each plans as plan (plan.key)}
						{@const hasFeature = getFeatureValue(feature, plan.key)}
						<div
							class="p-2 border-l border-surface-500/20 bg-surface-50-950 text-center {plan.featured
								? 'bg-primary-500/5'
								: ''}"
						>
							{#if hasFeature}
								<Check
									class="w-4 h-4 md:w-6 md:h-6 mx-auto text-success-700-300 "
									aria-hidden="true"
								/>
								<span class="sr-only">Included</span>
							{:else}
								<X class="w-3 h-3 md:w-4 md:h-4 mx-auto opacity-20" aria-hidden="true" />
								<span class="sr-only">Not included</span>
							{/if}
						</div>
					{/each}
				{/each}

				<!-- CTA row -->
				<div class="p-2 bg-surface-50-950 font-semibold text-xs">Choose Plan</div>
				{#each plans as plan (plan.key)}
					<div
						class="p-2 border-l border-surface-500/20 bg-surface-50-950 {plan.featured
							? 'bg-primary-500/5'
							: ''}"
					>
						{#if plan.included}
							{#if !data?.user}
								<a href="/auth/signup" class="btn preset-tonal-primary w-full">Create Account</a>
							{:else}
								<p class="text-center text-xs opacity-60">Included with your account</p>
							{/if}
						{:else}
							<form
								method="POST"
								action="?/subscribe"
								use:enhance={subscribeEnhance}
								data-price-key={plan.key}
							>
								<input type="hidden" name="priceKey" value={plan.key} />
								<button type="submit" disabled={loading} class="btn preset-tonal-primary w-full">
									{loading && activePriceKey === plan.key ? 'Redirecting...' : 'Get ' + plan.name}
								</button>
							</form>
						{/if}
					</div>
				{/each}
			</div>
		</div>

		<div class="mt-8 grid grid-cols-1 gap-4 lg:grid-cols-2">
			<div class="card preset-outlined-surface-100-900 p-5 space-y-3">
				<h3 class="text-lg font-semibold">For Researchers, Journalists, and Academics</h3>
				<p class="text-sm">
					AppGoblin supports independent research and journalism. If you're a student, academic
					researcher, or investigative journalist working on mobile advertising, privacy, or app
					ecosystems, you're welcome to reach out for collaboration.
				</p>
			</div>

			<div class="card preset-outlined-surface-100-900 p-5 space-y-3">
				<h3 class="text-lg font-semibold">Free Resources</h3>
				<p class="text-sm">
					Many of AppGoblin's marketing data and ASO features are free to browse. You can also use
					the
					<a
						href="/free-app-datasets"
						class="underline decoration-primary-500/60 hover:decoration-primary-500"
					>
						free app datasets page
					</a>
					for free app metrics and app description exports with a free account. Additional open source
					data sets are available for free download at
					<a
						href="https://github.com/appgoblin-dev/appgoblin-data"
						class="underline decoration-primary-500/60 hover:decoration-primary-500"
					>
						github.com/appgoblin-dev/appgoblin-data
					</a>
					. Feel free to reach out if there are other parts of data you'd like to see exported.
				</p>
				<p class="text-sm">
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
