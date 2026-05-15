SELECT
    ccts.company_domain,
    ccts.company_name,
    ccts.store,
    'all' AS app_category,
    ccts.tag_source,
    COALESCE(parent_domain.domain_name, resolved_domain.domain_name)
        AS parent_company_domain,
    COALESCE(parent_company.name, resolved_company.name) AS parent_company_name,
    COALESCE(SUM(ccts.app_count), 0) AS app_count,
    COALESCE(SUM(ccts.installs_d30), 0) AS installs_d30
FROM
    frontend.companies_category_tag_stats AS ccts
LEFT JOIN domains AS input_domain
    ON
        ccts.company_domain = input_domain.domain_name
LEFT JOIN adtech.company_domain_mapping AS cdm
    ON
        input_domain.id = cdm.domain_id
LEFT JOIN adtech.companies AS resolved_company
    ON
        cdm.company_id = resolved_company.id
LEFT JOIN domains AS resolved_domain
    ON
        resolved_company.domain_id = resolved_domain.id
LEFT JOIN adtech.companies AS parent_company
    ON
        resolved_company.parent_company_id = parent_company.id
LEFT JOIN domains AS parent_domain
    ON
        parent_company.domain_id = parent_domain.id
WHERE
    ccts.store IN (
        1, 2
    )
GROUP BY
    ccts.company_domain,
    ccts.company_name,
    resolved_domain.domain_name,
    resolved_company.name,
    parent_domain.domain_name,
    parent_company.name,
    ccts.store,
    ccts.tag_source;
