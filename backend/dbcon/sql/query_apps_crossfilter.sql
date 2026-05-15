WITH
include_apps AS (
    SELECT c.store_app
    FROM adtech.combined_store_apps_companies AS c
    WHERE
        cardinality(cast(:include_domains AS text [])) > 0
        AND c.ad_domain = any(cast(:include_domains AS text []))
        AND (
            NOT cast(:require_sdk_api AS boolean)
            OR c.sdk = TRUE
            OR c.api_call = TRUE
        )
    GROUP BY c.store_app
    HAVING
        count(DISTINCT c.ad_domain)
        = cardinality(cast(:include_domains AS text []))
),

exclude_apps AS (
    SELECT DISTINCT c.store_app
    FROM adtech.combined_store_apps_companies AS c
    WHERE
        cardinality(cast(:exclude_domains AS text [])) > 0
        AND c.ad_domain = any(cast(:exclude_domains AS text []))
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
        cardinality(cast(:include_domains AS text [])) = 0
        OR EXISTS (
            SELECT 1
            FROM include_apps AS ia
            WHERE ia.store_app = sao.id
        )
    )
    AND
    sao.store_last_updated > cast(:mydate AS date)
    AND (NOT cast(:require_iap AS boolean) OR sao.in_app_purchases = TRUE)
    AND (NOT cast(:require_ads AS boolean) OR sao.ad_supported = TRUE)
    AND (cast(:category AS text) IS NULL OR sao.category LIKE :category)
    AND (cast(:store AS int) IS NULL OR sao.store = :store)
    AND (
        cast(:ranking_country AS text) IS NULL
        OR (
            :ranking_country = 'overall'
            AND EXISTS (
                SELECT 1
                FROM frontend.store_app_ranks_latest AS sar
                WHERE sar.store_id = sao.store_id
            )
        )
        OR (
            :ranking_country <> 'overall'
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
        cast(:min_installs AS bigint) IS NULL
        OR :min_installs = 0
        OR sao.installs >= :min_installs
    )
    AND (

        cast(:max_installs AS bigint) IS NULL
        OR sao.installs <= :max_installs
    )
    AND (

        cast(:min_rating_count AS bigint) IS NULL
        OR sao.rating_count >= :min_rating_count
    )
    AND (

        cast(:max_rating_count AS bigint) IS NULL
        OR sao.rating_count <= :max_rating_count
    )
    AND (

        cast(:min_installs_d30 AS bigint) IS NULL
        OR sao.installs_sum_4w >= :min_installs_d30
    )
    AND (

        cast(:max_installs_d30 AS bigint) IS NULL
        OR sao.installs_sum_4w <= :max_installs_d30
    )
    -- Exclusion check
    AND NOT EXISTS (
        SELECT 1 FROM exclude_apps AS ea
        WHERE ea.store_app = sao.id
    )
ORDER BY
    sao.installs DESC NULLS LAST
LIMIT :limit
;
