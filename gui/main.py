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
        self.components['topic_list'] = TopicList(50, 100, 300, 500)
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
        
        # Network test components
        self.components['test_url_input'] = TextInput(200, 100, 400, 35, "ws://localhost:9090")
        self.components['test_timeout_input'] = TextInput(200, 150, 100, 35, "5")
        self.components['test_btn'] = Button(200, 200, None, 40, "Test Connection", self.test_connection)
        
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
        """Render point cloud using Open3D offscreen rendering."""
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
            
            max_points = 50000
            if len(points) > max_points:
                step = len(points) // max_points
                points = points[::step]
            
            if self.o3d_geometry is None:
                self.o3d_geometry = o3d.geometry.PointCloud()
            
            self.o3d_geometry.points = o3d.utility.Vector3dVector(points)
            
            if len(points) > 0:
                z_coords = points[:, 2]
                z_min, z_max = np.min(z_coords), np.max(z_coords)
                if z_max > z_min:
                    z_normalized = (z_coords - z_min) / (z_max - z_min)
                    colors = np.zeros((len(points), 3))
                    colors[:, 0] = z_normalized
                    colors[:, 1] = z_normalized
                    colors[:, 2] = z_normalized
                    self.o3d_geometry.colors = o3d.utility.Vector3dVector(colors)
                else:
                    self.o3d_geometry.paint_uniform_color([1.0, 1.0, 1.0])
            
            if not self.o3d_window_created:
                self.o3d_vis = o3d.visualization.Visualizer()
                self.o3d_vis.create_window("3D Point Cloud View", 
                                        width=self.o3d_window_size[0], 
                                        height=self.o3d_window_size[1], 
                                        visible=False)
                self.o3d_vis.add_geometry(self.o3d_geometry)
                
                opt = self.o3d_vis.get_render_option()
                opt.background_color = np.array([0.0, 0.0, 0.0])
                opt.point_size = 1.5
                
                ctr = self.o3d_vis.get_view_control()
                ctr.set_zoom(0.7)
                
                self.o3d_window_created = True
            else:
                self.o3d_vis.update_geometry(self.o3d_geometry)
            
            self.o3d_vis.poll_events()
            self.o3d_vis.update_renderer()
            
            img = self.o3d_vis.capture_screen_float_buffer(do_render=True)
            img_array = np.asarray(img)
            img_array = (img_array * 255).astype(np.uint8)
            img_array = np.flipud(img_array)
            
            self.app_state['pc_surface_o3d'] = pygame.surfarray.make_surface(img_array.swapaxes(0, 1))
            self.o3d_last_update = current_time
            
        except Exception as e:
            print(f"Open3D render error: {e}")
    
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
            
            topics = sorted(topics, key=lambda x: x[0])
            self.components['topic_list'].set_items(topics)
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
        """Test network connection."""
        url = self.components['test_url_input'].text.strip()
        timeout_str = self.components['test_timeout_input'].text.strip()
        
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
