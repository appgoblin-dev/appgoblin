WITH adv_mmp AS (
    SELECT DISTINCT
        cr_1.advertiser_store_app_id,
        cr_1.mmp_domain_id,
        ad.domain_name AS mmp_domain
    FROM creative_records AS cr_1
    LEFT JOIN domains AS ad
        ON
            cr_1.mmp_domain_id = ad.id
            AND cr_1.advertiser_store_app_id IS NOT NULL
    WHERE cr_1.mmp_domain_id IS NOT NULL
    UNION
    SELECT DISTINCT
        csac.store_app AS advertiser_store_app_id,
        c.domain_id AS mmp_domain_id,
        csac.ad_domain AS mmp_domain
    FROM adtech.combined_store_apps_companies AS csac
    LEFT JOIN adtech.company_categories AS cc
        ON csac.company_id = cc.company_id
    LEFT JOIN adtech.companies AS c
        ON csac.company_id = c.id
    WHERE
        cc.category_id = 2
        AND csac.company_id > 0
),

ad_network_domain_ids AS (
    SELECT
        cr_1.advertiser_store_app_id,
        coalesce(icp.domain_id, ic.domain_id) AS domain_id
    FROM creative_records AS cr_1
    INNER JOIN adtech.company_domain_mapping AS icdm
        ON cr_1.creative_initial_domain_id = icdm.domain_id
    LEFT JOIN adtech.companies AS ic
        ON icdm.company_id = ic.id
    LEFT JOIN adtech.companies AS icp
        ON ic.parent_company_id = icp.id
    LEFT JOIN api_calls AS ac_1
        ON cr_1.api_call_id = ac_1.id
    LEFT JOIN version_code_api_scan_results AS vcasr_1
        ON ac_1.run_id = vcasr_1.id
    WHERE
        vcasr_1.run_at >= :start_date
        AND vcasr_1.run_at < :next_month_start_date
    UNION
    SELECT
        cr_1.advertiser_store_app_id,
        coalesce(hcp.domain_id, hc.domain_id) AS domain_id
    FROM creative_records AS cr_1
    INNER JOIN adtech.company_domain_mapping AS hcdm
        ON cr_1.creative_host_domain_id = hcdm.domain_id
    LEFT JOIN adtech.companies AS hc
        ON hcdm.company_id = hc.id
    LEFT JOIN adtech.companies AS hcp
        ON hc.parent_company_id = hcp.id
    LEFT JOIN api_calls AS ac_1
        ON cr_1.api_call_id = ac_1.id
    LEFT JOIN version_code_api_scan_results AS vcasr_1
        ON ac_1.run_id = vcasr_1.id
    WHERE
        vcasr_1.run_at >= :start_date
        AND vcasr_1.run_at < :next_month_start_date
),

ad_network_domains AS (
    SELECT
        adi.advertiser_store_app_id,
        ad.domain_name AS ad_network_domain
    FROM ad_network_domain_ids AS adi
    LEFT JOIN domains AS ad ON adi.domain_id = ad.id
),

creative_rankings AS (
    SELECT
        ca_1.md5_hash,
        ca_1.file_extension,
        cr_1.advertiser_store_app_id,
        vcasr_1.run_at,
        row_number() OVER (
            PARTITION BY cr_1.advertiser_store_app_id
            ORDER BY vcasr_1.run_at DESC
        ) AS rn
    FROM creative_records AS cr_1
    LEFT JOIN creative_assets AS ca_1
        ON cr_1.creative_asset_id = ca_1.id
    LEFT JOIN api_calls AS ac_1
        ON cr_1.api_call_id = ac_1.id
    LEFT JOIN version_code_api_scan_results AS vcasr_1
        ON ac_1.run_id = vcasr_1.id
    WHERE
        vcasr_1.run_at >= :start_date
        AND vcasr_1.run_at < :next_month_start_date
)

SELECT
    saa.name AS advertiser_name,
    saa.store_id AS advertiser_store_id,
    saa.icon_url_100 AS advertiser_icon_url_100,
    saa.category AS advertiser_category,
    saa.installs AS advertiser_installs,
    count(DISTINCT ca.phash) AS unique_creatives,
    count(DISTINCT ac.store_app) AS unique_publishers,
    min(vcasr.run_at) AS first_seen,
    max(vcasr.run_at) AS last_seen,
    array_agg(DISTINCT adis.ad_network_domain) AS ad_network_domains,
    avg(sap.installs) AS avg_publisher_installs,
    nullif(
        array_agg(DISTINCT adv_mmp.mmp_domain) FILTER (
            WHERE adv_mmp.mmp_domain IS NOT NULL
        ),
        '{}'::CHARACTER VARYING []
    ) AS mmp_domains,
    array(
        SELECT crk.md5_hash
        FROM creative_rankings AS crk
        WHERE crk.advertiser_store_app_id = saa.id AND crk.rn <= 5
        ORDER BY crk.rn
    ) AS top_md5_hashes
FROM creative_records AS cr
LEFT JOIN api_calls AS ac
    ON cr.api_call_id = ac.id
LEFT JOIN creative_assets AS ca
    ON cr.creative_asset_id = ca.id
LEFT JOIN frontend.store_apps_overview AS sap
    ON ac.store_app = sap.id
LEFT JOIN frontend.store_apps_overview AS saa
    ON cr.advertiser_store_app_id = saa.id
LEFT JOIN version_code_api_scan_results AS vcasr
    ON ac.run_id = vcasr.id
LEFT JOIN adv_mmp
    ON cr.advertiser_store_app_id = adv_mmp.advertiser_store_app_id
LEFT JOIN ad_network_domains AS adis
    ON cr.advertiser_store_app_id = adis.advertiser_store_app_id
WHERE
    vcasr.run_at >= :start_date
    AND vcasr.run_at < :next_month_start_date
    AND cr.advertiser_store_app_id IS NOT NULL
GROUP BY
    saa.name,
    saa.store_id,
    saa.category,
    saa.installs,
    saa.id,
    saa.icon_url_100,
    saa.rating,
    saa.rating_count,
    saa.installs_sum_1w,
    saa.installs_sum_4w
ORDER BY unique_publishers DESC
LIMIT 50;
