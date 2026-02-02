SELECT 
	adapter_string,
    adapter_company_domain,
    adapter_company_name,
	adapter_logo_url,
	app_category,
	app_count
     FROM frontend.mediation_adapter_app_counts maac 
WHERE mediation_company_domain = :company_domain
     ;