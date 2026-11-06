WITH new_apps AS (
    SELECT
        sao.id,
        sao.name,
        sao.store_id,
        sao.store,
        sao.category,
        sao.installs,
        sao.rating,
        sao.rating_count,
        sao.installs_sum_1w,
        sao.installs_sum_4w,
        sao.installs_z_score_2w,
        sao.installs_z_score_4w,
        sao.release_date,
        sao.icon_128,
        sao.developer_name,
        sao.developer_id,
        sao.ad_supported,
        sao.in_app_purchases,
        sao.country_id
    FROM frontend.store_apps_overview AS sao
    WHERE
        sao.release_date >= :start_date - INTERVAL '45 days'
        AND sao.release_date < :next_month_start_date
        AND sao.created_at >= :start_date - INTERVAL '200 days'
),

new_apps_with_ads AS (
    SELECT DISTINCT
        na.id,
        na.name,
        na.store_id,
        na.store,
        na.category,
        na.installs,
        na.rating,
        na.rating_count,
        na.installs_sum_1w,
        na.installs_sum_4w,
        na.installs_z_score_2w,
        na.installs_z_score_4w,
        na.release_date,
        na.icon_128,
        na.developer_name,
        na.developer_id,
        na.ad_supported,
        na.in_app_purchases,
        na.country_id,
        cr.id AS creative_record_id
    FROM new_apps AS na
    INNER JOIN creative_records AS cr
        ON na.id = cr.advertiser_store_app_id
    INNER JOIN api_calls AS ac
        ON cr.api_call_id = ac.id
    INNER JOIN version_code_api_scan_results AS vcasr
        ON ac.run_id = vcasr.id
    WHERE
        vcasr.run_at >= :start_date
        AND vcasr.run_at < :next_month_start_date
),

new_app_ad_networks AS (
    SELECT DISTINCT
        naw.id,
        coalesce(phc.name, hc.name) AS ad_network_name,
        coalesce(phad.domain_name, had.domain_name) AS ad_network_domain,
        coalesce(phc.logo_url, hc.logo_url) AS ad_network_logo_url
    FROM new_apps_with_ads AS naw
    LEFT JOIN creative_records AS cr
        ON naw.id = cr.advertiser_store_app_id
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
        cc.category_id = 1
        AND hc.id != 48
    UNION
    SELECT DISTINCT
        naw.id,
        coalesce(pic.name, ic.name) AS ad_network_name,
        coalesce(piad.domain_name, iad.domain_name) AS ad_network_domain,
        coalesce(pic.logo_url, ic.logo_url) AS ad_network_logo_url
    FROM new_apps_with_ads AS naw
    LEFT JOIN creative_records AS cr
        ON naw.id = cr.advertiser_store_app_id
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
        cc.category_id = 1
        AND ic.id != 48
),

new_app_mmps AS (
    SELECT DISTINCT
        naw.id,
        ad.domain_name AS mmp_domain
    FROM new_apps_with_ads AS naw
    LEFT JOIN creative_records AS cr
        ON naw.id = cr.advertiser_store_app_id
    LEFT JOIN domains AS ad
        ON cr.mmp_domain_id = ad.id
    WHERE cr.mmp_domain_id IS NOT NULL
    UNION
    SELECT DISTINCT
        csac.store_app AS id,
        d.domain_name AS mmp_domain
    FROM adtech.combined_domain_apps AS csac
    LEFT JOIN adtech.company_categories AS cc
        ON csac.company_id = cc.company_id
    LEFT JOIN adtech.companies AS c
        ON csac.company_id = c.id
    LEFT JOIN domains AS d
        ON c.domain_id = d.id
    INNER JOIN new_apps_with_ads AS naw
        ON csac.store_app = naw.id
    WHERE cc.category_id = 2 AND csac.company_id > 0
),

new_app_creatives AS (
    SELECT
        naw.id,
        ca.phash,
        ca.md5_hash,
        ca.file_extension
    FROM new_apps_with_ads AS naw
    LEFT JOIN creative_records AS cr
        ON naw.id = cr.advertiser_store_app_id
    LEFT JOIN creative_assets AS ca
        ON cr.creative_asset_id = ca.id
    LEFT JOIN api_calls AS ac
        ON cr.api_call_id = ac.id
    LEFT JOIN version_code_api_scan_results AS vcasr
        ON ac.run_id = vcasr.id
    WHERE
        vcasr.run_at >= :start_date
        AND vcasr.run_at < :next_month_start_date
        AND ca.phash IS NOT NULL
)

SELECT
    naw.name,
    naw.store_id,
    naw.store,
    naw.category,
    naw.installs,
    naw.rating,
    naw.rating_count,
    naw.installs_sum_1w,
    naw.installs_sum_4w,
    naw.installs_z_score_2w,
    naw.installs_z_score_4w,
    naw.release_date,
    naw.icon_128,
    naw.developer_name,
    naw.developer_id,
    naw.ad_supported,
    naw.in_app_purchases,
    cc.alpha2 AS advertiser_country,
    nullif(
        array_agg(DISTINCT nana.ad_network_name::TEXT) FILTER (
            WHERE nana.ad_network_name IS NOT NULL
        ),
        '{}'::TEXT []
    ) AS ad_network_names,
    nullif(
        array_agg(DISTINCT nana.ad_network_domain::TEXT) FILTER (
            WHERE nana.ad_network_domain IS NOT NULL
        ),
        '{}'::TEXT []
    ) AS ad_network_domains,
    nullif(
        array_agg(DISTINCT nana.ad_network_logo_url::TEXT) FILTER (
            WHERE nana.ad_network_logo_url IS NOT NULL
        ),
        '{}'::TEXT []
    ) AS ad_network_logo_urls,
    nullif(
        array_agg(DISTINCT nam.mmp_domain::TEXT) FILTER (
            WHERE nam.mmp_domain IS NOT NULL
        ),
        '{}'::TEXT []
    ) AS mmp_domains,
    count(DISTINCT nac.phash) AS creative_count,
    nullif(
        array_agg(DISTINCT nac.md5_hash::TEXT) FILTER (
            WHERE nac.md5_hash IS NOT NULL
        ),
        '{}'::TEXT []
    ) AS md5_hashes,
    nullif(
        array_agg(DISTINCT nac.file_extension::TEXT) FILTER (
            WHERE nac.file_extension IS NOT NULL
        ),
        '{}'::TEXT []
    ) AS md5_file_extensions
FROM new_apps_with_ads AS naw
LEFT JOIN new_app_ad_networks AS nana ON naw.id = nana.id
LEFT JOIN new_app_mmps AS nam ON naw.id = nam.id
LEFT JOIN new_app_creatives AS nac ON naw.id = nac.id
LEFT JOIN countries AS cc ON naw.country_id = cc.id
GROUP BY
    naw.id,
    naw.name,
    naw.store_id,
    naw.store,
    naw.category,
    naw.installs,
    naw.rating,
    naw.rating_count,
    naw.installs_sum_1w,
    naw.installs_sum_4w,
    naw.installs_z_score_2w,
    naw.installs_z_score_4w,
    naw.release_date,
    naw.icon_128,
    naw.developer_name,
    naw.developer_id,
    naw.ad_supported,
    naw.in_app_purchases,
    naw.country_id,
    cc.alpha2
ORDER BY naw.installs DESC NULLS LAST, naw.name ASC
LIMIT 40;
