SELECT
    store,
    tag_source,
    company_domain,
    COALESCE(company_name, company_domain) AS company_name,
    SUM(app_count) AS app_count,
    SUM(installs_d30) AS installs_d30
FROM
    frontend.companies_category_tag_type_stats
WHERE
    type_url_slug = :type_slug
GROUP BY
    store,
    tag_source,
    company_domain,
    COALESCE(company_name, company_domain);
