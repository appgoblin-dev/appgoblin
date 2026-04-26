WITH creative_clusters AS (
    SELECT
        ac.vhash,
        ac.file_extension,
        -- Most common md5 within each vhash+file_extension cluster
        MODE() WITHIN GROUP (ORDER BY ac.md5_hash) AS representative_md5,
        COUNT(DISTINCT ac.pub_store_id) AS unique_publisher_apps,
        COUNT(DISTINCT ac.advertiser_store_id) AS unique_advertisers,
        COUNT(DISTINCT ac.adv_name) AS unique_adv_names,
        COUNT(DISTINCT ac.pub_name) AS unique_pub_names,
        COUNT(DISTINCT ac.host_domain) AS unique_ad_networks,
        COUNT(DISTINCT ac.ad_domain) AS unique_ad_domains,
        COUNT(DISTINCT ac.mmp_name) AS unique_mmps,

        -- Aggregate the most common value for each descriptive column
        MODE() WITHIN GROUP (ORDER BY ac.adv_name) AS top_adv_name,
        MODE() WITHIN GROUP (ORDER BY ac.advertiser_store_id)
            AS top_advertiser_store_id,
        MODE() WITHIN GROUP (ORDER BY ac.pub_name) AS top_pub_name,
        MODE() WITHIN GROUP (ORDER BY ac.host_domain) AS top_host_domain,
        MODE() WITHIN GROUP (ORDER BY ac.host_domain_company_name)
            AS top_host_domain_company,
        MODE() WITHIN GROUP (ORDER BY ac.host_domain_company_domain)
            AS top_host_domain_company_domain,
        MODE() WITHIN GROUP (ORDER BY ac.ad_domain) AS top_ad_domain,
        MODE() WITHIN GROUP (ORDER BY ac.ad_domain_company_name)
            AS top_ad_domain_company,
        MODE() WITHIN GROUP (ORDER BY ac.ad_domain_company_domain)
            AS top_ad_domain_company_domain,
        MODE() WITHIN GROUP (ORDER BY ac.mmp_name) AS top_mmp_name,
        MODE() WITHIN GROUP (ORDER BY ac.mmp_domain) AS top_mmp_domain,
        MODE() WITHIN GROUP (ORDER BY sao.category) AS advertiser_category,

        -- Pull a representative icon URL for dashboard rendering
        MODE() WITHIN GROUP (ORDER BY ac.adv_icon_url_100) AS adv_icon_url_100,
        MODE() WITHIN GROUP (ORDER BY ac.pub_icon_url_100) AS pub_icon_url_100,

        MIN(ac.run_at) AS first_seen_at,
        MAX(ac.run_at) AS last_seen_at

    FROM frontend.advertiser_creatives AS ac
    LEFT JOIN frontend.store_apps_overview AS sao
        ON ac.advertiser_store_id = sao.store_id
    WHERE
        (
            CAST(:app_category AS text) IS NULL
            OR sao.category LIKE CAST(:app_category AS text)
        )
        AND (
            CAST(:file_format AS text) IS NULL
            OR (
                CAST(:file_format AS text) = 'video'
                AND ac.file_extension IN ('mp4', 'webm', 'ogg', 'avi', 'mov')
            )
            OR (
                CAST(:file_format AS text) = 'image'
                AND ac.file_extension IN (
                    'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'
                )
            )
            OR (
                CAST(:file_format AS text) = 'html'
                AND ac.file_extension IN ('html', 'htm')
            )
        )
        AND (
            CAST(:company AS text) IS NULL
            OR ac.host_domain ILIKE CAST(:company AS text)
            OR ac.host_domain_company_name ILIKE CAST(:company AS text)
            OR ac.ad_domain ILIKE CAST(:company AS text)
            OR ac.ad_domain_company_name ILIKE CAST(:company AS text)
            OR ac.mmp_name ILIKE CAST(:company AS text)
            OR ac.mmp_domain ILIKE CAST(:company AS text)
            OR ac.adv_name ILIKE CAST(:company AS text)
        )
    GROUP BY ac.vhash, ac.file_extension
)

SELECT *
FROM creative_clusters
ORDER BY unique_publisher_apps DESC, last_seen_at DESC
LIMIT :mylimit;
