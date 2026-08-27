<script lang="ts">
	import History from '@lucide/svelte/icons/history';
	import Plus from '@lucide/svelte/icons/plus';
	import Minus from '@lucide/svelte/icons/minus';
	import X from '@lucide/svelte/icons/x';

	import Crown from '@lucide/svelte/icons/crown';

	let {
		data
	}: {
		data: {
			sdkHistory: { history: Record<string, any>[] };
			myapp: any;
			hasB2BSdkAccess: boolean;
			versionTimeline: Record<string, any>[];
		};
	} = $props();

	function formatDateTime(date: string | null) {
		if (!date) return '—';
		return new Date(date).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function isScanStatusRow(entry: Record<string, any>): boolean {
		return !entry.sdk_name;
	}

	function scanStatusLabel(entry: Record<string, any>): string {
		if (entry.sdk_scan_result == null) return 'Scan Failed';
		if (entry.sdk_scan_result === 1) return 'No Changes';
		return 'Scan Unknown';
	}

	function scanStatusColor(entry: Record<string, any>): string {
		if (entry.sdk_scan_result == null) return 'bg-error-50-950';
		return 'preset-tonal-surface';
	}

	function changeStatusLabel(status: string | null): string {
		switch (status) {
			case 'added_initial':
				return 'Initially Added';
			case 'added':
				return 'Added';
			case 'removed':
				return 'Removed';
			default:
				return status ?? '';
		}
	}

	function changeStatusColor(status: string | null): string {
		if (status === 'removed') return 'bg-error-50-950';
		return 'bg-success-50-950';
	}

	let sortedHistory = $derived(
		[...(data.sdkHistory.history ?? [])].sort(
			(a, b) =>
				new Date(b.version_code_created_at ?? 0).getTime() -
				new Date(a.version_code_created_at ?? 0).getTime()
		)
	);
</script>

<div class="p-2 md:p-16 mt-2 md:mt-4">
	<div class="flex items-center gap-2 mb-6">
		<History size={24} class="text-surface-600" />
		<h1 class="text-2xl font-bold">SDK Change History</h1>
	</div>

	<p class="text-sm md:text-base mb-6 text-surface-600">
		Historical SDK additions and removals across versions of {data.myapp.name ?? 'this app'}.
	</p>

	{#if !data.hasB2BSdkAccess}
		<div class="mb-4 p-3 bg-warning-50-950/20 rounded-lg border border-warning-800-200">
			<p class="text-sm text-warning-950-50 flex items-center gap-2">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
				>
					<rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
					<path d="M7 11V7a5 5 0 0 1 10 0v4" />
				</svg>
				<Crown class="inline w-4 h-4 mr-0.5 -mt-0.5 text-primary-900-100" aria-hidden="true" />B2B
				SDK Intelligence tier.
				<a href="/pricing" class="underline hover:text-primary-600-400">Upgrade</a>
				to unlock.
			</p>
		</div>
	{/if}

	{#if data.hasB2BSdkAccess}
		{#if sortedHistory.length > 0}
			<div class="overflow-x-auto">
				<table class="w-full text-left border-collapse">
					<thead>
						<tr
							class="border-b border-surface-300-600 text-sm uppercase tracking-wide text-surface-500"
						>
							<th class="py-3 px-4 font-medium">Date</th>
							<th class="py-3 px-4 font-medium">Version</th>
							<th class="py-3 px-4 font-medium">Status</th>
							<th class="py-3 px-4 font-medium">SDK / Company</th>
						</tr>
					</thead>
					<tbody>
						{#each sortedHistory as entry (entry.version_code_created_at + (entry.sdk_name ?? ''))}
							{#if isScanStatusRow(entry)}
								<!-- Scan status row: no change or failed -->
								<tr class="border-b border-surface-100-900 hover:bg-surface-50-950 transition">
									<td class="py-3 px-4 text-sm">{formatDateTime(entry.version_code_created_at)}</td>
									<td class="py-3 px-4 font-mono text-sm">{entry.version_code ?? '—'}</td>
									<td class="py-3 px-4">
										<span
											class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium {scanStatusColor(
												entry
											)}"
										>
											{#if entry.sdk_scan_result == null}
												<X size={12} />
											{/if}
											{scanStatusLabel(entry)}
										</span>
									</td>
									<td class="py-3 px-4 text-surface-500 italic">—</td>
								</tr>
							{:else}
								<!-- SDK change row -->
								<tr class="border-b border-surface-200-800 hover:bg-surface-100-900/50 transition">
									<td class="py-3 px-4 text-sm">{formatDateTime(entry.version_code_created_at)}</td>
									<td class="py-3 px-4 font-mono text-sm">{entry.version_code ?? '—'}</td>
									<td class="py-3 px-4">
										<span
											class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium {changeStatusColor(
												entry.status
											)}"
										>
											{#if entry.status === 'removed'}
												<Minus size={12} />
											{:else}
												<Plus size={12} />
											{/if}
											{changeStatusLabel(entry.status)}
										</span>
									</td>
									<td class="py-3 px-4">
										<div class="flex items-center gap-2">
											{#if entry.company_logo_url}
												<img
													src="https://media.appgoblin.info/{entry.company_logo_url}"
													alt={entry.company_name ?? ''}
													class="w-10 h-10 rounded-full object-contain shrink-0"
												/>
											{/if}
											<div class="flex flex-col">
												<span class="font-medium text-sm md:text-base leading-tight"
													>{entry.sdk_name ?? 'Unknown SDK'}</span
												>
												{#if entry.company_domain}
													<a
														href="/companies/{entry.company_domain}"
														class="text-xs text-primary-700-300 hover:underline leading-tight"
													>
														{entry.company_name ?? entry.company_domain}
													</a>
												{/if}
											</div>
										</div>
									</td>
								</tr>
							{/if}
						{/each}
					</tbody>
				</table>
			</div>
		{:else}
			<div class="p-8 text-center text-surface-500">
				<p>No SDK history available for this app.</p>
			</div>
		{/if}
	{/if}

	<hr class="my-8 border-surface-300-600" />

	<div class="flex items-center gap-2 mb-6">
		<History size={20} class="text-surface-600" />
		<h2 class="text-xl font-bold">App Version Timeline</h2>
	</div>

	<p class="text-sm md:text-base mb-6 text-surface-600">
		All crawled versions of {data.myapp.name ?? 'this app'}. SDK scan results shown below are
		available with the B2B SDK Intelligence tier.
	</p>

	{#if data.versionTimeline && data.versionTimeline.length > 0}
		<div class="overflow-x-auto">
			<table class="w-full text-left border-collapse">
				<thead>
					<tr
						class="border-b border-surface-300-600 text-sm uppercase tracking-wide text-surface-500"
					>
						<th class="py-3 px-4 font-medium">Version</th>
						<th class="py-3 px-4 font-medium">Downloaded At</th>
						<th class="py-3 px-4 font-medium">SDK Scan Result</th>
						<th class="py-3 px-4 font-medium">SDKs Last Scanned</th>
					</tr>
				</thead>
				<tbody>
					{#each data.versionTimeline as entry}
						<tr class="border-b border-surface-200-800 hover:bg-surface-100-900/50 transition">
							<td class="py-3 px-4 font-mono text-sm">{entry.app_version_code ?? '—'}</td>
							<td class="py-3 px-4 text-sm">
								{entry.downloaded_at ? formatDateTime(entry.downloaded_at) : '—'}
							</td>

							<td class="py-3 px-4">
								{#if entry.sdk_scan_result == null}
									<span class="text-surface-500 italic">Pending</span>
								{:else if entry.sdk_scan_result === 1}
									<span class="text-success-700-300 font-medium">Scanned</span>
								{:else}
									<span class="text-surface-500">—</span>
								{/if}
							</td>
							<td class="py-3 px-4 text-sm">
								{entry.sdks_last_scanned_at ? formatDateTime(entry.sdks_last_scanned_at) : '—'}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{:else}
		<div class="p-8 text-center text-surface-500">
			<p>No version timeline available for this app.</p>
		</div>
	{/if}
</div>
