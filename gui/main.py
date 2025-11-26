#!/usr/bin/env python
"""Main GUI application using modular architecture."""
import sys
import os
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pygame
import threading
import json
import time
import math
from typing import Optional, Dict, Any, List
import queue

try:
    from rosclient import RosClient, MockRosClient, DroneState, ConnectionState
except ImportError:
    print("Warning: rosclient module not found. Please ensure it's in the Python path.")
    raise

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
    HAS_NUMPY = True
except ImportError:
    HAS_CV2 = False
    HAS_NUMPY = False
    np = None
    print("Warning: cv2/numpy not available. Image display will be disabled.")

try:
    import open3d as o3d
    HAS_OPEN3D = True
except ImportError:
    HAS_OPEN3D = False
    print("Warning: open3d not available. Advanced 3D display will be disabled.")

from gui.design.design_system import DesignSystem
from gui.layout.layout_manager import LayoutManager
from gui.components import (
    Button, TextInput, Checkbox, Label, Card, Field,
    ImageDisplayComponent, PointCloudDisplayComponent,
    MapComponent, JSONEditor, TopicList
)
from gui.renderers import PointCloudRenderer, HAS_POINTCLOUD
from gui.renderers.ui_renderer import get_renderer
from gui.renderers.realtime_optimizer import get_optimizer
from gui.tabs import (
    ConnectionTab, StatusTab, ImageTab, ControlTab,
    PointCloudTab, View3DTab, MapTab, NetworkTab
)

try:
    from gui.tabs import RosbagTab
    HAS_ROSBAG_TAB = True
except ImportError:
    HAS_ROSBAG_TAB = False
    RosbagTab = None


class RosClientPygameGUI:
    """Industrial-grade Pygame GUI for RosClient with modular architecture."""
    
    def __init__(self):
        pygame.init()
        DesignSystem.init_dpi()  # Initialize DPI awareness first
        DesignSystem.init_fonts()
        
        # Scale screen dimensions by DPI
        base_width = 1400
        base_height = 900
        self.screen_width = DesignSystem.scale_int(base_width)
        self.screen_height = DesignSystem.scale_int(base_height)
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("ROS Client - Fighter Cockpit Interface")
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.dt = 0
        
        # Multi-drone client state
        self.drones: Dict[str, Dict[str, Any]] = {}
        self.current_drone_id: Optional[str] = None
        self.drone_counter = 0
        
        # Legacy single client support
        self.client: Optional[RosClient] = None
        self.is_connected = False
        
        # Update threads
        self.update_thread: Optional[threading.Thread] = None
        self.stop_update = threading.Event()
        self.image_queue = queue.Queue(maxsize=1)
        self.current_image = None
        
        # Tabs
        self.tabs = ["Connection", "Status", "Image", "Control", "Point Cloud", "3D View", "Map", "Network Test", "ROS Bag"]
        self.current_tab = 0
        
        # Layout manager
        self.layout = LayoutManager(self.screen_width, self.screen_height)
        
        # Rendering system
        self.renderer = get_renderer()
        self.optimizer = get_optimizer()
        
        # Application state (shared with tabs)
        self.app_state: Dict[str, Any] = {
            'drones': self.drones,
            'current_drone_id': self.current_drone_id,
            'current_image': self.current_image,
            'pc_surface_simple': None,
            'pc_surface_o3d': None,
            'pc_camera': (0.0, 0.0, 1.0),
            'pc_last_interaction_time': 0.0,
            'pc_interaction_throttle': 0.016,
            'command_history': [],
            'test_results': [],
            'connection_logs': [],
            'status_data': {},
        }
        
        # UI Components
        self.components: Dict[str, Any] = {}
        self.setup_ui()
        
        # Initialize tabs
        self.tab_instances: List[Any] = [
            ConnectionTab(self.screen, self.screen_width, self.screen_height, self.components),
            StatusTab(self.screen, self.screen_width, self.screen_height, self.components),
            ImageTab(self.screen, self.screen_width, self.screen_height, self.components),
            ControlTab(self.screen, self.screen_width, self.screen_height, self.components),
            PointCloudTab(self.screen, self.screen_width, self.screen_height, self.components),
            View3DTab(self.screen, self.screen_width, self.screen_height, self.components),
            MapTab(self.screen, self.screen_width, self.screen_height, self.components),
            NetworkTab(self.screen, self.screen_width, self.screen_height, self.components),
        ]
        
        # Add RosbagTab if available
        if HAS_ROSBAG_TAB and RosbagTab:
            self.tab_instances.append(
                RosbagTab(self.screen, self.screen_width, self.screen_height, self.components)
            )
        else:
            # Add placeholder if not available
            self.tab_instances.append(None)
        
        # Performance optimization: caching and threading
        self.image_cache = None
        self.image_cache_lock = threading.Lock()
        self.pc_cache = None
        self.pc_cache_lock = threading.Lock()
        self.pc_render_cache = None
        self.pc_render_cache_params = None
        self.image_thread = None
        self.pc_thread = None
        self.render_thread = None
        self.stop_render_threads = threading.Event()
        
        # Point cloud state
        self.current_point_cloud = None
        self.pc_camera_angle_x = 0.0
        self.pc_camera_angle_y = 0.0
        self.pc_zoom = 1.0
        self.pc_last_render_time = 0.0
        self.pc_render_interval = 0.033  # ~30 FPS
        self.pc_last_interaction_time = 0.0
        self.pc_interaction_throttle = 0.016  # ~60 FPS
        
        # Open3D state
        self.o3d_vis = None
        self.o3d_geometry = None
        self.o3d_window_created = False
        self.o3d_last_update = 0.0
        self.o3d_update_interval = 0.033
        self.o3d_window_size = (1200, 800)
        
        # Image update throttling
        self.image_last_update_time = 0.0
        self.image_update_interval = 0.033  # ~30 FPS
        
        # Initialize point cloud renderer
        if HAS_POINTCLOUD:
            self.pc_renderer = PointCloudRenderer(width=800, height=600)
        else:
            self.pc_renderer = None
        
        # Setup update loop
        self.setup_update_loop()
        
    def setup_ui(self):
        """Setup UI components."""
        # Connection tab components
        self.components['drone_name_input'] = TextInput(200, 100, 200, 35, "Drone 1")
        self.components['connection_url_input'] = TextInput(420, 100, 400, 35, "ws://localhost:9090")
        self.components['use_mock_checkbox'] = Checkbox(200, 150, "Use Mock Client (Test Mode)", False)
        # Use auto-sizing buttons (width=None for auto-size based on text)
        self.components['add_drone_btn'] = Button(200, 200, None, 40, "Add Drone", self.add_drone)
        self.components['connect_btn'] = Button(0, 200, None, 40, "Connect", self.connect)
        self.components['disconnect_btn'] = Button(0, 200, None, 40, "Disconnect", self.disconnect)
        self.components['disconnect_btn'].color = DesignSystem.COLORS['error']
        self.components['remove_drone_btn'] = Button(0, 200, None, 40, "Remove", self.remove_drone)
        self.components['remove_drone_btn'].color = DesignSystem.COLORS['error']
        
        # Status display
        self.components['status_fields'] = {}
        
        # Control tab components
        self.components['topic_list'] = TopicList(50, 100, 450, 500)
        self.components['topic_list'].on_select = self.on_topic_selected
        self.components['control_topic_input'] = TextInput(370, 100, 380, 40, "/control")
        self.components['control_type_input'] = TextInput(770, 100, 380, 40, "controller_msgs/cmd")
        self.components['json_editor'] = JSONEditor(370, 160, 780, 340, '{\n    "cmd": 1\n}')
        
        # Preset command buttons - use auto-sizing
        preset_commands = [
            ("Takeoff", '{\n    "cmd": 1\n}'),
            ("Land", '{\n    "cmd": 2\n}'),
            ("Return", '{\n    "cmd": 3\n}'),
            ("Hover", '{\n    "cmd": 4\n}'),
        ]
        self.components['preset_buttons'] = []
        for i, (name, cmd) in enumerate(preset_commands):
            btn = Button(370 + i * 140, 520, None, 38, name, 
                        lambda c=cmd: self.set_preset_command(c))
            self.components['preset_buttons'].append(btn)
        
        self.components['format_json_btn'] = Button(370, 570, None, 42, "Format JSON", 
                                                     self.format_json, DesignSystem.COLORS['accent'])
        self.components['send_command_btn'] = Button(520, 570, None, 42, "Send Command", 
                                                     self.send_control_command,
                                                     DesignSystem.COLORS['success'])
        
        # Display components
        self.components['status_image_display'] = ImageDisplayComponent(0, 0, 0, 0, "Camera Stream")
        self.components['status_pointcloud_display'] = PointCloudDisplayComponent(0, 0, 0, 0, "Point Cloud")
        self.components['image_display'] = ImageDisplayComponent(0, 0, 0, 0, "Image Stream")
        self.components['pointcloud_display'] = PointCloudDisplayComponent(0, 0, 0, 0, "Point Cloud Stream")
        self.components['map_display'] = MapComponent(0, 0, 0, 0, "")
        
        # Network test components - Quick Test
        self.components['network_host_input'] = TextInput(0, 0, 300, 35, "localhost")
        self.components['ping_btn'] = Button(0, 0, None, 35, "Ping", self.ping_test)
        self.components['ws_test_btn'] = Button(0, 0, None, 35, "Test WebSocket", self.test_websocket)
        self.components['ros_test_btn'] = Button(0, 0, None, 35, "Test ROS", self.test_ros_quick)
        
        # Port Scan components
        self.components['scan_host_input'] = TextInput(0, 0, 200, 35, "localhost")
        self.components['port_range_input'] = TextInput(0, 0, 200, 35, "22,80,443,9090")
        self.components['tcp_checkbox'] = Checkbox(0, 0, "TCP", True)
        self.components['udp_checkbox'] = Checkbox(0, 0, "UDP", False)
        self.components['scan_btn'] = Button(0, 0, None, 35, "Scan Ports", self.scan_ports)
        
        # Device Discovery components
        self.components['network_input'] = TextInput(0, 0, 200, 35, "192.168.1.0/24")
        self.components['discover_btn'] = Button(0, 0, None, 35, "Discover Devices", self.discover_devices)
        
        # ROS Discovery components
        self.components['ros_network_input'] = TextInput(0, 0, 200, 35, "192.168.1.0/24")
        self.components['auto_detect_network_btn'] = Button(0, 0, None, 30, "Auto Detect", self.auto_detect_network)
        self.components['discover_ros_btn'] = Button(0, 0, None, 35, "Discover ROS Devices", self.discover_ros_devices)
        self.components['test_all_ros_btn'] = Button(0, 0, None, 35, "Test All ROS", self.test_all_ros_devices)
        
        # ROS Test components
        self.components['ros_url_input'] = TextInput(0, 0, 400, 35, "ws://localhost:9090")
        self.components['ros_connection_btn'] = Button(0, 0, None, 35, "Test ROS Connection", self.test_ros_connection)
        
        # Results
        self.components['save_results_btn'] = Button(0, 0, None, 30, "Save Results", self.save_network_results)
        self.components['save_ros_devices_btn'] = Button(0, 0, None, 30, "Save ROS Devices", self.save_ros_devices)
        self.components['save_ros_devices_btn'] = Button(0, 0, None, 30, "Save ROS Devices", self.save_ros_devices)
        
        # Legacy components (for backward compatibility)
        self.components['test_url_input'] = self.components['ros_url_input']
        self.components['test_timeout_input'] = TextInput(0, 0, 100, 35, "5")
        self.components['test_btn'] = self.components['ros_connection_btn']
        
    def on_topic_selected(self, topic_data):
        """Handle topic selection."""
        if isinstance(topic_data, tuple):
            self.components['control_topic_input'].text = topic_data[0]
            if topic_data[1]:
                self.components['control_type_input'].text = topic_data[1]
        else:
            self.components['control_topic_input'].text = topic_data
    
    def setup_update_loop(self):
        """Setup periodic update loop with caching and threading at 30 FPS."""
        def update_loop():
            update_interval = 0.033  # 30 FPS
            while not self.stop_update.is_set():
                try:
                    has_connected_drones = any(
                        drone_info.get('client') and drone_info.get('is_connected')
                        for drone_info in self.drones.values()
                    )
                    
                    if has_connected_drones:
                        # Update trajectory for all drones
                        for drone_id, drone_info in self.drones.items():
                            if drone_info.get('client') and drone_info.get('is_connected'):
                                try:
                                    pos = drone_info['client'].get_position()
                                    if len(pos) >= 3 and pos[0] != 0.0 and pos[1] != 0.0:
                                        drone_info['trajectory'].append((pos[0], pos[1], pos[2]))
                                        if len(drone_info['trajectory']) > 1000:
                                            drone_info['trajectory'] = drone_info['trajectory'][-1000:]
                                except:
                                    pass
                        
                        # Update based on current tab
                        if self.current_tab == 1:  # Status tab
                            self.update_status()
                            if HAS_CV2:
                                self.update_image_async()
                            if HAS_POINTCLOUD:
                                self.update_pointcloud_async()
                                self.update_pointcloud_simple()
                        elif self.current_tab == 2 and HAS_CV2:  # Image tab
                            self.update_image_async()
                        elif self.current_tab == 4 and HAS_POINTCLOUD:  # Point cloud tab
                            self.update_pointcloud_async()
                            self.update_pointcloud_simple()
                        elif self.current_tab == 5 and HAS_OPEN3D:  # 3D View tab
                            self.update_pointcloud_open3d_async()
                        elif self.current_tab == 3:  # Control tab
                            self.update_topic_list()
                    
                    # Check for rosbag client and update data
                    rosbag_client = self.app_state.get('rosbag_client')
                    if rosbag_client and rosbag_client.is_connected():
                        # Update image from rosbag
                        if HAS_CV2 and (self.current_tab == 1 or self.current_tab == 2):
                            self.update_image_from_rosbag(rosbag_client)
                        # Update point cloud from rosbag
                        if HAS_POINTCLOUD and (self.current_tab == 1 or self.current_tab == 4):
                            self.update_pointcloud_from_rosbag(rosbag_client)
                except Exception as e:
                    print(f"Update error: {e}")
                time.sleep(update_interval)
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
        self.start_render_threads()
    
    def add_drone(self):
        """Add a new drone to the management list."""
        name = self.components['drone_name_input'].text.strip()
        url = self.components['connection_url_input'].text.strip()
        
        if not name:
            self.add_log("Error: Please enter drone name")
            return
        if not url:
            self.add_log("Error: Please enter WebSocket address")
            return
        
        drone_id = f"drone_{self.drone_counter}"
        self.drone_counter += 1
        
        self.drones[drone_id] = {
            'name': name,
            'url': url,
            'client': None,
            'is_connected': False,
            'use_mock': False,
            'image': None,
            'pointcloud': None,
            'trajectory': []
        }
        
        if self.current_drone_id is None:
            self.current_drone_id = drone_id
        
        self.add_log(f"Added drone: {name} ({url})")
        self.app_state['current_drone_id'] = self.current_drone_id
    
    def remove_drone(self):
        """Remove the currently selected drone."""
        if self.current_drone_id is None:
            self.add_log("Error: No drone selected")
            return
        
        drone_id = self.current_drone_id
        drone_info = self.drones.get(drone_id)
        
        if drone_info:
            if drone_info['client']:
                try:
                    drone_info['client'].terminate()
                except:
                    pass
            
            del self.drones[drone_id]
            self.add_log(f"Removed drone: {drone_info['name']}")
            
            if len(self.drones) > 0:
                self.current_drone_id = list(self.drones.keys())[0]
            else:
                self.current_drone_id = None
                self.client = None
                self.is_connected = False
        
        self.app_state['current_drone_id'] = self.current_drone_id
    
    def connect(self):
        """Connect the currently selected drone to ROS bridge."""
        if self.current_drone_id is None:
            self.add_log("Error: No drone selected")
            return
        
        drone_id = self.current_drone_id
        drone_info = self.drones[drone_id]
        url = drone_info['url']
        use_mock = self.components['use_mock_checkbox'].checked
        
        def connect_thread():
            try:
                self.add_log(f"Connecting {drone_info['name']} to {url}...")
                
                if use_mock:
                    client = MockRosClient(url)
                    self.add_log(f"Using Mock Client (Test Mode) for {drone_info['name']}")
                else:
                    client = RosClient(url)
                    client.connect_async()
                
                time.sleep(2)
                
                if client.is_connected():
                    drone_info['client'] = client
                    drone_info['is_connected'] = True
                    drone_info['use_mock'] = use_mock
                    
                    self.client = client
                    self.is_connected = True
                    
                    self.add_log(f"Connection successful for {drone_info['name']}!")
                    self.update_topic_list()
                else:
                    self.add_log(f"Connection failed for {drone_info['name']}, please check address and network")
            except Exception as e:
                self.add_log(f"Connection error for {drone_info['name']}: {e}")
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def disconnect(self):
        """Disconnect the currently selected drone from ROS bridge."""
        if self.current_drone_id is None:
            self.add_log("Error: No drone selected")
            return
        
        drone_id = self.current_drone_id
        drone_info = self.drones.get(drone_id)
        
        try:
            if drone_info and drone_info['client']:
                drone_info['client'].terminate()
                drone_info['client'] = None
                drone_info['is_connected'] = False
                self.add_log(f"Disconnected {drone_info['name']}")
            
            if self.current_drone_id == drone_id:
                self.is_connected = False
                self.client = None
        except Exception as e:
            self.add_log(f"Disconnect error: {e}")
    
    def add_log(self, message: str):
        """Add log message."""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        if 'connection_logs' not in self.app_state:
            self.app_state['connection_logs'] = []
        self.app_state['connection_logs'].append(log_entry)
        if len(self.app_state['connection_logs']) > 50:
            self.app_state['connection_logs'].pop(0)
    
    def update_status(self):
        """Update status display for the currently selected drone."""
        if self.current_drone_id is None:
            return
        
        drone_info = self.drones.get(self.current_drone_id)
        if not drone_info or not drone_info['client'] or not drone_info['is_connected']:
            return
        
        client = drone_info['client']
        self.client = client
        self.is_connected = drone_info['is_connected']
        
        try:
            state = client.get_status()
            pos = client.get_position()
            ori = client.get_orientation()
            
            if len(pos) >= 3 and pos[0] != 0.0 and pos[1] != 0.0:
                drone_info['trajectory'].append((pos[0], pos[1], pos[2]))
                if len(drone_info['trajectory']) > 1000:
                    drone_info['trajectory'] = drone_info['trajectory'][-1000:]
            
            status_data = {
                "connected": ("Connected" if state.connected else "Disconnected",
                             DesignSystem.COLORS['success'] if state.connected else DesignSystem.COLORS['error']),
                "armed": ("Armed" if state.armed else "Disarmed",
                         DesignSystem.COLORS['warning'] if state.armed else DesignSystem.COLORS['text_secondary']),
                "mode": (state.mode or "N/A", DesignSystem.COLORS['text']),
                "battery": (f"{state.battery:.1f}%", 
                           DesignSystem.COLORS['error'] if state.battery < 20 else
                           DesignSystem.COLORS['warning'] if state.battery < 50 else
                           DesignSystem.COLORS['success']),
                "latitude": (f"{pos[0]:.6f}", DesignSystem.COLORS['text']),
                "longitude": (f"{pos[1]:.6f}", DesignSystem.COLORS['text']),
                "altitude": (f"{pos[2]:.2f}m", DesignSystem.COLORS['text']),
                "roll": (f"{ori[0]:.2f}°", DesignSystem.COLORS['text']),
                "pitch": (f"{ori[1]:.2f}°", DesignSystem.COLORS['text']),
                "yaw": (f"{ori[2]:.2f}°", DesignSystem.COLORS['text']),
                "landed": ("Landed" if state.landed else "Flying", DesignSystem.COLORS['text']),
                "reached": ("Yes" if state.reached else "No", DesignSystem.COLORS['text']),
                "returned": ("Yes" if state.returned else "No", DesignSystem.COLORS['text']),
                "tookoff": ("Yes" if state.tookoff else "No", DesignSystem.COLORS['text']),
            }
            
            self.app_state['status_data'] = status_data
            
            for key, (value, color) in status_data.items():
                if key in self.components['status_fields']:
                    self.components['status_fields'][key].set_value(value, color)
        except Exception:
            pass
    
    def update_image_async(self):
        """Update image display asynchronously with caching at 30 FPS."""
        if self.current_drone_id is None:
            return
        
        drone_info = self.drones.get(self.current_drone_id)
        if not drone_info or not drone_info.get('client') or not drone_info.get('is_connected'):
            return
        
        client = drone_info['client']
        self.client = client
        self.is_connected = drone_info['is_connected']
        
        current_time = time.time()
        if current_time - self.image_last_update_time < self.image_update_interval:
            return
        
        if self.image_thread and self.image_thread.is_alive():
            return
        
        def update_image_thread():
            try:
                image_data = client.get_latest_image()
                if image_data:
                    frame, timestamp = image_data
                    max_width, max_height = 800, 600
                    h, w = frame.shape[:2]
                    scale = min(max_width / w, max_height / h)
                    new_w, new_h = int(w * scale), int(h * scale)
                    frame_resized = cv2.resize(frame, (new_w, new_h))
                    frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
                    frame_rotated = np.rot90(frame_rgb, k=3)
                    frame_flipped = np.fliplr(frame_rotated)
                    new_image = pygame.surfarray.make_surface(frame_flipped)
                    
                    with self.image_cache_lock:
                        self.image_cache = new_image
                        self.current_image = new_image
                        self.app_state['current_image'] = new_image
                    self.image_last_update_time = time.time()
            except Exception:
                pass
        
        self.image_thread = threading.Thread(target=update_image_thread, daemon=True)
        self.image_thread.start()
    
    def update_pointcloud_async(self):
        """Update point cloud display asynchronously with caching."""
        if self.current_drone_id is None:
            return
        
        drone_info = self.drones.get(self.current_drone_id)
        if not drone_info or not drone_info.get('client') or not drone_info.get('is_connected'):
            return
        
        client = drone_info['client']
        self.client = client
        self.is_connected = drone_info['is_connected']
        
        if self.pc_thread and self.pc_thread.is_alive():
            return
        
        def update_pc_thread():
            try:
                pc_data = client.get_latest_point_cloud()
                if pc_data:
                    points, timestamp = pc_data
                    with self.pc_cache_lock:
                        self.pc_cache = points
                        self.current_point_cloud = points
                    self.pc_render_cache_params = None
            except Exception as e:
                print(f"Point cloud update error: {e}")
        
        self.pc_thread = threading.Thread(target=update_pc_thread, daemon=True)
        self.pc_thread.start()
    
    def update_pointcloud_simple(self):
        """Update point cloud display with simple rendering."""
        # Check for rosbag point cloud first
        rosbag_pc = self.app_state.get('rosbag_pointcloud')
        if rosbag_pc is not None:
            with self.pc_cache_lock:
                self.current_point_cloud = rosbag_pc
        
        if self.current_point_cloud is None:
            return
        
        current_time = time.time()
        if current_time - self.pc_last_render_time >= self.pc_render_interval:
            cache_key = (self.pc_camera_angle_x, self.pc_camera_angle_y, self.pc_zoom)
            if self.pc_render_cache_params != cache_key or self.pc_render_cache is None:
                self.render_pointcloud_simple()
                self.pc_render_cache_params = cache_key
                self.pc_last_render_time = current_time
            else:
                with self.pc_cache_lock:
                    if self.pc_render_cache is not None:
                        self.app_state['pc_surface_simple'] = self.pc_render_cache
    
    def update_image_from_rosbag(self, rosbag_client):
        """Update image from rosbag client."""
        try:
            image_data = rosbag_client.get_latest_image()
            if image_data:
                frame, timestamp = image_data
                if frame is not None and HAS_CV2:
                    max_width, max_height = 800, 600
                    h, w = frame.shape[:2]
                    scale = min(max_width / w, max_height / h)
                    new_w, new_h = int(w * scale), int(h * scale)
                    frame_resized = cv2.resize(frame, (new_w, new_h))
                    frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
                    frame_rotated = np.rot90(frame_rgb, k=3)
                    frame_flipped = np.fliplr(frame_rotated)
                    new_image = pygame.surfarray.make_surface(frame_flipped)
                    
                    with self.image_cache_lock:
                        self.image_cache = new_image
                        self.current_image = new_image
                        self.app_state['current_image'] = new_image
        except Exception as e:
            pass
    
    def update_pointcloud_from_rosbag(self, rosbag_client):
        """Update point cloud from rosbag client."""
        try:
            pc_data = rosbag_client.get_latest_point_cloud()
            if pc_data:
                points, timestamp = pc_data
                if points is not None and len(points) > 0:
                    with self.pc_cache_lock:
                        self.pc_cache = points
                        self.current_point_cloud = points
                        self.app_state['rosbag_pointcloud'] = points
                    self.pc_render_cache_params = None  # Invalidate cache to trigger re-render
        except Exception as e:
            pass
    
    def render_pointcloud_simple(self):
        """Render point cloud using professional renderer."""
        if not HAS_POINTCLOUD or self.pc_renderer is None:
            return
        
        try:
            with self.pc_cache_lock:
                points = self.current_point_cloud
            if points is None:
                return
            
            self.pc_renderer.set_camera(self.pc_camera_angle_x, 
                                       self.pc_camera_angle_y, 
                                       self.pc_zoom)
            
            surface = self.pc_renderer.render(points)
            
            if surface is not None:
                with self.pc_cache_lock:
                    self.pc_render_cache = surface
                    self.app_state['pc_surface_simple'] = surface
        except Exception as e:
            print(f"Point cloud simple render error: {e}")
    
    def start_render_threads(self):
        """Start background render threads for smooth interaction."""
        def render_loop():
            while not self.stop_render_threads.is_set():
                try:
                    if HAS_POINTCLOUD and self.pc_renderer is not None:
                        with self.pc_cache_lock:
                            has_data = self.current_point_cloud is not None
                        if has_data:
                            current_time = time.time()
                            if current_time - self.pc_last_render_time >= self.pc_render_interval:
                                cache_key = (self.pc_camera_angle_x, self.pc_camera_angle_y, self.pc_zoom)
                                with self.pc_cache_lock:
                                    cache_valid = (self.pc_render_cache_params == cache_key and 
                                                 self.pc_render_cache is not None)
                                if not cache_valid:
                                    self.render_pointcloud_simple()
                                    with self.pc_cache_lock:
                                        self.pc_render_cache_params = cache_key
                                    self.pc_last_render_time = current_time
                except Exception as e:
                    print(f"Render thread error: {e}")
                time.sleep(0.01)
        
        self.render_thread = threading.Thread(target=render_loop, daemon=True)
        self.render_thread.start()
    
    def update_pointcloud_open3d_async(self):
        """Update point cloud using Open3D asynchronously."""
        if not HAS_OPEN3D or self.current_point_cloud is None:
            return
        self.render_pointcloud_open3d()
    
    def render_pointcloud_open3d(self):
        """Render point cloud using Open3D offscreen rendering with high-performance optimizations."""
        if not HAS_OPEN3D or self.current_point_cloud is None:
            return
        
        try:
            current_time = time.time()
            if current_time - self.o3d_last_update < self.o3d_update_interval:
                return
            
            with self.pc_cache_lock:
                points = self.current_point_cloud
            if points is None or len(points) == 0:
                return
            
            if not isinstance(points, np.ndarray):
                points = np.array(points, dtype=np.float32)
            
            # Adaptive point cloud sampling based on performance
            # Use voxel downsampling for better quality than uniform sampling
            max_points = 100000  # Increased for better quality
            original_count = len(points)
            
            if original_count > max_points:
                # Use voxel downsampling for better spatial distribution
                try:
                    # Calculate adaptive voxel size based on point cloud extent
                    if original_count > 0:
                        min_bound = np.min(points, axis=0)
                        max_bound = np.max(points, axis=0)
                        extent = np.max(max_bound - min_bound)
                        # Voxel size should be proportional to extent and target point count
                        voxel_size = extent / (max_points ** (1/3)) * 1.2
                        voxel_size = max(0.01, min(voxel_size, 1.0))  # Clamp to reasonable range
                        
                        # Create temporary point cloud for downsampling
                        temp_pcd = o3d.geometry.PointCloud()
                        temp_pcd.points = o3d.utility.Vector3dVector(points)
                        temp_pcd = temp_pcd.voxel_down_sample(voxel_size=voxel_size)
                        points = np.asarray(temp_pcd.points)
                except Exception:
                    # Fallback to uniform sampling if voxel downsampling fails
                    step = original_count // max_points
                    points = points[::step]
            
            # Reuse geometry if it exists, otherwise create new
            if self.o3d_geometry is None:
                self.o3d_geometry = o3d.geometry.PointCloud()
            
            # Only update if points changed significantly
            points_changed = True
            if hasattr(self, '_last_o3d_points_count'):
                if abs(len(points) - self._last_o3d_points_count) < len(points) * 0.01:
                    # Less than 1% change, might not need update
                    points_changed = False
            
            if points_changed or not hasattr(self, '_last_o3d_points_count'):
                self.o3d_geometry.points = o3d.utility.Vector3dVector(points)
                self._last_o3d_points_count = len(points)
            
            # Compute colors with optimized gradient
            if len(points) > 0:
                z_coords = points[:, 2]
                z_min, z_max = np.min(z_coords), np.max(z_coords)
                if z_max > z_min:
                    # Use height-based coloring with smooth gradient
                    z_normalized = (z_coords - z_min) / (z_max - z_min)
                    # Enhanced color mapping: blue (low) -> cyan -> white (high)
                    colors = np.zeros((len(points), 3), dtype=np.float32)
                    colors[:, 0] = z_normalized * 0.5 + 0.5  # R: 0.5 to 1.0
                    colors[:, 1] = z_normalized * 0.7 + 0.3  # G: 0.3 to 1.0
                    colors[:, 2] = z_normalized * 0.5 + 0.5  # B: 0.5 to 1.0
                    # Clamp to [0, 1]
                    colors = np.clip(colors, 0.0, 1.0)
                    self.o3d_geometry.colors = o3d.utility.Vector3dVector(colors)
                else:
                    self.o3d_geometry.paint_uniform_color([1.0, 1.0, 1.0])
            
            # Initialize Open3D visualizer with optimized settings
            if not self.o3d_window_created:
                self.o3d_vis = o3d.visualization.Visualizer()
                self.o3d_vis.create_window("3D Point Cloud View", 
                                        width=self.o3d_window_size[0], 
                                        height=self.o3d_window_size[1], 
                                        visible=False)
                self.o3d_vis.add_geometry(self.o3d_geometry)
                
                # Optimize render options for performance
                opt = self.o3d_vis.get_render_option()
                opt.background_color = np.array([0.0, 0.0, 0.0])
                opt.point_size = 1.5
                # Enable optimizations
                opt.show_coordinate_frame = False  # Disable for performance
                
                # Set initial view
                ctr = self.o3d_vis.get_view_control()
                ctr.set_zoom(0.7)
                
                self.o3d_window_created = True
                self.app_state['o3d_vis'] = self.o3d_vis
                self.app_state['o3d_geometry'] = self.o3d_geometry
            else:
                # Only update geometry if points changed
                if points_changed:
                    self.o3d_vis.update_geometry(self.o3d_geometry)
            
            # Poll events and update renderer
            self.o3d_vis.poll_events()
            self.o3d_vis.update_renderer()
            
            # Capture screen with optimized settings
            img = self.o3d_vis.capture_screen_float_buffer(do_render=True)
            img_array = np.asarray(img)
            img_array = (img_array * 255).astype(np.uint8)
            img_array = np.flipud(img_array)
            
            # Convert to pygame surface
            self.app_state['pc_surface_o3d'] = pygame.surfarray.make_surface(img_array.swapaxes(0, 1))
            self.o3d_last_update = current_time
            
        except Exception as e:
            print(f"Open3D render error: {e}")
            import traceback
            traceback.print_exc()
    
    def set_preset_command(self, command):
        """Set preset command."""
        if isinstance(command, dict):
            command = command.get('text', '')
            preset_commands = {
                'Takeoff': '{\n    "cmd": 1\n}',
                'Land': '{\n    "cmd": 2\n}',
                'Return': '{\n    "cmd": 3\n}',
                'Hover': '{\n    "cmd": 4\n}',
            }
            command = preset_commands.get(command, '')
        
        if not isinstance(command, str):
            command = str(command)
        
        self.components['json_editor'].text = command
        self.components['json_editor'].cursor_pos = [0, 0]
    
    def format_json(self):
        """Format JSON in editor."""
        self.components['json_editor'].format_json()
    
    def update_topic_list(self):
        """Update topic list from currently selected drone."""
        try:
            from rosclient.clients.config import DEFAULT_TOPICS
            topics = [(topic.name, topic.type) for topic in DEFAULT_TOPICS.values()]
            topic_list = self.components['topic_list']
            
            if self.current_drone_id is not None:
                drone_info = self.drones.get(self.current_drone_id)
                if drone_info and drone_info.get('client') and drone_info.get('is_connected'):
                    client = drone_info['client']
                    self.client = client
                    self.is_connected = drone_info['is_connected']
                    
                    if hasattr(client, '_ts_mgr') and client._ts_mgr:
                        if hasattr(client._ts_mgr, '_topics'):
                            for topic_name in client._ts_mgr._topics.keys():
                                if not any(t[0] == topic_name for t in topics):
                                    topics.append((topic_name, ""))
                            
                            # Set topic info for enhanced display
                            for topic_name, topic_data in client._ts_mgr._topics.items():
                                topic_info = {
                                    'subscribed': hasattr(topic_data, 'subscribed') and topic_data.subscribed,
                                    'active': True,  # Topic exists in manager
                                    'message_count': getattr(topic_data, 'message_count', 0),
                                }
                                topic_list.set_topic_info(topic_name, topic_info)
            
            topics = sorted(topics, key=lambda x: x[0])
            topic_list.set_items(topics)
        except Exception as e:
            self.components['topic_list'].set_items([])
    
    def send_control_command(self):
        """Send control command to currently selected drone."""
        if self.current_drone_id is None:
            self.add_log("Warning: No drone selected")
            return
        
        drone_info = self.drones.get(self.current_drone_id)
        if not drone_info or not drone_info.get('client') or not drone_info.get('is_connected'):
            self.add_log("Warning: Selected drone is not connected")
            return
        
        client = drone_info['client']
        self.client = client
        self.is_connected = drone_info['is_connected']
        
        try:
            topic = self.components['control_topic_input'].text.strip()
            topic_type = self.components['control_type_input'].text.strip()
            message_json = self.components['json_editor'].text
            
            message = json.loads(message_json)
            
            client.publish(topic, message, topic_type)
            
            cmd_str = f"{topic}: {message_json}"
            self.app_state['command_history'].append(cmd_str)
            if len(self.app_state['command_history']) > 50:
                self.app_state['command_history'].pop(0)
            
            self.add_log(f"Command sent to {topic}")
        except json.JSONDecodeError:
            self.add_log("Error: Invalid JSON format")
        except Exception as e:
            self.add_log(f"Error sending command: {e}")
    
    def test_connection(self):
        """Test network connection (legacy method)."""
        url = self.components['test_url_input'].text.strip()
        timeout_str = self.components.get('test_timeout_input', TextInput(0, 0, 100, 35, "5")).text.strip()
        
        try:
            timeout = float(timeout_str)
        except ValueError:
            timeout = 5.0
        
        def test_thread():
            try:
                self.app_state['test_results'].append(f"Testing connection to {url}...")
                client = RosClient(url)
                client.connect_async()
                time.sleep(timeout)
                
                if client.is_connected():
                    self.app_state['test_results'].append(f"✓ Connection successful to {url}")
                else:
                    self.app_state['test_results'].append(f"✗ Connection failed to {url}")
                client.terminate()
            except Exception as e:
                self.app_state['test_results'].append(f"✗ Error: {e}")
            
            if len(self.app_state['test_results']) > 50:
                self.app_state['test_results'].pop(0)
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def ping_test(self):
        """Ping test handler."""
        host = self.components['network_host_input'].text.strip()
        if not host:
            self.add_log("Error: Please enter a host to ping")
            return
        
        # Get network tab and call ping method
        if len(self.tab_instances) > 7 and self.tab_instances[7] is not None:
            network_tab = self.tab_instances[7]  # Network tab index
            if hasattr(network_tab, 'ping_test'):
                network_tab.ping_test(host)
            else:
                self.add_log("Network tab method not available")
        else:
            self.add_log("Network tab not initialized")
    
    def test_websocket(self):
        """WebSocket test handler."""
        host = self.components['network_host_input'].text.strip()
        if not host:
            self.add_log("Error: Please enter a host")
            return
        
        # Construct WebSocket URL if not already
        if not host.startswith(("ws://", "wss://")):
            url = f"ws://{host}"
        else:
            url = host
        
        if len(self.tab_instances) > 7 and self.tab_instances[7] is not None:
            network_tab = self.tab_instances[7]
            if hasattr(network_tab, 'test_websocket'):
                network_tab.test_websocket(url)
            else:
                self.add_log("Network tab method not available")
        else:
            self.add_log("Network tab not initialized")
    
    def test_ros_quick(self):
        """Quick ROS test handler."""
        host = self.components['network_host_input'].text.strip()
        if not host:
            self.add_log("Error: Please enter a host")
            return
        
        if not host.startswith(("ws://", "wss://")):
            url = f"ws://{host}:9090"
        else:
            url = host
        
        if len(self.tab_instances) > 7 and self.tab_instances[7] is not None:
            network_tab = self.tab_instances[7]
            if hasattr(network_tab, 'test_ros_connection'):
                network_tab.test_ros_connection(url)
            else:
                self.add_log("Network tab method not available")
        else:
            self.add_log("Network tab not initialized")
    
    def scan_ports(self):
        """Port scan handler."""
        host = self.components['scan_host_input'].text.strip()
        port_range_str = self.components['port_range_input'].text.strip()
        
        if not host:
            self.add_log("Error: Please enter a host")
            return
        
        # Parse port range
        ports = []
        try:
            for port_str in port_range_str.split(','):
                port_str = port_str.strip()
                if '-' in port_str:
                    start, end = map(int, port_str.split('-'))
                    ports.extend(range(start, end + 1))
                else:
                    ports.append(int(port_str))
        except ValueError:
            self.add_log("Error: Invalid port range format")
            return
        
        # Determine protocol
        protocol = "tcp"
        if self.components['udp_checkbox'].checked and not self.components['tcp_checkbox'].checked:
            protocol = "udp"
        
        if len(self.tab_instances) > 7 and self.tab_instances[7] is not None:
            network_tab = self.tab_instances[7]
            if hasattr(network_tab, 'port_scan'):
                network_tab.port_scan(host, ports, protocol)
            else:
                self.add_log("Network tab method not available")
        else:
            self.add_log("Network tab not initialized")
    
    def discover_devices(self):
        """Device discovery handler."""
        network = self.components['network_input'].text.strip()
        if not network:
            self.add_log("Error: Please enter a network range")
            return
        
        if len(self.tab_instances) > 7 and self.tab_instances[7] is not None:
            network_tab = self.tab_instances[7]
            if hasattr(network_tab, 'device_discovery'):
                network_tab.device_discovery(network)
            else:
                self.add_log("Network tab method not available")
        else:
            self.add_log("Network tab not initialized")
    
    def auto_detect_network(self):
        """Auto-detect local network."""
        if len(self.tab_instances) > 7 and self.tab_instances[7] is not None:
            network_tab = self.tab_instances[7]
            if hasattr(network_tab, 'get_local_network'):
                local_network = network_tab.get_local_network()
                self.components['ros_network_input'].text = local_network
                self.add_log(f"Auto-detected network: {local_network}")
            else:
                self.components['ros_network_input'].text = "192.168.1.0/24"
        else:
            self.components['ros_network_input'].text = "192.168.1.0/24"
    
    def discover_ros_devices(self):
        """ROS device discovery handler."""
        network = self.components['ros_network_input'].text.strip()
        if not network:
            self.add_log("Error: Please enter a network range")
            return
        
        if len(self.tab_instances) > 7 and self.tab_instances[7] is not None:
            network_tab = self.tab_instances[7]
            if hasattr(network_tab, 'discover_ros_devices'):
                network_tab.discover_ros_devices(network)
            else:
                self.add_log("Network tab method not available")
        else:
            self.add_log("Network tab not initialized")
    
    def test_all_ros_devices(self):
        """Test all discovered ROS devices."""
        if len(self.tab_instances) > 7 and self.tab_instances[7] is not None:
            network_tab = self.tab_instances[7]
            if hasattr(network_tab, 'test_all_ros_devices'):
                network_tab.test_all_ros_devices()
            else:
                self.add_log("Network tab method not available")
        else:
            self.add_log("Network tab not initialized")
    
    def test_ros_connection(self):
        """ROS connection test handler."""
        url = self.components['ros_url_input'].text.strip()
        if not url:
            self.add_log("Error: Please enter a ROS URL")
            return
        
        if len(self.tab_instances) > 7 and self.tab_instances[7] is not None:
            network_tab = self.tab_instances[7]
            if hasattr(network_tab, 'test_ros_connection'):
                network_tab.test_ros_connection(url)
            else:
                self.add_log("Network tab method not available")
        else:
            self.add_log("Network tab not initialized")
    
    def save_network_results(self):
        """Save network test results."""
        from tkinter import filedialog
        import tkinter as tk
        
        root = tk.Tk()
        root.withdraw()
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filepath:
            if len(self.tab_instances) > 7 and self.tab_instances[7] is not None:
                network_tab = self.tab_instances[7]
                if hasattr(network_tab, 'save_results'):
                    network_tab.save_results(filepath)
                else:
                    self.add_log("Network tab method not available")
            else:
                self.add_log("Network tab not initialized")
        
        root.destroy()
    
    def save_ros_devices(self):
        """Save discovered ROS devices."""
        from tkinter import filedialog
        import tkinter as tk
        
        root = tk.Tk()
        root.withdraw()
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save ROS Devices"
        )
        
        if filepath:
            if len(self.tab_instances) > 7 and self.tab_instances[7] is not None:
                network_tab = self.tab_instances[7]
                if hasattr(network_tab, 'save_ros_devices'):
                    network_tab.save_ros_devices(filepath)
                else:
                    self.add_log("Network tab method not available")
            else:
                self.add_log("Network tab not initialized")
        
        root.destroy()
    
    def handle_events(self):
        """Handle all pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Tab switching
            if event.type == pygame.MOUSEBUTTONDOWN:
                tab_height = 45
                tab_width = self.screen_width // len(self.tabs)
                if event.pos[1] < tab_height:
                    tab_index = event.pos[0] // tab_width
                    if 0 <= tab_index < len(self.tabs):
                        self.current_tab = tab_index
            
            # Update app state
            self.app_state['drones'] = self.drones
            self.app_state['current_drone_id'] = self.current_drone_id
            pc_camera = self.app_state.get('pc_camera', (0.0, 0.0, 1.0))
            self.app_state['pc_camera'] = (self.pc_camera_angle_x, self.pc_camera_angle_y, self.pc_zoom)
            
            # Handle tab-specific events
            if 0 <= self.current_tab < len(self.tab_instances):
                if self.tab_instances[self.current_tab].handle_event(event, self.app_state):
                    # Sync camera from app_state if updated
                    if 'pc_camera' in self.app_state:
                        pc_camera = self.app_state['pc_camera']
                        self.pc_camera_angle_x = pc_camera[0]
                        self.pc_camera_angle_y = pc_camera[1]
                        self.pc_zoom = pc_camera[2]
                        self.pc_render_cache_params = None
    
    def update(self):
        """Update game state."""
        self.dt = self.clock.tick(60) / 1000.0
        
        # Update app state
        self.app_state['drones'] = self.drones
        self.app_state['current_drone_id'] = self.current_drone_id
        self.app_state['pc_camera'] = (self.pc_camera_angle_x, self.pc_camera_angle_y, self.pc_zoom)
        
        # Update current tab
        if 0 <= self.current_tab < len(self.tab_instances):
            self.tab_instances[self.current_tab].update(self.dt, self.app_state)
    
    def draw(self):
        """Draw everything using optimized rendering system."""
        # Clear screen
        self.screen.fill(DesignSystem.COLORS['bg'])
        
        # Draw subtle grid pattern using renderer
        for y in range(0, self.screen_height, 60):
            pygame.draw.line(self.screen, DesignSystem.COLORS['bg_secondary'],
                           (0, y), (self.screen_width, y), 1)
        
        # Draw tab bar
        self.draw_tab_bar()
        
        # Update app state before drawing
        self.app_state['drones'] = self.drones
        self.app_state['current_drone_id'] = self.current_drone_id
        self.app_state['current_image'] = self.current_image
        
        # Draw current tab
        if 0 <= self.current_tab < len(self.tab_instances):
            self.tab_instances[self.current_tab].draw(self.app_state)
        
        # Update FPS counter
        self.optimizer.update_fps()
        
        # Use dirty regions for partial updates if needed
        # For now, we do full screen updates, but the infrastructure is ready
        pygame.display.flip()
        
        # Clear dirty regions after drawing
        self.optimizer.clear_dirty()
    
    def draw_tab_bar(self):
        """Draw tab bar using optimized renderer."""
        tab_height = 45
        tab_width = self.screen_width // len(self.tabs)
        
        for i, tab_name in enumerate(self.tabs):
            x = i * tab_width
            is_active = (i == self.current_tab)
            
            color = DesignSystem.COLORS['surface_active'] if is_active else DesignSystem.COLORS['surface']
            
            tab_rect = pygame.Rect(x, 0, tab_width, tab_height)
            self.renderer.draw_rect(self.screen, tab_rect, color)
            
            if not is_active:
                pygame.draw.line(self.screen, DesignSystem.COLORS['border'],
                               (x, tab_height - 1), (x + tab_width, tab_height - 1), 1)
            
            # Render text using optimized renderer
            text_width, text_height = self.renderer.measure_text(tab_name, 'label')
            text_x = x + tab_width // 2 - text_width // 2
            text_y = tab_height // 2 - text_height // 2
            self.renderer.render_text(self.screen, tab_name,
                                     (text_x, text_y),
                                     size='label',
                                     color=DesignSystem.COLORS['text'])
    
    def run(self):
        """Main game loop."""
        if 'connection_logs' not in self.app_state:
            self.app_state['connection_logs'] = []
        self.add_log("Waiting for connection...")
        
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
        
        # Cleanup
        self.stop_update.set()
        self.stop_render_threads.set()
        
        for drone_id, drone_info in self.drones.items():
            if drone_info.get('client'):
                try:
                    drone_info['client'].terminate()
                except:
                    pass
        
        if self.client:
            try:
                self.client.terminate()
            except:
                pass
        
        if HAS_OPEN3D and self.o3d_window_created and self.o3d_vis:
            try:
                self.o3d_vis.destroy_window()
            except:
                pass
        
        pygame.quit()


def main():
    """Main entry point."""
    app = RosClientPygameGUI()
    app.run()


if __name__ == "__main__":
    main()
