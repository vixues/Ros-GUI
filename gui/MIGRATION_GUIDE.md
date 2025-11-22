# 迁移指南

## 概述

本文档说明如何从原始的 `rosclient_gui_pygame.py` 迁移到新的模块化架构。

## 已完成的工作

### ✅ 核心模块（100%完成）

1. **设计系统** (`gui/design/`)
   - 完整的颜色、字体、样式系统
   - 单例模式，全局共享

2. **组件库** (`gui/components/`)
   - 基础组件：UIComponent, Panel, Card, Label, Field
   - 交互组件：Button, TextInput, Checkbox, Items
   - 显示组件：ImageDisplayComponent, PointCloudDisplayComponent
   - 高级组件：MapComponent, JSONEditor, TopicList

3. **渲染器** (`gui/renderers/`)
   - PointCloudRenderer：优化的3D点云渲染

4. **布局管理** (`gui/layout/`)
   - LayoutManager：自动布局计算

5. **标签页基础** (`gui/tabs/`)
   - BaseTab：标签页基类
   - ConnectionTab：连接标签页
   - StatusTab：状态标签页

## 如何使用新模块

### 方式1：直接使用新组件（推荐）

```python
from gui.design import DesignSystem
from gui.components import Button, Card, Label
from gui.renderers import PointCloudRenderer

# 初始化
DesignSystem.init_fonts()

# 创建组件
button = Button(100, 100, 120, 40, "Click Me")
card = Card(50, 50, 400, 300, "My Card")
card.add_child(button)

# 在事件循环中
for event in pygame.event.get():
    button.handle_event(event)
    card.handle_event(event)

# 更新
button.update(dt)
card.update(dt)

# 绘制
card.draw(screen)
```

### 方式2：使用标签页系统

```python
from gui.tabs import ConnectionTab, StatusTab

# 创建标签页
connection_tab = ConnectionTab(screen, width, height, components)
status_tab = StatusTab(screen, width, height, components)

# 应用状态
app_state = {
    'drones': drones,
    'current_drone_id': current_drone_id,
    'connection_logs': connection_logs,
    'status_data': status_data,
    'current_image': current_image,
    'pc_surface_simple': pc_surface_simple,
    'pc_camera': (angle_x, angle_y, zoom),
}

# 绘制
if current_tab == 0:
    connection_tab.draw(app_state)
elif current_tab == 1:
    status_tab.draw(app_state)

# 事件处理
if connection_tab.handle_event(event, app_state):
    # 事件已处理
    pass
```

## 迁移步骤

### 步骤1：替换组件创建

**旧代码**:
```python
# 手动创建和定位组件
self.button = Button(100, 100, 120, 40, "Click", callback)
```

**新代码**:
```python
# 使用新组件系统
from gui.components import Button
self.button = Button(100, 100, 120, 40, "Click", callback)
```

### 步骤2：替换绘制代码

**旧代码**:
```python
def draw_button(self):
    pygame.draw.rect(self.screen, color, self.button_rect)
    # ... 手动绘制
```

**新代码**:
```python
def draw_button(self):
    self.button.draw(self.screen)
```

### 步骤3：使用标签页系统

**旧代码**:
```python
def draw_connection_tab(self):
    # 大量手动绘制代码
    ...
```

**新代码**:
```python
from gui.tabs import ConnectionTab

def __init__(self):
    self.connection_tab = ConnectionTab(
        self.screen, self.screen_width, self.screen_height, 
        self.components
    )

def draw_connection_tab(self):
    app_state = self.get_app_state()
    self.connection_tab.draw(app_state)
```

## 兼容性说明

- ✅ 原始文件 `rosclient_gui_pygame.py` 仍然可用
- ✅ 新模块可以独立使用
- ✅ 可以逐步迁移，不需要一次性完成
- ✅ 新旧代码可以共存

## 优势

1. **代码组织**: 清晰的模块结构
2. **可维护性**: 易于理解和修改
3. **可扩展性**: 易于添加新功能
4. **可测试性**: 组件可独立测试
5. **可重用性**: 组件可在不同场景复用

## 下一步

1. 完成剩余标签页（6个）
2. 重构主应用类
3. 编写测试
4. 性能优化
5. 移除旧代码

## 示例：创建自定义组件

```python
from gui.components.base import UIComponent
from gui.design import DesignSystem

class MyCustomComponent(UIComponent):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.value = 0
    
    def draw(self, surface):
        if not self.visible:
            return
        # 使用设计系统
        pygame.draw.rect(surface, DesignSystem.COLORS['surface'], self.rect)
        font = DesignSystem.get_font('label')
        text = font.render(str(self.value), True, DesignSystem.COLORS['text'])
        surface.blit(text, self.rect.topleft)
```

## 示例：创建自定义标签页

```python
from gui.tabs.base_tab import BaseTab
from gui.components import Label, Card

class MyCustomTab(BaseTab):
    def __init__(self, screen, screen_width, screen_height, components):
        super().__init__(screen, screen_width, screen_height)
        self.components = components
    
    def draw(self, app_state):
        # 使用组件绘制
        label = Label(50, 50, "My Tab", 'title')
        label.draw(self.screen)
    
    def handle_event(self, event, app_state):
        # 处理事件
        return False
    
    def update(self, dt, app_state):
        # 更新状态
        pass
```

