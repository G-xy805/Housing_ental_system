# ============================================
# MySQL 初始化脚本
# ============================================
# 此脚本在 MySQL 容器首次启动时自动执行
# 用于创建数据库和用户权限
# ============================================

-- 设置字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS housing_rental 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- 授予用户权限
GRANT ALL PRIVILEGES ON housing_rental.* TO 'housing_user'@'%';

-- 刷新权限
FLUSH PRIVILEGES;

-- 使用数据库
USE housing_rental;

-- 输出初始化完成信息
SELECT 'Database housing_rental initialized successfully!' AS message;
