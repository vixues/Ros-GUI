# 前后端集成指南 (Frontend-Backend Integration Guide)

## 快速开始

### 1. 启动后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（可选）
cp .env.example .env
# 编辑 .env 设置数据库等配置

# 运行数据库迁移
alembic upgrade head

# 启动服务器
python -m backend.server
# 或
uvicorn backend.server:app --reload --host 0.0.0.0 --port 8000
```

后端运行在: http://localhost:8000
API文档: http://localhost:8000/docs

### 2. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 开发模式（Mock数据）
npm run dev

# 开发模式（连接真实后端）
# 修改 .env 或创建 .env.local:
# VITE_USE_MOCK=false
# VITE_API_URL=http://localhost:8000
npm run dev
```

前端运行在: http://localhost:5173

## 开发模式切换

### Mock模式（无需后端）

```bash
# frontend/.env
VITE_USE_MOCK=true
VITE_API_URL=http://localhost:8000
```

适用场景：
- 后端未启动
- 前端功能开发
- UI/UX测试

### 真实API模式

```bash
# frontend/.env
VITE_USE_MOCK=false
VITE_API_URL=http://localhost:8000
```

适用场景：
- 集成测试
- 完整功能验证
- 生产环境部署

## API端点映射

| 功能 | 前端服务 | 后端路由 | 方法 |
|------|---------|---------|------|
| 登录 | `authService.login()` | `/api/auth/login` | POST |
| 获取用户信息 | `authService.getMe()` | `/api/auth/me` | GET |
| 获取无人机列表 | `droneService.getDrones()` | `/api/drones` | GET |
| 连接无人机 | `droneService.connectDrone()` | `/api/drones/{id}/connect` | POST |
| 获取任务列表 | `taskService.getTasks()` | `/api/tasks` | GET |
| 创建任务 | `taskService.createTask()` | `/api/tasks` | POST |
| 更新任务 | `taskService.updateTask()` | `/api/tasks/{id}` | PUT |
| 删除任务 | `taskService.deleteTask()` | `/api/tasks/{id}` | DELETE |
| 获取日志 | `logService.getLogs()` | `/api/logs` | GET |
| AI聊天 | `agentService.sendMessage()` | `/api/agent/sessions/{id}/message` | POST |

## 数据类型对照

### TypeScript (Frontend) ↔ Python (Backend)

```typescript
// Frontend: types.ts
export interface Drone {
  id: number;
  serial_number: string;
  name?: string;
  status: DroneStatus;
  battery_level: number;
  latitude?: number;
  longitude?: number;
  altitude?: number;
}
```

```python
# Backend: schemas/drone.py
class DroneResponse(BaseModel):
    id: int
    name: str
    drone_id: str
    status: str
    battery: float
    latitude: Optional[float]
    longitude: Optional[float]
    altitude: Optional[float]
```

### 枚举类型对照

```typescript
// Frontend
export enum TaskStatus {
  PENDING = "PENDING",
  IN_PROGRESS = "IN_PROGRESS",
  COMPLETED = "COMPLETED",
  FAILED = "FAILED"
}
```

```python
# Backend
class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
```

## 认证流程

### 1. 登录获取Token

```typescript
// Frontend
const response = await authService.login({
  username: 'admin',
  password: 'password'
});
// response.access_token 自动保存到 localStorage
```

### 2. 自动携带Token

所有后续请求自动在Header中携带Token：

```typescript
// httpClient.ts 自动处理
headers: {
  'Authorization': `Bearer ${token}`
}
```

### 3. Token过期处理

```typescript
// httpClient.ts
if (response.status === 401) {
  // 自动清除token并跳转登录页
  this.setToken(null);
  window.location.hash = '/login';
}
```

## 错误处理

### 统一错误格式

```typescript
// Frontend捕获
try {
  await droneService.getDrones();
} catch (error: ApiError) {
  console.error(error.message);
  // error.status: HTTP状态码
  // error.message: 错误消息
  // error.detail: 详细信息
}
```

### 通知用户

```typescript
// 使用Store的通知系统
const { addNotification } = useStore();

try {
  await taskService.createTask(data);
  addNotification('success', '任务创建成功');
} catch (error) {
  addNotification('error', '任务创建失败');
}
```

## 调试技巧

### 1. 查看API请求

浏览器开发者工具 -> Network标签

### 2. 后端日志

```bash
# 启动后端时查看日志
python -m backend.server
# 所有请求和错误都会打印
```

### 3. API文档

访问 http://localhost:8000/docs 查看完整API文档和测试

### 4. Mock数据调试

```typescript
// frontend/services/mockService.ts
// 修改Mock数据进行测试
let MOCK_DRONES = generateMockDrones(64);
```

## 部署注意事项

### 生产环境配置

```bash
# Backend .env
DEBUG=False
DATABASE_URL=postgresql://...
SECRET_KEY=<strong-secret-key>

# Frontend .env.production
VITE_USE_MOCK=false
VITE_API_URL=https://api.yourdomain.com
```

### CORS配置

后端已配置CORS，如需修改：

```python
# backend/config.py
CORS_ORIGINS = [
    "http://localhost:5173",
    "https://yourdomain.com"
]
```

## 常见问题

### Q: 前端无法连接后端？
A: 检查：
1. 后端是否运行在 http://localhost:8000
2. `.env` 中 `VITE_API_URL` 是否正确
3. `VITE_USE_MOCK` 是否设为 `false`

### Q: 401 Unauthorized错误？
A: 
1. 检查是否已登录
2. Token是否过期
3. 重新登录获取新Token

### Q: 数据格式不匹配？
A: 
1. 检查TypeScript类型定义
2. 查看后端Schema定义
3. 确保前后端类型一致

### Q: Mock数据不更新？
A: 
1. Mock数据存储在内存中
2. 刷新页面重置Mock数据
3. 或修改 `mockService.ts` 初始数据

## 测试建议

1. **单独测试前端**: 使用Mock模式
2. **单独测试后端**: 使用Postman或API文档
3. **集成测试**: 关闭Mock模式，完整测试流程
4. **端到端测试**: 模拟真实用户操作

