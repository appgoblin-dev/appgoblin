import { defineEnvVars } from '@sveltejs/kit/env';

export const variables = defineEnvVars({
	STRIPE_WEBHOOK_SECRET: { static: true },
	STRIPE_PRICE_B2B_SDK_SEAT_MO: { static: true },
	STRIPE_PRICE_B2B_SDK_SEAT_YR: { static: true },
	STRIPE_PRICE_B2B_PREMIUM_SEAT_MO: { static: true },
	STRIPE_PRICE_B2B_PREMIUM_SEAT_YR: { static: true },
	ALTCHA_HMAC_SECRET: { static: true },
	APPGOBLIN_ENDPOINT_URL: { static: true },
	EMAIL_HOST: { static: true },
	EMAIL_PORT: { static: true },
	EMAIL_USER: { static: true },
	EMAIL_PASSWORD: { static: true },
	APPGOBLIN_DOWNLOADS_BASE: { static: true },
	STRIPE_SECRET_KEY: { static: true },
	STRIPE_PROFILE_ID: { static: true },
	STRIPE_TEMPO_DEPOSIT_ADDRESS: { static: true },
	PGHOST: { static: true },
	PGPORT: { static: true },
	PGDATABASE: { static: true },
	PGUSER: { static: true },
	PGPASSWORD: { static: true },
	ENCRYPTION_KEY: { static: true }
});
