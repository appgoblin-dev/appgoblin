SELECT
    sar.crawled_date,
    c.alpha2 AS country,
    sar.rank,
    sc.collection,
    sca.category
FROM
    frontend.app_ranks_weekly AS sar
LEFT JOIN countries AS c
    ON sar.country = c.id
LEFT JOIN store_apps AS sa
    ON sar.store_app = sa.id
LEFT JOIN store_collections AS sc
    ON sar.store_collection = sc.id
LEFT JOIN store_categories AS sca
    ON sar.store_category = sca.id
WHERE
    sa.store_id = :store_id
    AND c.alpha2 = :country
    AND sar.crawled_date >= :start_date;
