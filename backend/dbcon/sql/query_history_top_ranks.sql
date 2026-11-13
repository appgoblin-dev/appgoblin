WITH top_apps AS (
    -- First identify all apps that were ever in top 10 during the period
    SELECT DISTINCT ar.store_app
    FROM frontend.app_ranks_weekly AS ar
    WHERE
        ar.store_collection = :collection_id
        AND ar.store_category = :category_id
        AND ar.country = :country_id
        AND ar.crawled_date >= :start_date
        AND ar.rank <= :mylimit
)

SELECT
    ar.crawled_date,
    ar.rank,
    sa.name,
    sa.store_id
FROM frontend.app_ranks_weekly AS ar
INNER JOIN top_apps AS ta
    ON ar.store_app = ta.store_app
LEFT JOIN store_apps AS sa
    ON ar.store_app = sa.id
WHERE
    ar.store_collection = :collection_id
    AND ar.store_category = :category_id
    AND ar.country = :country_id
    AND ar.crawled_date >= :start_date
ORDER BY
    sa.store_id ASC,
    ar.crawled_date DESC;
