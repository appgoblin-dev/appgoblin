<script lang="ts">
	import DeveloperSDKOverview from '$lib/DeveloperSDKOverview.svelte';
	import type { DeveloperSDKResponse } from '../../../../types';

	interface Props {
		data: DeveloperSDKResponse;
	}

	let { data }: Props = $props();
</script>

<h2 class="text-2xl font-bold">SDKs by Company</h2>
<p class="text-sm md:text-base p-2 md:p-4">Developers SDKS</p>

<div>
	{#await data.devSDKs}
		<div>
			<span>Loading...</span>
		</div>
	{:then sdks}
		{#if typeof sdks == 'string'}
			Failed to load sdks
		{:else}
			<div class="preset-filled-surface-100-900 p-2 md:p-8 mt-2 md:mt-4">
				<DeveloperSDKOverview myPackageInfo={sdks} companyTypes={data.companyTypes} />
			</div>
		{/if}
	{:catch error}
		<p style="color: red">{error.message}</p>
	{/await}
</div>
