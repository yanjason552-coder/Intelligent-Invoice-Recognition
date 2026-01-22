#!/bin/bash

# 本地开发环境启动脚本
# 使用方法: ./scripts/dev-local.sh

echo "🚀 启动本地开发环境..."

# 检查是否在正确的目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 启动数据库和邮件服务
echo "📦 启动数据库和邮件服务..."
docker compose up db mailcatcher -d

# 等待数据库启动
echo "⏳ 等待数据库启动..."
sleep 5

# 检查数据库是否就绪
echo "🔍 检查数据库连接..."
until docker compose exec -T db pg_isready -U postgres; do
    echo "⏳ 等待数据库就绪..."
    sleep 2
done

echo "✅ 数据库已就绪"

# 启动后端开发服务器
echo "🐍 启动后端开发服务器..."
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# 启动前端开发服务器
echo "⚛️ 启动前端开发服务器..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "🎉 本地开发环境已启动!"
echo ""
echo "📱 前端: http://localhost:5173"
echo "🔧 后端: http://localhost:8000"
echo "📊 API文档: http://localhost:8000/docs"
echo "📧 邮件: http://localhost:1080"
echo "🗄️ 数据库管理: http://localhost:8080"
echo ""
echo "💡 提示:"
echo "   - 前端代码修改会自动热重载"
echo "   - 后端代码修改会自动重启"
echo "   - 按 Ctrl+C 停止所有服务"
echo ""

# 等待用户中断
trap "echo '🛑 正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID; docker compose down; exit" INT

# 保持脚本运行
wait 