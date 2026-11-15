SELECT
    c.name AS company_name,
    ad.domain_name AS ad_domain_url,
    aae.publisher_id,
    aae.relationship,
    pdcr.crawled_at AS developer_domain_crawled_at
FROM
    frontend.adstxt_domain_entries AS aesa
LEFT JOIN app_urls_map AS aum ON aesa.pub_domain_id = aum.pub_domain
LEFT JOIN store_apps AS sa
    ON
        aum.store_app = sa.id
LEFT JOIN app_ads_entrys AS aae
    ON
        aesa.app_ad_entry_id = aae.id
LEFT JOIN domains AS ad
    ON
        aesa.ad_domain_id = ad.id
LEFT JOIN adstxt_crawl_results AS pdcr
    ON
        aesa.pub_domain_id = pdcr.domain_id
LEFT JOIN adtech.company_domain_mapping AS cdm
    ON ad.id = cdm.domain_id
LEFT JOIN adtech.companies AS c
    ON
        cdm.company_id = c.id
WHERE
    sa.store_id = :store_id
    AND UPPER(aae.relationship) = :relationship;
