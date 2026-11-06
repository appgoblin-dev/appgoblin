WITH cr_advertisers_raw AS (
    -- strong signal: the original single-value column
    SELECT
        cr.id AS creative_record_id,
        cr.advertiser_store_app_id,
        FALSE AS is_weak_signal
    FROM creative_records AS cr
    WHERE cr.advertiser_store_app_id IS NOT NULL

    UNION ALL

    -- weak signal: exploded array
    SELECT
        cr.id AS creative_record_id,
        unnest(cr.advertiser_store_app_ids) AS advertiser_store_app_id,
        TRUE AS is_weak_signal
    FROM creative_records AS cr
    WHERE cr.advertiser_store_app_ids IS NOT NULL
),

cr_advertisers AS MATERIALIZED (
    -- one row per (creative, advertiser) pair. If both a strong and weak
    -- signal point at the same pair, strong wins (is_weak_signal = FALSE)
    SELECT
        creative_record_id,
        advertiser_store_app_id,
        bool_and(is_weak_signal) AS is_weak_signal,
        count(*) > 1 AS corroborated_by_both_signals
    FROM cr_advertisers_raw
    GROUP BY creative_record_id, advertiser_store_app_id
),

adv_mmp AS (
    SELECT DISTINCT
        cra.advertiser_store_app_id,
        cr_1.mmp_domain_id,
        ad.domain_name AS mmp_domain
    FROM creative_records AS cr_1
    INNER JOIN cr_advertisers AS cra
        ON cr_1.id = cra.creative_record_id
    LEFT JOIN domains AS ad
        ON cr_1.mmp_domain_id = ad.id
    WHERE cr_1.mmp_domain_id IS NOT NULL
    UNION
    SELECT DISTINCT
        csac.store_app AS advertiser_store_app_id,
        c.domain_id AS mmp_domain_id,
        d.domain_name AS mmp_domain
    FROM adtech.combined_domain_apps AS csac
    LEFT JOIN adtech.company_categories AS cc
        ON csac.company_id = cc.company_id
    LEFT JOIN adtech.companies AS c
        ON csac.company_id = c.id
    LEFT JOIN domains AS d ON c.domain_id = d.id
    WHERE
        cc.category_id = 2
        AND csac.company_id > 0
),

ad_network_domain_ids AS (
    SELECT
        cra.advertiser_store_app_id,
        coalesce(icp.domain_id, ic.domain_id) AS domain_id
    FROM creative_records AS cr_1
    INNER JOIN cr_advertisers AS cra
        ON cr_1.id = cra.creative_record_id
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
        cra.advertiser_store_app_id,
        coalesce(hcp.domain_id, hc.domain_id) AS domain_id
    FROM creative_records AS cr_1
    INNER JOIN cr_advertisers AS cra
        ON cr_1.id = cra.creative_record_id
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

-- publisher stats computed in isolation, BEFORE any join to adv_mmp
publisher_stats AS (
    SELECT
        cra.advertiser_store_app_id,
        cra.is_weak_signal,
        ac.store_app AS publisher_store_app_id,
        sap.installs AS publisher_installs
    FROM cr_advertisers AS cra
    INNER JOIN creative_records AS cr
        ON cra.creative_record_id = cr.id
    LEFT JOIN api_calls AS ac
        ON cr.api_call_id = ac.id
    LEFT JOIN frontend.store_apps_overview AS sap
        ON ac.store_app = sap.id
    LEFT JOIN version_code_api_scan_results AS vcasr
        ON ac.run_id = vcasr.id
    WHERE
        ac.store_app IS NOT NULL
        AND vcasr.run_at >= :start_date
        AND vcasr.run_at < :next_month_start_date
),

-- same publisher can run multiple creatives for the same advertiser;
-- Strong wins on conflict, same rule as cr_advertisers.
publisher_stats_dedup AS (
    SELECT
        advertiser_store_app_id,
        publisher_store_app_id,
        max(publisher_installs) AS publisher_installs,
        bool_and(is_weak_signal) AS is_weak_signal
    FROM publisher_stats
    GROUP BY advertiser_store_app_id, publisher_store_app_id
),

publisher_agg AS (
    SELECT
        advertiser_store_app_id,
        count(DISTINCT publisher_store_app_id) AS unique_publishers,
        count(DISTINCT publisher_store_app_id)
        FILTER (WHERE NOT is_weak_signal) AS unique_publishers_strong,
        count(DISTINCT publisher_store_app_id)
        FILTER (WHERE is_weak_signal) AS unique_publishers_weak,
        avg(publisher_installs) AS avg_publisher_installs,
        avg(publisher_installs)
        FILTER (WHERE NOT is_weak_signal) AS avg_publisher_installs_strong,
        avg(publisher_installs)
        FILTER (WHERE is_weak_signal) AS avg_publisher_installs_weak
    FROM publisher_stats_dedup
    GROUP BY advertiser_store_app_id
),

allres AS (
    SELECT
        saa.name AS advertiser_name,
        saa.store_id AS advertiser_store_id,
        saa.category AS advertiser_category,
        cc.alpha2 AS advertiser_country,
        saa.installs AS advertiser_installs,
        saa.installs_sum_1w AS weekly_installs,
        saa.developer_name,
        bool_or(cra.is_weak_signal) AS has_weak_signal_creatives,
        bool_and(cra.is_weak_signal) AS weak_signal_only,
        count(DISTINCT ca.phash) AS unique_creatives,
        count(DISTINCT ca.phash)
        FILTER (WHERE NOT cra.is_weak_signal) AS unique_creatives_strong,
        count(DISTINCT ca.phash)
        FILTER (WHERE cra.is_weak_signal) AS unique_creatives_weak,
        min(vcasr.run_at) AS first_seen,
        max(vcasr.run_at) AS last_seen,
        array_agg(DISTINCT adis.ad_network_domain) AS ad_network_domains,
        max(pa.unique_publishers) AS unique_publishers,
        max(pa.unique_publishers_strong) AS unique_publishers_strong,
        max(pa.unique_publishers_weak) AS unique_publishers_weak,
        max(pa.avg_publisher_installs) AS avg_publisher_installs,
        --    max(pa.avg_publisher_installs_strong) AS avg_publisher_installs_strong,
        --    max(pa.avg_publisher_installs_weak) AS avg_publisher_installs_weak,
        nullif(
            array_agg(DISTINCT adv_mmp.mmp_domain) FILTER (
                WHERE adv_mmp.mmp_domain IS NOT NULL
            ),
            '{}'::CHARACTER VARYING []
        ) AS mmp_domains
    FROM creative_records AS cr
    INNER JOIN cr_advertisers AS cra
        ON cr.id = cra.creative_record_id
    LEFT JOIN creative_assets AS ca
        ON cr.creative_asset_id = ca.id
    LEFT JOIN api_calls AS ac
        ON cr.api_call_id = ac.id
    LEFT JOIN frontend.store_apps_overview AS saa
        ON cra.advertiser_store_app_id = saa.id
    LEFT JOIN version_code_api_scan_results AS vcasr
        ON ac.run_id = vcasr.id
    LEFT JOIN publisher_agg AS pa
        ON cra.advertiser_store_app_id = pa.advertiser_store_app_id
    LEFT JOIN adv_mmp
        ON cra.advertiser_store_app_id = adv_mmp.advertiser_store_app_id
    LEFT JOIN ad_network_domains AS adis
        ON cra.advertiser_store_app_id = adis.advertiser_store_app_id
    LEFT JOIN countries AS cc
        ON saa.country_id = cc.id
    WHERE
        vcasr.run_at >= :start_date
        AND vcasr.run_at < :next_month_start_date
    GROUP BY
        saa.name,
        saa.store_id,
        saa.category,
        cc.alpha2,
        saa.installs,
        saa.rating,
        saa.rating_count,
        saa.installs_sum_1w,
        saa.installs_sum_4w,
        saa.developer_name
    ORDER BY unique_publishers DESC
)

SELECT * FROM allres;
