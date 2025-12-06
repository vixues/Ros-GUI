#!/bin/bash

# ROS-GUI 快速启动脚本

echo "🚀 Starting ROS-GUI Platform..."
echo ""

# 检查是否在项目根目录
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# 启动后端
echo "📦 Starting Backend..."
cd backend

# 检查Python虚拟环境
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null

# 安装依赖（如果需要）
if [ ! -f ".deps_installed" ]; then
    echo "Installing backend dependencies..."
    pip install -r requirements.txt
    touch .deps_installed
fi

# 运行数据库迁移
echo "Running database migrations..."
alembic upgrade head 2>/dev/null || echo "⚠️  Skipping migrations (database may not be configured)"

# 启动后端服务器（后台运行）
echo "Starting backend server..."
python -m backend.server &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"

cd ..

# 启动前端
echo ""
echo "🎨 Starting Frontend..."
cd frontend

# 检查node_modules
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# 启动前端开发服务器
echo "Starting frontend dev server..."
npm run dev &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"

cd ..

echo ""
echo "🎉 ROS-GUI Platform is running!"
echo ""
echo "📍 Frontend: http://localhost:5173"
echo "📍 Backend:  http://localhost:8000"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services..."
echo ""

# 等待用户中断
trap "echo ''; echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

# 保持脚本运行
wait

