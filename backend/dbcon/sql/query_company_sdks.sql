SELECT
    cso.company_name,
    cso.sdk_name,
    cso.pattern_type,
    cso.pattern_value,
    cso.parent_company_name,
    cso.app_count
FROM
    frontend.companies_sdks_overview AS cso
WHERE
    cso.company_domain = :company_domain
    OR cso.parent_company_domain = :company_domain
ORDER BY cso.app_count DESC NULLS LAST;
