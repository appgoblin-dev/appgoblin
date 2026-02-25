SELECT
    id,
    name,
    store_id,
    store,
    category,
    rating,
    rating_count,
    installs,
    installs_sum_1w,
    installs_sum_4w,
    ratings_sum_1w,
    installs_z_score_2w,
    installs_z_score_4w,
    store_last_updated,
    created_at,
    updated_at,
    crawl_result,
    release_date,
    featured_image_url,
    phone_image_url_1,
    phone_image_url_2,
    phone_image_url_3,
    tablet_image_url_1,
    tablet_image_url_2,
    tablet_image_url_3,
    description,
    description_short,
    developer_id,
    developer_name,
    developer_url,
    adstxt_last_crawled,
    adstxt_crawl_result,
    ad_supported,
    in_app_purchases,
    version_code,
    sdk_last_crawled,
    sdk_last_crawl_result,
    sdk_successful_last_crawled,
    api_last_crawled,
    run_result AS api_crawl_result,
    api_successful_last_crawled,
    CASE
        WHEN icon_url_100 IS NOT NULL
            THEN
                CONCAT(
                    'https://media.appgoblin.info/app-icons/',
                    store_id,
                    '/',
                    icon_url_100
                )
        ELSE icon_url_512
    END AS app_icon_url,
    COALESCE(ad_creative_count, 0) AS ad_creative_count,
    COALESCE(ad_mon_creatives, 0) AS ad_monetized_creative_count
FROM
    frontend.store_apps_overview
WHERE
    store_id = :store_id;
