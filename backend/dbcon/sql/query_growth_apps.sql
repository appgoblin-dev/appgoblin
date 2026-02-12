SELECT
    store_id,
    app_name,
    developer_name,
    app_category,
    in_app_purchases,
    ad_supported,
    icon_url_100,
    installs,
    rating_count,
    installs_sum_1w,
    ratings_sum_1w,
    installs_avg_2w,
    ratings_avg_2w,
    installs_z_score_2w,
    ratings_z_score_2w,
    installs_sum_4w,
    ratings_sum_4w,
    installs_avg_4w,
    ratings_avg_4w,
    installs_z_score_4w,
    ratings_z_score_4w
FROM frontend.z_scores_top_apps
WHERE
    store = :store
    AND (app_category = :app_category OR :app_category IS NULL)
ORDER BY
    COALESCE(
        COALESCE(installs_z_score_2w, 0), COALESCE(ratings_z_score_2w, 0)
    ) DESC
LIMIT 100;
