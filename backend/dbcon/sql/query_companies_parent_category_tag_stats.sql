SELECT
    company_domain,
    store,
    app_category,
    tag_source,
    COALESCE(company_name, company_domain) AS company_name,
    COALESCE(SUM(app_count), 0) AS app_count,
    COALESCE(SUM(installs_d30), 0) AS installs_d30
FROM
    frontend.companies_parent_category_tag_stats
WHERE
    app_category LIKE :app_category
GROUP BY company_domain, company_name, store, app_category, tag_source;
