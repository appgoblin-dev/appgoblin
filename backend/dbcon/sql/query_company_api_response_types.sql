SELECT
    response.company_domain,
    response.tld_url,
    response.response_type,
    COALESCE(response.app_count_30d, 0) AS app_count_30d,
    COALESCE(response.observed_call_count_30d, 0) AS observed_call_count_30d,
    COALESCE(response.app_count_alltime, 0) AS app_count_alltime,
    COALESCE(response.observed_call_count_alltime, 0)
        AS observed_call_count_alltime
FROM frontend.api_call_response_types AS response
WHERE
    EXISTS (
        SELECT 1
        FROM adtech.companies AS company
        INNER JOIN
            domains AS primary_domain
            ON company.domain_id = primary_domain.id
        LEFT JOIN
            adtech.companies AS parent
            ON company.parent_company_id = parent.id
        LEFT JOIN
            domains AS parent_domain
            ON parent.domain_id = parent_domain.id
        WHERE
            primary_domain.domain_name = response.company_domain
            AND EXISTS (
                SELECT 1
                FROM adtech.company_domain_mapping AS mapping
                INNER JOIN
                    domains AS observed_domain
                    ON mapping.domain_id = observed_domain.id
                WHERE
                    mapping.company_id = company.id
                    AND observed_domain.domain_name = response.tld_url
            )
            AND (
                (:is_secondary AND response.tld_url = :company_domain)
                OR (
                    NOT :is_secondary
                    AND primary_domain.domain_name = :company_domain
                )
                OR (
                    NOT :is_secondary
                    AND :is_parent
                    AND parent_domain.domain_name = :company_domain
                )
            )
    )
    OR (
        response.tld_url = :company_domain
        AND response.company_domain = response.tld_url
        AND NOT EXISTS (
            SELECT 1
            FROM adtech.company_domain_mapping AS mapping
            INNER JOIN
                domains AS observed_domain
                ON mapping.domain_id = observed_domain.id
            WHERE observed_domain.domain_name = response.tld_url
        )
    )
ORDER BY
    COALESCE(response.app_count_30d, 0) DESC,
    COALESCE(response.observed_call_count_30d, 0) DESC,
    COALESCE(response.app_count_alltime, 0) DESC,
    COALESCE(response.observed_call_count_alltime, 0) DESC,
    response.company_domain,
    CASE WHEN response.tld_url IS NULL THEN 1 ELSE 0 END,
    response.tld_url ASC,
    CASE WHEN response.response_type IS NULL THEN 1 ELSE 0 END,
    response.response_type ASC
LIMIT 20;
