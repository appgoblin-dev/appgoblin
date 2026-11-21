SELECT
    ac.tld_url,
    ac.url,
    ac.called_at,
    sa.store_id,
    sa.name,
    sa.icon_64,
    ac.request_mime_type,
    ac.response_mime_type
FROM api_calls AS ac
INNER JOIN store_apps AS sa ON ac.store_app = sa.id
INNER JOIN
    domains AS observed_domain
    ON ac.tld_url = observed_domain.domain_name
WHERE
    sa.store = 1
    AND sa.store_id IS NOT NULL
    AND ac.called_at IS NOT NULL
    AND EXISTS (
        SELECT 1
        FROM adtech.company_domain_mapping AS mapping
        INNER JOIN
            adtech.companies AS company
            ON mapping.company_id = company.id
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
            mapping.domain_id = observed_domain.id
            AND (
                (
                    :is_secondary
                    AND observed_domain.domain_name = :company_domain
                )
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
ORDER BY ac.called_at DESC, ac.id DESC
LIMIT :sample_limit;
