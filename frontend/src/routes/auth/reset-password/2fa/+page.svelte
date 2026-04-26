<script lang="ts">
	import { enhance } from '$app/forms';

	import type { ActionData } from './$types';

	export let form: ActionData;
</script>

<div>
	<h2 class="text-2xl font-bold">Two-factor authentication</h2>
	<p class="text-sm text-surface-500">Enter the code from your authenticator app.</p>
	<form method="post" use:enhance action="?/totp">
		<label class="label" for="form-totp.code">Code</label>
		<input class="input" id="form-totp.code" name="code" required /><br />
		<button class="btn preset-filled">Verify</button>
		<p>{form?.totp?.message ?? ''}</p>
	</form>
	<section>
		<h2 class="text-lg font-bold">Use your recovery code instead</h2>
		<form method="post" use:enhance action="?/recovery_code">
			<label class="label" for="form-recovery-code.code">Recovery code</label>
			<input class="input" id="form-recovery-code.code" name="code" required /><br />
			<button class="btn preset-filled">Verify</button>
			<p>{form?.recoveryCode?.message ?? ''}</p>
		</form>
	</section>
</div>
