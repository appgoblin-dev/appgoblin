WITH target_app AS (
    SELECT id AS store_app
    FROM
        frontend.store_apps_overview
    WHERE
        store_id = :store_id
),

versions AS (
    SELECT
        vc.id AS version_code_id,
        vc.created_at AS version_code_created_at,
        DENSE_RANK() OVER (
            ORDER BY vc.created_at, vc.id
        ) AS version_seq
    FROM version_codes AS vc
    INNER JOIN target_app AS ta ON vc.store_app = ta.store_app
    WHERE
        EXISTS (
            SELECT 1
            FROM adtech.app_sdks AS ap
            WHERE ap.store_app = ta.store_app AND ap.version_code_id = vc.id
        )
        OR (
            vc.version_code != '-1'
            AND EXISTS (
                SELECT 1
                FROM version_code_sdk_scan_results AS vcssr
                WHERE
                    vcssr.version_code_id = vc.id
                    AND vcssr.scan_result = 1
            )
        )
),

all_versions AS (
    SELECT DISTINCT
        vc.id AS version_code_id,
        vc.created_at AS version_code_created_at,
        vc.version_code,
        DENSE_RANK() OVER (
            ORDER BY
                vc.created_at,
                vc.id
        ) AS version_seq
    FROM
        version_codes AS vc
    INNER JOIN target_app AS ta
        ON
            vc.store_app = ta.store_app
    WHERE
        version_code != '-1'
),

last_scan_success AS (
    SELECT
        vcssr.version_code_id,
        vcssr.scan_result AS sdk_scan_result,
        MAX(vcssr.scanned_at) AS last_scanned_at
    FROM
        version_code_sdk_scan_results AS vcssr
    INNER JOIN all_versions AS av
        ON
            vcssr.version_code_id = av.version_code_id
    WHERE vcssr.scan_result = 1
    GROUP BY 1, 2
),

sdks AS (
    SELECT DISTINCT ap.sdk_id
    FROM
        adtech.app_sdks AS ap
    INNER JOIN target_app AS ta ON
        ap.store_app = ta.store_app
),

grid AS (
    SELECT
        v.version_code_id,
        v.version_code_created_at,
        v.version_seq,
        s.sdk_id,
        CASE
            WHEN a.sdk_id IS NOT NULL THEN 1
            ELSE 0
        END AS present
    FROM
        versions AS v
    CROSS JOIN sdks AS s
    LEFT JOIN adtech.app_sdks AS a
        ON
            v.version_code_id = a.version_code_id
            AND s.sdk_id = a.sdk_id
            AND a.store_app = (
                SELECT store_app
                FROM
                    target_app
            )
),

changes AS (
    SELECT
        *,
        LAG(present) OVER (
            PARTITION BY sdk_id
            ORDER BY
                version_seq
        ) AS prev_present
    FROM
        grid
),

myall AS (
    SELECT
        co.name AS company_name,
        d.domain_name AS company_domain,
        sd.sdk_name,
        changes.version_code_id,
        --		vc.version_code,
        changes.version_code_created_at,
        CASE
            WHEN
                present = 1
                AND changes.version_seq = 1 THEN 'added_initial'
            WHEN
                present = 1
                AND COALESCE(prev_present, 0) = 0 THEN 'added'
            WHEN
                present = 0
                AND prev_present = 1 THEN 'removed'
        END AS status
    FROM
        changes
    LEFT JOIN adtech.sdks AS sd
        ON
            changes.sdk_id = sd.id
    LEFT JOIN adtech.companies AS co
        ON
            sd.company_id = co.id
    LEFT JOIN domains AS d
        ON
            co.domain_id = d.id
    WHERE
        (
            present = 1
            AND (
                prev_present IS NULL
                OR prev_present = 0
            )
        )
        OR (
            present = 0
            AND prev_present = 1
        )
)

SELECT
    ma.company_name,
    ma.company_domain,
    ma.sdk_name,
    av.version_code,
    av.version_code_created_at,
    ls.sdk_scan_result,
    ma.status
FROM all_versions AS av
LEFT JOIN myall AS ma ON av.version_code_id = ma.version_code_id
LEFT JOIN last_scan_success AS ls
    ON
        av.version_code_id = ls.version_code_id
ORDER BY
    av.version_code_created_at DESC;
