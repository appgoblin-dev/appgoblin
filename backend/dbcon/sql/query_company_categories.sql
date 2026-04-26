SELECT DISTINCT
    c2.name AS company_type,
    c2.url_slug as company_type_slug,
    d.domain_name AS company_domain
FROM
    adtech.company_categories cc
LEFT JOIN adtech.companies c ON cc.company_id = c.id
LEFT JOIN domains d ON c.domain_id = d.id
LEFT JOIN adtech.categories c2 ON cc.category_id = c2.id
WHERE
    d.domain_name IS NOT NULL
    AND c2.url_slug IS NOT NULL;