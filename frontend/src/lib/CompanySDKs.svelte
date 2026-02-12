<script lang="ts">
	import type { CompanySDKsDict } from '../types';
	import WhiteCard from './WhiteCard.svelte';

	interface Props {
		mySdks: CompanySDKsDict;
	}

	let { mySdks }: Props = $props();

	const uniquePaths = $derived([
		...new Set(
			Object.values(mySdks.companies || {})
				.flatMap((c) => c.sdks || [])
				.flatMap((c) => c.package_patterns || [])
				.filter((path) => path != null)
		)
	]);

	function truncateList(list: string[], maxItems = 3) {
		return list.slice(0, maxItems);
	}
</script>

<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 p-2 md:p-4">
	{#each Object.entries(mySdks.companies) as [companyName, sdks]}
		{#each Object.entries(sdks) as [sdkName, patterns]}
			<div class="col-span-1">
				<WhiteCard>
					{#snippet title()}
						<span class="text-sm font-semibold">{companyName} - {sdkName}</span>
					{/snippet}
					<div class="p-4 text-xs">
						<h4 class="font-medium text-primary-900-100 uppercase tracking-wider mb-1">
							Package Patterns
						</h4>
						<ul class="list-disc list-inside space-y-0.5">
							{#if patterns && patterns.package_patterns.length > 0}
								{#each truncateList(patterns.package_patterns) as pattern}
									<li class=""><a href={`/sdks/${pattern}`} rel="nofollow">{pattern}</a></li>
								{/each}
							{:else}
								<li class="">No package patterns found</li>
							{/if}
						</ul>
					</div>
				</WhiteCard>
			</div>
		{/each}
	{/each}

	<!-- Separate card for unique paths -->
	{#if uniquePaths.length > 0}
		<WhiteCard>
			{#snippet title()}
				<h3 class="text-sm font-semibold text-primary-900-100">Unique Path Patterns</h3>
			{/snippet}
			<div class="p-4 text-xs">
				<ul class="list-disc list-inside space-y-0.5">
					{#each truncateList(uniquePaths) as path}
						<li class="">{path}</li>
					{/each}
				</ul>
			</div>
		</WhiteCard>
	{/if}
</div>
