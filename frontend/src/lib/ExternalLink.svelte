<script lang="ts">
	import ExternalLinkSvg from './svg/ExternalLinkSVG.svelte';
	interface Props {
		domain: string;
	}

	let { domain }: Props = $props();

	function replace_domain_parts(domain: string) {
		return domain.replace('github.com-', 'github.com/');
	}
</script>

<a
	href={`https://${replace_domain_parts(domain)}`}
	target="_blank"
	rel="noopener noreferrer"
	class="flex items-center"
>
	<span class="inline-flex items-center gap-1 text-tertiary-400-600 hover:">
		{replace_domain_parts(domain)}
		<ExternalLinkSvg />
	</span>
</a>
