-- 添加 SM2 加密开关配置（默认禁用，方便开发）
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
VALUES
    (
        (SELECT IFNULL(MAX(id), 0) + 1 FROM sys_params t1),
        'server.enable_sm2_encrypt',
        'false',
        'boolean',
        1,
        '是否启用SM2加密（开发环境可设置为false，生产环境建议设置为true）',
        (SELECT id FROM sys_user WHERE username = 'admin' LIMIT 1),
        NOW(),
        (SELECT id FROM sys_user WHERE username = 'admin' LIMIT 1),
        NOW()
    )
ON DUPLICATE KEY UPDATE param_value = param_value;

