<script lang="ts">
	import WhiteCard from './WhiteCard.svelte';
	import CompanyButton from './CompanyButton.svelte';
	import { formatNumber } from '#lib/utils/formatNumber.js';
	import { resolve } from '$app/paths';
	import type { SdkPatternCompany } from '../types';

	let { matches }: { matches: SdkPatternCompany[] } = $props();

	const maxAppCount = $derived(
		matches.reduce<number | null>(
			(maximum, match) =>
				match.app_count === null ? maximum : Math.max(maximum ?? match.app_count, match.app_count),
			null
		)
	);
	const companyGroups = $derived(
		Array.from(
			matches
				.reduce((groups, match) => {
					const key = match.company_domain || match.company_name;
					const group = groups.get(key) ?? { company: match, matches: [] };
					group.matches.push(match);
					groups.set(key, group);
					return groups;
				}, new Map<string, { company: SdkPatternCompany; matches: SdkPatternCompany[] }>())
				.values()
		)
	);

	function patternTitle(patternType: string) {
		return patternType
			.replaceAll('_', ' ')
			.replace(/\b\w/g, (character) => character.toUpperCase());
	}
</script>

<WhiteCard>
	{#snippet title()}
		<span class="text-sm font-semibold">Matching Companies ({companyGroups.length})</span>
	{/snippet}
	<div class="p-4 space-y-4">
		{#if maxAppCount !== null}
			<div class="rounded-lg bg-surface-100-900/20 p-3">
				<p class="text-xs font-medium uppercase tracking-wider text-surface-600-400">
					Most-matched SDK part
				</p>
				<p class="flex items-baseline gap-2">
					<span class="text-3xl font-bold">{formatNumber(maxAppCount)}</span>
					<span class="text-lg">apps</span>
				</p>
			</div>
		{/if}
		{#each companyGroups as group (group.company.company_domain || group.company.company_name)}
			{@const mappedSdks = Array.from(
				new Map(
					group.matches
						.filter((match) => match.sdk_slug)
						.map((match) => [match.sdk_slug, match] as const)
				).values()
			)}
			{@const groupedPatterns = group.matches.reduce<Record<string, SdkPatternCompany[]>>(
				(groups, match) => {
					(groups[match.pattern_type] ??= []).push(match);
					return groups;
				},
				{}
			)}
			<div class="text-xs">
				<div class="flex flex-wrap items-center gap-2 mb-3">
					{#if group.company.company_domain}
						<CompanyButton
							companyName={group.company.company_name}
							companyDomain={group.company.company_domain}
							companyLogoUrl={group.company.company_logo_url ?? undefined}
							size="lg"
						/>
					{:else}
						<p class="text-sm font-semibold">{group.company.company_name}</p>
					{/if}
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
				{:else if group.company.sdk_name}
					<p class="mb-3 text-sm text-gray-500">{group.company.sdk_name}</p>
				{/if}

				{#if group.company.parent_company_name}
					<p class="mb-3 text-gray-500">
						Parent company: {group.company.parent_company_name}
						{#if group.company.parent_company_domain}({group.company.parent_company_domain}){/if}
					</p>
				{/if}

				{#each Object.entries(groupedPatterns) as [patternType, patterns]}
					<h4 class="font-medium uppercase tracking-wider mb-1 mt-3">
						{patternTitle(patternType)}
					</h4>
					<ul class="list-disc list-inside space-y-0.5">
						{#each patterns as pattern}
							<li>
								{#if pattern.app_count !== null}
									<span class="mr-2 text-sm font-semibold"
										>{formatNumber(pattern.app_count)} apps</span
									>
								{/if}
								<a href={`/sdks/${pattern.pattern_value}`} rel="nofollow">{pattern.pattern_value}</a
								>
							</li>
						{/each}
					</ul>
				{/each}
			</div>
		{/each}
	</div>
</WhiteCard>
