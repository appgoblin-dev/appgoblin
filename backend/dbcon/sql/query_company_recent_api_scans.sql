SELECT
    sa.store,
    sa.store_id,
    sa.name,
    sa.icon_64,
    scan.run_at AS scanned_at
FROM version_code_api_scan_results AS scan
INNER JOIN version_codes AS version ON scan.version_code_id = version.id
INNER JOIN store_apps AS sa ON version.store_app = sa.id
WHERE
    sa.store = 1
    AND scan.run_at IS NOT NULL
    AND sa.store_id IS NOT NULL
    AND EXISTS (
        SELECT 1
        FROM api_calls AS ac
        INNER JOIN
            domains AS observed_domain
            ON ac.tld_url = observed_domain.domain_name
        INNER JOIN
            adtech.company_domain_mapping AS mapping
            ON observed_domain.id = mapping.domain_id
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
            ac.run_id = scan.id
            AND ac.store_app = sa.id
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
ORDER BY scan.run_at DESC, scan.id DESC
LIMIT :sample_limit;
