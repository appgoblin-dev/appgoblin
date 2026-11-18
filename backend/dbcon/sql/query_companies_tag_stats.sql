--  This table has two types of potential rows that are merged
--  For example, example.com is a company that has it's own data
--  but if example.com is also a parent
--  Then it makes more sense to show the parent company data, and exclude the example.com only data
--  This make sense here where we are exporting a single flat overview DF data
WITH all_company_stats AS (
    SELECT
        ccts.company_domain,
        ccts.store,
        ccts.app_category,
        ccts.tag_source,
        COALESCE(ccts.company_name, ccts.company_domain) AS company_name,
        COALESCE(parent_domain.domain_name, resolved_domain.domain_name)
            AS parent_company_domain,
        COALESCE(parent_company.name, resolved_company.name)
            AS parent_company_name,
        COALESCE(SUM(ccts.app_count), 0) AS app_count,
        COALESCE(SUM(ccts.installs_d30), 0) AS installs_d30
    FROM frontend.companies_category_tag_stats AS ccts
    LEFT JOIN domains AS input_domain
        ON ccts.company_domain = input_domain.domain_name
    LEFT JOIN adtech.company_domain_mapping AS cdm
        ON input_domain.id = cdm.domain_id
    LEFT JOIN adtech.companies AS resolved_company
        ON cdm.company_id = resolved_company.id
    LEFT JOIN domains AS resolved_domain
        ON resolved_company.domain_id = resolved_domain.id
    LEFT JOIN adtech.companies AS parent_company
        ON resolved_company.parent_company_id = parent_company.id
    LEFT JOIN domains AS parent_domain
        ON parent_company.domain_id = parent_domain.id
    WHERE
        ccts.store IN (1, 2)
        AND ccts.tag_source IS DISTINCT FROM 'sdk_adapter'
        -- Pass NULL to get all categories, or 'game%' etc for filtered view
        AND (
            CAST(:app_category AS text) IS NULL
            OR ccts.app_category LIKE :app_category
        )
    GROUP BY
        ccts.company_domain,
        ccts.company_name,
        resolved_domain.domain_name,
        resolved_company.name,
        parent_domain.domain_name,
        parent_company.name,
        ccts.store,
        ccts.app_category,
        ccts.tag_source
),

parent_stats AS (
    SELECT
        company_domain,
        COALESCE(company_name, company_domain) AS company_name,
        company_domain AS parent_company_domain,
        COALESCE(company_name, company_domain) AS parent_company_name,
        store,
        app_category,
        tag_source,
        COALESCE(SUM(app_count), 0) AS app_count,
        COALESCE(SUM(installs_d30), 0) AS installs_d30
    FROM frontend.companies_parent_category_tag_stats
    WHERE
        store IN (1, 2)
        AND tag_source IS DISTINCT FROM 'sdk_adapter'
        AND (
            CAST(:app_category AS text) IS NULL
            OR app_category LIKE :app_category
        )
    GROUP BY company_domain, company_name, store, app_category, tag_source
),

parent_domains AS (
    SELECT DISTINCT company_domain
    FROM frontend.companies_parent_category_tag_stats
    WHERE tag_source IS DISTINCT FROM 'sdk_adapter'
),

unioned AS (
    SELECT * FROM parent_stats

    UNION ALL

    SELECT
        company_domain,
        company_name,
        parent_company_domain,
        parent_company_name,
        store,
        app_category,
        tag_source,
        app_count,
        installs_d30
    FROM all_company_stats
    WHERE company_domain NOT IN (SELECT company_domain FROM parent_domains)
),

company_totals AS (
    SELECT
        company_domain,
        SUM(installs_d30) AS total_installs_d30,
        ROW_NUMBER() OVER (ORDER BY SUM(installs_d30) DESC) AS company_rank
    FROM unioned
    WHERE
        company_domain IS NOT NULL
        AND company_domain NOT LIKE 'no-%'
    GROUP BY company_domain
)

SELECT
    u.company_domain,
    u.company_name,
    u.store,
    -- When no category filter, collapse all categories into 'all'
    CASE
        WHEN CAST(:app_category AS text) IS NULL THEN 'all' ELSE u.app_category
    END
        AS app_category,
    u.tag_source,
    u.parent_company_domain,
    u.parent_company_name,
    SUM(u.app_count) AS app_count,
    SUM(u.installs_d30) AS installs_d30,
    ct.company_rank
FROM unioned AS u
INNER JOIN company_totals AS ct
    ON u.company_domain = ct.company_domain
WHERE
    ct.company_rank <= 1000
    AND u.company_domain IS NOT NULL
    AND u.company_domain NOT LIKE 'no-%'
GROUP BY
    u.company_domain,
    u.company_name,
    u.store,
    CASE
        WHEN CAST(:app_category AS text) IS NULL THEN 'all' ELSE u.app_category
    END,
    u.tag_source,
    u.parent_company_domain,
    u.parent_company_name,
    ct.company_rank
ORDER BY ct.company_rank ASC, u.store ASC, u.tag_source ASC;
