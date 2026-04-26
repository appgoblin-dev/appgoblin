<script lang="ts">
	import IconiOS from './svg/IconiOS.svelte';
	import IconGoogle from './svg/IconGoogle.svelte';

	const buttonSelectedColor = 'p-1 preset-filled-secondary-100-900';
	const buttonDeselectedColor = 'p-1';

	interface Props {
		values: any;
		selectedCategory: string;
	}

	let { values, selectedCategory: selectedCategory = $bindable() }: Props = $props();

	let isSelected = $derived(checkSelected());

	function checkSelected() {
		return selectedCategory == values.id;
	}

	function setSelectedClass(isSelected: boolean) {
		return isSelected ? buttonSelectedColor : buttonDeselectedColor;
	}
</script>

<div class="flex w-full justify-between p-1 {setSelectedClass(isSelected)}">
	<div class="grow">
		{values.name}
	</div>

	{#if Number(values.android) > 0 || values.name == 'Games'}
		<div class="justify-end mr-2 md:mr-5">
			<IconGoogle size="16" />
		</div>
	{:else}
		<div class="opacity-20 justify-end mr-2 md:mr-5">
			<IconGoogle size="16" />
		</div>
	{/if}
	{#if Number(values.ios) > 0}
		<div class="justify-end mr-2 md:mr-5">
			<IconiOS size="16" />
		</div>
	{:else}
		<div class="opacity-20 justify-end mr-2 md:mr-5">
			<IconiOS size="16" />
		</div>
	{/if}
</div>
