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
INNER JOIN store_apps AS sa ON sa.id = ac.store_app
INNER JOIN domains AS observed_domain ON observed_domain.domain_name = ac.tld_url
WHERE
    sa.store = 1
    AND sa.store_id IS NOT NULL
    AND ac.called_at IS NOT NULL
    AND EXISTS (
        SELECT 1
        FROM adtech.company_domain_mapping AS mapping
        INNER JOIN adtech.companies AS company ON company.id = mapping.company_id
        INNER JOIN domains AS primary_domain ON primary_domain.id = company.domain_id
        LEFT JOIN adtech.companies AS parent ON parent.id = company.parent_company_id
        LEFT JOIN domains AS parent_domain ON parent_domain.id = parent.domain_id
        WHERE
            mapping.domain_id = observed_domain.id
            AND (
                (:is_secondary AND observed_domain.domain_name = :company_domain)
                OR (NOT :is_secondary AND primary_domain.domain_name = :company_domain)
                OR (NOT :is_secondary AND :is_parent AND parent_domain.domain_name = :company_domain)
            )
    )
ORDER BY ac.called_at DESC, ac.id DESC
LIMIT :sample_limit;
