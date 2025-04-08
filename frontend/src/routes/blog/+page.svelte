<script>
	import PostsList from '$lib/blog/PostsList.svelte';
	import Pagination from '$lib/blog/Pagination.svelte';
	import { siteDescription } from '$lib/blog/config';

	let { data } = $props();
</script>

<svelte:head>
	<title>AppGoblin Blog</title>
	<meta data-key="description" name="description" content={siteDescription} />
</svelte:head>

<h1 class="h1">AppGoblin Blog</h1>

<PostsList posts={data.posts} />

<Pagination currentPage={1} totalPosts={data.total} />
