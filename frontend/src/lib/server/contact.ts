import nodemailer from 'nodemailer';
import {
	APPGOBLIN_ENDPOINT_URL,
	EMAIL_HOST,
	EMAIL_PORT,
	EMAIL_USER,
	EMAIL_PASSWORD
} from '$app/env/private';
import { STRIPE_PLAN_LABELS, type BillingCycle, type StripePriceKey } from '#lib/plans.js';

let transporter: ReturnType<typeof nodemailer.createTransport> | null = null;

function getTransporter() {
	if (transporter) return transporter;

	if (!EMAIL_PASSWORD) {
		if (import.meta.env.DEV) {
			console.warn('EMAIL_PASSWORD not set — contact emails will be logged to console');
			return null;
		}
		throw new Error('EMAIL_PASSWORD environment variable is required in production');
	}

	transporter = nodemailer.createTransport({
		host: EMAIL_HOST,
		port: parseInt(EMAIL_PORT),
		secure: true,
		auth: {
			user: EMAIL_USER,
			pass: EMAIL_PASSWORD
		}
	});

	return transporter;
}

export async function sendContactEmail(
	name: string,
	email: string,
	message: string
): Promise<void> {
	const t = getTransporter();

	const emailLine = email ? `Email: ${email}` : 'No email provided';
	const textBody = `New contact form submission\n\nName: ${name}\n${emailLine}\nMessage:\n${message}`;
	const emailHtml = email
		? `<p><strong>Email:</strong> <a href="mailto:${email}">${email}</a></p>`
		: '<p><em>No email provided</em></p>';
	const htmlBody = `
		<div>
			<h2>New contact form submission</h2>
			<p><strong>Name:</strong> ${name}</p>
			${emailHtml}
			<p><strong>Message:</strong></p>
			<blockquote>${message}</blockquote>
		</div>
	`;

	if (!t) {
		console.log(`[DEV] Contact form: ${name}${email ? ` <${email}>` : ' (no email)'}`);
		console.log(`[DEV] Message: ${message}`);
		return;
	}

	const mailOptions: Record<string, unknown> = {
		from: `"AppGoblin Contact" <${EMAIL_USER}>`,
		to: EMAIL_USER,
		subject: `Contact form: ${name}`,
		text: textBody,
		html: htmlBody
	};
	if (email) {
		mailOptions.replyTo = email;
	}

	await t.sendMail(mailOptions);
}

export async function sendPricingPlanSelectionEmail(
	planKey: StripePriceKey,
	billingCycle: BillingCycle
): Promise<void> {
	const t = getTransporter();
	const planName = STRIPE_PLAN_LABELS[planKey];
	const selectedAt = new Date().toISOString();
	const subject = `Pricing signup started: ${planName}`;
	const text = `A visitor selected the ${planName} plan (${billingCycle} billing) and started the signup flow.\n\nSelected at: ${selectedAt}`;
	const html = `
		<div>
			<h2>New pricing signup started</h2>
			<p><strong>Plan:</strong> ${planName}</p>
			<p><strong>Billing:</strong> ${billingCycle}</p>
			<p><strong>Selected at:</strong> ${selectedAt}</p>
		</div>
	`;

	if (!t) {
		console.log(`[DEV] ${subject} (${billingCycle})`);
		return;
	}

	await t.sendMail({
		from: `"AppGoblin Contact" <${EMAIL_USER}>`,
		to: EMAIL_USER,
		subject,
		text,
		html
	});
}

export async function sendPricingPlanCompletionEmail(
	planKey: StripePriceKey,
	billingCycle: BillingCycle,
	userEmail: string,
	checkoutSessionId: string
): Promise<void> {
	const t = getTransporter();
	const planName = STRIPE_PLAN_LABELS[planKey];
	const completedAt = new Date().toISOString();
	const subject = `Pricing signup completed: ${planName}`;
	const text = [
		`A customer completed signup for the ${planName} plan (${billingCycle} billing).`,
		'',
		`Customer email: ${userEmail}`,
		`Checkout session: ${checkoutSessionId}`,
		`Completed at: ${completedAt}`
	].join('\n');
	const html = `
		<div>
			<h2>Pricing signup completed</h2>
			<p><strong>Plan:</strong> ${planName}</p>
			<p><strong>Billing:</strong> ${billingCycle}</p>
			<p><strong>Customer email:</strong> ${userEmail}</p>
			<p><strong>Checkout session:</strong> ${checkoutSessionId}</p>
			<p><strong>Completed at:</strong> ${completedAt}</p>
		</div>
	`;

	if (!t) {
		console.log(`[DEV] ${subject} (${billingCycle}) for ${userEmail}`);
		return;
	}

	await t.sendMail({
		from: `"AppGoblin Contact" <${EMAIL_USER}>`,
		to: EMAIL_USER,
		subject,
		text,
		html
	});
}

export async function sendOrganizationInvitationEmail(
	email: string,
	organizationName: string,
	invitationToken: string
): Promise<void> {
	const t = getTransporter();
	const signupUrl = `${APPGOBLIN_ENDPOINT_URL}/auth/invitation-signup?token=${encodeURIComponent(invitationToken)}`;
	const subject = `You’re invited to join ${organizationName} on AppGoblin`;
	const text = [
		`You’ve been invited to join an organization: '${organizationName}' on AppGoblin.`,
		'',
		'Confirm or create your AppGoblin account here:',
		signupUrl,
		''
	].join('\n');
	const html = `
		<div>
			<h2>You’re invited to AppGoblin</h2>
			<p>You’ve been invited to join <strong>${organizationName}</strong> on AppGoblin.</p>
			<p><a href="${signupUrl}">Create your AppGoblin account</a></p>
		</div>
	`;

	if (!t) {
		console.log(`[DEV] Organization invitation to ${email}: ${signupUrl}`);
		return;
	}

	await t.sendMail({
		from: `"AppGoblin" <${EMAIL_USER}>`,
		to: email,
		subject,
		text,
		html
	});
}

export async function sendMappingRequestEmail(
	userId: number,
	userEmail: string,
	username: string,
	mapType: string,
	valueToBeMapped: string,
	additionalInfo: Record<string, unknown> | null
): Promise<void> {
	const t = getTransporter();
	const additionalInfoText = additionalInfo ? JSON.stringify(additionalInfo) : 'None';
	const subject = `Mapping request: ${valueToBeMapped}`;
	const text = [
		'A new mapping request was submitted.',
		'',
		`User ID: ${userId}`,
		`Username: ${username}`,
		`User email: ${userEmail}`,
		`Mapping type: ${mapType}`,
		`Value: ${valueToBeMapped}`,
		`Additional info: ${additionalInfoText}`
	].join('\n');
	const html = `
		<div>
			<h2>New mapping request</h2>
			<p><strong>User ID:</strong> ${userId}</p>
			<p><strong>Username:</strong> ${username}</p>
			<p><strong>User email:</strong> ${userEmail}</p>
			<p><strong>Mapping type:</strong> ${mapType}</p>
			<p><strong>Value:</strong> ${valueToBeMapped}</p>
			<p><strong>Additional info:</strong> ${additionalInfoText}</p>
		</div>
	`;

	if (!t) {
		console.log(`[DEV] ${subject}\n${text}`);
		return;
	}

	await t.sendMail({
		from: `"AppGoblin Contact" <${EMAIL_USER}>`,
		to: EMAIL_USER,
		subject,
		text,
		html
	});
}
