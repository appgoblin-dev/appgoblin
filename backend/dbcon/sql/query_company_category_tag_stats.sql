SELECT
    company_domain,
    company_name,
    store,
    tag_source,
    app_category,
    COALESCE(app_count, 0) AS app_count,
    COALESCE(installs_total, 0) AS installs_total,
    COALESCE(installs_d30, 0) AS installs_d30
FROM
    frontend.companies_category_tag_stats
WHERE
    company_domain = :company_domain
    AND (app_category LIKE :app_category OR :app_category IS NULL);
