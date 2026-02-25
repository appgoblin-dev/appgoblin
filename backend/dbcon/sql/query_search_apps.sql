-- noqa: disable=LT02
-- noqa: disable=LT08
-- noqa: disable=RF02
-- noqa: disable=PRS
-- SQLFluff currently unable to parse the double @ below
-- https://github.com/sqlfluff/sqlfluff/issues/4837
WITH apps AS (
    SELECT *
    FROM frontend.store_apps_overview
    WHERE
        textsearchable @@ to_tsquery('simple', :searchinput) AND store IN (1, 2)
),
ranked_apps AS (
    SELECT
        a.*,
        row_number() OVER (
            PARTITION BY a.store
            ORDER BY
                a.installs_sum_4w DESC NULLS LAST
        ) AS store_rank,
        row_number() OVER (
            ORDER BY
                a.store ASC,
                a.installs_sum_4w DESC NULLS LAST
        ) % (SELECT count(DISTINCT store) FROM apps) AS round_robin_rank
    FROM apps AS a
)
SELECT
    store,
    store_id,
    name,
    developer_name,
    icon_url_100,
    icon_url_512,
    featured_image_url,
    installs,
    rating,
    rating_count
FROM ranked_apps
ORDER BY store_rank, round_robin_rank
LIMIT :mylimit;
