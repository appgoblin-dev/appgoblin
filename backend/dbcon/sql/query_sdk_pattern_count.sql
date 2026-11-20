SELECT COALESCE(SUM(stats.app_count), 0) AS total_count
FROM version_strings AS vs
INNER JOIN adtech.sdk_string_stats AS stats
    ON vs.id = stats.string_id
WHERE LOWER(vs.value_name) LIKE LOWER(:value_pattern) || '%';
