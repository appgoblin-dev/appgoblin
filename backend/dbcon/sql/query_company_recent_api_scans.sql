SELECT
    sa.store,
    sa.store_id,
    sa.name,
    sa.icon_64,
    scan.run_at AS scanned_at
FROM version_code_api_scan_results AS scan
INNER JOIN version_codes AS version ON version.id = scan.version_code_id
INNER JOIN store_apps AS sa ON sa.id = version.store_app
WHERE
    sa.store = 1
    AND scan.run_at IS NOT NULL
    AND sa.store_id IS NOT NULL
    AND EXISTS (
        SELECT 1
        FROM api_calls AS ac
        INNER JOIN domains AS observed_domain ON observed_domain.domain_name = ac.tld_url
        INNER JOIN adtech.company_domain_mapping AS mapping ON mapping.domain_id = observed_domain.id
        INNER JOIN adtech.companies AS company ON company.id = mapping.company_id
        INNER JOIN domains AS primary_domain ON primary_domain.id = company.domain_id
        LEFT JOIN adtech.companies AS parent ON parent.id = company.parent_company_id
        LEFT JOIN domains AS parent_domain ON parent_domain.id = parent.domain_id
        WHERE
            ac.run_id = scan.id
            AND ac.store_app = sa.id
            AND (
                (:is_secondary AND observed_domain.domain_name = :company_domain)
                OR (NOT :is_secondary AND primary_domain.domain_name = :company_domain)
                OR (NOT :is_secondary AND :is_parent AND parent_domain.domain_name = :company_domain)
            )
    )
ORDER BY scan.run_at DESC, scan.id DESC
LIMIT :sample_limit;
