SELECT
    company_domain,
    company_name,
    logo_url,
    has_api_signal,
    has_sdk_signal,
    has_publisher_signal,
    has_app_ads_direct,
    has_app_ads_reseller
FROM frontend.companies_overview
WHERE
    company_name ILIKE '%' || :searchinput || '%'
    OR company_domain ILIKE '%' || :searchinput || '%'
ORDER BY
    CASE WHEN company_name IS NOT NULL THEN 3 ELSE 0 END
    + CASE WHEN
        has_api_signal THEN 2 ELSE 0 END
    + CASE WHEN has_sdk_signal THEN 2 ELSE 0 END
    + CASE WHEN has_publisher_signal THEN 1 ELSE 0 END
    + CASE WHEN has_app_ads_direct THEN 1 ELSE 0 END
    + CASE WHEN has_app_ads_reseller THEN 1 ELSE 0 END
    DESC
LIMIT :mylimit;
