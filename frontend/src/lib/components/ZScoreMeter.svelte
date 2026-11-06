<script lang="ts">
	type ZScoreMeterProps = {
		value: number;
		min?: number;
		max?: number;
		size?: 'sm' | 'md' | 'lg';
	};

	let { value, min = 100, max = 5000, size = 'md' }: ZScoreMeterProps = $props();

	// Calculate percentage for the meter (0-100%)
	const percentage = $derived(Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100)));

	// Determine bar color
	const barColor = $derived(
		(() => {
			if (percentage >= 90) return 'bg-success-900-100';
			if (percentage >= 75) return 'bg-success-700-300';
			if (percentage >= 60) return 'bg-success-800-200';
			if (percentage >= 40) return 'bg-success-800-200';
			if (percentage >= 25) return 'bg-success-900-100';
			return 'bg-success-900-100';
		})()
	);

	// Size classes
	const sizeClasses = $derived({
		sm: 'h-2 text-xs',
		md: 'h-3 text-sm',
		lg: 'h-4 text-base'
	});
</script>

<div class="relative">
	<!-- Background bar -->
	<div class="w-full bg-surface-200-700 rounded-full {sizeClasses[size]}">
		<!-- Progress bar -->
		<div
			class="h-full rounded-full transition-all duration-300 ease-out {barColor}"
			style="width: {percentage}%"
		></div>
	</div>
</div>
