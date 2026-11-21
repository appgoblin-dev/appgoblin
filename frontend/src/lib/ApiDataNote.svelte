<script lang="ts">
	let {
		endpoint
	}: {
		endpoint: string;
	} = $props();
</script>

<p class="mt-4 text-sm text-surface-600-400">
	Data also available via the
	<a href="/api-docs" class="underline font-semibold hover:text-primary-600-400"
		>AppGoblin MCP and API</a
	>
	(<code class="text-xs">{endpoint}</code>).
</p>
