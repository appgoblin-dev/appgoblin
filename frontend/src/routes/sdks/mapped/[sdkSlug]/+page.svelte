<script lang="ts">
	import { enhance } from '$app/forms';
	import { page } from '$app/state';
	import Crown from '@lucide/svelte/icons/crown';
	import Mail from '@lucide/svelte/icons/mail';
	import Loader2 from '@lucide/svelte/icons/loader-2';
	import SDKOverviewTable from '#lib/SDKOverviewTable.svelte';
	import CompanyButton from '#lib/CompanyButton.svelte';
	import { formatNumber } from '#lib/utils/formatNumber.js';
	import WhiteCard from '#lib/WhiteCard.svelte';
	import ApiDataNote from '#lib/ApiDataNote.svelte';

	type MappedSdkCompany = {
		company_domain?: string | null;
		company_name?: string | null;
		company_logo_url?: string | null;
	};

	let { data, form } = $props();
	const companies = $derived.by(() => {
		const source: MappedSdkCompany[] = data.companies?.length
			? data.companies
			: data.owner?.company_domain
				? [data.owner]
				: [];
		const seen = new Set();
		return source.filter((company) => {
			const key = company.company_domain ?? company.company_name;
			if (seen.has(key)) return false;
			seen.add(key);
			return true;
		});
	});
	const maxPackageAppCount = $derived.by(() => {
		const packagePatterns: { app_count: number | null }[] = data.patterns.package_patterns;
		return packagePatterns.reduce(
			(maximum, pattern) =>
				pattern.app_count === null
					? maximum
					: Math.max(maximum ?? pattern.app_count, pattern.app_count),
			null as number | null
		);
	});
	let isExporting = $state(false);
	let exportMessage = $derived(typeof form?.exportMessage === 'string' ? form.exportMessage : '');
	let exportError = $derived(typeof form?.error === 'string' ? form.error : '');
</script>

<svelte:head><meta name="robots" content="noindex, nofollow" /></svelte:head>

<div class="p-2 md:p-4 space-y-4 md:space-y-6">
	<header class="px-2 md:px-4 space-y-2">
		<nav aria-label="SDK hierarchy" class="text-sm text-surface-600-400">
			Companies <span aria-hidden="true">/</span> SDK <span aria-hidden="true">/</span> SDK Parts
		</nav>
		<h1 class="text-3xl md:text-4xl font-bold break-all">{data.sdk_name}</h1>
	</header>

	<section class="grid grid-cols-1 md:grid-cols-2 gap-4 px-2 md:px-4">
		<WhiteCard>
			{#snippet title()}Companies{/snippet}
			<div class="p-4 space-y-3 text-sm">
				<p>
					This SDK is mapped from package, path, mediation, and adapter patterns found in mobile
					apps.
					{#if maxPackageAppCount !== null}
						Its most-matched package pattern appears in {formatNumber(maxPackageAppCount)}
						{maxPackageAppCount === 1 ? 'app' : 'apps'}.
					{/if}
				</p>
				{#if companies.length > 0}
					<div class="flex flex-wrap gap-2">
						{#each companies as company (company.company_domain ?? company.company_name)}
							{#if company.company_domain}
								<CompanyButton
									companyName={company.company_name ?? undefined}
									companyDomain={company.company_domain}
									companyLogoUrl={company.company_logo_url ?? undefined}
									size="md"
								/>
							{:else}
								<p>{company.company_name}</p>
							{/if}
						{/each}
					</div>
				{:else}
					<p class="text-surface-600-400">No company is currently mapped to this SDK.</p>
				{/if}
			</div>
		</WhiteCard>

		<WhiteCard>
			{#snippet title()}SDK Parts{/snippet}
			<div class="p-4 text-xs space-y-3">
				{#each [['Package patterns', data.patterns.package_patterns], ['Path patterns', data.patterns.paths], ['Mediation patterns', data.patterns.mediation_patterns], ['Adapter patterns', data.patterns.adapter_patterns ?? []]] as [title, patterns]}
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
				<div class="space-y-2">
					<p class="text-xs font-medium uppercase tracking-wider text-surface-600-400">
						Generate &amp; Email Full Report
					</p>
					<div class="flex flex-wrap gap-2">
						{#each [{ latestOnly: false, label: 'All Apps including Historical Versions', report: 'sdk-mapped-all-versions' }, { latestOnly: true, label: 'All Apps by Latest Version', report: 'sdk-mapped-latest-versions' }] as report}
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
								<input type="hidden" name="latest_only" value={String(report.latestOnly)} />
								<button
									type="submit"
									disabled={!data.hasB2BSdkAccess || isExporting}
									class="btn preset-tonal-primary flex items-center gap-2 text-sm"
									data-umami-event="paid-report-generate"
									data-umami-event-source="sdk-mapped"
									data-umami-event-report={report.report}
									data-umami-event-sdk={data.sdk_slug ?? ''}
									data-umami-event-userid={page.data.user?.id}
								>
									{#if isExporting}<Loader2 size={16} class="animate-spin" />{:else}<Mail
											size={16}
										/>{/if}
									{isExporting ? 'Queueing CSV Email...' : report.label}
								</button>
							</form>
						{/each}
					</div>
				</div>
				{#if exportMessage}
					<p class="text-success-900-100 text-sm">
						{exportMessage}
						<a href="/account/reports" class="underline hover:text-primary-600-400">
							View Generated Reports
						</a>
					</p>
				{/if}
				{#if exportError}<p class="text-error-900-100 text-sm">{exportError}</p>{/if}
			</div>
		</WhiteCard>
	</section>

	{#if data.isSignedIn}
		<section class="px-2 md:px-4">
			<WhiteCard>
				{#snippet title()}Matched Apps{/snippet}
				<p class="px-4 pt-3 text-sm text-surface-600-400">
					{#if data.hasB2BSdkAccess}
						Showing the top {formatNumber(data.apps.length)} matching apps.
					{:else}
						B2B full access preview. Signed-in users see the top 3 apps.
					{/if}
					The full report exports all matching app records.
				</p>
				{#if data.apps.length > 0}
					<SDKOverviewTable entries_table={data.apps} previewMode={!data.hasB2BSdkAccess} />
				{:else}
					<p class="p-4 text-sm md:text-base">No matching apps found.</p>
				{/if}
			</WhiteCard>
		</section>
	{:else}
		<section class="px-2 md:px-4">
			<WhiteCard>
				{#snippet title()}Matched Apps{/snippet}
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
	<ApiDataNote endpoint={'/api/v1/sdks/{sdk_slug}'} />
</div>
