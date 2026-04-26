WITH creative_ad_networks AS (
    SELECT DISTINCT
        cr.id AS creative_record_id,
        pub.id AS publisher_id,
        ca.phash,
        cr.advertiser_store_app_id AS advertiser_store_app,
        coalesce(phc.name, hc.name) AS parent_ad_network_name,
        coalesce(phad.domain_name, had.domain_name) AS parent_ad_network_domain,
        had.domain_name AS ad_network_domain,
        coalesce(phc.logo_url, hc.logo_url) AS company_logo_url
    FROM creative_records AS cr
    LEFT JOIN creative_assets AS ca
        ON cr.creative_asset_id = ca.id
    LEFT JOIN store_apps AS adv_app
        ON cr.advertiser_store_app_id = adv_app.id
    LEFT JOIN api_calls AS ac
        ON cr.api_call_id = ac.id
    LEFT JOIN version_code_api_scan_results AS pub
        ON ac.run_id = pub.id
    LEFT JOIN adtech.company_domain_mapping AS hcdm
        ON cr.creative_host_domain_id = hcdm.domain_id
    LEFT JOIN adtech.companies AS hc
        ON hcdm.company_id = hc.id
    LEFT JOIN adtech.companies AS phc
        ON hc.parent_company_id = phc.id
    LEFT JOIN domains AS had
        ON hc.domain_id = had.id
    LEFT JOIN domains AS phad
        ON phc.domain_id = phad.id
    LEFT JOIN adtech.company_categories AS cc
        ON hc.id = cc.company_id
    WHERE
        pub.run_at >= :start_date
        AND pub.run_at < :next_month_start_date
        AND had.domain_name IS NOT NULL
        AND cc.category_id = 1
        AND hc.id != 48
    UNION
    SELECT DISTINCT
        cr.id AS creative_record_id,
        pub.id AS publisher_id,
        ca.phash,
        cr.advertiser_store_app_id AS advertiser_store_app,
        coalesce(pic.name, ic.name) AS parent_ad_network_name,
        coalesce(piad.domain_name, iad.domain_name) AS parent_ad_network_domain,
        iad.domain_name AS ad_network_domain,
        coalesce(pic.logo_url, ic.logo_url) AS company_logo_url
    FROM creative_records AS cr
    LEFT JOIN creative_assets AS ca
        ON cr.creative_asset_id = ca.id
    LEFT JOIN store_apps AS adv_app
        ON cr.advertiser_store_app_id = adv_app.id
    LEFT JOIN api_calls AS ac
        ON cr.api_call_id = ac.id
    LEFT JOIN version_code_api_scan_results AS pub
        ON ac.run_id = pub.id
    LEFT JOIN adtech.company_domain_mapping AS icdm
        ON cr.creative_initial_domain_id = icdm.domain_id
    LEFT JOIN adtech.companies AS ic
        ON icdm.company_id = ic.id
    LEFT JOIN adtech.companies AS pic
        ON ic.parent_company_id = pic.id
    LEFT JOIN domains AS iad
        ON ic.domain_id = iad.id
    LEFT JOIN domains AS piad
        ON pic.domain_id = piad.id
    LEFT JOIN adtech.company_categories AS cc
        ON ic.id = cc.company_id
    WHERE
        pub.run_at >= :start_date
        AND pub.run_at < :next_month_start_date
        AND iad.domain_name IS NOT NULL
        AND cc.category_id = 1
        AND ic.id != 48
)

SELECT
    parent_ad_network_name AS ad_network_name,
    parent_ad_network_domain AS ad_network_domain,
    company_logo_url,
    array_agg(DISTINCT ad_network_domain) AS all_domains,
    count(DISTINCT publisher_id) AS publisher_count,
    count(DISTINCT advertiser_store_app) AS advertiser_count,
    count(DISTINCT phash) AS creatives_count
FROM creative_ad_networks
GROUP BY
    parent_ad_network_name,
    parent_ad_network_domain,
    company_logo_url
ORDER BY publisher_count DESC
LIMIT 10;
