<script lang="ts">
	import { page } from '$app/state';
	import { enhance } from '$app/forms';
	import Crown from '@lucide/svelte/icons/crown';
	import Mail from '@lucide/svelte/icons/mail';
	import Loader2 from '@lucide/svelte/icons/loader-2';
	let pattern = page.params.pattern;
	import SDKOverviewTable from '#lib/SDKOverviewTable.svelte';
	import SDKPatternCompany from '#lib/SDKPatternCompany.svelte';
	let { data, form } = $props();
	import WhiteCard from '#lib/WhiteCard.svelte';
	let isExporting = $state(false);
	let exportMessage = $derived(typeof form?.exportMessage === 'string' ? form.exportMessage : '');
	let exportError = $derived(typeof form?.error === 'string' ? form.error : '');
</script>

<svelte:head>
	<meta name="robots" content="noindex, nofollow" />
</svelte:head>

<div class="p-2 md:p-4 space-y-4 md:space-y-6">
	<header class="px-2 md:px-4">
		<p class="text-sm uppercase tracking-wider text-surface-600-400">SDK pattern</p>
		<h1 class="text-3xl md:text-4xl font-bold break-all">{pattern}</h1>
	</header>

	<div class="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 px-2 md:px-4">
		<WhiteCard>
			{#snippet title()}
				Info
			{/snippet}
			<p class="p-2 md:p-4 text-sm md:text-base">
				These are apps and companies that had some part of an Android Manifest, Info.plist,
				directories or files that matched this string.
			</p>
		</WhiteCard>

		{#await data.matchedCompanies}
			loading
		{:then myMatchedCompanies}
			{#if myMatchedCompanies.companies.length > 0}
				<SDKPatternCompany matches={myMatchedCompanies.companies} />
			{:else}
				<p class="p-2 md:p-4 text-sm md:text-base">
					No companies matched this string, if you know how to match this string, please contact us
					on Discord.
				</p>
			{/if}
		{/await}
	</div>

	{#await data.matchedApps}
		loading
	{:then myMatchedApps}
		<section class="px-2 md:px-4">
			<WhiteCard>
				{#snippet title()}
					Matching Apps <span class="text-sm font-normal text-surface-600-400"
						>({myMatchedApps.apps.length})</span
					>
				{/snippet}
				{#if !data.hasB2BSdkAccess}
					<div
						class="mx-2 md:mx-4 mt-2 p-3 bg-warning-50-950/20 rounded-lg border border-warning-800-200"
					>
						<p class="text-sm text-warning-950-50 flex items-center gap-2">
							<Crown class="w-4 h-4 text-primary-900-100" aria-hidden="true" />
							B2B SDK Intelligence tier.
							<a href="/pricing" class="underline hover:text-primary-600-400">Upgrade</a> to unlock full
							reports.
						</p>
					</div>
				{/if}
				<form
					method="POST"
					action="?/emailExport"
					use:enhance={() => {
						isExporting = true;
						return async ({ update }) => {
							await update({ reset: false });
							isExporting = false;
						};
					}}
					class="mt-2 px-2 md:px-4"
				>
					<button
						type="submit"
						disabled={!data.hasB2BSdkAccess || isExporting}
						class="btn preset-tonal-primary flex items-center gap-2 text-sm"
						data-umami-event="paid-report-generate"
						data-umami-event-source="sdk-pattern"
						data-umami-event-report="sdk-pattern-full"
						data-umami-event-pattern={pattern}
						data-umami-event-userid={page.data.user?.id}
					>
						{#if isExporting}<Loader2 size={16} class="animate-spin" />{:else}<Mail
								size={16}
							/>{/if}
						{isExporting ? 'Queueing CSV Email...' : 'Generate & Email Full Report'}
					</button>
				</form>
				{#if exportMessage}<p class="px-2 md:px-4 pt-2 text-success-900-100 text-sm">
						{exportMessage}
					</p>{/if}
				{#if exportError}<p class="px-2 md:px-4 pt-2 text-error-900-100 text-sm">
						{exportError}
					</p>{/if}
				{#if myMatchedApps.apps.length > 0}
					<SDKOverviewTable
						entries_table={myMatchedApps.apps}
						previewMode={!data.hasB2BSdkAccess}
					/>
				{:else}
					<p class="p-4 text-sm md:text-base">No matching apps found.</p>
				{/if}
			</WhiteCard>
		</section>
	{/await}
</div>
