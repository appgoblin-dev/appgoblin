<script>
	import { enhance } from '$app/forms';
	let titlePadding = 'p-2 md:p-4';
	let contentPadding = 'p-2 md:p-4';
	let cardPadding = 'p-2 md:p-4';
	let pricingText = 'mt-2 text-sm opacity-80';

	let loading = false;
</script>

<svelte:head>
	<title>Pricing - AppGoblin</title>
</svelte:head>

<div class="p-2 px-2 md:px-16 lg:px-32 grid grid-cols-1 gap-4 md:gap-8">
	<h1 class="text-3xl font-bold text-primary-900-100">Pricing</h1>

	<div class="card preset-filled-surface-100-900 {cardPadding}">
		<h2 class="h2 {titlePadding}">Paid Datasets</h2>
		<div class={contentPadding}>
			<p>Some datasets for B2B companies and are offered as paid features.</p>

			<br />

			<div class="space-y-6 grid grid-cols-1 md:grid-cols-4 gap-4">
				<div class="card preset-filled-surface-50-950 p-4">
					<h4 class="h4 font-semibold text-primary-900-100">ASO & Marketing Tools</h4>
					<p class={pricingText}>Free</p>
					<p class="my-2 font-bold">
						Use Cases: ASO, SDK analysis, tracker analysis, app trends, app competitor analysis.
					</p>
					<ul class="list-disc list-inside space-y-2">
						<li class="list-disc">
							Free access to AppGoblin's web tools for app marketing and app competitor analysis.
						</li>
					</ul>
				</div>
				<div class="card preset-filled-surface-50-950 p-4">
					<h4 class="h4 font-semibold text-primary-900-100">B2B Competitor SDK Client List</h4>
					<p class={pricingText}>$300 per company list</p>
					<p class="my-2 font-bold">
						Use Cases: B2B Competitor analysis. Sales prospecting. Market research.
					</p>
					<ul class="list-disc list-inside space-y-2">
						<li class="list-disc">See exactly which apps are using a company or SDK.</li>
						<li>Publisher Name and Domain</li>
						<li class="list-disc">Includes app installs</li>
						<li class="list-disc">Other AppGoblin stats available on request.</li>
					</ul>
					<a
						class="btn preset-outlined-tertiary-500 p-2 md:p-4 mt-4"
						href="mailto:contact@appgoblin.info?subject=Competitor%20SDK%20Client%20List"
					>
						<p class="text-center text-sm md:text-base">Get Client List</p>
					</a>
				</div>
				<div class="card preset-filled-surface-50-950 p-4 space-y-2">
					<h4 class="h4 font-semibold text-primary-900-100">Full App-Ads.txt Datasets</h4>
					<p class={pricingText}>$300/month</p>
					<p class="my-2 font-bold">
						Use Cases: Programmatic fraud detection. Ad network analysis. DSP bid enrichment.
					</p>
					<ul class="list-disc list-inside space-y-2">
						<li class="list-disc">Reports updated daily</li>
						<li class="list-disc">Data available as large compressed TSV (~60GB uncompressed)</li>
						<li class="list-disc">Individual ad networks.</li>
						<li class="list-disc">Small customizations available.</li>
					</ul>
					<form
						method="POST"
						action="?/subscribe"
						use:enhance={() => {
							loading = true;

							return async ({ result }) => {
								console.log('Form result:', result);

								if (result.type === 'redirect') {
									console.log('Redirecting to:', result.location);
									window.location.href = result.location;
									return; // Don't set loading = false, we're leaving the page
								}

								if (result.type === 'failure') {
									console.error('Form failed:', result.data);
								}

								loading = false;
							};
						}}
					>
						<button
							type="submit"
							disabled={loading}
							class="btn preset-filled-primary-500 w-full mt-4"
						>
							{loading ? 'Redirecting to checkout...' : 'Subscribe Now'}
						</button>
					</form>
				</div>

				<div class="card preset-filled-surface-50-950 p-4">
					<h4 class="h4 font-semibold text-primary-900-100">Custom Reports, API Integrations</h4>
					<p class={pricingText}>Contact for quote</p>
					<p>
						Need something specific? Custom reports, API integrations, or deeper analytics can be
						arranged. Please reach out with your requirements for a quote.
					</p>
					<a
						class="btn preset-outlined-tertiary-500 p-2 md:p-4 mt-4"
						href="mailto:contact@appgoblin.info?subject=Custom%20Reports%20and%20API%20Integrations"
					>
						<p class="text-center text-sm md:text-base">Contact for Quote</p>
					</a>
				</div>
			</div>
		</div>
	</div>
</div>
