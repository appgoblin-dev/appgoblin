<script lang="ts">
	import { page } from '$app/state';
	import ExternalLink from 'lucide-svelte/icons/external-link';

	let {
		title,
		description,
		backendPath,
		primaryLabel = undefined,
		secondaryHref = undefined,
		secondaryLabel = undefined
	}: {
		title: string;
		description: string;
		backendPath: string;
		primaryLabel?: string;
		secondaryHref?: string;
		secondaryLabel?: string;
	} = $props();

	const docsUrl = $derived.by(() => {
		const { hostname, origin } = page.url;
		const backendOrigin =
			hostname === 'localhost' || hostname === '127.0.0.1' ? 'http://localhost:8000' : origin;
		return `${backendOrigin}${backendPath}`;
	});
</script>

<div class="container mx-auto px-4 py-6 md:py-8 space-y-6">
	<div class="card preset-tonal p-6 md:p-8 space-y-4">
		<div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
			<div class="space-y-2 max-w-3xl">
				<h1 class="text-2xl md:text-3xl font-bold">{title}</h1>
				<p class="text-sm md:text-base text-surface-600-400">{description}</p>
				<p class="text-xs md:text-sm text-surface-500">
					This page is generated from Litestar's OpenAPI schema and is limited to public
					<code class="bg-surface-200-800 px-1.5 py-0.5 rounded text-xs">/api/v1/*</code>
					endpoints.
				</p>
			</div>
			<div class="flex flex-wrap gap-3">
				{#if secondaryHref && secondaryLabel}
					<a href={secondaryHref} class="btn preset-tonal text-sm">{secondaryLabel}</a>
				{/if}
				{#if primaryLabel}
					<a
						href={docsUrl}
						target="_blank"
						rel="noreferrer"
						class="btn preset-filled-primary-500 flex items-center gap-2 text-sm"
					>
						<ExternalLink size={16} />
						{primaryLabel}
					</a>
				{/if}
			</div>
		</div>
	</div>

	<div class="card overflow-hidden border border-surface-300-700 bg-surface-50-950">
		<iframe
			{title}
			src={docsUrl}
			class="block w-full min-h-[75vh] md:min-h-[82vh] bg-white"
			loading="eager"
		></iframe>
	</div>
</div>
