<script lang="ts">
	let { data } = $props();

	let title = 'Blog | AppGoblin Latest News';
	const description =
		'Latest news and updates from the AppGoblin team. Grow your app with free ASO tools and analytics from AppGoblin.';
	const keywords =
		'blog, appgoblin, aso, app store optimization, app marketing, app growth, monetization, reports, analysis, sdks, competitor analysis';

	// Get the most recent post (first in the sorted array)
	const featuredPost = $derived(data.posts[0]);
	// Get the remaining posts
	const otherPosts = $derived(data.posts.slice(1));
</script>

<svelte:head>
	<title>{title}</title>
	<link rel="canonical" href="https://appgoblin.info/blog" />
	<meta property="og:title" content={title} />
	<meta name="twitter:title" content={title} />
	<meta name="description" content={description} />
	<meta name="keywords" content={keywords} />
	<meta property="og:description" content={description} />
	<meta name="twitter:description" content={description} />
	{@html `<script type="application/ld+json">${data.structuredData}</script>`}
</svelte:head>

<div class="container mx-auto px-4 py-8">
	<!-- Header Section -->
	<div class="text-center mb-12">
		<h1 class="text-4xl font-bold text-base-content mb-4">AppGoblin Blog</h1>
		<p class="text-lg text-base-content/70 max-w-2xl mx-auto">
			Latest insights, updates, and strategies for mobile app marketing and ASO. Stay ahead with
			free tools and expert analysis from the AppGoblin team.
		</p>
	</div>

	<!-- Featured Post and Other Posts Section -->
	<div class="mb-16">
		<div class="grid lg:grid-cols-3 gap-8">
			<!-- Featured Post -->
			<div class="lg:col-span-2">
				<article class="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow duration-300">
					<div class="card-body p-0">
						<!-- Featured Post Image -->
						{#if featuredPost.heroImage}
							<figure class="overflow-hidden">
								<a
									href={featuredPost.relativeURL}
									class="hover:text-primary transition-colors duration-200"
								>
									<img
										class="w-full h-64 object-cover border border-base-300"
										src={featuredPost.heroImage}
										alt={featuredPost.title}
										loading="eager"
									/>
								</a>
							</figure>
						{/if}

						<!-- Featured Post Content -->
						<div class="p-8">
							<div class="mb-4 text-sm">
								Latest Post <time datetime={featuredPost.pubDate.toISOString()}>
									{featuredPost.pubDate.toLocaleDateString('en-us', {
										year: 'numeric',
										month: 'long',
										day: 'numeric'
									})}
								</time>
							</div>

							<h2 class="text-2xl md:text-3xl font-bold text-base-content mb-4 leading-tight">
								<a
									href={featuredPost.relativeURL}
									class="hover:text-primary transition-colors duration-200"
								>
									{featuredPost.title}
								</a>
							</h2>

							<p class="text-base-content/70 mb-6 leading-relaxed">
								{featuredPost.description}
							</p>

							<a href={featuredPost.relativeURL} class="btn btn-primary w-fit">
								Read More
								<svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M9 5l7 7-7 7"
									></path>
								</svg>
							</a>
						</div>
					</div>
				</article>
			</div>

			<!-- Other Posts Sidebar -->
			<div class="lg:col-span-1">
				<h3 class="text-xl font-semibold text-base-content mb-6">More Posts</h3>
				<div class="space-y-6">
					{#each otherPosts.slice(0, 3) as post (post.id)}
						<article
							class="card bg-base-100 shadow-sm hover:shadow-md transition-shadow duration-300 group"
						>
							<div class="card-body p-0">
								<!-- Post Image -->
								{#if post.heroImage}
									<figure class="overflow-hidden">
										<a
											href={post.relativeURL}
											class="hover:text-primary transition-colors duration-200"
										>
											<img
												class="w-full h-32 object-cover group-hover:scale-105 transition-transform duration-300 border border-base-300"
												src={post.heroImage}
												alt={post.title}
												loading="lazy"
											/>
										</a>
									</figure>
								{/if}

								<!-- Post Content -->
								<div class="p-4">
									<div class="mb-2">
										<time
											class="text-xs text-primary font-medium"
											datetime={post.pubDate.toISOString()}
										>
											{post.pubDate.toLocaleDateString('en-us', {
												year: 'numeric',
												month: 'short',
												day: 'numeric'
											})}
										</time>
									</div>

									<h4 class="text-base font-semibold text-base-content mb-2 leading-tight">
										<a
											href={post.relativeURL}
											class="hover:text-primary transition-colors duration-200"
										>
											{post.title}
										</a>
									</h4>

									<p class="text-base-content/70 text-xs leading-relaxed mb-3 line-clamp-2">
										{post.description}
									</p>

									<a
										href={post.relativeURL}
										class="text-primary hover:text-primary/80 font-medium text-xs inline-flex items-center transition-colors duration-200"
									>
										Read More
										<svg class="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M9 5l7 7-7 7"
											></path>
										</svg>
									</a>
								</div>
							</div>
						</article>
					{/each}
				</div>
			</div>
		</div>
	</div>

	<!-- Remaining Posts Section -->
	<div>
		<div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
			{#each otherPosts.slice(3) as post (post.id)}
				<article
					class="card bg-base-100 shadow-sm hover:shadow-md transition-shadow duration-300 group"
				>
					<div class="card-body p-0">
						<!-- Post Image -->
						{#if post.heroImage}
							<figure class="overflow-hidden">
								<a
									href={post.relativeURL}
									class="hover:text-primary transition-colors duration-200"
								>
									<img
										class="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300 border border-base-300"
										src={post.heroImage}
										alt={post.title}
										loading="lazy"
									/>
								</a>
							</figure>
						{/if}

						<!-- Post Content -->
						<div class="p-6">
							<div class="mb-3">
								<time
									class="text-sm text-primary font-medium"
									datetime={post.pubDate.toISOString()}
								>
									{post.pubDate.toLocaleDateString('en-us', {
										year: 'numeric',
										month: 'short',
										day: 'numeric'
									})}
								</time>
							</div>

							<h3 class="text-lg font-semibold text-base-content mb-3 leading-tight">
								<a
									href={post.relativeURL}
									class="hover:text-primary transition-colors duration-200"
								>
									{post.title}
								</a>
							</h3>

							<p class="text-base-content/70 text-sm leading-relaxed mb-4">
								{post.description}
							</p>

							<a
								href={post.relativeURL}
								class="text-primary hover:text-primary/80 font-medium text-sm inline-flex items-center transition-colors duration-200"
							>
								Read More
								<svg class="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M9 5l7 7-7 7"
									></path>
								</svg>
							</a>
						</div>
					</div>
				</article>
			{/each}
		</div>
	</div>
</div>
