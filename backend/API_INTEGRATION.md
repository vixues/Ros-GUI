# Backend API Specification

## 新增端点 (New Endpoints)

### Tasks API

#### Create Task
```http
POST /api/tasks
Authorization: Bearer <token>

Request Body:
{
  "title": "任务标题",
  "description": "任务描述",
  "priority": "HIGH",
  "status": "PENDING",
  "assigned_drone_ids": [1, 2, 3]
}

Response:
{
  "status": 201,
  "message": "Task created successfully",
  "data": {
    "id": 1,
    "title": "任务标题",
    ...
  }
}
```

#### Get Tasks
```http
GET /api/tasks?skip=0&limit=100&status=IN_PROGRESS
Authorization: Bearer <token>

Response:
{
  "status": 200,
  "message": "Tasks retrieved successfully",
  "data": [...]
}
```

#### Update Task
```http
PUT /api/tasks/{task_id}
Authorization: Bearer <token>

Request Body:
{
  "status": "COMPLETED"
}
```

#### Delete Task
```http
DELETE /api/tasks/{task_id}
Authorization: Bearer <token>
```

### Logs API

#### Get System Logs
```http
GET /api/logs?level=ERROR&module=SWARM&limit=100
Authorization: Bearer <token>

Response:
{
  "status": 200,
  "message": "Logs retrieved successfully",
  "data": [
    {
      "id": 1,
      "timestamp": "2024-12-06T10:30:00Z",
      "level": "ERROR",
      "module": "SWARM",
      "message": "Connection lost",
      "metadata": {},
      "user_id": 1
    }
  ]
}
```

## 数据库迁移

新增了两个表：

### tasks 表
- id (主键)
- title
- description
- status (ENUM: PENDING, IN_PROGRESS, COMPLETED, FAILED)
- priority (ENUM: LOW, MEDIUM, HIGH, CRITICAL)
- assigned_drone_ids (数组)
- created_by, updated_by
- created_at, updated_at

### system_logs 表
- id (主键)
- timestamp
- level (ENUM: INFO, WARNING, ERROR, CRITICAL, SUCCESS)
- module
- message
- metadata (JSON)
- user_id

## 运行迁移

```bash
cd backend
alembic upgrade head
```

## API响应格式

所有API统一返回格式：

```typescript
{
  status: number,      // HTTP状态码
  message: string,     // 说明消息
  data: T,            // 实际数据
  error_code?: string  // 错误代码(可选)
}
```

## 前后端完整对接

### 1. 认证流程
```
Frontend: authService.login() 
  -> POST /api/auth/login 
  -> Backend: auth_router.login()
  -> Response: { access_token, user }
```

### 2. 无人机管理
```
Frontend: droneService.getDrones()
  -> GET /api/drones
  -> Backend: drones_router.get_drones()
  -> DroneService.get_drones()
  -> Response: Drone[]
```

### 3. 任务管理
```
Frontend: taskService.createTask()
  -> POST /api/tasks
  -> Backend: tasks_router.create_task()
  -> TaskService.create_task()
  -> Response: Task
```

### 4. AI代理
```
Frontend: agentService.sendMessage()
  -> POST /api/agent/sessions/{id}/message
  -> Backend: agent_router.send_agent_message()
  -> AgentService.process_message()
  -> Response: { response, actions }
```

## 服务层架构

```
backend/
├── routers/          # API路由层
│   ├── auth.py
│   ├── drones.py
│   ├── tasks.py      # ✓ 新增
│   ├── logs.py       # ✓ 新增
│   └── agent.py
├── services/         # 业务逻辑层
│   ├── drone_service.py
│   ├── task_service.py     # ✓ 新增
│   ├── log_service.py      # ✓ 新增
│   └── agent_service.py
├── models/           # 数据模型层
│   ├── drone.py
│   ├── task.py       # ✓ 新增
│   ├── log.py        # ✓ 新增
│   └── user.py
└── schemas/          # 数据验证层
    ├── drone.py
    ├── task.py       # ✓ 新增
    ├── log.py        # ✓ 新增
    └── response.py
```

