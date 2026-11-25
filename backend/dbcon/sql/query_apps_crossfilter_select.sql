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
    sao.tv_supported,
    sao.is_removed,
    sao.developer_name,
    sao.developer_id,
    sao.developer_url,
    sao.store,
    sao.icon_64,
    sao.monthly_ad_revenue
    + sao.monthly_iap_revenue AS estimated_monthly_revenue
