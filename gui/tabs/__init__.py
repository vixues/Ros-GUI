"""Tab implementations for the GUI."""
from .base_tab import BaseTab
from .connection_tab import ConnectionTab
from .status_tab import StatusTab
from .image_tab import ImageTab
from .control_tab import ControlTab
from .pointcloud_tab import PointCloudTab
from .view_3d_tab import View3DTab
from .map_tab import MapTab
from .network_tab import NetworkTab

try:
    from .rosbag_tab import RosbagTab
    HAS_ROSBAG_TAB = True
except ImportError:
    HAS_ROSBAG_TAB = False
    RosbagTab = None

__all__ = [
    'BaseTab',
    'ConnectionTab',
    'StatusTab',
    'ImageTab',
    'ControlTab',
    'PointCloudTab',
    'View3DTab',
    'MapTab',
    'NetworkTab',
]
if HAS_ROSBAG_TAB:
    __all__.append('RosbagTab')
