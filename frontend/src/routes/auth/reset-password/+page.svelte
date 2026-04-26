<script lang="ts">
	import { enhance } from '$app/forms';

	import type { ActionData } from './$types';

	export let form: ActionData;
</script>

<div>
	<h2 class="text-2xl font-bold">Enter your new password</h2>
	<form method="post" use:enhance>
		<label class="label" for="form-reset.password">Password</label>
		<input
			class="input"
			type="password"
			id="form-reset.password"
			name="password"
			autocomplete="new-password"
			required
		/><br />
		<button class="btn preset-filled">Reset password</button>
		<p>{form?.message ?? ''}</p>
	</form>
</div>
