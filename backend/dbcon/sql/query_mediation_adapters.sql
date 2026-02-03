SELECT
    adapter_company_name,
    adapter_logo_url,
    app_category,
    app_count,
    COALESCE(adapter_company_domain, adapter_string) AS adapter_company_domain
FROM frontend.mediation_adapter_app_counts
WHERE mediation_company_domain = :company_domain;
