<script>
	let { posts = [] } = $props();
</script>

<ul class="card preset-tonal p-18">
	{#each posts as post}
		<li class="p-8">
			<article>
				<a href="/blog/{post.slug}">
					<img
						src={post.coverImage}
						alt=""
						width={post.coverWidth}
						height={post.coverHeight}
						style="ratio: {post.coverWidth} / {post.coverHeight}"
					/>
					<h4 class="h4 text-primary-900-100">
						{post.title}
					</h4>
					{post.date}
				</a>
			</article>

			<p>{post.excerpt}</p>
		</li>
	{/each}
</ul>
