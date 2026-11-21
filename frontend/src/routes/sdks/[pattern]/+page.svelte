<script lang="ts">
	import { page } from '$app/state';
	import { enhance } from '$app/forms';
	import Crown from '@lucide/svelte/icons/crown';
	import Mail from '@lucide/svelte/icons/mail';
	import Loader2 from '@lucide/svelte/icons/loader-2';
	import SDKOverviewTable from '#lib/SDKOverviewTable.svelte';
	import SDKPatternCompany from '#lib/SDKPatternCompany.svelte';
	import RequestMappingButton from '#lib/RequestMappingButton.svelte';
	import { resolve } from '$app/paths';
	import WhiteCard from '#lib/WhiteCard.svelte';
	import ApiDataNote from '#lib/ApiDataNote.svelte';

	let { data, form } = $props();
	const pattern = $derived(page.params.pattern ?? '');
	const countFormatter = new Intl.NumberFormat('en-US');
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

	<section class="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 px-2 md:px-4">
		<div>
			<p class="text-xs font-medium uppercase tracking-wider text-surface-600-400">
				Exact SDK string match
			</p>
			<p class="text-lg font-semibold">
				{#if data.isSignedIn}
					{#await data.matchedApps}
						Checking app count...
					{:then myMatchedApps}
						<code>{pattern}</code> was found in {countFormatter.format(myMatchedApps.total_count)}
						{myMatchedApps.total_count === 1 ? 'app' : 'apps'}.
					{/await}
				{:else}
					{#await data.matchedCount}
						Checking app count...
					{:then myMatchedCount}
						<code>{pattern}</code> was found in {countFormatter.format(myMatchedCount.total_count)}
						{myMatchedCount.total_count === 1 ? 'app' : 'apps'}.
					{/await}
				{/if}
			</p>
			<p class="text-sm text-surface-600-400">
				Counts apps where this exact SDK string appears in a manifest, Info.plist, directory, or
				file.
			</p>
		</div>

		{#await data.matchedCompanies}
			loading
		{:then myMatchedCompanies}
			{#if myMatchedCompanies.companies.length > 0}
				<SDKPatternCompany matches={myMatchedCompanies.companies} {pattern} />
			{:else}
				<div class="p-2 md:p-4 space-y-3 text-sm md:text-base">
					<p>
						No companies matched this string. If you know how to map it, please
						<a href={resolve('/contact')} class="underline hover:text-primary-600-400">contact us</a
						>.
					</p>
					<RequestMappingButton
						mapType="app_sdk"
						valueToBeMapped={pattern}
						label="Request SDK mapping"
					/>
				</div>
			{/if}
		{/await}
	</section>

	<section class="px-2 md:px-4">
		<WhiteCard>
			{#snippet title()}B2B SDK Intelligence{/snippet}
			<div class="p-4 space-y-3">
				{#if !data.hasB2BSdkAccess}
					<div class="p-3 bg-warning-50-950/20 rounded-lg border border-warning-800-200">
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
						{isExporting ? 'Queueing CSV Email...' : 'Generate & Email Prefix-Match Report'}
					</button>
				</form>
				<p class="text-sm text-surface-600-400">
					This report includes SDK values that start with <code>{pattern}*</code>.
				</p>
				{#if exportMessage}<p class="text-success-900-100 text-sm">{exportMessage}</p>{/if}
				{#if exportError}<p class="text-error-900-100 text-sm">{exportError}</p>{/if}
			</div>
		</WhiteCard>
	</section>

	{#if data.isSignedIn}
		{#await data.matchedApps}
			loading
		{:then myMatchedApps}
			{#if myMatchedApps}
				<section class="px-2 md:px-4">
					<WhiteCard>
						{#snippet title()}
							Matched Apps <span class="text-sm font-normal text-surface-600-400"
								>({countFormatter.format(myMatchedApps.total_count)})</span
							>
						{/snippet}
						<p class="px-2 md:px-4 pt-2 text-sm text-surface-600-400">
							{#if data.hasB2BSdkAccess}
								Showing {countFormatter.format(myMatchedApps.apps.length)} matching records (up to 100
								in the table).
							{:else}
								B2B full access preview. Signed-in users see the top 3 matching records.
							{/if}
							The total is based on the last statistics refresh. The full report exports all current matching
							records; an app may appear more than once.
						</p>
						{#if myMatchedApps.apps.length > 0}
							<SDKOverviewTable
								entries_table={myMatchedApps.apps}
								previewMode={!data.hasB2BSdkAccess}
								showMatchPath
							/>
						{:else}
							<p class="p-4 text-sm md:text-base">No matching apps found.</p>
						{/if}
					</WhiteCard>
				</section>
			{/if}
		{/await}
	{:else}
		<section class="px-2 md:px-4">
			<WhiteCard>
				{#snippet title()}
					Matched Apps
					<span class="text-sm font-normal text-surface-600-400">
						{#await data.matchedCount}
							(count loading)
						{:then myMatchedCount}
							({countFormatter.format(myMatchedCount.total_count)})
						{/await}
					</span>
				{/snippet}
				<p class="p-4 text-sm">
					<a
						class="underline"
						href={`/auth/login?redirectTo=${encodeURIComponent(page.url.pathname)}`}>Sign in</a
					>
					to view the matching apps preview.
				</p>
			</WhiteCard>
		</section>
	{/if}
</div>
<ApiDataNote endpoint={'/api/v1/apps/{store_id}/sdks'} />
