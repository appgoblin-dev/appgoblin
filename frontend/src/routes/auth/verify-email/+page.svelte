<script lang="ts">
	import { enhance } from '$app/forms';

	import type { ActionData, PageData } from './$types';

	let { data, form }: { data: PageData; form: ActionData } = $props();

	const verificationEmailsRemaining = $derived(
		form?.resend?.verificationEmailsRemaining ??
			form?.verify?.verificationEmailsRemaining ??
			data.verificationEmailsRemaining
	);
	const highlightSpamNotice = $derived(
		form?.resend?.highlightSpamNotice ??
			form?.verify?.highlightSpamNotice ??
			data.highlightSpamNotice
	);
</script>

<h2 class="text-2xl font-bold">Verify your email address</h2>
<p>We sent an 8-digit code to {data.email}.</p>
{#if highlightSpamNotice}
	<div
		class="mt-4 rounded border border-warning-500/40 bg-warning-500/10 p-4 text-base font-semibold leading-6"
	>
		AppGoblin sends verification emails through an independent provider. Please check spam or junk
		for the latest message before requesting another email.
	</div>
{:else}
	<p class="mt-2 text-sm text-surface-600-400">
		AppGoblin sends verification emails through an independent provider, so please check spam or
		junk if you do not see the code.
	</p>
{/if}
{#if data.notice}
	<div
		class="mt-4 rounded border border-error-500/30 bg-error-500/10 p-3 text-sm font-medium text-error-600"
	>
		{data.notice}
	</div>
{/if}
<form class="space-y-1" method="post" use:enhance action="?/verify">
	<label class="label" for="form-verify.code">Code</label>
	<input class="input" id="form-verify.code" name="code" required />
	<button class="btn preset-filled">Verify</button>
	<p>{form?.verify?.message ?? ''}</p>
</form>
<form method="post" use:enhance action="?/resend">
	<button class="btn preset-tonal" disabled={verificationEmailsRemaining === 0}>Resend code</button>
	<p class="mt-2 text-sm text-surface-600-400">
		You can request {verificationEmailsRemaining} more verification email{verificationEmailsRemaining ===
		1
			? ''
			: 's'}.
	</p>
	<p>{form?.resend?.message ?? ''}</p>
</form>
<a class="btn preset-tonal" href="/auth/settings">Change email</a>
