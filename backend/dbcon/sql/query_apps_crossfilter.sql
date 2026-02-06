WITH 
-- Only process if domains are specified
include_apps AS (
    SELECT
        c.store_app
    FROM adtech.combined_store_apps_companies c
    WHERE
        cardinality(:include_domains ::text[]) > 0
        AND c.ad_domain = ANY(:include_domains ::text[])
        AND (
            NOT :require_sdk_api ::boolean 
            OR c.sdk = TRUE 
            OR c.api_call = TRUE
        )
    GROUP BY c.store_app
    HAVING COUNT(DISTINCT c.ad_domain) = cardinality(:include_domains ::text[])
),
exclude_apps AS (
    SELECT DISTINCT
        c.store_app
    FROM adtech.combined_store_apps_companies c
    WHERE
        cardinality(:exclude_domains ::text[]) > 0
        AND c.ad_domain = ANY(:exclude_domains ::text[])
)
SELECT
    sao.id,
    sao.store_id,
    sao.name,
    sao.installs_est as installs,
    sao.rating_count,
    sao.installs_sum_4w_est as installs_d30,
    sao.ratings_sum_4w AS ratings_d30,
    sao.in_app_purchases,
    sao.ad_supported,
    sao.store,
    sao.icon_url_100
FROM frontend.store_apps_overview sao
WHERE EXISTS (
  SELECT 1
  FROM include_apps ia
  WHERE ia.store_app = sao.id
)
AND
    sao.store_last_updated > :mydate ::date
    AND (NOT :require_iap ::boolean OR sao.in_app_purchases = TRUE)
    AND (NOT :require_ads ::boolean OR sao.ad_supported = TRUE)
    AND (:category ::text IS NULL OR sao.category = :category)
    AND (:store ::int IS NULL OR sao.store = :store)
    AND (:min_installs ::bigint IS NULL OR :min_installs = 0 OR sao.installs_est >= :min_installs)
    AND (:max_installs ::bigint IS NULL OR sao.installs_est <= :max_installs)
    AND (:min_rating_count ::bigint IS NULL OR sao.rating_count >= :min_rating_count)
    AND (:max_rating_count ::bigint IS NULL OR sao.rating_count <= :max_rating_count)
    AND (:min_installs_d30 ::bigint IS NULL OR sao.installs_sum_4w_est >= :min_installs_d30)
    AND (:max_installs_d30 ::bigint IS NULL OR sao.installs_sum_4w_est <= :max_installs_d30)
    -- Exclusion check
    AND NOT EXISTS (
        SELECT 1 FROM exclude_apps ea WHERE ea.store_app = sao.id
    )
ORDER BY
    installs_est DESC
LIMIT 100;