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
		unique_mmps: number;

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

	type CreativeOrientation = 'portrait' | 'landscape';

	import { createCreativeModal } from '$lib/stores/creativeModal.svelte';
	import CreativeModal from '$lib/CreativeModal.svelte';
	import CompanyButton from '$lib/CompanyButton.svelte';

	let {
		data,
		orientation = 'landscape'
	}: {
		data: CreativeCluster;
		orientation?: CreativeOrientation;
	} = $props();

	// If the file is video, construct proper video URL, otherwise use image
	let isVideo = $derived(['mp4', 'webm'].includes(data.file_extension.toLowerCase()));
	// Raw URL is derived client-side only (never serialized in page data) to prevent browser prefetching
	let mediaUrl = $derived(
		`https://media.appgoblin.info/creatives/raw/${data.representative_md5.substring(0, 3)}/${data.representative_md5}.${data.file_extension}`
	);
	let thumbUrl = $derived(data.creative_thumb_url);
	let isPortrait = $derived(orientation === 'portrait');
	let thumbLoadFailed = $state(false);

	let isHovered = $state(false);

	const creativeModal = createCreativeModal();

	function handleThumbLoadError(event: Event) {
		thumbLoadFailed = true;
		const image = event.currentTarget as HTMLImageElement;
		image.onerror = null;
		image.style.display = 'none';
	}
</script>

<!-- Creative Modal -->
<CreativeModal
	bind:isOpen={creativeModal.isOpen}
	creativeUrl={creativeModal.creativeUrl}
	title={creativeModal.title}
/>

<div
	class="card card-hover overflow-hidden rounded-xl border shadow-sm transition-all flex h-full flex-col"
	role="group"
	onmouseenter={() => (isHovered = true)}
	onmouseleave={() => (isHovered = false)}
>
	<!-- Media Display area -->
	<button
		class={`relative bg-black w-full overflow-hidden flex items-center justify-center cursor-pointer group ${isPortrait ? 'max-h-[260px] md:max-h-[340px] lg:max-h-[420px]' : 'max-h-[140px] md:max-h-[180px] lg:max-h-[250px]'}`}
		onclick={() =>
			creativeModal.open(mediaUrl, data.top_adv_name || data.top_advertiser_store_id || 'Creative')}
		aria-label="View Media"
	>
		{#if isVideo}
			<!-- Primary static structure defining natural size -->
			{#if !thumbLoadFailed}
				<img
					src={thumbUrl}
					alt={data.vhash}
					class={`w-full ${isPortrait ? 'h-full object-contain' : 'h-auto object-contain'} opacity-90 transition-opacity`}
					loading="lazy"
					decoding="async"
					onerror={handleThumbLoadError}
				/>
			{/if}

			{#if isHovered}
				<video
					src={mediaUrl}
					poster={thumbLoadFailed ? undefined : thumbUrl}
					class="absolute inset-0 w-full h-full object-contain bg-black/90"
					autoplay
					muted
					loop
					playsinline
				></video>
			{:else}
				<!-- Play icon overlay -->
				<div
					class="absolute inset-0 flex flex-col items-center justify-center opacity-70 group-hover:bg-black/30 transition-all duration-300"
				>
					<div class="bg-primary-500 rounded-full p-1.5 md:p-2 lg:p-3">
						<svg
							class="h-4 w-4 text-gray-800 md:h-5 md:w-5 lg:h-6 lg:w-6"
							fill="currentColor"
							viewBox="0 0 24 24"
						>
							<path d="M8 5v14l11-7z" />
						</svg>
					</div>
				</div>
			{/if}
		{:else}
			{#if !thumbLoadFailed}
				<img
					src={thumbUrl}
					alt={data.vhash}
					class={`w-full ${isPortrait ? 'h-full object-contain' : 'h-auto object-contain'}`}
					loading="lazy"
					decoding="async"
					onerror={handleThumbLoadError}
				/>
			{/if}
			<div
				class="absolute inset-0 hidden group-hover:flex items-center justify-center bg-black/30 transition-all duration-300"
			>
				<div class="bg-primary-500 rounded-full p-1.5 opacity-90 md:p-2 lg:p-3">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="18"
						height="18"
						viewBox="0 0 24 24"
						fill="none"
						stroke="black"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
						><path d="M15 3h6v6"></path><path d="M10 14 21 3"></path><path
							d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"
						></path></svg
					>
				</div>
			</div>
		{/if}

		<div class="absolute right-1.5 top-1.5 z-10 md:right-2 md:top-2">
			<span
				class="badge variant-filled-surface text-[10px] font-semibold uppercase opacity-90 shadow-sm md:text-xs"
			>
				{data.file_extension}
			</span>
		</div>
	</button>

	<!-- Info Area -->
	<div class="flex flex-grow flex-col justify-between p-2.5 md:p-3 lg:p-3.5">
		<div>
			<!-- Advertiser Details -->
			<div class="mb-2 flex items-center gap-2 md:mb-2.5 md:gap-2.5">
				{#if data.adv_icon_url}
					<img
						src={data.adv_icon_url}
						class="h-6 w-6 rounded shadow-sm flex-shrink-0 md:h-8 md:w-8 lg:h-9 lg:w-9"
						alt="adv icon"
					/>
				{:else}
					<div
						class="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded text-[9px] opacity-50 md:h-8 md:w-8 md:text-[10px] lg:h-9 lg:w-9"
					>
						App
					</div>
				{/if}
				<div class="overflow-hidden">
					{#if data.top_advertiser_store_id}
						<a
							href={`/apps/${data.top_advertiser_store_id}`}
							class="block truncate text-xs font-bold hover:text-primary-500 md:text-sm"
							title={data.top_adv_name || data.top_advertiser_store_id}
						>
							{data.top_adv_name || data.top_advertiser_store_id}
						</a>
					{:else}
						<div class="block truncate text-[11px] font-medium md:text-xs">Unknown Advertiser</div>
					{/if}
					<div class="mt-1 flex flex-col items-start gap-1 text-xs opacity-70">
						{#if data.top_ad_domain_company || data.top_ad_domain}
							<CompanyButton
								companyName={data.top_ad_domain_company || 'Ad'}
								companyDomain={data.top_ad_domain || ''}
								companyLogoUrl={data.company_logo_url_ad || ''}
								size="sm"
							/>
						{:else if data.top_host_domain_company || data.top_host_domain}
							<CompanyButton
								companyName={data.top_host_domain_company || 'Network'}
								companyDomain={data.top_host_domain || ''}
								companyLogoUrl={data.company_logo_url_host || ''}
								size="sm"
							/>
						{/if}
					</div>
				</div>
			</div>

			<!-- Publisher / Reach context -->
			<div class="flex flex-col gap-1 rounded p-1.5 text-[11px] md:p-2 md:text-xs">
				<div class="flex justify-between items-center text-surface-600-300-token">
					<span>Unique Publishers:</span>
					<span class="font-bold">{data.unique_publisher_apps}</span>
				</div>
				<div class="flex justify-between items-center text-surface-600-300-token">
					<span>Seen recently:</span>
					<span>{data.last_seen_at?.split('T')[0]}</span>
				</div>
			</div>
		</div>
	</div>
</div>
