<script lang="ts">
	import LogIn from 'lucide-svelte/icons/log-in';
	type FollowEntity = 'app' | 'company';

	let {
		entity,
		label,
		initialFollowing = false,
		storeId,
		companyId,
		compact = false,
		fullWidth = false
	}: {
		entity: FollowEntity;
		label: string;
		initialFollowing?: boolean;
		storeId?: string;
		companyId?: number;
		compact?: boolean;
		fullWidth?: boolean;
	} = $props();

	let following = $state(false);
	let isLoading = $state(false);
	let message = $state('');

	$effect(() => {
		following = initialFollowing;
	});

	async function toggleFollow() {
		if (isLoading) return;
		isLoading = true;
		message = '';

		try {
			const response = await fetch('/api/follows', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					entity,
					follow: !following,
					storeId,
					companyId
				})
			});

			if (response.ok) {
				following = !following;
			} else if (response.status === 401) {
				message = 'Sign in to use follow tracking.';
			} else {
				message = 'Failed to update follow state.';
			}
		} catch {
			message = 'Failed to update follow state.';
		} finally {
			isLoading = false;
		}
	}
</script>

<div class="space-y-1">
	<button
		type="button"
		class={`btn ${following ? 'preset-tonal-secondary-outlined' : 'preset-tonal-secondary'} ${compact ? 'btn-sm' : ''} ${fullWidth ? 'w-full justify-center' : ''}`}
		onclick={toggleFollow}
		disabled={isLoading}
	>
		{#if isLoading}
			Saving...
		{:else if following}
			Following {label}
		{:else}
			<LogIn class="h-3.5 w-3.5" aria-hidden="true" /> Follow {label}
		{/if}
	</button>
	{#if message}
		<p class="text-xs text-warning-600">{message}</p>
	{/if}
</div>
