SELECT
    myregion,
    bucket,
    file_key,
    report_name,
    row_count,
    last_modified
FROM public.s3_reports
WHERE domain_name = :company_domain
ORDER BY report_name, file_key;
