export type PlanSummary = {
	name: string;
	limits: string;
	description: string;
};

const FREE_PLAN: PlanSummary = {
	name: 'Free',
	limits: '60 req/min, 1,000 req/day, 10,000 req/month',
	description: 'Basic account access, saved watchlists, and low-volume API exploration.'
};

const PLAN_SUMMARIES: Record<string, PlanSummary> = {
	'Premium Access': {
		name: 'Premium Access',
		limits: '100 req/min, 10,000 req/day',
		description:
			'Higher API throughput for individual research, integrations, and reporting workflows.'
	},
	'Business SDK': {
		name: 'Business SDK',
		limits: '100 req/min, 50,000 req/day, 1 million req/month',
		description: 'Expanded API access sized for SDK intelligence, internal tooling, and team usage.'
	},
	'App-Ads.txt': {
		name: 'App-Ads.txt',
		limits: '100 req/min, 50,000 req/day, 1 million req/month',
		description:
			'Expanded API access for app-ads.txt analysis, automation, and recurring reporting.'
	},
	'Premium B2B': {
		name: 'Premium B2B',
		limits: '150 req/min, 100,000 req/day, 5 million req/month',
		description: 'Highest throughput for team-wide SDK, API, and app-ads.txt analysis pipelines.'
	}
};

export function getPlanSummary(subscriptionTier: string | null | undefined): PlanSummary {
	if (!subscriptionTier) {
		return FREE_PLAN;
	}

	return (
		PLAN_SUMMARIES[subscriptionTier] ?? {
			name: subscriptionTier,
			limits: FREE_PLAN.limits,
			description: 'Active subscription with account access and API usage enabled.'
		}
	);
}
