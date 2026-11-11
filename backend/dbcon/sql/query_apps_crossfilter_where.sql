WHERE
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
                FROM frontend.app_ranks_latest AS sar
                WHERE sar.store_id = sao.store_id
            )
        )
        OR (
            :ranking_country <> 'overall'
            AND EXISTS (
                SELECT 1
                FROM frontend.app_ranks_latest AS sar
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