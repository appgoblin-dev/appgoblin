<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import type { CompanyOverviewScope } from '../types';

	interface CategoryOption {
		value: string;
		label: string;
		total: number;
		locked: boolean;
	}

	interface Props {
		overview: CompanyOverviewScope | null | undefined;
		label?: string;
		description?: string;
		compact?: boolean;
		hasB2BAccess?: boolean;
	}

	let {
		overview,
		label = 'App Categories',
		description = 'Filter the company view by app category.',
		compact = false,
		hasB2BAccess = false
	}: Props = $props();

	function getCategoryName(category: string): string {
		if (category === 'all') return 'Overall';

		return category
			.replace('game_', 'Games: ')
			.replace('_and_', ' & ')
			.replaceAll('_', ' ')
			.replace(/\b\w/g, (char) => char.toUpperCase());
	}

	function buildCategoryOptions(
		currentOverview: CompanyOverviewScope | null | undefined
	): CategoryOption[] {
		if (!currentOverview?.categories) {
			return [{ value: 'overall', label: 'Overall', total: 0, locked: false }];
		}

		const options = Object.entries(currentOverview.categories)
			.map(([id, stats]) => ({
				value: id === 'all' ? 'overall' : id,
				label: getCategoryName(id),
				total: Math.max(
					stats.sdk_android_total_apps + stats.sdk_ios_total_apps,
					stats.sdk_adapter_total_apps ?? 0
				),
				locked: !['all', 'games'].includes(id) && !hasB2BAccess
			}))
			.filter((option) => option.value === 'overall' || option.total > 0)
			.sort((left, right) => {
				if (left.value === 'overall') return -1;
				if (right.value === 'overall') return 1;
				if (right.total !== left.total) return right.total - left.total;
				return left.label.localeCompare(right.label);
			});

		return options.length > 0
			? options
			: [{ value: 'overall', label: 'Overall', total: 0, locked: false }];
	}

	async function handleCategoryChange(event: Event) {
		const nextCategory = (event.currentTarget as HTMLSelectElement).value;
		const domain = page.params.domain;

		if (!domain) return;

		// Don't navigate to locked categories for non-B2B users
		if (!['overall', 'games'].includes(nextCategory) && !hasB2BAccess) {
			// Reset the select back to the current category
			const select = event.currentTarget as HTMLSelectElement;
			select.value = page.params.category || 'overall';
			return;
		}

		const href =
			nextCategory === 'overall' ? `/companies/${domain}` : `/companies/${domain}/${nextCategory}`;
		await goto(href);
	}

	let categoryOptions = $derived(buildCategoryOptions(overview));
	let selectedCategory = $derived(page.params.category || 'overall');
</script>

{#if compact}
	<div class="min-w-[220px]">
		<label class="label">
			<span
				class="label-text flex items-center gap-1.5 text-[11px] uppercase tracking-[0.14em] opacity-60"
				>{label}</span
			>
			<select
				id="company-category-select"
				class="select rounded"
				value={selectedCategory}
				onchange={handleCategoryChange}
			>
				{#each categoryOptions as option (option.value)}
					<option value={option.value} disabled={option.locked}
						>{option.label}{option.locked ? ' 🔒 B2B' : ''}</option
					>
				{/each}
			</select>
		</label>
	</div>
{:else}
	<section class="mb-6 rounded border p-3 md:p-4">
		<div class="mb-3 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
			<div>
				<div class="flex items-center gap-2 text-sm font-semibold">
					<span>{label}</span>
				</div>
				<p class="mt-1 text-xs opacity-70">{description}</p>
			</div>
		</div>

		<div class="grid gap-2.5 md:grid-cols-[220px_auto] md:items-end">
			<div>
				<label class="label">
					<span
						class="label-text flex items-center gap-1.5 text-[11px] uppercase tracking-[0.14em] opacity-60"
						>Category</span
					>
					<select
						id="company-category-select"
						class="select rounded"
						value={selectedCategory}
						onchange={handleCategoryChange}
					>
						{#each categoryOptions as option (option.value)}
							<option value={option.value} disabled={option.locked}
								>{option.label}{option.locked ? ' 🔒 B2B' : ''}</option
							>
						{/each}
					</select>
				</label>
			</div>
		</div>
	</section>
{/if}
