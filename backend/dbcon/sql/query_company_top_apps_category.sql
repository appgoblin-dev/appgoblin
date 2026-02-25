WITH ranked_apps AS (
    SELECT *
    FROM
        frontend.company_top_apps
    WHERE
        company_domain = :company_domain
        AND app_category LIKE :mapped_category
        AND app_company_category_rank <= :mylimit
)

SELECT
    ra.company_domain,
    ra.store,
    ra.name,
    ra.store_id,
    ra.developer_name,
    ra.icon_url_100,
    ra.app_company_category_rank AS rank,
    ra.installs_d30,
    ra.sdk,
    ra.api_call,
    ra.app_ads_direct
FROM ranked_apps AS ra;
