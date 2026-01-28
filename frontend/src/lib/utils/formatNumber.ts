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
