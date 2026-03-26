-- SRM check helper: expected 50/50 split by users
SELECT
    ab_group,
    COUNT(DISTINCT client_id) AS users
FROM data_raw_fintech_credit_offer
GROUP BY 1
ORDER BY 1;
