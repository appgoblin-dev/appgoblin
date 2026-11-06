SELECT
    ac.called_at,
    ac.run_id,
    vcasr.run_at,
    vc.version_code,
    c.name AS company_name,
    cd.domain_name AS company_domain,
    c.logo_url AS company_logo_url,
    ac.tld_url,
    ac.url,
    cc.alpha2 AS country,
    ips.org AS servers,
    ac.request_mime_type,
    ac.response_mime_type,
    ca.md5_hash AS creative_md5_hash,
    ca.file_extension AS creative_file_extension,
    saa.store_id AS advertiser_store_id,
    saa.icon_64 AS advertiser_icon_url_100
FROM
    api_calls AS ac
LEFT JOIN store_apps AS sa ON ac.store_app = sa.id
LEFT JOIN version_code_api_scan_results AS vcasr ON ac.run_id = vcasr.id
LEFT JOIN version_codes AS vc ON vcasr.version_code_id = vc.id
LEFT JOIN domains AS ad ON ac.tld_url = ad.domain_name
LEFT JOIN adtech.company_domain_mapping AS cdm ON ad.id = cdm.domain_id
LEFT JOIN adtech.companies AS c ON cdm.company_id = c.id
LEFT JOIN domains AS cd ON c.domain_id = cd.id
LEFT JOIN ip_geo_snapshots AS ips ON ac.ip_geo_snapshot_id = ips.id
LEFT JOIN creative_records AS cr ON ac.id = cr.api_call_id
LEFT JOIN countries AS cc ON ips.country_id = cc.id
LEFT JOIN creative_assets AS ca ON cr.creative_asset_id = ca.id
LEFT JOIN store_apps AS saa ON cr.advertiser_store_app_id = saa.id
WHERE
    sa.store_id = :store_id;
