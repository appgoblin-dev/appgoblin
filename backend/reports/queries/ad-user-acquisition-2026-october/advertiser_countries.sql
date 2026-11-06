WITH advertiser_store_apps AS (
    SELECT DISTINCT cr.advertiser_store_app_id
    FROM creative_records AS cr
    LEFT JOIN api_calls AS ac ON cr.api_call_id = ac.id
    LEFT JOIN version_code_api_scan_results AS vcasr ON ac.run_id = vcasr.id
    WHERE
        cr.advertiser_store_app_id IS NOT NULL
        AND vcasr.run_at >= :start_date
        AND vcasr.run_at < :next_month_start_date
)

SELECT
    cc.alpha2 AS country_code,
    count(*) AS advertiser_count
FROM advertiser_store_apps AS asa
LEFT JOIN
    frontend.store_apps_overview AS saa
    ON asa.advertiser_store_app_id = saa.id
LEFT JOIN countries AS cc ON saa.country_id = cc.id
WHERE cc.alpha2 IS NOT NULL
GROUP BY cc.alpha2
ORDER BY advertiser_count DESC;
