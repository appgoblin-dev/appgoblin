SELECT
    ad_domain AS company_domain,
    company_id,
    parent_id,
    year,
    quarter,
    store,
    tag_source,
    COALESCE(total_apps, 0) AS total_apps,
    COALESCE(total_apps_in_quarter, 0) AS total_apps_in_quarter,
    COALESCE(apps_lost, 0) AS apps_lost,
    COALESCE(apps_added, 0) AS apps_added,
    pct_market_share,
    pct_apps_added,
    pct_apps_lost
FROM adtech.combined_companies_history
WHERE ad_domain = :company_domain
ORDER BY year ASC, quarter ASC, store ASC, tag_source ASC;