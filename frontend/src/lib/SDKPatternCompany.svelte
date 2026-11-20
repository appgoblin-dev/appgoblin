<script lang="ts">
	import WhiteCard from './WhiteCard.svelte';
	import CompanyButton from './CompanyButton.svelte';
	import { formatNumber } from '#lib/utils/formatNumber.js';
	import { resolve } from '$app/paths';
	import type { SdkPatternCompany } from '../types';

	let { matches }: { matches: SdkPatternCompany[] } = $props();

	const company = $derived(matches[0]);
	const mappedSdks = $derived(
		Array.from(
			new Map(
				matches.filter((match) => match.sdk_slug).map((match) => [match.sdk_slug, match] as const)
			).values()
		)
	);
	const groupedPatterns = $derived(
		matches.reduce<Record<string, SdkPatternCompany[]>>((groups, match) => {
			(groups[match.pattern_type] ??= []).push(match);
			return groups;
		}, {})
	);

	function patternTitle(patternType: string) {
		return patternType
			.replaceAll('_', ' ')
			.replace(/\b\w/g, (character) => character.toUpperCase());
	}
</script>

<WhiteCard>
	{#snippet title()}
		<span class="text-sm font-semibold">Matching Company</span>
	{/snippet}
	<div class="p-4 text-xs">
		<div class="flex flex-wrap items-center gap-2 mb-4">
			<CompanyButton
				companyName={company.company_name}
				companyDomain={company.company_domain}
				companyLogoUrl={company.company_logo_url ?? undefined}
				size="lg"
			/>
		</div>

		{#if mappedSdks.length > 0}
			<div class="mb-3 text-sm">
				<p class="font-medium">Mapped SDKs</p>
				<ul class="space-y-1 mt-1">
					{#each mappedSdks as sdk (sdk.sdk_slug)}
						<li>
							<a
								class="underline"
								href={resolve('/sdks/mapped/[sdkSlug]', { sdkSlug: sdk.sdk_slug! })}
							>
								View {sdk.sdk_name || sdk.sdk_slug}
							</a>
						</li>
					{/each}
				</ul>
			</div>
		{:else if company.sdk_name}
			<p class="mb-3 text-sm text-gray-500">{company.sdk_name}</p>
		{/if}

		{#if company.parent_company_name}
			<p class="mb-3 text-gray-500">
				Parent company: {company.parent_company_name}
				{#if company.parent_company_domain}({company.parent_company_domain}){/if}
			</p>
		{/if}

		{#each Object.entries(groupedPatterns) as [patternType, patterns]}
			<h4 class="font-medium uppercase tracking-wider mb-1 mt-3">{patternTitle(patternType)}</h4>
			<ul class="list-disc list-inside space-y-0.5">
				{#each patterns as pattern}
					<li>
						<a href={`/sdks/${pattern.pattern_value}`} rel="nofollow">{pattern.pattern_value}</a>
						{#if pattern.app_count !== null}
							<span class="text-gray-500">({formatNumber(pattern.app_count)} apps)</span>
						{/if}
					</li>
				{/each}
			</ul>
		{/each}
	</div>
</WhiteCard>
