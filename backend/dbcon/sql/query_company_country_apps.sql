WITH ranked_countries AS (
    SELECT
        store,
        country,
        app_count,
        DENSE_RANK() OVER (
            PARTITION BY domain_name, store
            ORDER BY app_count DESC, country ASC
        ) AS rnk
    FROM frontend.company_category_country_stats
    WHERE
        domain_name = :company_domain
        AND (app_category LIKE :app_category OR :app_category IS NULL)
)

SELECT
    store,
    CASE
        WHEN rnk <= 5 THEN country
        ELSE 'Others'
    END AS country,
    SUM(app_count) AS app_count
FROM ranked_countries
GROUP BY
    store,
    CASE
        WHEN rnk <= 5 THEN country
        ELSE 'Others'
    END
ORDER BY
    store ASC,
    -- Places the 'other' row at the bottom of each group
    MIN(rnk) ASC,
    app_count DESC;
