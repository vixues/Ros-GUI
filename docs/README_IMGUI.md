# ROS GUI - ImGui 实现

基于 ImGui 的 ROS 客户端 GUI 应用，使用后端 API 进行通信。

## 架构说明

本实现采用前后端分离架构：

- **后端服务** (`backend/server.py`): 使用 FastAPI 实现，封装 `rosclient` 功能，提供 REST API
- **前端 GUI** (`gui_imgui.py`): 使用 ImGui 实现，通过 HTTP 请求与后端通信

## 安装依赖

### 1. 安装 Python 依赖

```bash
pip install -r requirements_gui.txt
```

### 2. 确保 rosclient 可用

确保 `rosclient` 模块在 Python 路径中可用。

## 使用方法

### 1. 启动后端服务

在一个终端中运行：

```bash
python start_backend.py
```

或者：

```bash
cd backend
python server.py
```

后端服务将在 `http://127.0.0.1:8000` 启动。

### 2. 启动前端 GUI

在另一个终端中运行：

```bash
python gui_imgui.py
```

## 功能特性

### 连接管理
- 连接到 ROS Bridge（WebSocket）
- 支持 Mock Client 模式（测试模式）
- 实时连接状态显示

### 状态监控
- 实时显示无人机状态信息
- 自动刷新（可配置）
- 显示位置、姿态、电池等信息

### 图像显示
- 实时显示相机图像
- 自动更新或手动获取
- 支持图像缩放和显示

### 点云显示
- 显示点云数据
- 自动更新或手动获取
- 点云统计信息

### 控制命令
- 发送 ROS Topic 消息
- 预设命令（起飞、降落、返航、悬停）
- JSON 消息编辑器
- 命令历史记录

### 录制功能
- 开始/停止录制
- 录制统计信息
- 保存录制文件

### 回放功能（Mock Client）
- 加载录制文件
- 播放/暂停/停止控制
- 播放进度显示

## API 文档

详细的 API 接口文档请参考 [API_DOCUMENTATION.md](API_DOCUMENTATION.md)。

启动后端服务后，也可以通过以下地址访问自动生成的 API 文档：

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 配置

### 修改后端地址

在 `gui_imgui.py` 中修改：

```python
BACKEND_URL = "http://127.0.0.1:8000"
API_BASE = f"{BACKEND_URL}/api"
```

### 修改后端端口

在 `backend/server.py` 的 `main()` 函数中修改：

```python
uvicorn.run(
    "backend.server:app",
    host="127.0.0.1",
    port=8000,  # 修改端口
    ...
)
```

## 开发说明

### 后端开发

后端使用 FastAPI 框架，主要文件：

- `backend/server.py`: 主服务器文件，定义所有 API 端点
- `backend/__init__.py`: 包初始化文件

### 前端开发

前端使用 ImGui，主要文件：

- `gui_imgui.py`: ImGui GUI 应用主文件

### 添加新功能

1. **后端**: 在 `backend/server.py` 中添加新的 API 端点
2. **前端**: 在 `gui_imgui.py` 的 `BackendClient` 类中添加对应方法，在相应的 tab 渲染函数中调用

## 故障排除

### 后端无法启动

1. 检查端口 8000 是否被占用
2. 检查 `rosclient` 模块是否可用
3. 查看后端日志输出

### 前端无法连接后端

1. 确认后端服务已启动
2. 检查 `BACKEND_URL` 配置是否正确
3. 检查防火墙设置

### 图像无法显示

1. 确认已安装 `Pillow` 和 `numpy`
2. 检查后端是否正确接收到图像数据
3. 查看控制台错误信息

## 与原始 tkinter 版本的对比

| 特性 | tkinter 版本 | ImGui 版本 |
|------|-------------|-----------|
| UI 框架 | tkinter | ImGui |
| 架构 | 直接使用 rosclient | 前后端分离 |
| 通信方式 | 直接调用 | HTTP REST API |
| 可扩展性 | 中等 | 高（API 可被其他客户端使用） |
| 跨平台 | 是 | 是 |
| 性能 | 中等 | 较高 |

## 许可证

与主项目相同。

