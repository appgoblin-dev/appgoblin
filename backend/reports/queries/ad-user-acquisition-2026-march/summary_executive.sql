SELECT
    count(DISTINCT store_app) AS apps_analyzed,
    count(*) AS https_tracked,
    count(DISTINCT tld_url) AS api_domains,
    count(DISTINCT cdm.company_id) AS adtech_companies,
    count(DISTINCT advertiser_store_app_id) AS advertisers,
    count(DISTINCT phash) AS creative_count
FROM
    api_calls AS ac
LEFT JOIN domains AS d ON ac.tld_url = d.domain_name
LEFT JOIN adtech.company_domain_mapping AS cdm ON d.id = cdm.domain_id
LEFT JOIN creative_records AS cr ON ac.id = cr.api_call_id
LEFT JOIN creative_assets AS ca ON cr.creative_asset_id = ca.id
WHERE
    called_at >= :start_date
    AND called_at < :next_month_start_date;
