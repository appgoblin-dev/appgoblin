<script lang="ts">
	import type { PageData } from './$types';
	import WhiteCard from '#lib/WhiteCard.svelte';

	let { data }: { data: PageData } = $props();
	let companyName = $derived(
		data.companyTree.is_secondary_domain
			? data.companyTree.queried_domain
			: data.companyTree.company_name ||
					data.companyTree.company_domain ||
					data.companyTree.queried_domain
	);
	let overview = $derived(
		!data.companyTree.is_secondary_domain && data.tabIndicators?.is_parent_domain
			? (data.companyDetails.parent_overview ?? data.companyDetails.domain_overview)
			: data.companyDetails.domain_overview
	);
	let stats = $derived(overview?.categories?.all);
	const numberFormatter = new Intl.NumberFormat('en-US');
	function formatDate(value: string): string {
		const date = new Date(value);
		return Number.isNaN(date.getTime())
			? 'Unknown date'
			: date.toLocaleString('en-US', {
					year: 'numeric',
					month: 'short',
					day: 'numeric',
					hour: '2-digit',
					minute: '2-digit'
				});
	}
</script>

<section class="mb-6 space-y-2">
	<h2 class="text-xl font-semibold">Apps Using {companyName} APIs</h2>
	<p>
		These are outgoing network calls from apps to {companyName}. These are observed connections, not
		necessarily direct integrations, as sometimes one SDK might load resources from other companies.
	</p>
	<p class="text-sm text-surface-500">
		Recent activity is a sample, not a complete list of calls or apps.
	</p>
</section>

{#if stats}
	<section class="mb-6" aria-label="API activity overview">
		<div class="p-4 bg-surface-100-900 rounded-md">
			<p class="text-sm">Apps with API calls</p>
			<p class="text-2xl font-bold">{numberFormatter.format(stats.api_android_total_apps ?? 0)}</p>
		</div>
	</section>
{/if}

<div class="mb-6">
	<WhiteCard>
		{#snippet title()}
			API response types
		{/snippet}
		<p class="px-3 pt-2 text-sm text-surface-500">
			A selection of response types by observed domain. App counts are distinct within each row; an
			app can appear in multiple rows. The last 30 days are based on when calls were recorded.
		</p>
		{#if data.apiApps.response_types.length > 0}
			<div class="overflow-x-auto p-2">
				<table class="table w-full text-sm">
					<thead>
						<tr
							><th>Company domain</th><th>Observed domain</th><th>Response type</th><th
								>Apps (30 days)</th
							><th>Calls (30 days)</th><th>Apps (all time)</th><th>Calls (all time)</th></tr
						>
					</thead>
					<tbody>
						{#each data.apiApps.response_types as response}
							<tr>
								<td class="break-all">{response.company_domain}</td>
								<td class="break-all">{response.tld_url || '(unknown)'}</td>
								<td class="break-all">{response.response_type}</td>
								<td>{numberFormatter.format(response.app_count_30d)}</td>
								<td>{numberFormatter.format(response.observed_call_count_30d)}</td>
								<td>{numberFormatter.format(response.app_count_alltime)}</td>
								<td>{numberFormatter.format(response.observed_call_count_alltime)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{:else}
			<p class="p-3 text-sm">No response type data available.</p>
		{/if}
	</WhiteCard>
</div>

<div class="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
	<WhiteCard>
		{#snippet title()}
			Recent API endpoints
		{/snippet}
		<p class="px-3 pt-2 text-sm text-surface-500">
			A recent sample of observed endpoints. Paths are shortened after the third slash and each
			endpoint is limited to 120 characters; query strings and credentials are omitted.
		</p>
		{#if data.apiApps.recent_endpoints.length > 0}
			<div class="overflow-x-auto p-2">
				<table class="table w-full text-sm">
					<thead><tr><th>Endpoint</th><th>Last observed</th></tr></thead>
					<tbody>
						{#each data.apiApps.recent_endpoints as endpoint (`${endpoint.host}${endpoint.path}`)}
							<tr>
								<td class="break-all">{endpoint.host}{endpoint.path}</td>
								<td>{formatDate(endpoint.last_seen)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{:else}
			<p class="p-3 text-sm">No recent endpoints available.</p>
		{/if}
	</WhiteCard>
	<WhiteCard>
		{#snippet title()}
			Recent requests
		{/snippet}
		<p class="px-3 pt-2 text-sm text-surface-500">
			Recent calls observed from apps during scans. Endpoints are shortened as described above.
		</p>
		{#if data.apiApps.recent_requests.length > 0}
			<div class="overflow-x-auto p-2">
				<table class="table w-full text-sm">
					<thead
						><tr><th>App</th><th>Endpoint</th><th>Response type</th><th>Observed</th></tr></thead
					>
					<tbody>
						{#each data.apiApps.recent_requests as request}
							<tr>
								<td>
									<a
										href={`/apps/${encodeURIComponent(request.store_id)}/data-flows`}
										class="flex items-center gap-2 hover:underline"
									>
										{#if request.icon_64}
											<img
												src={`https://media.appgoblin.info/app-icons/${encodeURIComponent(request.store_id)}/${encodeURIComponent(request.icon_64)}`}
												alt=""
												class="w-8 h-8 rounded shrink-0"
												loading="lazy"
											/>
										{/if}
										<span>{request.name || request.store_id}</span>
									</a>
								</td>
								<td class="break-all">{request.host}{request.path}</td>
								<td>{request.response_mime_type || '—'}</td>
								<td>{formatDate(request.called_at)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{:else}
			<p class="p-3 text-sm">No recent requests available.</p>
		{/if}
	</WhiteCard>
</div>
