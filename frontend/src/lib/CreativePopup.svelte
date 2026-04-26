<script lang="ts" generics="TData, TValue">
	import CreativeModal from '$lib/CreativeModal.svelte';
	import { createCreativeModal } from '$lib/stores/creativeModal.svelte';

	let { md5_hash, file_extension }: { md5_hash: string; file_extension: string } = $props();

	// Creative modal state
	const creativeModal = createCreativeModal();
</script>

<button
	class="text-xs text-blue-600 hover:text-blue-800 underline cursor-pointer relative group"
	onclick={() =>
		creativeModal.open(
			`https://media.appgoblin.info/creatives/raw/${md5_hash.substring(0, 3)}/${md5_hash}.${file_extension}`,
			`Creative: ${md5_hash}`
		)}
>
	<div class="relative">
		<img
			src="https://media.appgoblin.info/creatives/thumbs/{md5_hash}.jpg"
			class="w-24 md:w-64 h-auto object-cover rounded text-xs"
			alt="Creative: {md5_hash}"
			loading="lazy"
		/>
		<!-- Play button overlay -->
		<div
			class="absolute inset-0 flex items-center justify-center bg-black/30 rounded opacity-70 group-hover:opacity-100 transition-opacity duration-200"
		>
			<div class="bg-primary-500 rounded-full p-2 md:p-3">
				<svg class="w-4 h-4 md:w-6 md:h-6 text-gray-800" fill="currentColor" viewBox="0 0 24 24">
					<path d="M8 5v14l11-7z" />
				</svg>
			</div>
		</div>
	</div>
</button>

<!-- Creative Modal -->
<CreativeModal
	bind:isOpen={creativeModal.isOpen}
	creativeUrl={creativeModal.creativeUrl}
	title={creativeModal.title}
/>
