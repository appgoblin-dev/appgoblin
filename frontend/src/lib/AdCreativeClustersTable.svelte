<script lang="ts">
	interface CreativeCluster {
		vhash: string;
		file_extension: string;
		representative_md5: string;
		unique_publisher_apps: number;
		unique_advertisers: number;
		unique_adv_names: number;
		unique_pub_names: number;
		unique_ad_networks: number;
		unique_ad_domains: number;
		unique_mmp_names: number;
		unique_mmp_domains: number;

		top_adv_name: string | null;
		top_advertiser_store_id: string | null;
		top_pub_name: string | null;
		top_host_domain: string | null;
		top_host_domain_company: string | null;
		top_ad_domain: string | null;
		top_ad_domain_company: string | null;
		top_mmp_name: string | null;
		top_mmp_domain: string | null;

		adv_icon_url: string | null;
		pub_icon_url: string | null;
		company_logo_url_host: string | null;
		company_logo_url_ad: string | null;

		first_seen_at: string;
		last_seen_at: string;
		creative_thumb_url: string;
	}

	import CompanyButton from '$lib/CompanyButton.svelte';

	let { data }: { data: CreativeCluster[] } = $props();

	const formatNumber = (num: number) => {
		if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
		if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
		return num.toFixed(0);
	};
</script>

<div class="overflow-x-auto">
	<table class="table min-inline-size-full whitespace-nowrap align-middle">
		<thead>
			<tr>
				<th class="px-4 py-3 text-left font-semibold">Creative</th>
				<th class="px-4 py-3 text-left font-semibold">Format</th>
				<th class="px-4 py-3 text-left font-semibold">Top Advertiser</th>
				<th class="px-4 py-3 text-left font-semibold">Top Ad Network</th>
				<th class="px-4 py-3 text-right font-semibold">Unique Pubs</th>
				<th class="px-4 py-3 text-right font-semibold">First Seen</th>
				<th class="px-4 py-3 text-right font-semibold">Last Seen</th>
			</tr>
		</thead>
		<tbody>
			{#each data as row}
				<tr class="border-b hover:bg-surface-hover-token">
					<!-- Thumbnail -->
					<td class="px-4 py-3">
						<img
							src={row.creative_thumb_url}
							alt={row.vhash}
							class="h-16 w-16 object-cover rounded shadow-sm border border-surface-200"
							onerror={(e) => ((e.currentTarget as HTMLImageElement).style.display = 'none')}
						/>
					</td>
					<!-- Format -->
					<td class="px-4 py-3">
						<span class="badge variant-filled-primary uppercase text-xs">
							{row.file_extension}
						</span>
					</td>
					<!-- Advertiser -->
					<td class="px-4 py-3 min-w-[200px]">
						<div class="flex items-center gap-3">
							{#if row.adv_icon_url}
								<img src={row.adv_icon_url} class="h-8 w-8 rounded shadow-sm" alt="icon" />
							{:else}
								<div class="h-8 w-8 rounded bg-surface-300-600-token"></div>
							{/if}
							<div class="flex flex-col">
								<a
									href={row.top_advertiser_store_id ? `/apps/${row.top_advertiser_store_id}` : '#'}
									class="font-semibold text-primary-500 hover:underline"
								>
									{row.top_adv_name || row.top_advertiser_store_id || 'Unknown'}
								</a>
							</div>
						</div>
					</td>
					<!-- Network -->
					<td class="px-4 py-3">
						<div class="flex flex-col gap-1 items-start">
							{#if row.top_host_domain}
								<CompanyButton
									companyName={row.top_host_domain_company || 'Network'}
									companyDomain={row.top_host_domain}
									companyLogoUrl={row.company_logo_url_host || ''}
									size="sm"
								/>
							{/if}
							{#if row.top_ad_domain && row.top_ad_domain !== row.top_host_domain}
								<div class="flex items-center gap-1">
									<span class="text-xs opacity-70">via</span>
									<CompanyButton
										companyName={row.top_ad_domain_company || 'Ad'}
										companyDomain={row.top_ad_domain}
										companyLogoUrl={row.company_logo_url_ad || ''}
										size="sm"
									/>
								</div>
							{/if}
							{#if !row.top_host_domain && !row.top_ad_domain}
								<span class="font-medium">-</span>
							{/if}
						</div>
					</td>
					<!-- Stats -->
					<td class="px-4 py-3 text-right font-semibold text-tertiary-600-300-token">
						{formatNumber(row.unique_publisher_apps)}
					</td>
					<!-- Dates -->
					<td class="px-4 py-3 text-right text-sm">
						{row.first_seen_at?.split('T')[0]}
					</td>
					<td class="px-4 py-3 text-right text-sm">
						{row.last_seen_at?.split('T')[0]}
					</td>
				</tr>
			{/each}
			{#if data.length === 0}
				<tr>
					<td colspan="8" class="px-4 py-8 text-center text-sm opacity-70">
						No creatives found.
					</td>
				</tr>
			{/if}
		</tbody>
	</table>
</div>

<style>
	/* Optional specialized styles here */
</style>
