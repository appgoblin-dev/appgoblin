<script lang="ts">
	import { countryCodeToEmoji } from '#lib/utils/countryCodeToEmoji.js';

	let { code, class: className = 'text-lg' }: { code?: string | null; class?: string } = $props();

	const normalizedCode = $derived(code ? code.trim().toUpperCase() : '');
</script>

<span class={className} title={normalizedCode}>{countryCodeToEmoji(normalizedCode)}</span>
