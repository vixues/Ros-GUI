# 快速开始指南

## 安装

### 1. 安装依赖

```bash
pip install -r requirements_gui.txt
```

### 2. 确保 rosclient 可用

确保 `rosclient` 模块在 Python 路径中。

## 运行

### 方式一：分别启动（推荐）

**终端 1 - 启动后端**:
```bash
python start_backend.py
```

**终端 2 - 启动前端**:
```bash
python gui_imgui.py
```

### 方式二：使用脚本（Windows）

**启动后端**:
```bash
python start_backend.py
```

**启动前端**:
```bash
start_gui.bat
```

### 方式三：使用脚本（Linux/Mac）

**启动后端**:
```bash
python start_backend.py
```

**启动前端**:
```bash
chmod +x start_gui.sh
./start_gui.sh
```

## 使用

1. **连接**: 在 Connection 标签页输入 WebSocket URL，点击 Connect
2. **查看状态**: 切换到 Status 标签页查看无人机状态
3. **查看图像**: 切换到 Image 标签页查看相机图像
4. **发送命令**: 切换到 Control 标签页发送控制命令

## 查看 API 文档

启动后端后，访问：
- http://127.0.0.1:8000/docs (Swagger UI)
- http://127.0.0.1:8000/redoc (ReDoc)

## 故障排除

### 后端无法启动
- 检查端口 8000 是否被占用
- 检查 rosclient 是否可用

### 前端无法连接
- 确认后端已启动
- 检查后端地址配置（默认 http://127.0.0.1:8000）

### 图像无法显示
- 确认已安装 Pillow 和 numpy
- 检查后端日志

## 更多信息

- 详细使用说明: [README_IMGUI.md](README_IMGUI.md)
- API 接口文档: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- 实现总结: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

