import { randomUUID } from 'node:crypto';

const UMAMI_ENDPOINT = 'https://caz.appgoblin.info/api/send';
const UMAMI_WEBSITE_ID = '3a063390-a9d5-4743-af11-e7ef3fc10cb3';
const MAX_IN_FLIGHT = 50;
let inFlight = 0;

type FailureStage =
	| 'configuration'
	| 'initialization'
	| 'verification'
	| 'handler'
	| 'settlement'
	| 'stripe_recording';
type StripeRecording = 'recorded' | 'disabled' | 'failed';

export function createX402Analytics(request: Request, resource: string) {
	const signature = request.headers.has('payment-signature')
		? 'payment-signature'
		: request.headers.has('x-payment')
			? 'x-payment'
			: null;
	const url = new URL(request.url);
	if (!signature || url.hostname !== 'appgoblin.info') return null;

	const attemptId = randomUUID();
	const path = url.pathname;
	function send(name: string, data: Record<string, string>) {
		if (inFlight >= MAX_IN_FLIGHT) return;
		inFlight++;
		void Promise.resolve()
			.then(() =>
				fetch(UMAMI_ENDPOINT, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json', 'User-Agent': 'AppGoblin-x402/1.0' },
					body: JSON.stringify({
						type: 'event',
						payload: {
							website: UMAMI_WEBSITE_ID,
							hostname: 'appgoblin.info',
							url: path,
							name,
							data: { attempt_id: attemptId, resource, signature_header: signature, ...data }
						}
					}),
					signal: AbortSignal.timeout(3000)
				})
			)
			.catch(() => {})
			.finally(() => {
				inFlight--;
			});
	}

	return {
		attempt: () => send('x402-attempt', {}),
		settled: (stripeRecording: StripeRecording) =>
			send('x402-settled', { stripe_recording: stripeRecording }),
		failed: (stage: FailureStage) => send('x402-failed', { stage })
	};
}
