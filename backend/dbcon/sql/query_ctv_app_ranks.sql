SELECT
    car.rank_num,
    car.app_name,
    car.store_id,
    car.store,
    -- The MV stores the icon file name; alias it so extend_app_icon_url can build the URL.
    car.app_icon AS icon_64,
    car.app_category,
    car.developer_name,
    car.developer_id,
    car.rating,
    car.rating_count,
    car.installs,
    car.monthly_installs,
    car.monthly_revenue,
    car.installs_z_score_2w,
    c.alpha2 AS country_code
FROM frontend.ctv_app_ranks AS car
LEFT JOIN countries AS c ON car.country_id = c.id
WHERE car.store = :store
ORDER BY car.rank_num ASC
LIMIT :mylimit;
