-- Build user-day funnel from raw event-level table
SELECT
    CAST(dt AS DATE) AS dt_day,
    client_id,
    ab_group,
    SUM(CASE WHEN event_type = 'home_view' THEN 1 ELSE 0 END) AS home_view,
    SUM(CASE WHEN event_type = 'offer_impression' THEN 1 ELSE 0 END) AS impressions,
    SUM(CASE WHEN event_type = 'offer_click' THEN 1 ELSE 0 END) AS clicks,
    SUM(CASE WHEN event_type = 'offer_apply' THEN 1 ELSE 0 END) AS applies,
    SUM(CASE WHEN event_type = 'offer_approved' THEN 1 ELSE 0 END) AS approvals,
    SUM(CASE WHEN event_type = 'revenue' THEN COALESCE(value, 0) ELSE 0 END) AS revenue
FROM data_raw_fintech_credit_offer
GROUP BY 1, 2, 3
ORDER BY 1, 2;
