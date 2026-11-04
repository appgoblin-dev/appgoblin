<script lang="ts">
	import { enhance } from '$app/forms';
	import { page } from '$app/state';
	import Mail from '@lucide/svelte/icons/mail';
	import Loader2 from '@lucide/svelte/icons/loader-2';
	import SDKOverviewTable from '#lib/SDKOverviewTable.svelte';
	import CompanyButton from '#lib/CompanyButton.svelte';
	import { formatNumber } from '#lib/utils/formatNumber.js';
	import WhiteCard from '#lib/WhiteCard.svelte';

	let { data, form } = $props();
	let isExporting = $state(false);
	let exportMessage = $derived(typeof form?.exportMessage === 'string' ? form.exportMessage : '');
	let exportError = $derived(typeof form?.error === 'string' ? form.error : '');
</script>

<input type="hidden" name="sdk_id" value={data.sdk_id} />

<svelte:head><meta name="robots" content="noindex, nofollow" /></svelte:head>

<div class="p-2 md:p-4 space-y-4 md:space-y-6">
	<header class="px-2 md:px-4">
		<p class="text-sm uppercase tracking-wider text-surface-600-400">SDK</p>
		<h1 class="text-3xl md:text-4xl font-bold break-all">{data.sdk_name}</h1>
	</header>

	<section class="grid grid-cols-1 md:grid-cols-2 gap-4 px-2 md:px-4">
		<WhiteCard>
			{#snippet title()}SDK information{/snippet}
			<div class="p-4 space-y-2 text-sm">
				<p>This SDK is mapped from package, path, and mediation patterns found in mobile apps.</p>
				{#if data.owner?.company_domain}
					<CompanyButton
						companyName={data.owner.company_name}
						companyDomain={data.owner.company_domain}
						companyLogoUrl={data.owner.company_logo_url ?? undefined}
						size="md"
					/>
				{/if}
			</div>
		</WhiteCard>
		<WhiteCard>
			{#snippet title()}SDK patterns{/snippet}
			<div class="p-4 text-xs space-y-3">
				{#each [['Package patterns', data.patterns.package_patterns], ['Path patterns', data.patterns.paths], ['Mediation patterns', data.patterns.mediation_patterns]] as [title, patterns]}
					{#if patterns.length}
						<div>
							<h3 class="font-medium uppercase tracking-wider mb-1">{title}</h3>
							<ul class="list-disc list-inside space-y-0.5">
								{#each patterns as pattern}
									<li>
										<a class="underline" href={`/sdks/${pattern.pattern}`} rel="nofollow"
											>{pattern.pattern}</a
										>{#if pattern.app_count !== null}
											<span class="text-gray-500">({formatNumber(pattern.app_count)} apps)</span
											>{/if}
									</li>
								{/each}
							</ul>
						</div>
					{/if}
				{/each}
			</div>
		</WhiteCard>
	</section>

	<section class="px-2 md:px-4">
		<WhiteCard>
			{#snippet title()}
				<div class="flex items-center justify-between gap-3">
					<span>Top apps</span>
					<div class="flex flex-col items-end gap-1">
						<span class="text-xs font-medium uppercase tracking-wider text-surface-600-400"
							>Generate &amp; Email Report</span
						>
						<div class="flex flex-wrap items-center justify-end gap-2">
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
								<input type="hidden" name="sdk_id" value={data.sdk_id} />
								<input type="hidden" name="sdk_slug" value={data.sdk_slug ?? ''} />
								<input type="hidden" name="latest_only" value="false" />
								<button
									type="submit"
									disabled={!data.hasB2BSdkAccess || isExporting}
									class="btn preset-tonal-primary flex items-center gap-2 text-sm"
									data-umami-event="paid-report-generate"
									data-umami-event-source="sdk-mapped"
									data-umami-event-report="sdk-mapped-all-versions"
									data-umami-event-sdk={data.sdk_slug ?? ''}
									data-umami-event-userid={page.data.user?.id}
								>
									{#if isExporting}<Loader2 size={16} class="animate-spin" />{:else}<Mail
											size={16}
										/>{/if}
									{isExporting ? 'Queueing CSV Email...' : 'All App Versions'}
								</button>
							</form>
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
								<input type="hidden" name="sdk_id" value={data.sdk_id} />
								<input type="hidden" name="sdk_slug" value={data.sdk_slug ?? ''} />
								<input type="hidden" name="latest_only" value="true" />
								<button
									type="submit"
									disabled={!data.hasB2BSdkAccess || isExporting}
									class="btn preset-tonal-primary text-sm"
									data-umami-event="paid-report-generate"
									data-umami-event-source="sdk-mapped"
									data-umami-event-report="sdk-mapped-latest-versions"
									data-umami-event-sdk={data.sdk_slug ?? ''}
									data-umami-event-userid={page.data.user?.id}
								>
									{#if isExporting}<Loader2 size={16} class="animate-spin" />{:else}<Mail
											size={16}
										/>{/if}
									{isExporting ? 'Queueing CSV Email...' : 'Latest App Versions Only'}
								</button>
							</form>
						</div>
					</div>
				</div>
			{/snippet}
			{#if exportMessage}<p class="px-4 text-success-900-100 text-sm">{exportMessage}</p>{/if}
			{#if exportError}<p class="px-4 text-error-900-100 text-sm">{exportError}</p>{/if}
			<SDKOverviewTable entries_table={data.apps} previewMode={!data.hasB2BSdkAccess} />
		</WhiteCard>
	</section>
</div>
