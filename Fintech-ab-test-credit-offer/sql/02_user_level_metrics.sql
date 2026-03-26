-- Build user-level metrics from user-day funnel
WITH user_level AS (
    SELECT
        client_id,
        ab_group,
        SUM(home_view) AS home_view,
        SUM(impressions) AS impressions,
        SUM(clicks) AS clicks,
        SUM(applies) AS applies,
        SUM(approvals) AS approvals,
        SUM(revenue) AS revenue
    FROM user_day_funnel
    GROUP BY 1, 2
)
SELECT
    *,
    CASE WHEN impressions > 0 THEN clicks * 1.0 / impressions ELSE 0 END AS ctr,
    CASE WHEN impressions > 0 THEN applies * 1.0 / impressions ELSE 0 END AS cr_apply,
    CASE WHEN home_view > 0 THEN applies * 1.0 / home_view ELSE 0 END AS cr_home_apply,
    CASE WHEN applies > 0 THEN approvals * 1.0 / applies ELSE 0 END AS approval_rate,
    revenue AS arpu
FROM user_level
ORDER BY ab_group, client_id;
