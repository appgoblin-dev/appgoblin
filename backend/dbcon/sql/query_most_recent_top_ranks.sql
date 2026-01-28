SELECT
    rank,
    name,
    store_id,
    store,
    installs,
    developer_name,
    rating_count,
    rating,
    installs_sum_1w,
    installs_sum_4w,
    ratings_sum_1w,
    ratings_sum_4w,
    CONCAT(
        'https://media.appgoblin.info/app-icons/',
        store_id,
        '/',
        icon_url_100
    ) AS app_icon_url
FROM
    frontend.store_app_ranks_latest
WHERE
    store_collection = :collection_id
    AND store_category = :category_id
    AND country = :country
ORDER BY rank ASC
LIMIT :mylimit;
