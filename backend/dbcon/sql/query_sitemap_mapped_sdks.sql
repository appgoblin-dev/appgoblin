SELECT DISTINCT
    sdk_slug
FROM frontend.companies_sdks_overview
WHERE
    sdk_slug IS NOT NULL
    AND BTRIM(sdk_slug) <> ''
ORDER BY sdk_slug;
