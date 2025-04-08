<!-- Renders any page at /blog/category/* -->
<script>
	import PostsList from '$lib/blog/PostsList.svelte';
	import Pagination from '$lib/blog/Pagination.svelte';
	import { postsPerPage } from '$lib/blog/config';

	let { data } = $props();

	const { page, posts, category, total } = data;

	let lowerBound = $derived(page * postsPerPage - (postsPerPage - 1) || 1);
	let upperBound = $derived(Math.min(page * postsPerPage, total));
</script>

<svelte:head>
	<title>Category: {category}</title>
</svelte:head>

<h1>Blog category: {category}</h1>

{#if posts.length}
	<PostsList {posts} />
	<Pagination currentPage={page} totalPosts={total} path="/blog/category/{category}/page" />
{:else}
	<p><strong>Ope!</strong> Sorry, couldn't find any posts in the category "{category}".</p>

	<p><a href="/blog">Back to blog</a></p>
{/if}
