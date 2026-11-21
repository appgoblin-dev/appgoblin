<script lang="ts">
	import ApiDataNote from '#lib/ApiDataNote.svelte';
	let { data, children }: { data: any; children: any } = $props();
</script>

{@render children()}
<ApiDataNote endpoint={'/api/v1/apps/{store_id}/sdks'} />
