SELECT
    agmh.week_start,
    agmh.weekly_installs,
    agmh.weekly_ratings,
    agmh.weekly_reviews,
    agmh.weekly_active_users,
    agmh.monthly_active_users,
    agmh.weekly_ad_revenue,
    agmh.weekly_iap_revenue,
    agmh.total_installs AS cumulative_installs,
    agmh.total_ratings AS cumulative_ratings,
    agmh.rating,
    agmh.one_star,
    agmh.two_star,
    agmh.three_star,
    agmh.four_star,
    agmh.five_star
FROM app_global_metrics_weekly AS agmh
INNER JOIN store_apps AS sa ON agmh.store_app = sa.id
WHERE
    sa.store_id = :store_id
    AND agmh.week_start >= CURRENT_DATE - INTERVAL '375 days'
ORDER BY agmh.week_start;
