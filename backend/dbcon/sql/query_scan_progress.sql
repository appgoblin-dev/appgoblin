WITH requested_version AS (
    SELECT
        vc.id,
        vc.version_code,
        vc.created_at,
        vc.updated_at,
        vc.crawl_result,
        EXISTS (
            SELECT 1
            FROM s3_file_keys AS sfk
            WHERE sfk.version_code_id = vc.id
        ) AS has_s3_key
    FROM version_codes AS vc
    INNER JOIN store_apps AS sa ON sa.id = vc.store_app
    WHERE sa.store_id = :store_id
        AND vc.created_at >= :requested_at
        AND vc.created_at <= CURRENT_TIMESTAMP
    ORDER BY vc.created_at ASC, vc.id ASC
    LIMIT 1
),
latest_sdk_scan AS (
    SELECT
        sr.version_code_id,
        sr.scanned_at,
        sr.scan_result
    FROM version_code_sdk_scan_results AS sr
    INNER JOIN requested_version AS rv ON rv.id = sr.version_code_id
    WHERE sr.scanned_at >= :requested_at
        AND sr.scanned_at <= CURRENT_TIMESTAMP
    ORDER BY sr.scanned_at DESC, sr.scan_result DESC NULLS LAST
    LIMIT 1
),
latest_waydroid_run AS (
    SELECT
        ar.version_code_id,
        ar.run_at,
        ar.run_result
    FROM version_code_api_scan_results AS ar
    INNER JOIN requested_version AS rv ON rv.id = ar.version_code_id
    WHERE ar.run_at >= :requested_at
        AND ar.run_at <= CURRENT_TIMESTAMP
    ORDER BY ar.run_at DESC, ar.run_result DESC NULLS LAST
    LIMIT 1
)
SELECT
    rv.version_code,
    rv.created_at AS version_created_at,
    rv.updated_at AS version_updated_at,
    rv.crawl_result AS version_crawl_result,
    COALESCE(rv.has_s3_key, FALSE) AS has_s3_key,
    sdk.scanned_at AS sdk_at,
    sdk.scan_result AS sdk_result,
    api.run_at AS waydroid_at,
    api.run_result AS waydroid_result
FROM (SELECT 1) AS anchor
LEFT JOIN requested_version AS rv ON TRUE
LEFT JOIN latest_sdk_scan AS sdk ON TRUE
LEFT JOIN latest_waydroid_run AS api ON TRUE
;
