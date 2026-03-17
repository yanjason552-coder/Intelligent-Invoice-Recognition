#!/bin/bash
# 数据库备份脚本
# 用于备份PostgreSQL数据库并可选上传到阿里云OSS

set -e

# 配置变量
BACKUP_DIR=${BACKUP_DIR:-/opt/invoice-app/backups}
RETENTION_DAYS=${RETENTION_DAYS:-7}
DB_CONTAINER=${DB_CONTAINER:-invoice-app-db-1}
DB_USER=${DB_USER:-postgres}
DB_NAME=${DB_NAME:-invoice_db}

# OSS配置（可选）
OSS_ENABLED=${OSS_ENABLED:-false}
OSS_BUCKET=${OSS_BUCKET:-your-bucket}
OSS_ENDPOINT=${OSS_ENDPOINT:-oss-cn-hangzhou.aliyuncs.com}
OSS_PREFIX=${OSS_PREFIX:-backups/database}

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=========================================="
echo "开始数据库备份"
echo "==========================================${NC}"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 生成备份文件名
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE=$BACKUP_DIR/postgres_${DATE}.sql
BACKUP_FILE_GZ=${BACKUP_FILE}.gz

# 检查Docker容器是否存在
if ! docker ps | grep -q $DB_CONTAINER; then
    echo -e "${RED}错误: 数据库容器 $DB_CONTAINER 未运行${NC}"
    exit 1
fi

# 执行备份
echo -e "${YELLOW}正在备份数据库...${NC}"
docker exec $DB_CONTAINER pg_dump -U $DB_USER -F p $DB_NAME > $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo -e "${GREEN}数据库备份成功: $BACKUP_FILE${NC}"
else
    echo -e "${RED}数据库备份失败${NC}"
    rm -f $BACKUP_FILE
    exit 1
fi

# 压缩备份文件
echo -e "${YELLOW}正在压缩备份文件...${NC}"
gzip $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo -e "${GREEN}备份文件压缩成功: $BACKUP_FILE_GZ${NC}"
    BACKUP_SIZE=$(du -h $BACKUP_FILE_GZ | cut -f1)
    echo "备份文件大小: $BACKUP_SIZE"
else
    echo -e "${RED}备份文件压缩失败${NC}"
    exit 1
fi

# 上传到OSS（如果启用）
if [ "$OSS_ENABLED" = "true" ]; then
    echo -e "${YELLOW}正在上传到OSS...${NC}"
    
    # 检查ossutil是否安装
    if ! command -v ossutil64 &> /dev/null && ! command -v ossutil &> /dev/null; then
        echo -e "${YELLOW}警告: ossutil未安装，跳过OSS上传${NC}"
        echo "安装ossutil: https://help.aliyun.com/document_detail/120075.html"
    else
        OSSUTIL_CMD=$(command -v ossutil64 || command -v ossutil)
        OSS_PATH="oss://$OSS_BUCKET/$OSS_PREFIX/postgres_${DATE}.sql.gz"
        
        $OSSUTIL_CMD cp $BACKUP_FILE_GZ $OSS_PATH
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}备份文件已上传到OSS: $OSS_PATH${NC}"
        else
            echo -e "${YELLOW}警告: OSS上传失败，但本地备份已保存${NC}"
        fi
    fi
fi

# 清理旧备份
echo -e "${YELLOW}清理 $RETENTION_DAYS 天前的备份...${NC}"
find $BACKUP_DIR -name "postgres_*.sql.gz" -mtime +$RETENTION_DAYS -delete
CLEANED_COUNT=$(find $BACKUP_DIR -name "postgres_*.sql.gz" | wc -l)
echo -e "${GREEN}保留的备份文件数: $CLEANED_COUNT${NC}"

# 显示备份统计
echo ""
echo -e "${GREEN}=========================================="
echo "备份完成"
echo "==========================================${NC}"
echo "备份文件: $BACKUP_FILE_GZ"
echo "文件大小: $BACKUP_SIZE"
echo "备份目录: $BACKUP_DIR"
if [ "$OSS_ENABLED" = "true" ]; then
    echo "OSS路径: oss://$OSS_BUCKET/$OSS_PREFIX/postgres_${DATE}.sql.gz"
fi
echo "保留天数: $RETENTION_DAYS"
echo "=========================================="

# 可选：发送备份通知（需要配置邮件或webhook）
# 这里可以添加发送邮件或webhook通知的代码

