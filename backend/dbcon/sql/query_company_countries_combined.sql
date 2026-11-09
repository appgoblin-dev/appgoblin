SELECT
    co.company_domain,
    co.country AS hq_country,
    co.tickers_direct,
    co.company_tickers,
    cdc.most_common_country AS api_ip_resolved_country
FROM frontend.companies_overview AS co
LEFT JOIN frontend.company_domain_country AS cdc
    ON co.company_domain = cdc.company_domain;
