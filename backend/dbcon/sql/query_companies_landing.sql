WITH companies AS (
    SELECT *
    FROM frontend.companies_overview
    WHERE company_domain IS NOT NULL AND company_domain NOT LIKE 'no-%'
), country_counts AS (
    SELECT country, COUNT(*) AS company_count
    FROM companies
    WHERE country IS NOT NULL AND TRIM(country) != ''
    GROUP BY country
    ORDER BY company_count DESC, country
    LIMIT 10
), listed AS (
    SELECT company_domain, company_name, tickers_direct, company_tickers
    FROM companies
    WHERE COALESCE(CARDINALITY(tickers_direct), 0) > 0
       OR COALESCE(CARDINALITY(company_tickers), 0) > 0
    ORDER BY company_name NULLS LAST, company_domain
    LIMIT 12
)
SELECT
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE has_api_signal) AS api,
    COUNT(*) FILTER (WHERE sdk_count > 0) AS sdk,
    COUNT(*) FILTER (WHERE has_app_ads_direct OR has_app_ads_reseller) AS app_ads,
    COUNT(*) FILTER (WHERE has_publisher_signal) AS publishers,
    COUNT(*) FILTER (
        WHERE COALESCE(CARDINALITY(tickers_direct), 0) > 0
           OR COALESCE(CARDINALITY(company_tickers), 0) > 0
    ) AS listed,
    COALESCE((SELECT JSON_AGG(country_counts) FROM country_counts), '[]'::json) AS countries,
    COALESCE((SELECT JSON_AGG(listed) FROM listed), '[]'::json) AS listed_companies
FROM companies;
