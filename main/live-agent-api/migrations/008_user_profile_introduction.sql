-- Migration: Add introduction field to user table
-- Date: 2025-02-01
-- Description: 添加用户简介字段，支持 Profile 功能

-- Add introduction column to user table
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS introduction TEXT;

-- Add comment for documentation
COMMENT ON COLUMN "user".introduction IS '用户简介/个性签名';
