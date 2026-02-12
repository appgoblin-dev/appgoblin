<script lang="ts">
	import Star from './Star.svelte';
	import generateId from './utils/generateIds.js';
	import type { Component } from 'svelte';

	interface Props {
		size?: number;
		total?: number;
		rating?: number;
		partialId?: string;
		icon?: Component;
		count?: boolean;
		children?: import('svelte').Snippet;
		text?: import('svelte').Snippet;
	}

	let {
		size = 24,
		total = 5,
		rating = 4,
		partialId = 'partialStar' + generateId(),
		icon = Star,
		count = false,
		children,
		text
	}: Props = $props();

	// generate unique id for full star and gray star
	const fullStarId: string = generateId();
	const grayStarId: string = generateId();
	const fullStars = $derived(Math.floor(rating));
	const rateDiffence = $derived(rating - fullStars);
	const percentRating = $derived(Math.round(rateDiffence * 100));
	const grayStars = $derived(total - (fullStars + Math.ceil(rateDiffence)));
</script>

<div class="my-rating flex items-center">
	{#if count}
		{@const SvelteComponent = icon}
		<SvelteComponent fillPercent={100} {size} />
		<p class="ml-2 text-sm font-bold text-primary-900-100">{rating}</p>
		{@render children?.()}
	{:else}
		{#each Array(fullStars) as star}
			{@const SvelteComponent_1 = icon}
			<SvelteComponent_1 {size} fillPercent={100} id={fullStarId} />
		{/each}
		{#if percentRating}
			{@const SvelteComponent_2 = icon}
			<SvelteComponent_2 {size} fillPercent={percentRating} id={partialId} />
		{/if}
		{#each Array(grayStars) as star}
			{@const SvelteComponent_3 = icon}
			<SvelteComponent_3 {size} fillPercent={0} id={grayStarId} />
		{/each}
		{#if text}
			{@render text?.()}
		{/if}
	{/if}
</div>

<!--
  @component
  [Go to docs](https://flowbite-svelte.com/)
  ## Props
  @prop export let divClass: string = 'flex items-center';
  @prop export let size: number = 24;
  @prop export let total: number = 5;
  @prop export let rating: number = 4;
  @prop export let partialId: string = 'partialStar' + generateId();
  @prop export let icon: ComponentType = Star;
  @prop export let count: boolean = false;
  -->
