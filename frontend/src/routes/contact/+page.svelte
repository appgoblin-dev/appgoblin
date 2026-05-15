<script>
	const channels = [
		{
			label: 'Email',
			description: 'Questions, demos, and general enquiries',
			href: 'mailto:contact@appgoblin.info',
			url: 'contact@appgoblin.info'
		},
		{
			label: 'GitHub',
			description: 'Report technical issues or request features',
			href: 'https://github.com/appgoblin-dev/appgoblin/issues',
			url: 'https://github.com/appgoblin-dev/appgoblin/issues'
		},
		{
			label: 'LinkedIn',
			description: 'Follow for regular updates',
			href: 'https://linkedin.com/company/AppGoblin',
			url: 'https://linkedin.com/company/AppGoblin'
		},
		{
			label: 'Discord',
			description: 'Community discussions, ASO, app marketing and ad tech',
			href: 'https://discord.gg/7jpWEhkXRW',
			url: 'https://discord.gg/7jpWEhkXRW'
		}
	];
</script>

<svelte:head>
	<title>Contact AppGoblin</title>
	<meta
		name="description"
		content="Get in touch with AppGoblin via email, GitHub, LinkedIn, or Discord. Ask questions, report issues, request features, or join the community."
	/>
	<meta property="og:title" content="Contact AppGoblin" />
	<meta property="og:description" content="Reach out via email, GitHub, LinkedIn, or Discord." />
	<meta property="og:image" content="https://appgoblin.info/goblin_purple_hat_250.png" />
	<meta property="og:url" content="https://appgoblin.info/contact" />
	<meta property="og:type" content="website" />
	<meta name="robots" content="index, follow" />
	<link rel="canonical" href="https://appgoblin.info/contact" />
</svelte:head>

<div class="mx-auto max-w-2xl px-4 py-6">
	<h1 class="text-3xl font-bold">Contact</h1>
	<p class="mt-3">Reach out through any channel you prefer.</p>

	<div class="mt-6 space-y-5">
		{#each channels as channel}
			<p>
				<strong>{channel.label}:</strong>
				{channel.description}<br />
				<a
					href={channel.href}
					target={channel.href.startsWith('http') ? '_blank' : undefined}
					rel={channel.href.startsWith('http') ? 'noreferrer' : undefined}
					class="underline break-all"
				>
					{channel.url}
				</a>
			</p>
		{/each}
	</div>
</div>
