SELECT
    sp.company_name,
    sp.company_domain,
    sp.parent_company_domain,
    sp.sdk_name,
    sp.sdk_slug,
    sp.pattern_type,
    sp.pattern_value,
    sp.app_count,
    sp.parent_company_name
FROM
    frontend.companies_sdks_overview AS sp
WHERE
    sp.pattern_value ILIKE :value_pattern || '%'
    OR
    :value_pattern ILIKE sp.pattern_value || '%';
