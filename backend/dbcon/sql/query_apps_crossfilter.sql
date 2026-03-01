--noqa: disable=LT01
WITH
include_apps AS (
    SELECT c.store_app
    FROM adtech.combined_store_apps_companies AS c
    WHERE
        cardinality(c.:include_domains ::text []) > 0
        AND c.ad_domain = any(c.:include_domains ::text [])
        AND (
            NOT c.:require_sdk_api ::boolean
            OR c.sdk = TRUE
            OR c.api_call = TRUE
        )
    GROUP BY c.store_app
    HAVING
        count(DISTINCT c.ad_domain) = cardinality(c.:include_domains ::text [])
),

exclude_apps AS (
    SELECT DISTINCT c.store_app
    FROM adtech.combined_store_apps_companies AS c
    WHERE
        cardinality(c.:exclude_domains ::text []) > 0
        AND c.ad_domain = any(c.:exclude_domains ::text [])
)

SELECT
    sao.id,
    sao.store_id,
    sao.name,
    sao.installs,
    sao.rating_count,
    sao.installs_sum_4w AS installs_d30,
    sao.monthly_active_users,
    sao.in_app_purchases,
    sao.ad_supported,
    sao.store,
    sao.icon_url_100,
    sao.monthly_ad_revenue
    + sao.monthly_iap_revenue AS estimated_monthly_revenue
FROM frontend.store_apps_overview AS sao
WHERE
    (
        cardinality(sao.:include_domains ::text []) = 0
        OR EXISTS (
            SELECT 1
            FROM include_apps AS ia
            WHERE ia.store_app = sao.id
        )
    )
    AND
    sao.store_last_updated > sao.:mydate ::date
    AND (NOT sao.:require_iap ::boolean OR sao.in_app_purchases = TRUE)
    AND (NOT sao.:require_ads ::boolean OR sao.ad_supported = TRUE)
    AND (sao.:category ::text IS NULL OR sao.category LIKE sao.:category)
    AND (sao.:store ::int IS NULL OR sao.store = sao.:store)
    AND (
        sao.:ranking_country ::text IS NULL
        OR (
            sao.:ranking_country = 'overall'
            AND EXISTS (
                SELECT 1
                FROM frontend.store_app_ranks_latest AS sar
                WHERE sar.store_id = sao.store_id
            )
        )
        OR (
            sao.:ranking_country <> 'overall'
            AND EXISTS (
                SELECT 1
                FROM frontend.store_app_ranks_latest AS sar
                WHERE
                    sar.store_id = sao.store_id
                    AND sar.country = :ranking_country
            )
        )
    )
    AND (
        sao.:min_installs ::bigint IS NULL
        OR sao.:min_installs = 0
        OR sao.installs >= sao.:min_installs
    )
    AND (

        sao.:max_installs ::bigint IS NULL
        OR sao.installs <= sao.:max_installs
    )
    AND (

        sao.:min_rating_count ::bigint IS NULL
        OR sao.rating_count >= sao.:min_rating_count
    )
    AND (

        sao.:max_rating_count ::bigint IS NULL
        OR sao.rating_count <= sao.:max_rating_count
    )
    AND (

        sao.:min_installs_d30 ::bigint IS NULL
        OR sao.installs_sum_4w >= sao.:min_installs_d30
    )
    AND (

        sao.:max_installs_d30 ::bigint IS NULL
        OR sao.installs_sum_4w <= sao.:max_installs_d30
    )
    -- Exclusion check
    AND NOT EXISTS (
        SELECT 1 FROM exclude_apps AS ea
        WHERE ea.store_app = sao.id
    )
ORDER BY
    sao.installs DESC NULLS LAST
LIMIT 100;
