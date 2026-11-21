import type { CompanyTabIndicators } from '../../types';

export function companySectionHasData(
	slug: string,
	tabIndicators: CompanyTabIndicators | null | undefined,
	mediationPartnerCount: number | null | undefined = null
): boolean {
	if (slug === 'mediation-partners') return (mediationPartnerCount ?? 0) > 0;
	if (!tabIndicators)
		return slug === 'overview' || slug === 'data-exports' || slug === 'app-adstxt';
	switch (slug) {
		case 'overview':
			return true;
		case 'api-apps':
			return Boolean(tabIndicators.has_api_signal);
		case 'creatives':
			return Boolean(tabIndicators.creatives_app_count);
		case 'trends':
			return Boolean(tabIndicators.has_trends);
		case 'apps-added':
			return Boolean(tabIndicators.apps_sdk_added_count);
		case 'apps-lost':
			return Boolean(tabIndicators.apps_sdk_lost_count);
		case 'apps-added-adstxt':
			return Boolean(tabIndicators.apps_adstxt_direct_added_count);
		case 'apps-lost-adstxt':
			return Boolean(tabIndicators.apps_adstxt_direct_lost_count);
		case 'sdks':
			return Boolean(tabIndicators.sdk_count);
		case 'mediation':
			return Boolean(tabIndicators.mediation_adapter_count);
		case 'app-adstxt':
			return Boolean(
				tabIndicators.adstxt_direct_app_count || tabIndicators.adstxt_parent_app_count
			);
		case 'data-exports':
			return Boolean(
				tabIndicators.has_api_signal ||
				tabIndicators.adstxt_direct_app_count ||
				tabIndicators.adstxt_parent_app_count ||
				tabIndicators.sdk_count
			);
		default:
			return true;
	}
}
