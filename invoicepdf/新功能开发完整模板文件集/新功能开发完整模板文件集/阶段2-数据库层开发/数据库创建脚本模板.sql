-- =============================================
-- 创建{业务模块}表
-- 创建时间：{创建时间}
-- 创建人：{创建人}
-- 描述：{业务模块}管理表
-- =============================================

-- 创建{业务模块}表
CREATE TABLE IF NOT EXISTS {业务模块} (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    {字段1} VARCHAR(50) NOT NULL UNIQUE,
    {字段2} VARCHAR(200) NOT NULL,
    {字段3} TEXT,
    {字段4} INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES user(id) ON DELETE SET NULL,
    updated_by UUID REFERENCES user(id) ON DELETE SET NULL
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_{业务模块}_{字段1} ON {业务模块}({字段1});
CREATE INDEX IF NOT EXISTS idx_{业务模块}_active ON {业务模块}(is_active);
CREATE INDEX IF NOT EXISTS idx_{业务模块}_{字段4} ON {业务模块}({字段4});
CREATE INDEX IF NOT EXISTS idx_{业务模块}_created_at ON {业务模块}(created_at);

-- 添加表注释
COMMENT ON TABLE {业务模块} IS '{业务模块}管理表';
COMMENT ON COLUMN {业务模块}.id IS '主键ID';
COMMENT ON COLUMN {业务模块}.{字段1} IS '{字段1}描述';
COMMENT ON COLUMN {业务模块}.{字段2} IS '{字段2}描述';
COMMENT ON COLUMN {业务模块}.{字段3} IS '{字段3}描述';
COMMENT ON COLUMN {业务模块}.{字段4} IS '{字段4}描述';
COMMENT ON COLUMN {业务模块}.is_active IS '是否启用';
COMMENT ON COLUMN {业务模块}.created_at IS '创建时间';
COMMENT ON COLUMN {业务模块}.updated_at IS '更新时间';
COMMENT ON COLUMN {业务模块}.created_by IS '创建人ID';
COMMENT ON COLUMN {业务模块}.updated_by IS '修改人ID';

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_{业务模块}_updated_at 
    BEFORE UPDATE ON {业务模块}
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 插入初始数据（可选）
-- INSERT INTO {业务模块} ({字段1}, {字段2}, {字段3}, {字段4}) VALUES 
-- ('DEFAULT', '默认{业务模块}', '系统默认{业务模块}', 0);
