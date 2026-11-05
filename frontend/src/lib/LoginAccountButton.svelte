<script lang="ts">
	import { page } from '$app/state';
	import { browser } from '$app/env';
	import { goto, invalidate } from '$app/navigation';
	import UserRound from '@lucide/svelte/icons/user-round';
	import LogIn from '@lucide/svelte/icons/log-in';

	type LiveUser = { id: number; username: string; emailVerified: boolean };

	let liveUser = $state<LiveUser | null | undefined>(undefined);
	let authChecked = $state(false);
	let retriedUrl: string | null = null;
	let lastInvalidation: string | null = null;
	let previousPath: string | null = null;
	let user = $derived(liveUser !== undefined ? liveUser : page.data.user);
	let loginHref = $derived(
		browser
			? `/auth/signup?redirectTo=${encodeURIComponent(page.url.pathname + page.url.search)}`
			: '/auth/signup'
	);

	$effect(() => {
		const pathname = page.url.pathname;
		if (pathname !== previousPath) {
			previousPath = pathname;
			retriedUrl = null;
			lastInvalidation = null;
		}
		const controller = new AbortController();
		const timeout = setTimeout(() => {
			controller.abort();
			authChecked = true;
		}, 5000);

		fetch('/auth/me', {
			credentials: 'same-origin',
			cache: 'no-store',
			signal: controller.signal
		})
			.then((res) => (res.ok ? res.json() : null))
			.then((data: { user: LiveUser | null } | null) => {
				if (controller.signal.aborted) return;
				authChecked = true;
				if (!data) return;
				liveUser = data.user;
				const url = page.url.href;
				if (page.status === 401 && data.user && retriedUrl !== url) {
					retriedUrl = url;
					// The URL is the current page, not a route ID.
					// eslint-disable-next-line svelte/no-navigation-without-resolve
					void goto(new URL(url), { refreshAll: true, replace: true }).catch(() => {});
				} else if (page.status !== 401) {
					const mismatch =
						data.user?.id !== page.data.user?.id ||
						data.user?.emailVerified !== page.data.user?.emailVerified;
					const key = JSON.stringify([url, data.user?.id, data.user?.emailVerified]);
					// Prerendered layouts cannot be updated by invalidation.
					if (mismatch && key !== lastInvalidation) {
						lastInvalidation = key;
						void invalidate('app:user').catch(() => {});
					} else if (!mismatch) {
						lastInvalidation = null;
					}
				}
			})
			.catch(() => {
				if (!controller.signal.aborted) authChecked = true;
			})
			.finally(() => clearTimeout(timeout));

		return () => {
			clearTimeout(timeout);
			controller.abort();
		};
	});
</script>

{#if user}
	<a
		href="/account"
		class="btn preset-tonal p-1.5 md:p-2 flex items-center gap-1 md:gap-2"
		title={user ? `Account: ${user.username}` : 'Login'}
	>
		<UserRound size={20} class="" />
		<span class="hidden lg:inline text-sm">{user.username}</span>
	</a>
{:else}
	<a
		href={loginHref}
		class:auth-pending={!authChecked}
		class="btn preset-tonal-primary inline-flex items-center gap-2 p-2"
		title="Login"
	>
		<span class="text-xs md:text-sm font-bold flex items-center gap-2">
			<LogIn size={18} /> LOGIN</span
		>
	</a>
{/if}

<style>
	@media (scripting: enabled) {
		.auth-pending {
			visibility: hidden;
		}
	}
</style>
