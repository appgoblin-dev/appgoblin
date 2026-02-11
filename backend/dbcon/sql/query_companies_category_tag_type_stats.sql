SELECT
    store,
    tag_source,
    company_domain,
    app_category,
    type_url_slug,
    app_count,
    installs_d30,
    COALESCE(company_name, company_domain) AS company_name
FROM
    frontend.companies_category_tag_type_stats
WHERE
    type_url_slug = :type_slug
    AND app_category LIKE :app_category;
