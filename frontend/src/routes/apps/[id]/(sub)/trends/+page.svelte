<script lang="ts">
	import type { AppGlobalMetrics, AppCountryMetrics } from '../../../../../types';
	import AppTrendsDashboard from '#lib/AppTrendsDash.svelte';
	import ApiDataNote from '#lib/ApiDataNote.svelte';

	interface Props {
		data: {
			appMetrics: AppGlobalMetrics[] | AppCountryMetrics[];
			selectedCountry: string;
			availableCountries: { code: string; name: string }[];
			myapp?: {
				store?: string;
			};
		};
	}
	let { data }: Props = $props();
</script>

<section class="mx-auto max-w-7xl space-y-4">
	{#if data.appMetrics && data.appMetrics.length > 0}
		<AppTrendsDashboard
			data={data.appMetrics}
			selectedCountry={data.selectedCountry}
			availableCountries={data.availableCountries}
			store={data.myapp?.store ?? ''}
		/>
	{:else}
		<div class="flex h-64 items-center justify-center">
			<div class="text-lg text-gray-500">No historical data found.</div>
		</div>
	{/if}
	<ApiDataNote endpoint={'/api/v1/apps/{store_id}/global-metrics-history'} />
</section>
