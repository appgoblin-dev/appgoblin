<script lang="ts">
	import { resolve } from '$app/paths';

	import WhiteCard from '#lib/WhiteCard.svelte';
	import AppDataFlowsNav from '#lib/AppDataFlowsNav.svelte';
	import CompanyButton from '#lib/CompanyButton.svelte';
	import RequestMappingButton from '#lib/RequestMappingButton.svelte';

	import type {
		AppAPIsOverview,
		AppAPIScanDiffRow,
		AppAPIScanDiffStatus
	} from '../../../../../../types';

	type Props = {
		data: {
			apis: AppAPIsOverview;
			myapp: { name: string; store_id: string };
		};
	};

	let { data }: Props = $props();

	const scanDiff = $derived(data.apis?.scan_diff ?? null);
	const apis = $derived(data.apis?.apis ?? []);

	type StatusFilter = 'all' | AppAPIScanDiffStatus;
	let statusFilter = $state<StatusFilter>('all');

	const rows = $derived<AppAPIScanDiffRow[]>(scanDiff?.rows ?? []);
	const visibleRows = $derived(
		statusFilter === 'all' ? rows : rows.filter((row) => row.status === statusFilter)
	);

	const counts = $derived({
		all: rows.length,
		new: rows.filter((row) => row.status === 'new').length,
		removed: rows.filter((row) => row.status === 'removed').length,
		unchanged: rows.filter((row) => row.status === 'unchanged').length
	});

	function formatDate(value: string | null) {
		if (!value) return 'Unknown date';
		return new Date(value).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	function statusLabel(status: AppAPIScanDiffStatus) {
		switch (status) {
			case 'new':
				return 'New';
			case 'removed':
				return 'No longer observed';
			default:
				return 'Unchanged';
		}
	}

	function statusClass(status: AppAPIScanDiffStatus) {
		switch (status) {
			case 'new':
				return 'bg-success-50-950 text-success-900-100';
			case 'removed':
				return 'bg-error-50-950 text-error-900-100';
			default:
				return 'bg-surface-100-900';
		}
	}

	const filters: { value: StatusFilter; label: string }[] = [
		{ value: 'all', label: 'All' },
		{ value: 'new', label: 'New' },
		{ value: 'removed', label: 'No longer observed' },
		{ value: 'unchanged', label: 'Unchanged' }
	];
</script>

<div class="p-2 md:p-8 mt-2 md:mt-4">
	<section class="space-y-6">
		<div>
			<h2 class="h4 md:h3 p-2">Data flow changes for {data.myapp.name}</h2>
			<p class="p-2">
				What changed between the two most recent scans. A vendor is "Detected" when at least one
				request to it was captured during that scan.
			</p>
		</div>

		<AppDataFlowsNav storeId={data.myapp.store_id} callCount={apis.length} hasDiff={!!scanDiff} />

		{#if !scanDiff}
			<WhiteCard>
				<div class="p-4 space-y-2">
					<p>
						A scan comparison needs at least two scans. This app currently has
						{apis.length === 0 ? 'no' : 'only one'} scan on record.
					</p>
					<a
						href={resolve('/apps/[id]/(sub)/data-flows', { id: data.myapp.store_id })}
						class="underline text-sm"
					>
						Back to the data flows overview
					</a>
				</div>
			</WhiteCard>
		{:else}
			<section class="grid grid-cols-2 md:grid-cols-4 gap-4">
				<div class="p-4 bg-surface-100-900 rounded-md">
					<p class="text-sm">Vendors compared</p>
					<p class="text-2xl font-bold">{counts.all}</p>
				</div>
				<div class="p-4 bg-success-50-950 rounded-md">
					<p class="text-sm">New</p>
					<p class="text-2xl font-bold">{counts.new}</p>
				</div>
				<div class="p-4 bg-error-50-950 rounded-md">
					<p class="text-sm">No longer observed</p>
					<p class="text-2xl font-bold">{counts.removed}</p>
				</div>
				<div class="p-4 bg-surface-100-900 rounded-md">
					<p class="text-sm">Unchanged</p>
					<p class="text-2xl font-bold">{counts.unchanged}</p>
				</div>
			</section>

			<WhiteCard>
				{#snippet title()}
					Scan comparison
				{/snippet}
				<div class="p-2 md:p-4 space-y-4">
					<p class="text-sm">
						Previous scan: <strong>{formatDate(scanDiff.previous_run_at)}</strong>
						{#if scanDiff.previous_run_id !== null}
							<span class="text-surface-600-400">(run {scanDiff.previous_run_id})</span>
						{/if}
						→ Latest scan: <strong>{formatDate(scanDiff.latest_run_at)}</strong>
						{#if scanDiff.latest_run_id !== null}
							<span class="text-surface-600-400">(run {scanDiff.latest_run_id})</span>
						{/if}
					</p>

					<div class="flex flex-wrap gap-2">
						{#each filters as filter (filter.value)}
							<button
								type="button"
								class="btn text-sm {statusFilter === filter.value
									? 'preset-filled-primary-500'
									: 'preset-tonal-surface'}"
								onclick={() => (statusFilter = filter.value)}
							>
								{filter.label} ({counts[filter.value]})
							</button>
						{/each}
					</div>

					<div class="overflow-x-auto">
						<table class="table table-hover table-auto w-full">
							<thead>
								<tr>
									<th class="text-left">Vendor</th>
									<th class="text-left">Previous scan</th>
									<th class="text-left">Latest scan</th>
									<th class="text-left">Status</th>
								</tr>
							</thead>
							<tbody>
								{#each visibleRows as row (row.vendor_key)}
									<tr>
										<td>
											{#if row.company_domain}
												<CompanyButton
													companyName={row.company_name ?? row.company_domain}
													companyDomain={row.company_domain}
													companyLogoUrl={row.company_logo_url ?? undefined}
												/>
											{:else}
												<div class="flex flex-wrap items-center gap-2">
													<span class="text-sm">{row.tld_url ?? row.vendor_key}</span>
													<RequestMappingButton
														mapType="company_domain_name"
														valueToBeMapped={row.tld_url ?? row.vendor_key}
														label="Request Mapping"
													/>
												</div>
											{/if}
										</td>
										<td class="text-sm">{row.previous}</td>
										<td class="text-sm">{row.latest}</td>
										<td>
											<span class="px-2 py-1 text-xs rounded-md {statusClass(row.status)}">
												{statusLabel(row.status)}
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>

					{#if visibleRows.length === 0}
						<p class="text-sm text-surface-600-400">No vendors match this filter.</p>
					{/if}
				</div>
			</WhiteCard>
		{/if}
	</section>
</div>
