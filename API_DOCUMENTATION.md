# ROS GUI Backend API 接口文档

## 概述

本文档描述了 ROS GUI 后端服务的 REST API 接口。后端服务使用 FastAPI 实现，提供与 ROS 客户端通信的 HTTP 接口。

**Base URL**: `http://127.0.0.1:8000`  
**API Base**: `http://127.0.0.1:8000/api`

## 通用说明

### 请求格式
- 所有请求使用 JSON 格式
- Content-Type: `application/json`

### 响应格式
- 成功响应：返回 JSON 对象
- 错误响应：返回 JSON 对象，包含 `detail` 字段描述错误信息

### 状态码
- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误或未连接
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

---

## API 接口列表

### 1. 获取连接状态

**GET** `/api/status`

获取当前 ROS 连接状态和无人机状态信息。

#### 响应示例

```json
{
  "connected": true,
  "url": "ws://192.168.27.152:9090",
  "use_mock": false,
  "state": {
    "connected": true,
    "armed": false,
    "mode": "GUIDED",
    "battery": 85.5,
    "latitude": 39.9042,
    "longitude": 116.4074,
    "altitude": 10.5,
    "roll": 0.1,
    "pitch": 0.2,
    "yaw": 45.0,
    "landed": true,
    "reached": false,
    "returned": false,
    "tookoff": false,
    "last_updated": 1234567890.123
  }
}
```

#### 字段说明

- `connected`: 是否已连接
- `url`: WebSocket 连接地址
- `use_mock`: 是否使用 Mock 客户端
- `state`: 无人机状态对象
  - `connected`: 连接状态
  - `armed`: 是否解锁
  - `mode`: 飞行模式
  - `battery`: 电池电量（百分比）
  - `latitude`: 纬度
  - `longitude`: 经度
  - `altitude`: 高度（米）
  - `roll`: 横滚角（度）
  - `pitch`: 俯仰角（度）
  - `yaw`: 偏航角（度）
  - `landed`: 是否着陆
  - `reached`: 是否到达目标
  - `returned`: 是否返航
  - `tookoff`: 是否起飞
  - `last_updated`: 最后更新时间戳

---

### 2. 连接到 ROS Bridge

**POST** `/api/connect`

建立与 ROS Bridge 的连接。

#### 请求体

```json
{
  "url": "ws://192.168.27.152:9090",
  "use_mock": false,
  "mock_config": {
    "playback_file": "path/to/recording.rosrec",
    "playback_loop": true
  }
}
```

#### 字段说明

- `url` (必需): WebSocket URL 地址
- `use_mock` (可选): 是否使用 Mock 客户端，默认 `false`
- `mock_config` (可选): Mock 客户端配置
  - `playback_file`: 回放文件路径
  - `playback_loop`: 是否循环播放

#### 响应示例

```json
{
  "message": "Connection initiated",
  "url": "ws://192.168.27.152:9090",
  "use_mock": false
}
```

---

### 3. 断开连接

**POST** `/api/disconnect`

断开与 ROS Bridge 的连接。

#### 响应示例

```json
{
  "message": "Disconnected"
}
```

---

### 4. 获取最新图像

**GET** `/api/image`

获取最新的相机图像（非阻塞，从缓存获取）。

#### 响应示例

```json
{
  "image": "base64_encoded_image_string",
  "timestamp": 1234567890.123,
  "width": 640,
  "height": 480,
  "format": "jpeg"
}
```

#### 字段说明

- `image`: Base64 编码的 JPEG 图像数据
- `timestamp`: 图像时间戳
- `width`: 图像宽度（像素）
- `height`: 图像高度（像素）
- `format`: 图像格式（固定为 "jpeg"）

---

### 5. 同步获取图像

**GET** `/api/image/fetch`

同步获取相机图像（阻塞，等待新图像）。

#### 响应格式

与 `/api/image` 相同。

---

### 6. 获取最新点云

**GET** `/api/pointcloud`

获取最新的点云数据（非阻塞，从缓存获取）。

#### 响应示例

```json
{
  "points": [
    [1.0, 2.0, 3.0],
    [1.1, 2.1, 3.1],
    ...
  ],
  "timestamp": 1234567890.123,
  "count": 10000
}
```

#### 字段说明

- `points`: 点云数据数组，每个元素为 `[x, y, z]` 坐标
- `timestamp`: 点云时间戳
- `count`: 点的数量（如果点云过大，会自动采样到 10000 个点）

---

### 7. 同步获取点云

**GET** `/api/pointcloud/fetch`

同步获取点云数据（阻塞，等待新数据）。

#### 响应格式

与 `/api/pointcloud` 相同。

---

### 8. 发布消息到 Topic

**POST** `/api/publish`

向指定的 ROS Topic 发布消息。

#### 请求体

```json
{
  "topic": "/control",
  "topic_type": "controller_msgs/cmd",
  "message": {
    "cmd": 1
  }
}
```

#### 字段说明

- `topic` (必需): Topic 名称
- `topic_type` (必需): Topic 类型
- `message` (必需): 消息内容（JSON 对象）

#### 响应示例

```json
{
  "message": "Published successfully",
  "topic": "/control"
}
```

---

### 9. 调用 ROS Service

**POST** `/api/service/call`

调用 ROS Service。

#### 请求体

```json
{
  "service_name": "/mavros/cmd/arming",
  "service_type": "mavros_msgs/CommandBool",
  "payload": {
    "value": true
  },
  "timeout": 5.0
}
```

#### 字段说明

- `service_name` (必需): Service 名称
- `service_type` (必需): Service 类型
- `payload` (可选): Service 请求载荷，默认 `{}`
- `timeout` (可选): 超时时间（秒），默认 `5.0`

#### 响应示例

```json
{
  "response": {
    "success": true,
    "result": {}
  }
}
```

---

### 10. 开始录制

**POST** `/api/recording/start`

开始录制 ROS 数据。

#### 请求体

```json
{
  "record_images": true,
  "record_pointclouds": true,
  "record_states": true,
  "image_quality": 85
}
```

#### 字段说明

- `record_images` (可选): 是否录制图像，默认 `true`
- `record_pointclouds` (可选): 是否录制点云，默认 `true`
- `record_states` (可选): 是否录制状态，默认 `true`
- `image_quality` (可选): 图像质量（0-100），默认 `85`

#### 响应示例

```json
{
  "message": "Recording started",
  "success": true
}
```

---

### 11. 停止录制

**POST** `/api/recording/stop`

停止录制。

#### 响应示例

```json
{
  "message": "Recording stopped",
  "success": true
}
```

---

### 12. 获取录制统计信息

**GET** `/api/recording/stats`

获取录制统计信息。

#### 响应示例

```json
{
  "stats": {
    "images_recorded": 100,
    "pointclouds_recorded": 50,
    "states_recorded": 200,
    "total_entries": 350,
    "dropped": 5,
    "queue_size": 10,
    "is_recording": false
  }
}
```

#### 字段说明

- `images_recorded`: 已录制的图像数量
- `pointclouds_recorded`: 已录制的点云数量
- `states_recorded`: 已录制的状态数量
- `total_entries`: 总条目数
- `dropped`: 丢弃的条目数
- `queue_size`: 队列大小
- `is_recording`: 是否正在录制

---

### 13. 保存录制

**POST** `/api/recording/save`

保存录制到文件。

#### 请求体

```json
{
  "file_path": "/path/to/recording.rosrec"
}
```

#### 字段说明

- `file_path` (必需): 保存文件路径

#### 响应示例

```json
{
  "message": "Recording saved",
  "file_path": "/path/to/recording.rosrec",
  "success": true
}
```

---

### 14. 控制回放（Mock Client）

**POST** `/api/playback/control`

控制回放（仅 Mock Client 可用）。

#### 请求体

```json
{
  "action": "play",
  "file_path": "/path/to/recording.rosrec"
}
```

#### 字段说明

- `action` (必需): 操作类型
  - `"play"`: 开始/继续播放
  - `"pause"`: 暂停播放
  - `"stop"`: 停止播放
  - `"load"`: 加载文件（需要 `file_path`）
- `file_path` (可选): 录制文件路径（仅用于 `load` 操作）

#### 响应示例

```json
{
  "message": "Playback play executed",
  "success": true
}
```

---

### 15. 获取回放信息（Mock Client）

**GET** `/api/playback/info`

获取回放信息（仅 Mock Client 可用）。

#### 响应示例

```json
{
  "is_playback_mode": true,
  "progress": 0.5,
  "current_time": 10.5,
  "is_playing": true
}
```

#### 字段说明

- `is_playback_mode`: 是否处于回放模式
- `progress`: 播放进度（0.0-1.0）
- `current_time`: 当前播放时间（秒）
- `is_playing`: 是否正在播放

---

## 错误处理

### 错误响应格式

```json
{
  "detail": "Error message description"
}
```

### 常见错误

1. **未连接错误** (`400 Bad Request`)
   ```json
   {
     "detail": "Not connected"
   }
   ```

2. **资源不存在** (`404 Not Found`)
   ```json
   {
     "detail": "No image available"
   }
   ```

3. **服务器错误** (`500 Internal Server Error`)
   ```json
   {
     "detail": "Internal server error description"
   }
   ```

---

## 使用示例

### Python 示例

```python
import requests

BASE_URL = "http://127.0.0.1:8000/api"

# 连接
response = requests.post(f"{BASE_URL}/connect", json={
    "url": "ws://192.168.27.152:9090",
    "use_mock": False
})
print(response.json())

# 获取状态
response = requests.get(f"{BASE_URL}/status")
status = response.json()
print(f"Connected: {status['connected']}")
print(f"Battery: {status['state']['battery']}%")

# 获取图像
response = requests.get(f"{BASE_URL}/image")
image_data = response.json()
# 解码 base64 图像
import base64
image_bytes = base64.b64decode(image_data["image"])

# 发布消息
response = requests.post(f"{BASE_URL}/publish", json={
    "topic": "/control",
    "topic_type": "controller_msgs/cmd",
    "message": {"cmd": 1}
})
print(response.json())

# 断开连接
response = requests.post(f"{BASE_URL}/disconnect")
print(response.json())
```

### cURL 示例

```bash
# 连接
curl -X POST http://127.0.0.1:8000/api/connect \
  -H "Content-Type: application/json" \
  -d '{"url": "ws://192.168.27.152:9090", "use_mock": false}'

# 获取状态
curl http://127.0.0.1:8000/api/status

# 获取图像
curl http://127.0.0.1:8000/api/image

# 发布消息
curl -X POST http://127.0.0.1:8000/api/publish \
  -H "Content-Type: application/json" \
  -d '{"topic": "/control", "topic_type": "controller_msgs/cmd", "message": {"cmd": 1}}'

# 断开连接
curl -X POST http://127.0.0.1:8000/api/disconnect
```

---

## API 文档访问

启动后端服务后，可以通过以下地址访问自动生成的 API 文档：

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **OpenAPI JSON**: http://127.0.0.1:8000/openapi.json

---

## 注意事项

1. 所有图像数据使用 Base64 编码的 JPEG 格式
2. 点云数据如果超过 10000 个点，会自动采样
3. 连接操作是异步的，需要等待几秒钟后检查状态
4. 回放功能仅在使用 Mock Client 时可用
5. 所有时间戳使用 Unix 时间戳（秒，浮点数）

