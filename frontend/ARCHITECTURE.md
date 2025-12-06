# Frontend Architecture

## 服务层架构 (Services Layer)

### 核心服务模块

```
services/
├── httpClient.ts      # HTTP基础客户端（错误处理、认证）
├── authService.ts     # 认证服务
├── droneService.ts    # 无人机管理
├── taskService.ts     # 任务管理
├── agentService.ts    # AI代理
├── logService.ts      # 日志服务
├── operationService.ts # 操作记录
├── mockService.ts     # Mock数据（开发用）
└── index.ts          # 统一导出
```

### API对接示例

```typescript
// 使用Mock数据开发
import { mockService } from './services/mockService';
const drones = await mockService.getDrones();

// 使用真实API
import { droneService } from './services/droneService';
const drones = await droneService.getDrones();
```

## 状态管理 (Zustand)

```typescript
import { useStore } from './store/useStore';

const { 
  drones, 
  fetchDrones, 
  tasks, 
  fetchTasks,
  addNotification 
} = useStore();
```

## 配置管理

`.env` 文件配置：
```bash
VITE_API_URL=http://localhost:8000
VITE_USE_MOCK=true  # Mock模式
```

## 快速开始

```bash
npm install
npm run dev
```

