WITH ranked_md5s AS (
    SELECT
        md5_hash,
        file_extension,
        right(phash, 12) AS phash,
        count(*) AS cnt,
        row_number() OVER (
            PARTITION BY right(phash, 12)
            ORDER BY count(*) DESC
        ) AS rn
    FROM creative_assets
    GROUP BY right(phash, 12), md5_hash, file_extension
),

most_common_md5 AS (
    SELECT
        phash,
        md5_hash,
        file_extension,
        cnt AS frequency
    FROM ranked_md5s
    WHERE rn = 1
),

top_adv_per_phash AS (
    SELECT DISTINCT ON (right(ca_inner.phash, 12))
        sa_inner.store_id,
        sa_inner.icon_url_100,
        right(ca_inner.phash, 12) AS phash
    FROM creative_assets AS ca_inner
    INNER JOIN creative_records AS cr_inner
        ON ca_inner.id = cr_inner.creative_asset_id
    INNER JOIN store_apps AS sa_inner
        ON cr_inner.advertiser_store_app_id = sa_inner.id
    LEFT JOIN api_calls AS ac_inner ON cr_inner.api_call_id = ac_inner.id
    LEFT JOIN version_code_api_scan_results AS pub_inner
        ON ac_inner.run_id = pub_inner.id
    WHERE
        pub_inner.run_at >= :start_date
        AND pub_inner.run_at < :next_month_start_date
    GROUP BY right(ca_inner.phash, 12), sa_inner.store_id, sa_inner.icon_url_100
    ORDER BY right(ca_inner.phash, 12), count(*) DESC
),

creative_stats AS (
    SELECT
        cr.advertiser_store_app_id,
        right(ca.phash, 12) AS phash,
        count(DISTINCT cr.advertiser_store_app_id) AS advertiser_count,
        count(DISTINCT pub.id) AS publisher_count,
        min(pub.run_at) AS first_seen,
        max(pub.run_at) AS last_seen
    FROM creative_records AS cr
    LEFT JOIN creative_assets AS ca ON cr.creative_asset_id = ca.id
    LEFT JOIN api_calls AS ac ON cr.api_call_id = ac.id
    LEFT JOIN store_apps AS adv_app ON ac.store_app = adv_app.id
    LEFT JOIN version_code_api_scan_results AS pub ON ac.run_id = pub.id
    WHERE
        pub.run_at >= :start_date
        AND pub.run_at < :next_month_start_date
        AND ca.phash IS NOT NULL
        AND ca.file_extension IN ('mp4', 'webm')
    GROUP BY right(ca.phash, 12), cr.advertiser_store_app_id
),

ranked_creatives AS (
    SELECT
        *,
        row_number() OVER (
            PARTITION BY advertiser_store_app_id
            ORDER BY publisher_count DESC, phash ASC
        ) AS rn
    FROM creative_stats
)

SELECT
    rc.phash,
    mcm.md5_hash,
    mcm.file_extension,
    advertiser_count,
    publisher_count,
    first_seen,
    last_seen,
    tap.store_id AS advertiser_store_id,
    tap.icon_url_100 AS advertiser_icon_url_100
FROM ranked_creatives AS rc
LEFT JOIN most_common_md5 AS mcm ON rc.phash = mcm.phash
LEFT JOIN top_adv_per_phash AS tap ON rc.phash = tap.phash
WHERE
    rn <= 2
    AND advertiser_store_app_id IS NOT NULL
ORDER BY publisher_count DESC
LIMIT 10;
