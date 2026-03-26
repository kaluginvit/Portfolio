-- Group-level aggregates for dashboard / validation
SELECT
    ab_group,
    COUNT(DISTINCT client_id) AS users,
    AVG(cr_apply) AS mean_cr_apply,
    VAR_SAMP(cr_apply) AS var_cr_apply,
    AVG(ctr) AS mean_ctr,
    VAR_SAMP(ctr) AS var_ctr,
    AVG(cr_home_apply) AS mean_cr_home_apply,
    VAR_SAMP(cr_home_apply) AS var_cr_home_apply,
    AVG(approval_rate) AS mean_approval_rate,
    VAR_SAMP(approval_rate) AS var_approval_rate,
    AVG(arpu) AS mean_arpu,
    VAR_SAMP(arpu) AS var_arpu
FROM user_level_metrics
GROUP BY 1
ORDER BY 1;
