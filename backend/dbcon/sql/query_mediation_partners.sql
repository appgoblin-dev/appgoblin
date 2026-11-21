SELECT
    mediation_domain,
    COALESCE(SUM(app_count), 0) AS app_count
FROM frontend.mediation_adapter_app_counts
WHERE
    adapter_domain = :company_domain
    AND mediation_domain IS NOT NULL
GROUP BY mediation_domain
ORDER BY app_count DESC, mediation_domain ASC;
