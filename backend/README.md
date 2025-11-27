# ROS GUI Backend - Professional Multi-Drone Management Platform

## 概述

这是一个专业的无人机管理控制平台后端，基于 FastAPI 构建，支持多无人机、多设备管理，数据库记录功能，以及大模型 Agent 控制功能。

## 功能特性

- ✅ **多无人机管理**: 支持同时管理多架无人机
- ✅ **多设备管理**: 支持管理各种设备（无人机、相机、传感器等）
- ✅ **数据库记录**: 使用 PostgreSQL + SQLAlchemy 2.x 记录所有操作
- ✅ **JWT 认证**: 基于 OAuth2PasswordBearer 的安全认证
- ✅ **Redis 缓存**: 减少数据库负载
- ✅ **统一响应格式**: 所有 API 使用统一的 ResponseModel
- ✅ **异步支持**: 全面使用 async/await
- ✅ **LLM Agent**: 支持大模型 Agent 控制功能
- ✅ **操作记录**: 记录所有操作历史
- ✅ **录制功能**: 支持图像、点云、状态录制

## 技术栈

- **FastAPI**: 现代、快速的 Web 框架
- **SQLAlchemy 2.x**: 异步 ORM
- **Alembic**: 数据库迁移
- **PostgreSQL**: 主数据库
- **Redis**: 缓存
- **JWT**: 认证
- **Pydantic 2.x**: 数据验证

## 项目结构

```
backend/
├── alembic/              # 数据库迁移
├── models/               # 数据库模型
│   ├── user.py          # 用户模型
│   ├── device.py        # 设备模型
│   ├── drone.py         # 无人机模型
│   ├── operation.py     # 操作记录模型
│   ├── recording.py     # 录制模型
│   └── agent.py         # Agent 模型
├── schemas/              # Pydantic 模式
│   ├── response.py      # 统一响应模型
│   ├── auth.py          # 认证模式
│   ├── device.py        # 设备模式
│   ├── drone.py         # 无人机模式
│   └── ...
├── routers/              # API 路由
│   ├── auth.py          # 认证路由
│   ├── drones.py        # 无人机路由
│   ├── devices.py       # 设备路由
│   └── ...
├── services/             # 业务逻辑层
│   ├── drone_service.py
│   ├── device_service.py
│   └── ...
├── config.py             # 配置管理
├── database.py           # 数据库连接
├── cache.py              # Redis 缓存
├── auth.py               # 认证逻辑
├── middleware.py         # 中间件
└── server.py             # 主应用
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements_backend.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置数据库、Redis 等连接信息。

### 3. 初始化数据库

```bash
# 创建迁移
alembic revision --autogenerate -m "Initial migration"

# 应用迁移
alembic upgrade head
```

### 4. 运行服务器

```bash
python -m backend.server
```

或使用 uvicorn：

```bash
uvicorn backend.server:app --reload
```

## API 文档

启动服务器后，访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 测试

运行测试：

```bash
pytest backend/tests/ -v --cov=backend --cov-report=html
```

## 代码规范

- 所有 API 使用 `APIRouter`
- 所有响应使用 `ResponseModel` (status, message, data)
- 所有数据库操作使用 `AsyncSession`
- 所有视图函数使用 `async def`
- 所有配置使用 `pydantic.BaseSettings`
- 所有 API 使用 JWT 认证（除登录和注册）

## 许可证

MIT License

