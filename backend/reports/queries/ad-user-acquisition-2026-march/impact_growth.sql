WITH advertiser_z_scores AS (
    SELECT *
    FROM (
        SELECT
            sazh.target_week,
            sazh.store,
            sazh.store_app,
            sazh.app_name,
            sazh.store_id,
            sazh.icon_url_100,
            sazh.target_week_installs,
            sazh.weekly_installs_pct,
            sazh.baseline_installs,
            sazh.baseline_installs_pct,
            sazh.installs_z_score_2w,
            sazh.installs_z_score_4w,
            sazh.installs_acceleration,
            sazh.wow_growth_pct,
            sazh.momentum_pct,
            sazh.has_reliable_baseline,
            sazh.in_app_purchases,
            sazh.ad_supported,
            (
                coalesce(sazh.installs_z_score_2w, 0) * 0.5
                + coalesce(sazh.momentum_pct, 0) / 100 * 0.3
                + coalesce(sazh.wow_growth_pct, 0) / 100 * 0.2
            ) AS composite_score,
            row_number() OVER (
                PARTITION BY sazh.target_week, sazh.store
                ORDER BY
                    (
                        coalesce(sazh.installs_z_score_2w, 0) * 0.5
                        + coalesce(sazh.momentum_pct, 0) / 100 * 0.3
                        + coalesce(sazh.wow_growth_pct, 0) / 100 * 0.2
                    ) DESC NULLS LAST
            ) AS rn
        FROM store_app_z_scores_history_2026 AS sazh
        WHERE
            sazh.target_week >= :first_target_week
            AND sazh.target_week < :next_month_start_date
            AND sazh.has_reliable_baseline = TRUE
            AND sazh.installs_z_score_2w > 1.5
    ) AS ranked
    WHERE rn <= 5
),

adv_mmp AS (
    SELECT DISTINCT
        cr_1.advertiser_store_app_id,
        cr_1.mmp_domain_id,
        ad.domain_name AS mmp_domain
    FROM creative_records AS cr_1
    LEFT JOIN domains AS ad ON cr_1.mmp_domain_id = ad.id
    WHERE
        cr_1.mmp_domain_id IS NOT NULL
        AND cr_1.advertiser_store_app_id IS NOT NULL
    UNION
    SELECT DISTINCT
        csac.store_app AS advertiser_store_app_id,
        c.domain_id AS mmp_domain_id,
        csac.ad_domain AS mmp_domain
    FROM adtech.combined_store_apps_companies AS csac
    LEFT JOIN adtech.company_categories AS cc ON csac.company_id = cc.company_id
    LEFT JOIN adtech.companies AS c ON csac.company_id = c.id
    WHERE cc.category_id = 2 AND csac.company_id > 0
),

main_results AS (
    SELECT
        adv.target_week AS best_week,
        adv.store,
        adv.app_name,
        adv.store_app,
        adv.store_id,
        adv.icon_url_100,
        adv.in_app_purchases,
        adv.ad_supported,
        adv.target_week_installs AS weekly_installs,
        adv.weekly_installs_pct AS weekly_percent_increase,
        adv.baseline_installs,
        adv.baseline_installs_pct,
        adv.installs_z_score_2w,
        adv.installs_z_score_4w,
        adv.installs_acceleration,
        adv.wow_growth_pct,
        adv.momentum_pct,
        adv.composite_score,
        ca.phash,
        ca.file_extension,
        had.domain_name AS host_ad_domain,
        hc.logo_url AS host_company_logo_url,
        iad.domain_name AS initial_ad_domain,
        ic.logo_url AS initial_company_logo_url,
        nullif(
            array_agg(DISTINCT am.mmp_domain) FILTER (
                WHERE am.mmp_domain IS NOT NULL
            ),
            '{}'::CHARACTER VARYING []
        ) AS mmp_domains,
        (
            SELECT ca_inner.md5_hash
            FROM creative_assets AS ca_inner
            INNER JOIN creative_records AS cr_inner
                ON ca_inner.id = cr_inner.creative_asset_id
            WHERE
                cr_inner.advertiser_store_app_id IS NOT NULL
                AND cr_inner.advertiser_store_app_id = adv.store_app
            GROUP BY ca_inner.md5_hash
            ORDER BY count(*) DESC
            LIMIT 1
        ) AS md5_hash,
        count(DISTINCT pub.id) AS pub_count
    FROM creative_records AS cr
    LEFT JOIN creative_assets AS ca ON cr.creative_asset_id = ca.id
    LEFT JOIN store_apps AS adv_app ON cr.advertiser_store_app_id = adv_app.id
    INNER JOIN advertiser_z_scores AS adv ON adv_app.id = adv.store_app
    LEFT JOIN api_calls AS ac ON cr.api_call_id = ac.id
    LEFT JOIN version_code_api_scan_results AS pub
        ON
            ac.run_id = pub.id
            AND pub.run_at >= adv.target_week - INTERVAL '8 days'
            AND pub.run_at < adv.target_week + INTERVAL '2 days'
    LEFT JOIN adtech.company_domain_mapping AS icdm
        ON cr.creative_initial_domain_id = icdm.domain_id
    LEFT JOIN adtech.companies AS ic ON icdm.company_id = ic.id
    LEFT JOIN domains AS iad ON ic.domain_id = iad.id
    LEFT JOIN adtech.company_domain_mapping AS hcdm
        ON cr.creative_host_domain_id = hcdm.domain_id
    LEFT JOIN adtech.companies AS hc ON hcdm.company_id = hc.id
    LEFT JOIN domains AS had ON hc.domain_id = had.id
    LEFT JOIN adv_mmp AS am ON adv_app.id = am.advertiser_store_app_id
    WHERE cr.advertiser_store_app_id IS NOT NULL
    GROUP BY
        adv.target_week,
        adv.store,
        adv.app_name,
        adv.store_app,
        adv.store_id,
        adv.icon_url_100,
        adv.in_app_purchases,
        adv.ad_supported,
        adv.target_week_installs,
        adv.weekly_installs_pct,
        adv.baseline_installs,
        adv.baseline_installs_pct,
        adv.installs_z_score_2w,
        adv.installs_z_score_4w,
        adv.installs_acceleration,
        adv.wow_growth_pct,
        adv.momentum_pct,
        adv.composite_score,
        ca.phash,
        ca.file_extension,
        had.domain_name,
        hc.logo_url,
        iad.domain_name,
        ic.logo_url
),

best_week_results AS (
    SELECT DISTINCT ON (store_app)
        best_week,
        store,
        store_app,
        app_name,
        store_id,
        icon_url_100,
        in_app_purchases,
        ad_supported,
        weekly_installs,
        weekly_percent_increase,
        baseline_installs,
        baseline_installs_pct,
        installs_z_score_2w,
        installs_z_score_4w,
        installs_acceleration,
        wow_growth_pct,
        momentum_pct,
        composite_score,
        phash,
        file_extension,
        host_ad_domain,
        host_company_logo_url,
        initial_ad_domain,
        initial_company_logo_url,
        mmp_domains,
        md5_hash,
        pub_count
    FROM main_results
    ORDER BY store_app ASC, composite_score DESC
)

SELECT
    best_week,
    app_name,
    store_id,
    icon_url_100,
    in_app_purchases,
    ad_supported,
    weekly_installs,
    weekly_percent_increase,
    baseline_installs,
    baseline_installs_pct,
    installs_z_score_2w,
    installs_z_score_4w,
    installs_acceleration,
    wow_growth_pct,
    momentum_pct,
    composite_score,
    phash,
    file_extension,
    host_ad_domain,
    host_company_logo_url,
    initial_ad_domain,
    initial_company_logo_url,
    mmp_domains,
    md5_hash,
    pub_count
FROM best_week_results
ORDER BY composite_score DESC, store_id ASC;
