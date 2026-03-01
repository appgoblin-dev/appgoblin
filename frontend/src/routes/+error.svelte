<script lang="ts">
	import { page } from '$app/state';
</script>

<div class="min-h-screen flex items-center justify-center p-6">
	<div class="max-w-2xl w-full text-center">
		<h1 class="text-4xl font-bold text-error-800-200 mb-4">
			{page.status}
		</h1>

		<h2 class="text-2xl font-semibold mb-6">
			{page.error?.message || 'An unexpected error occurred'}
		</h2>

		{#if page.status === 404}
			<p class="mt-4 text-base text-surface-600-400">
				The page you're looking for could not be found.
			</p>
		{:else if page.status === 503}
			<p class="mt-4 text-base text-surface-600-400">
				The service is temporarily unavailable. The backend may be restarting or experiencing high
				load.
			</p>
			<p class="mt-2 text-sm text-surface-500-400">Please try again in a few moments.</p>
		{:else if page.status === 504}
			<p class="mt-4 text-base text-surface-600-400">
				The request timed out. The backend may be processing a large request or experiencing issues.
			</p>
			<p class="mt-2 text-sm text-surface-500-400">
				Please try again or contact support if the problem persists.
			</p>
		{:else if page.status === 500}
			<p class="mt-4 text-base text-surface-600-400">An internal server error occurred.</p>
			<p class="mt-2 text-base text-surface-600-400">
				Please try again later or contact support if the problem persists.
			</p>
		{:else if page.status >= 400 && page.status < 500}
			<p class="mt-4 text-base text-surface-600-400">There was a problem with your request.</p>
		{:else}
			<p class="mt-4 text-base text-surface-600-400">
				Something went wrong. Please try again later.
			</p>
		{/if}
		<div class="mt-8 text-sm text-surface-500-400">
			<p>Need help? Reach out on:</p>
			<div class="flex gap-4 justify-center mt-2">
				<a href="mailto:support@appgoblin.info" class="link">Email</a>
				<span>•</span>
				<a href="https://github.com/appgoblin-dev/appgoblin" class="link">GitHub</a>
				<span>•</span>
				<a href="https://discord.gg/7jpWEhkXRW" class="link">Discord</a>
			</div>
		</div>
		<div class="mt-8 flex gap-4 justify-center">
			<a href="/" class="btn variant-filled-primary"> Back to Homepage </a>
			<button onclick={() => window.history.back()} class="btn variant-soft"> Go Back </button>
		</div>
	</div>
</div>
