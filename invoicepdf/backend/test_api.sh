#!/bin/bash
# 票据识别系统API测试脚本 (Linux/Mac)
# 使用方法: chmod +x test_api.sh && ./test_api.sh

BASE_URL="${BASE_URL:-http://localhost:8000}"
USERNAME="${USERNAME:-test@example.com}"
PASSWORD="${PASSWORD:-test123456}"

echo "========================================"
echo "  票据识别系统 API 测试脚本"
echo "========================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# 1. 登录获取Token
echo -e "${YELLOW}步骤1: 登录获取Token...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USERNAME&password=$PASSWORD")

if [ $? -ne 0 ]; then
  echo -e "${RED}✗ 登录失败: 无法连接到服务器${NC}"
  echo "请检查："
  echo "  1. 后端服务是否启动 ($BASE_URL)"
  echo "  2. 网络连接是否正常"
  exit 1
fi

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo -e "${RED}✗ 登录失败: 无法获取Token${NC}"
  echo "响应: $LOGIN_RESPONSE"
  exit 1
fi

echo -e "${GREEN}✓ 登录成功，Token已获取${NC}"
echo ""

# 2. 查询票据列表
echo -e "${YELLOW}步骤2: 查询票据列表...${NC}"
INVOICES=$(curl -s -X GET "$BASE_URL/api/v1/invoices/query?skip=0&limit=10" \
  -H "Authorization: Bearer $TOKEN")

if [ $? -eq 0 ]; then
  COUNT=$(echo $INVOICES | grep -o '"count":[0-9]*' | cut -d':' -f2)
  echo -e "${GREEN}✓ 查询成功，找到 $COUNT 条记录${NC}"
else
  echo -e "${RED}✗ 查询失败${NC}"
fi
echo ""

# 3. 获取OCR配置
echo -e "${YELLOW}步骤3: 获取OCR配置...${NC}"
CONFIG=$(curl -s -X GET "$BASE_URL/api/v1/config/ocr" \
  -H "Authorization: Bearer $TOKEN")

if [ $? -eq 0 ]; then
  PROVIDER=$(echo $CONFIG | grep -o '"provider":"[^"]*' | cut -d'"' -f4)
  echo -e "${GREEN}✓ 获取配置成功${NC}"
  echo -e "${GRAY}  Provider: $PROVIDER${NC}"
else
  echo -e "${RED}✗ 获取配置失败${NC}"
fi
echo ""

# 4. 获取模板列表
echo -e "${YELLOW}步骤4: 获取模板列表...${NC}"
TEMPLATES=$(curl -s -X GET "$BASE_URL/api/v1/templates/?skip=0&limit=10" \
  -H "Authorization: Bearer $TOKEN")

if [ $? -eq 0 ]; then
  COUNT=$(echo $TEMPLATES | grep -o '"count":[0-9]*' | cut -d':' -f2)
  echo -e "${GREEN}✓ 查询成功，找到 $COUNT 个模板${NC}"
else
  echo -e "${RED}✗ 查询失败${NC}"
fi
echo ""

# 5. 获取待审核票据
echo -e "${YELLOW}步骤5: 获取待审核票据...${NC}"
PENDING=$(curl -s -X GET "$BASE_URL/api/v1/invoices/review/pending?skip=0&limit=10" \
  -H "Authorization: Bearer $TOKEN")

if [ $? -eq 0 ]; then
  COUNT=$(echo $PENDING | grep -o '"count":[0-9]*' | cut -d':' -f2)
  echo -e "${GREEN}✓ 查询成功，找到 $COUNT 条待审核记录${NC}"
else
  echo -e "${RED}✗ 查询失败${NC}"
fi
echo ""

echo "========================================"
echo -e "${GREEN}  测试完成！${NC}"
echo "========================================"
echo ""
echo -e "${YELLOW}提示：${NC}"
echo -e "${GRAY}  - 访问 $BASE_URL/docs 查看完整API文档${NC}"
echo -e "${GRAY}  - 详细测试手册: backend/TESTING_MANUAL.md${NC}"
echo ""

