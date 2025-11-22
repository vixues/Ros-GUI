# GUI Module Structure

This directory contains the modularized GUI components for the RosClient application.

## Directory Structure

```
gui/
├── __init__.py                 # Main exports
├── main.py                     # Main application entry point
├── design/                     # Design system
│   ├── __init__.py
│   └── design_system.py        # Colors, fonts, spacing, etc.
├── components/                  # UI Components
│   ├── __init__.py
│   ├── base.py                # Base components (UIComponent, Panel, Card, Label, Field)
│   ├── interactive.py         # Interactive components (Button, TextInput, Checkbox, Items)
│   ├── display.py             # Display components (ImageDisplay, PointCloudDisplay)
│   └── advanced.py            # Advanced components (MapComponent, JSONEditor, TopicList)
├── renderers/                  # Renderers
│   ├── __init__.py
│   └── point_cloud.py         # Point cloud renderer
├── layout/                     # Layout management
│   ├── __init__.py
│   └── layout_manager.py      # Layout manager for automatic sizing
└── tabs/                       # Tab implementations (to be created)
    ├── __init__.py
    ├── connection_tab.py
    ├── status_tab.py
    ├── image_tab.py
    ├── control_tab.py
    ├── pointcloud_tab.py
    ├── 3d_view_tab.py
    ├── map_tab.py
    └── network_tab.py
```

## Module Overview

### Design System (`design/`)
- **design_system.py**: Centralized design system with colors, fonts, spacing, and styling constants
  - Color palette (black theme with industrial styling)
  - Typography system (console monospace fonts)
  - Spacing and border radius constants
  - Font initialization and management

### Components (`components/`)
- **base.py**: Foundation components
  - `ComponentPort`: Port-based message passing system
  - `UIComponent`: Base class for all UI components
  - `Panel`: Container component with styling
  - `Card`: Card component with shadow and border
  - `Label`: Text label component
  - `Field`: Label + value display component

- **interactive.py**: Interactive user input components
  - `Button`: Button with hover/press states
  - `TextInput`: Text input with cursor
  - `Checkbox`: Checkbox component
  - `Items`: List component with selection

- **display.py**: Display components (to be created)
  - `ImageDisplayComponent`: Image display with scaling
  - `PointCloudDisplayComponent`: Point cloud 3D view with controls

- **advanced.py**: Advanced components (to be created)
  - `MapComponent`: Map display for drone positions
  - `JSONEditor`: Advanced JSON editor with syntax highlighting
  - `TopicList`: Specialized topic list component

### Renderers (`renderers/`)
- **point_cloud.py**: Professional point cloud renderer
  - Optimized 3D projection rendering
  - Adaptive sampling for performance
  - Filtering and downsampling
  - Color schemes and axis display

### Layout (`layout/`)
- **layout_manager.py**: Automatic layout calculation
  - Content area calculation
  - Header and component area sizing
  - Padding and spacing management
  - Renderer size calculation

### Tabs (`tabs/`)
- Individual tab implementations (to be created)
  - Each tab is a separate module for better organization
  - Tabs handle their own UI setup and event handling

## Usage

```python
from gui import RosClientPygameGUI

# Create and run the GUI
app = RosClientPygameGUI()
app.run()
```

## Refactoring Status

The GUI has been partially refactored into a modular structure:

✅ **Completed:**
- Design system module
- Base components module
- Interactive components module
- Point cloud renderer module
- Layout manager module

🔄 **In Progress:**
- Display components (ImageDisplay, PointCloudDisplay)
- Advanced components (MapComponent, JSONEditor)

⏳ **To Do:**
- Tab implementations (split into separate modules)
- Main application class refactoring
- Complete integration testing

## Benefits of Modular Structure

1. **Maintainability**: Each module has a clear responsibility
2. **Reusability**: Components can be easily reused across different parts of the application
3. **Testability**: Individual components can be tested in isolation
4. **Scalability**: Easy to add new components or features
5. **Code Organization**: Clear separation of concerns

## Migration Notes

The original `rosclient_gui_pygame.py` file is still functional. The new modular structure is being gradually integrated. The `main.py` currently imports from the original file to maintain backward compatibility while the refactoring is completed.

