<script lang="ts">
	import { enhance } from '$app/forms';

	import type { ActionData, PageData } from './$types';

	export let data: PageData;
	export let form: ActionData;
</script>

<h2 class="text-2xl font-bold">Create a free account</h2>
<p>New to AppGoblin? Create a free account to get started.</p>
<a class="btn preset-filled" href="/auth/signup"
	><span class="text-black font-semibold">Create AppGoblin Account</span></a
>
<br />
<form class="space-y-2" method="post" use:enhance>
	{#if data.redirectTo}
		<input type="hidden" name="redirectTo" value={data.redirectTo} />
	{/if}
	<h2 class="text-2xl font-bold">Already have an account? Sign In</h2>
	<label class="label" for="form-login.email">Email</label>
	<input
		class="input"
		type="email"
		id="form-login.email"
		name="email"
		autocomplete="username"
		required
		value={form?.email ?? ''}
	/><br />
	<label class="label" for="form-login.password">Password</label>
	<input
		class="input"
		type="password"
		id="form-login.password"
		name="password"
		autocomplete="current-password"
		required
	/><br />
	<button class="btn preset-filled">Sign In</button>
	<a class="btn preset-tonal" href="/auth/forgot-password">Forgot password?</a>
	<p>{form?.message ?? ''}</p>
</form>
