<script lang="ts">
	import Crown from '@lucide/svelte/icons/crown';
	import CompanyAppChangesTable from '#lib/CompanyAppChangesTable.svelte';
	import CompanySectionLink from '#lib/utils/CompanySectionLink.svelte';
	import type { CompanyOverviewApps, CompanyTabIndicators } from '../../../../types';
	import { formatNumber } from '#lib/utils/formatNumber.js';
	import ApiDataNote from '#lib/ApiDataNote.svelte';

	type MergedAppChanges = {
		android: CompanyOverviewApps[];
		ios: CompanyOverviewApps[];
	};

	interface Props {
		data: {
			appChanges: MergedAppChanges;
			companyName: string;
			hasB2BSdkAccess: boolean;
			tabIndicators: CompanyTabIndicators | null;
		};
	}

	let { data }: Props = $props();

	let addedCount = $derived(
		data.tabIndicators?.apps_sdk_added_count ?? data.tabIndicators?.apps_sdk_added_count_direct ?? 0
	);
</script>

<section class="mb-4 space-y-2">
	<h2 class="text-xl font-semibold">Recently Added Apps</h2>
	<p class="text-sm mb-3">
		This view tracks the quarterly adoption of this company's SDK and API-call signals across the
		latest available quarter and the quarter before it. Compare
		<CompanySectionLink slug="apps-added-adstxt">app-ads.txt additions</CompanySectionLink> and
		<CompanySectionLink slug="apps-lost">SDK/API losses</CompanySectionLink>.
		{#if addedCount > 0}
			<span class="opacity-70">
				{formatNumber(addedCount)} app{addedCount === 1 ? '' : 's'} added across the latest two quarters.
			</span>
		{/if}
	</p>
</section>

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
			<Crown class="inline w-4 h-4 mr-0.5 -mt-0.5 text-primary-900-100" aria-hidden="true" />B2B SDK
			Intelligence tier.
			<a href="/pricing" class="underline hover:text-primary-600-400">Upgrade</a>
			to unlock.
		</p>
	</div>
{/if}

<CompanyAppChangesTable
	android={data.appChanges.android}
	ios={data.appChanges.ios}
	companyName={data.companyName}
	previewMode={!data.hasB2BSdkAccess}
	statusLabel="Added"
/>
<ApiDataNote endpoint={'/api/v1/companies/{company_domain}/app-changes'} />
