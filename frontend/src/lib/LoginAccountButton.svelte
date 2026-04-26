<script lang="ts">
	import { page } from '$app/state';
	import { browser } from '$app/environment';
	import UserRound from 'lucide-svelte/icons/user-round';
	import LogIn from 'lucide-svelte/icons/log-in';

	// Access user from page data (set by root +layout.server.ts)
	let user = $derived(page.data.user);
</script>

{#if browser}
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
			href="/account"
			class="btn preset-tonal-primary inline-flex items-center gap-2 p-2"
			title="Login"
		>
			<span class="text-xs md:text-sm font-bold flex items-center gap-2">
				<LogIn size={18} /> LOGIN</span
			>
		</a>
	{/if}
{/if}
