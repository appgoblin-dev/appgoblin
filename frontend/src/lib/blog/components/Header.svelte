<script lang="ts">
	// Skeleton
	import { AppBar } from '@skeletonlabs/skeleton-svelte';
	// Icons
	import IconLogo from '@lucide/svelte/icons/rocket';
	// Utils
	import { SITE_TITLE } from '@src/consts';

	// For best results limit to 3-5 options max
	const navigation = [
		{ label: 'Blog', href: '/blog' },
		{ label: 'About', href: '/about' },
		// Enable this to show the test sandbox page
		// { label: 'Sandbox', href: '/sandbox' }
	];
</script>

<header
	class="sticky top-0 z-10 border-b border-surface-100-900 bg-surface-50-950/80 backdrop-blur-xl"
>
	<AppBar
		background="bg-transparent"
		toolbarGap="gap-10"
		toolbarClasses="items-center"
		classes="container mx-auto"
	>
		<!-- Snippet: Lead -->
		{#snippet lead()}
			<a
				href="/"
				class="btn-icon md:btn-icon-lg from-secondary-500 to-tertiary-500 rounded-full bg-linear-to-tr text-white"
				title={SITE_TITLE}
			>
				<IconLogo />
			</a>
		{/snippet}

		<!-- Snippet: Trail -->
		{#snippet trail()}
			<nav class="hidden gap-8 md:flex">
				<a
					class="btn hover:preset-tonal-tertiary"
					href="https://skeleton.dev/"
					target="_blank"
					rel="noreferrer"
				>
					Documentation
				</a>
			</nav>
		{/snippet}

		<!-- Navigation -->
		<nav class="flex gap-2">
			{#each navigation as route}
				<a
					class="btn hover:preset-tonal-tertiary"
					href={route.href}
				>
					{route.label}
				</a>
			{/each}
		</nav>
	</AppBar>
</header>
