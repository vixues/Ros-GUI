# 🚀 快速参考指南 (Quick Reference)

## 一分钟启动

### Windows
```bash
start.bat
```

### Linux/Mac
```bash
chmod +x start.sh
./start.sh
```

---

## 常用命令

### Frontend
```bash
cd frontend

# 开发模式（Mock数据）
npm run dev

# 开发模式（真实API）
# 修改 .env: VITE_USE_MOCK=false
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

### Backend
```bash
cd backend

# 开发模式
python -m backend.server

# 生产模式（推荐使用uvicorn）
uvicorn backend.server:app --host 0.0.0.0 --port 8000

# 数据库迁移
alembic upgrade head

# 创建新迁移
alembic revision --autogenerate -m "description"
```

---

## API快速测试

### 使用curl

#### 登录
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"
```

#### 获取无人机列表
```bash
curl -X GET http://localhost:8000/api/drones \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 创建任务
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试任务",
    "description": "这是一个测试任务",
    "priority": "HIGH"
  }'
```

### 使用API文档
访问 http://localhost:8000/docs 进行交互式测试

---

## 前端服务使用示例

### 基础用法
```typescript
import { droneService, taskService, mockService } from './services';

// 获取无人机
const drones = await droneService.getDrones();

// 创建任务
const task = await taskService.createTask({
  title: '巡逻任务',
  priority: 'HIGH'
});

// Mock模式（开发）
const mockDrones = await mockService.getDrones();
```

### Store使用
```typescript
import { useStore } from './store/useStore';

function MyComponent() {
  const { 
    drones, 
    fetchDrones, 
    addNotification 
  } = useStore();

  useEffect(() => {
    fetchDrones();
  }, [fetchDrones]);

  return <div>{drones.length} drones</div>;
}
```

---

## 环境配置速查

### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8000
VITE_USE_MOCK=true              # true=Mock, false=真实API
VITE_ENABLE_LLM=false
VITE_ENABLE_REALTIME=false
```

### Backend (.env)
```bash
DEBUG=True
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname
SECRET_KEY=your-secret-key
CORS_ORIGINS=["http://localhost:5173"]
```

---

## 常见问题速查

### Q: 前端无法连接后端？
```bash
# 1. 检查后端是否运行
curl http://localhost:8000/health

# 2. 检查前端配置
cat frontend/.env
# VITE_USE_MOCK应该是false
# VITE_API_URL应该正确

# 3. 检查CORS
# 后端 .env 中 CORS_ORIGINS 应包含前端地址
```

### Q: 401 Unauthorized?
```typescript
// 重新登录获取新token
const auth = await authService.login({ 
  username, 
  password 
});
```

### Q: Mock数据不对？
```typescript
// 修改 Mock数据
// frontend/services/mockService.ts
let MOCK_DRONES = generateMockDrones(64);
```

---

## 目录结构速查

```
Ros-GUI/
├── frontend/
│   ├── services/        # ⭐ API服务层
│   ├── store/          # ⭐ 状态管理
│   ├── lib/            # ⭐ 工具和配置
│   ├── components/      # React组件
│   └── pages/          # 页面组件
├── backend/
│   ├── routers/        # ⭐ API路由
│   ├── services/       # ⭐ 业务逻辑
│   ├── models/         # ⭐ 数据模型
│   └── schemas/        # ⭐ 数据验证
└── docs/
    ├── README.md           # 主文档
    ├── INTEGRATION.md      # 集成指南
    └── VERIFICATION_CHECKLIST.md  # 测试清单
```

---

## API端点速查表

| 功能 | 方法 | 端点 | 认证 |
|------|------|------|------|
| 登录 | POST | `/api/auth/login` | ❌ |
| 获取用户 | GET | `/api/auth/me` | ✅ |
| 无人机列表 | GET | `/api/drones` | ✅ |
| 连接无人机 | POST | `/api/drones/{id}/connect` | ✅ |
| 任务列表 | GET | `/api/tasks` | ✅ |
| 创建任务 | POST | `/api/tasks` | ✅ |
| 更新任务 | PUT | `/api/tasks/{id}` | ✅ |
| 系统日志 | GET | `/api/logs` | ✅ |
| AI消息 | POST | `/api/agent/sessions/{id}/message` | ✅ |

---

## 开发工作流

### 1. 新功能开发
```bash
# Frontend: Mock模式开发UI
cd frontend
# .env: VITE_USE_MOCK=true
npm run dev

# Backend: 实现API
cd backend
# 1. 创建model
# 2. 创建schema
# 3. 创建service
# 4. 创建router
python -m backend.server

# 集成测试
# Frontend .env: VITE_USE_MOCK=false
# 测试前后端对接
```

### 2. 数据库变更
```bash
cd backend

# 1. 修改models/
# 2. 创建迁移
alembic revision --autogenerate -m "add new table"

# 3. 应用迁移
alembic upgrade head

# 4. 回滚（如需要）
alembic downgrade -1
```

### 3. 部署流程
```bash
# Frontend
cd frontend
npm run build
# 部署 dist/ 到Web服务器

# Backend
cd backend
# 使用 gunicorn/uvicorn
uvicorn backend.server:app --workers 4
```

---

## 调试技巧

### Frontend调试
```typescript
// 1. 开发工具
// F12 -> Network 查看API请求

// 2. 日志输出
console.log('API Response:', data);

// 3. Store状态
const state = useStore.getState();
console.log('Current State:', state);
```

### Backend调试
```python
# 1. 启用DEBUG模式
DEBUG=True python -m backend.server

# 2. 查看日志
# 所有请求都会打印

# 3. 使用API文档测试
# http://localhost:8000/docs
```

---

## 性能优化提示

### Frontend
- 使用React.memo()减少重渲染
- 实现虚拟滚动（大列表）
- 启用代码分割（React.lazy）
- 优化图片加载

### Backend
- 添加数据库索引
- 实现Redis缓存
- 使用连接池
- 启用查询优化

---

## 安全提示

### ⚠️ 生产环境必做
```bash
# Backend
SECRET_KEY=使用强随机密钥（至少32字符）
DEBUG=False
CORS_ORIGINS=["https://yourdomain.com"]  # 不要用 "*"

# Frontend
VITE_USE_MOCK=false
VITE_API_URL=https://api.yourdomain.com
```

---

## 监控和日志

### 日志查询
```typescript
// 获取错误日志
const logs = await logService.getLogs({
  level: 'ERROR',
  limit: 100
});

// 按模块筛选
const logs = await logService.getLogs({
  module: 'SWARM',
  level: 'WARNING'
});
```

### 操作记录
```typescript
// 查询操作历史
const operations = await operationService.getOperations({
  drone_id: 1,
  operation_type: 'PUBLISH'
});
```

---

## 快速链接

- 📚 [完整文档](./README.md)
- 🔗 [前后端集成](./INTEGRATION.md)
- ✅ [验收清单](./VERIFICATION_CHECKLIST.md)
- 📊 [项目总结](./PROJECT_SUMMARY.md)
- 🎨 [前端架构](./frontend/ARCHITECTURE.md)
- 🔧 [后端API](./backend/API_INTEGRATION.md)

---

## 联系支持

遇到问题？查看：
1. 相关文档
2. API文档: http://localhost:8000/docs
3. 提交Issue

---

**记住：先看文档，再动手！** 📖

