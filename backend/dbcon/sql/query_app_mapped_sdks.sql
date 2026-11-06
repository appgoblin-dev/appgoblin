SELECT DISTINCT
    cso.company_domain,
    cso.sdk_slug
FROM frontend.store_apps_overview AS sa
INNER JOIN adtech.app_sdks AS asd
    ON sa.id = asd.store_app
INNER JOIN frontend.companies_sdks_overview AS cso
    ON asd.sdk_id = cso.sdk_id
WHERE
    sa.store_id = :store_id
    AND cso.company_domain IS NOT NULL
    AND cso.sdk_slug IS NOT NULL
ORDER BY cso.company_domain, cso.sdk_slug;
