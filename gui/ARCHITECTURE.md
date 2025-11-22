# GUI 架构文档

## 模块化架构概览

GUI 已重构为专业的模块化架构，遵循单一职责原则和关注点分离。

## 目录结构

```
gui/
├── __init__.py                 # 主入口导出
├── main.py                     # 主应用入口（过渡期）
├── design/                     # 设计系统
│   ├── __init__.py
│   └── design_system.py        # 颜色、字体、样式常量
├── components/                  # UI组件库
│   ├── __init__.py
│   ├── base.py                # 基础组件（UIComponent, Panel, Card, Label, Field）
│   ├── interactive.py         # 交互组件（Button, TextInput, Checkbox, Items）
│   ├── display.py             # 显示组件（ImageDisplay, PointCloudDisplay）
│   └── advanced.py            # 高级组件（MapComponent, JSONEditor, TopicList）
├── renderers/                  # 渲染器
│   ├── __init__.py
│   └── point_cloud.py          # 点云3D渲染器
├── layout/                     # 布局管理
│   ├── __init__.py
│   └── layout_manager.py       # 自动布局计算
└── tabs/                       # 标签页实现
    ├── __init__.py
    ├── base_tab.py            # 标签页基类
    ├── connection_tab.py       # 连接标签页
    └── status_tab.py          # 状态标签页
```

## 核心模块说明

### 1. 设计系统 (design/)

**职责**: 集中管理所有视觉样式

- **DesignSystem**: 单例类，包含：
  - `COLORS`: 颜色调色板（黑色工业主题）
  - `FONTS`: 字体系统（控制台等宽字体）
  - `SPACING`: 间距常量
  - `RADIUS`: 圆角常量
  - `init_fonts()`: 字体初始化
  - `get_font()`: 获取字体

**使用示例**:
```python
from gui.design import DesignSystem

# 初始化字体
DesignSystem.init_fonts()

# 获取颜色
bg_color = DesignSystem.COLORS['bg']

# 获取字体
font = DesignSystem.get_font('label')
```

### 2. 组件系统 (components/)

#### 2.1 基础组件 (base.py)

**职责**: 提供组件基础设施和容器组件

- **ComponentPort**: 基于端口的消息传递系统
  - 支持信号、回调和参数三种端口类型
  - 自动处理函数签名检测
  
- **UIComponent**: 所有组件的基类
  - 端口系统集成
  - 事件处理接口
  - 更新和绘制接口

- **Panel**: 面板容器
  - 子组件管理
  - 事件转发
  - 相对坐标转换

- **Card**: 卡片组件
  - 标题栏支持
  - 内容区域管理
  - 阴影效果

- **Label**: 文本标签
  - 自动大小计算
  - 对齐支持（左/中/右）

- **Field**: 字段显示
  - 标签+值显示
  - 颜色状态支持

#### 2.2 交互组件 (interactive.py)

**职责**: 用户输入和交互组件

- **Button**: 按钮
  - 悬停/按下状态
  - 动画效果
  - 端口系统回调

- **TextInput**: 文本输入
  - 光标支持
  - 键盘导航
  - 占位符文本

- **Checkbox**: 复选框
  - 选中状态
  - 标签显示

- **Items**: 列表组件
  - 选择支持
  - 滚动支持
  - 项目类型显示

#### 2.3 显示组件 (display.py)

**职责**: 专业数据显示组件

- **ImageDisplayComponent**: 图像显示
  - 自动缩放
  - 保持宽高比
  - 占位符支持

- **PointCloudDisplayComponent**: 点云显示
  - 3D视图控制
  - 立方体导航
  - 相机控制
  - 拖拽旋转

#### 2.4 高级组件 (advanced.py)

**职责**: 复杂功能组件

- **MapComponent**: 地图显示
  - 无人机位置显示
  - 轨迹绘制
  - 图例显示

- **JSONEditor**: JSON编辑器
  - 语法高亮
  - 选择/复制/粘贴
  - 撤销/重做
  - 行号显示

- **TopicList**: 主题列表
  - 继承自Items
  - 主题专用功能

### 3. 渲染器 (renderers/)

**职责**: 专业渲染功能

- **PointCloudRenderer**: 点云渲染器
  - 优化的3D投影
  - 自适应采样
  - 过滤和下采样
  - 颜色方案
  - 轴显示
  - 性能统计

### 4. 布局管理 (layout/)

**职责**: 自动布局计算

- **LayoutManager**: 布局管理器
  - 内容区域计算
  - 标题区域计算
  - 组件区域计算
  - 内边距管理
  - 渲染器大小计算

### 5. 标签页 (tabs/)

**职责**: 标签页实现

- **BaseTab**: 标签页基类
  - 抽象接口定义
  - 依赖注入模式

- **ConnectionTab**: 连接标签页
  - 多无人机管理
  - 连接配置
  - 日志显示

- **StatusTab**: 状态标签页
  - 状态字段显示
  - 相机和点云显示

## 设计模式

### 1. 组件端口系统

所有组件通过端口系统进行通信：

```python
# 创建端口
component.add_port('on_click', 'callback')

# 连接处理器
component.connect_port('on_click', my_handler)

# 发射信号
component.emit_signal('click', data)
```

### 2. 依赖注入

标签页通过依赖注入接收应用状态：

```python
# 标签页接收应用状态
def draw(self, app_state: Dict[str, Any]):
    drones = app_state.get('drones', {})
    current_drone_id = app_state.get('current_drone_id')
```

### 3. 设计系统单例

设计系统作为单例，全局共享样式：

```python
# 所有组件共享同一设计系统
DesignSystem.COLORS['primary']
DesignSystem.get_font('label')
```

## 使用指南

### 导入组件

```python
# 设计系统
from gui.design import DesignSystem

# 基础组件
from gui.components import UIComponent, Panel, Card, Label, Field

# 交互组件
from gui.components import Button, TextInput, Checkbox, Items

# 显示组件
from gui.components import ImageDisplayComponent, PointCloudDisplayComponent

# 高级组件
from gui.components import MapComponent, JSONEditor, TopicList

# 渲染器
from gui.renderers import PointCloudRenderer

# 布局管理器
from gui.layout import LayoutManager

# 标签页
from gui.tabs import BaseTab, ConnectionTab, StatusTab
```

### 创建组件

```python
# 初始化设计系统
DesignSystem.init_fonts()

# 创建按钮
button = Button(100, 100, 120, 40, "Click Me", callback=my_handler)

# 创建卡片
card = Card(50, 50, 400, 300, "My Card")
card.add_child(button)

# 绘制
card.draw(screen)
```

### 事件处理

```python
# 在事件循环中
for event in pygame.event.get():
    if button.handle_event(event):
        # 事件已处理
        continue
```

## 扩展指南

### 添加新组件

1. 继承 `UIComponent`
2. 实现 `handle_event()`, `update()`, `draw()` 方法
3. 在 `components/__init__.py` 中导出

### 添加新标签页

1. 继承 `BaseTab`
2. 实现 `draw()`, `handle_event()`, `update()` 方法
3. 使用依赖注入接收应用状态
4. 在 `tabs/__init__.py` 中导出

### 添加新渲染器

1. 在 `renderers/` 目录创建新文件
2. 实现渲染逻辑
3. 在 `renderers/__init__.py` 中导出

## 性能优化

1. **渲染缓存**: 点云渲染器使用缓存机制
2. **自适应采样**: 根据点数量自动调整采样率
3. **向量化操作**: 使用numpy进行批量计算
4. **事件节流**: 鼠标交互使用节流机制

## 测试建议

1. **单元测试**: 每个组件独立测试
2. **集成测试**: 测试组件组合
3. **性能测试**: 测试渲染性能
4. **UI测试**: 测试用户交互

## 迁移路径

当前 `rosclient_gui_pygame.py` 仍然可用。新模块化结构可以逐步集成：

1. **阶段1**: 使用新组件替换旧组件（已完成）
2. **阶段2**: 迁移标签页到新结构（进行中）
3. **阶段3**: 重构主应用类使用新模块（待完成）
4. **阶段4**: 完全移除旧代码（待完成）

## 注意事项

- 所有模块依赖 `pygame`
- 点云功能需要 `numpy`
- 图像功能需要 `cv2`（可选）
- 3D视图需要 `open3d`（可选）
- 保持向后兼容性

