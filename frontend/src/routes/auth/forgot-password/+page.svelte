<script lang="ts">
	import { enhance } from '$app/forms';

	import type { ActionData } from './$types';

	export let form: ActionData;
</script>

<div class="p-6 md:p-8 space-y-6">
	<h2 class="text-2xl font-bold">Forgot your password?</h2>
	<p class="text-sm text-surface-500">
		Please enter your email address and we will send you a link to reset your password. If you
		encounter issues, please contact support.
	</p>
	<form method="post" use:enhance>
		<label for="label form-forgot.email">Email</label>
		<input
			class="input"
			type="email"
			id="form-forgot.email"
			name="email"
			required
			value={form?.email ?? ''}
		/><br />
		<button class="btn preset-filled">Send</button>
		<p>{form?.message ?? ''}</p>
	</form>
	<a class="btn preset-tonal" href="/login">Sign in</a>
</div>
