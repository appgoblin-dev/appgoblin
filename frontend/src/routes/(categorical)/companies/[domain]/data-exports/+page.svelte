<script lang="ts">
	import WhiteCard from '$lib/WhiteCard.svelte';

	export let data: {
		canDownload: boolean;
		companyName: string;
		downloadUrls: {
			appAdsTxt: string | null;
			companyVerifiedAndroid: string | null;
			companyVerifiedIos: string | null;
		} | null;
	};
</script>

<WhiteCard>
	{#snippet title()}
		<span>{data.companyName}'s Data Exports</span>
	{/snippet}
	<div class="p-4 flex flex-col gap-4">
		<p>Raw data downloads for {data.companyName}.</p>

		{#if data.canDownload && data.downloadUrls}
			<div class="flex flex-wrap gap-4">
				{#if data.downloadUrls.appAdsTxt}
					<a
						href={data.downloadUrls.appAdsTxt}
						class="btn preset-filled-primary-500"
						download
						target="_blank"
						rel="noopener noreferrer"
					>
						Download {data.companyName}'s app-ads.txt (iOS + Android)
					</a>
				{/if}
				{#if data.downloadUrls.companyVerifiedAndroid}
					<a
						href={data.downloadUrls.companyVerifiedAndroid}
						class="btn preset-filled-primary-500"
						download
						target="_blank"
						rel="noopener noreferrer"
					>
						Download {data.companyName}'s SDK/API traffic (Android)
					</a>
				{/if}
				{#if data.downloadUrls.companyVerifiedIos}
					<a
						href={data.downloadUrls.companyVerifiedIos}
						class="btn preset-filled-primary-500"
						download
						target="_blank"
						rel="noopener noreferrer"
					>
						Download {data.companyName}'s SDK/API traffic (iOS)
					</a>
				{/if}
			</div>
		{:else}
			<div class="flex flex-wrap gap-4">
				<a
					href="/pricing"
					class="btn preset-tonal inline-flex items-center gap-2 opacity-90 cursor-pointer"
					aria-label="Locked – upgrade to download"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="18"
						height="18"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
						aria-hidden="true"
					>
						<rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
						<path d="M7 11V7a5 5 0 0 1 10 0v4" />
					</svg>
					<span>Download {data.companyName}'s app-ads.txt</span>
					<span class="text-sm">(subscribers only)</span>
				</a>
				<a
					href="/pricing"
					class="btn preset-tonal inline-flex items-center gap-2 opacity-90 cursor-pointer"
					aria-label="Locked – upgrade to download"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="18"
						height="18"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
						aria-hidden="true"
					>
						<rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
						<path d="M7 11V7a5 5 0 0 1 10 0v4" />
					</svg>
					<span>Download {data.companyName}'s SDK/API traffic (Android)</span>
					<span class="text-sm">(subscribers only)</span>
				</a>
				<a
					href="/pricing"
					class="btn preset-tonal inline-flex items-center gap-2 opacity-90 cursor-pointer"
					aria-label="Locked – upgrade to download"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="18"
						height="18"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
						aria-hidden="true"
					>
						<rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
						<path d="M7 11V7a5 5 0 0 1 10 0v4" />
					</svg>
					<span>Download {data.companyName}'s SDK/API traffic (iOS)</span>
					<span class="text-sm">(subscribers only)</span>
				</a>
			</div>
			<p class="text-surface-600-400 text-sm">
				Data exports are included with a paid subscription.
				<a href="/pricing" class="underline hover:text-primary-600-400">View pricing</a> to unlock.
			</p>
		{/if}
	</div>
</WhiteCard>
