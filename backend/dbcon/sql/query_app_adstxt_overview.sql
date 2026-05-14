WITH all_apps AS (
    SELECT DISTINCT
        sa.store_id,
        c.name AS company_name,
        ad.domain_name AS ad_domain_url,
        aae.relationship
    FROM
        frontend.adstxt_entries_store_apps AS aesa
    LEFT JOIN store_apps AS sa
        ON
            aesa.store_app = sa.id
    LEFT JOIN app_ads_entrys AS aae
        ON
            aesa.app_ad_entry_id = aae.id
    LEFT JOIN adtech.company_domain_mapping AS cdm
        ON aesa.ad_domain_id = cdm.domain_id
    LEFT JOIN adtech.companies AS c
        ON
            cdm.company_id = c.id
    LEFT JOIN domains AS ad ON
        aesa.ad_domain_id = ad.id
)

SELECT
    ad_domain_url AS company_domain,
    company_name,
    relationship,
    count(*)
FROM
    all_apps
WHERE
    store_id = :store_id
GROUP BY
    ad_domain_url,
    company_name,
    relationship;
