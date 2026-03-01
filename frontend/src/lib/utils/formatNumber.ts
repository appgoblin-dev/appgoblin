/**
 * Formats a number with appropriate suffix (K, M, B, T)
 * @param num - The number to format
 * @returns Formatted string with suffix
 */
export function formatNumber(num: number): string | number {
	if (num >= 1000000000000) return (num / 1000000000000).toFixed(1).replace(/\.0$/, '') + 'T';
	if (num >= 1000000000) return (num / 1000000000).toFixed(1).replace(/\.0$/, '') + 'B';
	if (num >= 1000000) return (num / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
	if (num >= 1000) return (num / 1000).toFixed(1).replace(/\.0$/, '') + 'K';
	if (num >= 10) return num.toFixed(0);
	if (num < 10 && num > 0) return num.toFixed(2);
	return num;
}

/**
 * Formats a number with locale string (adds commas)
 * @param num - The number to format
 * @returns Formatted string with commas
 */
export function formatNumberLocale(num: number): string {
	if (num) {
		return num.toLocaleString();
	} else {
		return '';
	}
}

/**
 * Formats revenue into nearest bucket with $ prefix
 * @param value - The revenue value to bucket
 * @returns Formatted string with bucket label (e.g., '$>1M') or empty string
 */
export function getRevenueBucket(value: number): string {
	if (value <= 0) return '';

	const buckets = [
		{ value: 10000, label: '$<10K' },
		{ value: 50000, label: '$>50K' },
		{ value: 100000, label: '$>100K' },
		{ value: 200000, label: '$>200K' },
		{ value: 500000, label: '$>500K' },
		{ value: 1000000, label: '$>1M' },
		{ value: 10000000, label: '$>10M' }
	];

	let closest = buckets[0];
	let minDiff = Math.abs(value - closest.value);

	for (const bucket of buckets) {
		const diff = Math.abs(value - bucket.value);
		if (diff < minDiff) {
			closest = bucket;
			minDiff = diff;
		}
	}

	return closest.label;
}
