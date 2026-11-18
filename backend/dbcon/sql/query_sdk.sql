SELECT
    asd.sdk_id,
    sd.sdk_name,
    sa.store,
    sa.store_id,
    sa.name AS app_name,
    sa.category,
    sa.is_removed,
    sa.developer_name,
    sa.installs,
    sa.installs_sum_4w,
    CONCAT(
        'https://media.appgoblin.info/app-icons/',
        sa.store_id,
        '/',
        sa.icon_64
    ) AS app_icon_url
FROM adtech.app_sdks_latestq AS asd
JOIN adtech.sdks AS sd
    ON asd.sdk_id = sd.id
LEFT JOIN frontend.store_apps_overview AS sa
    ON asd.store_app = sa.id
WHERE asd.sdk_id = :sdk_id
LIMIT :mylimit;