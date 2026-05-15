SELECT
    company_domain,
    company_name,
    company_domain AS parent_company_domain,
    company_name AS parent_company_name,
    store,
    'all' AS app_category,
    tag_source,
    COALESCE(SUM(app_count), 0) AS app_count,
    COALESCE(SUM(installs_d30), 0) AS installs_d30
FROM
    frontend.companies_parent_category_tag_stats
WHERE
    store IN (1, 2)
GROUP BY company_domain, company_name, store, tag_source;
