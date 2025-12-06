# ROS-GUI - Professional Multi-Drone Management Platform

专业的多无人机管理和控制平台，集成LLM智能代理支持。

## 🌟 主要特性

- ✅ **专业前端架构**: 模块化服务层、Zustand状态管理、TypeScript类型安全
- ✅ **完整后端API**: FastAPI + PostgreSQL + Redis，RESTful API设计
- ✅ **无人机管理**: 实时状态监控、远程控制、航点规划
- ✅ **任务系统**: 任务创建、分配、状态追踪
- ✅ **AI智能代理**: 自然语言控制无人机群
- ✅ **系统日志**: 完整的操作日志和审计追踪
- ✅ **Mock开发模式**: 前后端可独立开发
- ✅ **类型安全**: 前后端完整类型定义和验证

## 🏗️ 项目架构

```
Ros-GUI/
├── frontend/              # React + TypeScript前端
│   ├── services/         # API服务层（模块化）
│   ├── store/           # Zustand状态管理
│   ├── components/      # React组件
│   ├── pages/          # 页面组件
│   ├── lib/            # 工具函数和配置
│   └── types.ts        # TypeScript类型定义
├── backend/             # FastAPI Python后端
│   ├── routers/        # API路由层
│   ├── services/       # 业务逻辑层
│   ├── models/         # 数据模型层
│   ├── schemas/        # 数据验证层
│   └── alembic/        # 数据库迁移
├── rosclient/          # ROS客户端库
├── uavcommander/       # UAV控制库
└── INTEGRATION.md      # 前后端集成指南
```

## 🚀 快速开始

### 前置要求

- **Frontend**: Node.js 16+, npm
- **Backend**: Python 3.10+, PostgreSQL 13+, Redis (可选)

### 1. 启动后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置数据库（可选，使用默认配置跳过）
cp .env.example .env
# 编辑 .env

# 运行数据库迁移
alembic upgrade head

# 启动服务器
python -m backend.server
```

后端地址: http://localhost:8000
API文档: http://localhost:8000/docs

### 2. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# Mock模式开发（无需后端）
npm run dev

# 或连接真实后端
# 创建 .env.local:
# VITE_USE_MOCK=false
# VITE_API_URL=http://localhost:8000
npm run dev
```

前端地址: http://localhost:5173

默认登录（Mock模式）:
- Username: `Commander`
- Password: 任意

## 📚 文档

- [前后端集成指南](./INTEGRATION.md) - 完整的前后端对接说明
- [Frontend架构](./frontend/ARCHITECTURE.md) - 前端架构和API使用
- [Backend API](./backend/API_INTEGRATION.md) - 后端API规范
- [Backend详细文档](./backend/README.md) - 后端架构说明

## 🔧 开发模式

### Mock开发（推荐用于前端开发）

```bash
# frontend/.env
VITE_USE_MOCK=true
```

优点：
- 无需启动后端
- 快速UI开发
- 完整的Mock数据

### 真实API模式

```bash
# frontend/.env
VITE_USE_MOCK=false
VITE_API_URL=http://localhost:8000
```

用于：
- 完整功能测试
- 集成测试
- 生产部署

## 🎯 核心功能

### 1. 无人机管理

```typescript
// Frontend
import { droneService } from './services/droneService';

// 获取无人机列表
const drones = await droneService.getDrones();

// 连接无人机
await droneService.connectDrone(id, {
  connection_url: 'ws://localhost:9090'
});

// 控制无人机
await droneService.landDrone(id);
await droneService.updateWaypoints(id, waypoints);
```

### 2. 任务管理

```typescript
// 创建任务
const task = await taskService.createTask({
  title: '巡逻任务',
  description: '执行区域巡逻',
  priority: 'HIGH',
  assigned_drone_ids: [1, 2, 3]
});

// 更新任务状态
await taskService.updateTask(taskId, {
  status: 'IN_PROGRESS'
});
```

### 3. AI智能代理

```typescript
// 创建会话
const session = await agentService.createSession();

// 发送自然语言指令
const response = await agentService.sendMessage(sessionId, {
  content: 'Set unit 5 altitude to 50 meters'
});
// 返回: { response, actions, type, data }
```

### 4. 系统日志

```typescript
// 查询日志
const logs = await logService.getLogs({
  level: 'ERROR',
  module: 'SWARM',
  limit: 100
});
```

## 🏢 技术栈

### Frontend
- **React 19** - UI框架
- **TypeScript** - 类型安全
- **Zustand** - 状态管理
- **React Router** - 路由
- **Vite** - 构建工具
- **TailwindCSS** - 样式

### Backend
- **FastAPI** - Web框架
- **SQLAlchemy** - ORM
- **Alembic** - 数据库迁移
- **PostgreSQL** - 数据库
- **Redis** - 缓存（可选）
- **Pydantic** - 数据验证

## 📦 API端点

### 认证
- `POST /api/auth/login` - 登录
- `POST /api/auth/register` - 注册
- `GET /api/auth/me` - 获取当前用户

### 无人机
- `GET /api/drones` - 获取无人机列表
- `POST /api/drones` - 创建无人机
- `POST /api/drones/{id}/connect` - 连接无人机
- `POST /api/drones/{id}/disconnect` - 断开连接
- `GET /api/drones/{id}/status` - 获取状态

### 任务
- `GET /api/tasks` - 获取任务列表
- `POST /api/tasks` - 创建任务
- `PUT /api/tasks/{id}` - 更新任务
- `DELETE /api/tasks/{id}` - 删除任务

### 日志
- `GET /api/logs` - 获取系统日志

### AI代理
- `POST /api/agent/sessions` - 创建会话
- `POST /api/agent/sessions/{id}/message` - 发送消息

详细API文档: http://localhost:8000/docs

## 🧪 测试

```bash
# Backend测试
cd backend
pytest

# Frontend测试（待实现）
cd frontend
npm test
```

## 📝 数据库

### 主要数据表

- **users** - 用户账户
- **drones** - 无人机信息
- **tasks** - 任务管理
- **system_logs** - 系统日志
- **operations** - 操作记录
- **agent_sessions** - AI会话
- **devices** - 设备管理
- **recordings** - 录制数据

### 运行迁移

```bash
cd backend
alembic upgrade head
```

## 🔒 安全

- JWT Token认证
- 密码哈希存储
- CORS配置
- SQL注入防护（ORM）
- XSS防护

## 🚢 部署

### Docker部署（推荐）

```bash
# 待实现
docker-compose up -d
```

### 手动部署

#### Backend
```bash
cd backend
gunicorn backend.server:app -w 4 -k uvicorn.workers.UvicornWorker
```

#### Frontend
```bash
cd frontend
npm run build
# 将 dist/ 部署到Web服务器
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可

MIT License

## 📧 联系

如有问题，请查看 [INTEGRATION.md](./INTEGRATION.md) 或提交Issue。

---

## 🎓 学习资源

- [FastAPI文档](https://fastapi.tiangolo.com/)
- [React文档](https://react.dev/)
- [Zustand文档](https://docs.pmnd.rs/zustand/)
- [TypeScript文档](https://www.typescriptlang.org/)

## 🔄 更新日志

### v2.0.0 (2024-12-06)
- ✅ 完整重构前端架构
- ✅ 模块化服务层设计
- ✅ 新增任务管理系统
- ✅ 新增系统日志功能
- ✅ 完善类型定义
- ✅ Mock开发模式
- ✅ 前后端完整对接
- ✅ 专业级代码组织

### v1.0.0
- 初始版本
