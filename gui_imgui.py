#!/usr/bin/env python
"""ImGui-based GUI for ROS Client using backend API."""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import json
import time
import threading
import base64
from typing import Optional, Dict, Any, List
from io import BytesIO

try:
    import imgui
    from imgui.integrations.glfw import GlfwRenderer
    import glfw
    import OpenGL.GL as gl
    HAS_IMGUI = True
except ImportError:
    HAS_IMGUI = False
    print("Warning: imgui, glfw, or OpenGL not available. Please install:")
    print("  pip install pyimgui[glfw] PyOpenGL")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("Warning: requests not available. Please install: pip install requests")

try:
    from PIL import Image
    import numpy as np
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Warning: PIL/numpy not available. Image display will be disabled.")

# Backend API configuration
BACKEND_URL = "http://127.0.0.1:8000"
API_BASE = f"{BACKEND_URL}/api"


class BackendClient:
    """Client for communicating with backend API."""
    
    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url
        self.session = requests.Session() if HAS_REQUESTS else None
        self.timeout = 5.0
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make HTTP request to backend."""
        if not self.session:
            return None
        
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API request error: {e}")
            return None
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get connection status."""
        return self._request("GET", "/status")
    
    def connect(self, url: str, use_mock: bool = False, mock_config: Optional[Dict] = None) -> bool:
        """Connect to ROS bridge."""
        data = {
            "url": url,
            "use_mock": use_mock,
            "mock_config": mock_config or {}
        }
        result = self._request("POST", "/connect", json=data)
        return result is not None
    
    def disconnect(self) -> bool:
        """Disconnect from ROS bridge."""
        result = self._request("POST", "/disconnect")
        return result is not None
    
    def get_image(self) -> Optional[Dict[str, Any]]:
        """Get latest image."""
        return self._request("GET", "/image")
    
    def fetch_image(self) -> Optional[Dict[str, Any]]:
        """Fetch image synchronously."""
        return self._request("GET", "/image/fetch")
    
    def get_pointcloud(self) -> Optional[Dict[str, Any]]:
        """Get latest point cloud."""
        return self._request("GET", "/pointcloud")
    
    def fetch_pointcloud(self) -> Optional[Dict[str, Any]]:
        """Fetch point cloud synchronously."""
        return self._request("GET", "/pointcloud/fetch")
    
    def publish(self, topic: str, topic_type: str, message: Dict[str, Any]) -> bool:
        """Publish message to topic."""
        data = {
            "topic": topic,
            "topic_type": topic_type,
            "message": message
        }
        result = self._request("POST", "/publish", json=data)
        return result is not None
    
    def start_recording(self, record_images: bool = True, record_pointclouds: bool = True,
                       record_states: bool = True, image_quality: int = 85) -> bool:
        """Start recording."""
        data = {
            "record_images": record_images,
            "record_pointclouds": record_pointclouds,
            "record_states": record_states,
            "image_quality": image_quality
        }
        result = self._request("POST", "/recording/start", json=data)
        return result is not None and result.get("success", False)
    
    def stop_recording(self) -> bool:
        """Stop recording."""
        result = self._request("POST", "/recording/stop")
        return result is not None and result.get("success", False)
    
    def get_recording_stats(self) -> Optional[Dict[str, Any]]:
        """Get recording statistics."""
        result = self._request("GET", "/recording/stats")
        return result.get("stats") if result else None
    
    def save_recording(self, file_path: str) -> bool:
        """Save recording to file."""
        data = {"file_path": file_path}
        result = self._request("POST", "/recording/save", json=data)
        return result is not None and result.get("success", False)
    
    def playback_control(self, action: str, file_path: Optional[str] = None) -> bool:
        """Control playback."""
        data = {"action": action}
        if file_path:
            data["file_path"] = file_path
        result = self._request("POST", "/playback/control", json=data)
        return result is not None and result.get("success", False)
    
    def get_playback_info(self) -> Optional[Dict[str, Any]]:
        """Get playback information."""
        return self._request("GET", "/playback/info")


class ImGuiROSClient:
    """ImGui-based ROS Client GUI."""
    
    def __init__(self):
        if not HAS_IMGUI:
            raise RuntimeError("ImGui dependencies not available")
        
        # Initialize GLFW
        if not glfw.init():
            raise RuntimeError("Failed to initialize GLFW")
        
        # Create window
        self.window = glfw.create_window(1400, 900, "ROS Client GUI - ImGui", None, None)
        if not self.window:
            glfw.terminate()
            raise RuntimeError("Failed to create window")
        
        glfw.make_context_current(self.window)
        glfw.swap_interval(1)  # Enable vsync
        
        # Initialize ImGui
        imgui.create_context()
        self.impl = GlfwRenderer(self.window)
        
        # Backend client
        self.backend = BackendClient()
        
        # Application state
        self.running = True
        self.current_tab = 0
        self.tabs = ["Connection", "Status", "Image", "Point Cloud", "Control", "Recording"]
        
        # Connection state
        self.connection_url = "ws://192.168.27.152:9090"
        self.use_mock = False
        self.is_connected = False
        self.status_data = {}
        
        # Image state
        self.current_image_texture = None
        self.image_width = 0
        self.image_height = 0
        self.image_info = "Waiting for image..."
        
        # Point cloud state
        self.pointcloud_data = None
        self.pointcloud_info = "Waiting for point cloud..."
        
        # Control state
        self.control_topic = "/control"
        self.control_type = "controller_msgs/cmd"
        self.control_message = '{\n    "cmd": 1\n}'
        self.command_history = []
        
        # Recording state
        self.recording_stats = {}
        self.auto_refresh = True
        self.auto_update_image = True
        self.auto_update_pc = True
        
        # Update thread
        self.update_thread = None
        self.stop_update = threading.Event()
        self.start_update_thread()
    
    def start_update_thread(self):
        """Start background update thread."""
        def update_loop():
            while not self.stop_update.is_set():
                try:
                    if self.is_connected:
                        # Update status
                        if self.auto_refresh:
                            status = self.backend.get_status()
                            if status:
                                self.status_data = status.get("state", {})
                                self.is_connected = status.get("connected", False)
                        
                        # Update image
                        if self.auto_update_image:
                            self.update_image()
                        
                        # Update point cloud
                        if self.auto_update_pc:
                            self.update_pointcloud()
                        
                        # Update recording stats
                        if hasattr(self, 'recording_active') and self.recording_active:
                            stats = self.backend.get_recording_stats()
                            if stats:
                                self.recording_stats = stats
                
                except Exception as e:
                    print(f"Update error: {e}")
                
                time.sleep(1.0)  # Update every second
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
    
    def update_image(self):
        """Update image from backend."""
        try:
            image_data = self.backend.get_image()
            if image_data and "image" in image_data:
                self.load_image_from_base64(image_data["image"])
                self.image_info = f"Size: {image_data.get('width', 0)}x{image_data.get('height', 0)}, Time: {image_data.get('timestamp', 0):.3f}"
        except Exception:
            pass
    
    def update_pointcloud(self):
        """Update point cloud from backend."""
        try:
            pc_data = self.backend.get_pointcloud()
            if pc_data and "points" in pc_data:
                self.pointcloud_data = pc_data
                self.pointcloud_info = f"Points: {pc_data.get('count', 0)}, Time: {pc_data.get('timestamp', 0):.3f}"
        except Exception:
            pass
    
    def load_image_from_base64(self, image_base64: str):
        """Load image from base64 string."""
        if not HAS_PIL:
            return
        
        try:
            # Decode base64
            image_data = base64.b64decode(image_base64)
            image = Image.open(BytesIO(image_data))
            
            # Convert to RGBA
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Convert to numpy array
            img_array = np.array(image)
            
            # Create OpenGL texture
            if self.current_image_texture is None:
                self.current_image_texture = gl.glGenTextures(1)
            
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.current_image_texture)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, image.width, image.height,
                           0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img_array)
            
            self.image_width = image.width
            self.image_height = image.height
        except Exception as e:
            print(f"Error loading image: {e}")
    
    def render_connection_tab(self):
        """Render connection tab."""
        imgui.begin_child("Connection Settings", 0, -100, border=True)
        
        imgui.text("WebSocket URL:")
        _, self.connection_url = imgui.input_text("##url", self.connection_url, 256)
        
        imgui.spacing()
        _, self.use_mock = imgui.checkbox("Use Mock Client (Test Mode)", self.use_mock)
        
        imgui.spacing()
        imgui.separator()
        imgui.spacing()
        
        if imgui.button("Connect", 150, 30):
            self.backend.connect(self.connection_url, self.use_mock)
            time.sleep(0.5)  # Give backend time to connect
            status = self.backend.get_status()
            if status:
                self.is_connected = status.get("connected", False)
        
        imgui.same_line()
        
        if imgui.button("Disconnect", 150, 30):
            self.backend.disconnect()
            self.is_connected = False
        
        imgui.spacing()
        
        # Connection status
        if self.is_connected:
            imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0, 1.0)
            imgui.text("Status: Connected")
            imgui.pop_style_color()
        else:
            imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 0.0, 0.0, 1.0)
            imgui.text("Status: Disconnected")
            imgui.pop_style_color()
        
        imgui.end_child()
        
        # Connection log
        imgui.begin_child("Connection Log", 0, 0, border=True)
        imgui.text("Connection log will appear here...")
        imgui.end_child()
    
    def render_status_tab(self):
        """Render status tab."""
        imgui.begin_child("Status Display", 0, -50, border=True)
        
        if self.status_data:
            imgui.columns(3, "StatusColumns", True)
            
            imgui.text("Connection:")
            imgui.next_column()
            connected = self.status_data.get("connected", False)
            if connected:
                imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0, 1.0)
                imgui.text("Connected")
                imgui.pop_style_color()
            else:
                imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 0.0, 0.0, 1.0)
                imgui.text("Disconnected")
                imgui.pop_style_color()
            imgui.next_column()
            imgui.next_column()
            
            imgui.separator()
            
            fields = [
                ("Armed", "armed", bool),
                ("Mode", "mode", str),
                ("Battery", "battery", float),
                ("Latitude", "latitude", float),
                ("Longitude", "longitude", float),
                ("Altitude", "altitude", float),
                ("Roll", "roll", float),
                ("Pitch", "pitch", float),
                ("Yaw", "yaw", float),
                ("Landed", "landed", bool),
            ]
            
            for label, key, value_type in fields:
                imgui.text(f"{label}:")
                imgui.next_column()
                
                value = self.status_data.get(key, None)
                if value is not None:
                    if value_type == bool:
                        imgui.text("Yes" if value else "No")
                    elif value_type == float:
                        imgui.text(f"{value:.6f}" if "lat" in key or "lon" in key else f"{value:.2f}")
                    else:
                        imgui.text(str(value))
                else:
                    imgui.text("N/A")
                
                imgui.next_column()
                imgui.next_column()
                imgui.separator()
            
            imgui.columns(1)
        else:
            imgui.text("No status data available. Please connect first.")
        
        imgui.end_child()
        
        imgui.spacing()
        _, self.auto_refresh = imgui.checkbox("Auto Refresh (1s)", self.auto_refresh)
        
        if imgui.button("Refresh Status", 150, 30):
            status = self.backend.get_status()
            if status:
                self.status_data = status.get("state", {})
                self.is_connected = status.get("connected", False)
    
    def render_image_tab(self):
        """Render image tab."""
        imgui.begin_child("Image Display", 0, -50, border=True)
        
        if self.current_image_texture and self.image_width > 0 and self.image_height > 0:
            # Calculate display size
            avail_width = imgui.get_content_region_available_width()
            avail_height = imgui.get_content_region_available_height() - 100
            
            # Maintain aspect ratio
            aspect = self.image_width / self.image_height
            if avail_width / aspect <= avail_height:
                display_width = avail_width
                display_height = avail_width / aspect
            else:
                display_height = avail_height
                display_width = avail_height * aspect
            
            imgui.image(self.current_image_texture, display_width, display_height)
        else:
            imgui.text("Waiting for image data...")
        
        imgui.end_child()
        
        imgui.spacing()
        _, self.auto_update_image = imgui.checkbox("Auto Update", self.auto_update_image)
        
        imgui.same_line()
        if imgui.button("Fetch Manual", 150, 30):
            image_data = self.backend.fetch_image()
            if image_data and "image" in image_data:
                self.load_image_from_base64(image_data["image"])
                self.image_info = f"Size: {image_data.get('width', 0)}x{image_data.get('height', 0)}"
        
        imgui.same_line()
        imgui.text(self.image_info)
    
    def render_pointcloud_tab(self):
        """Render point cloud tab."""
        imgui.begin_child("Point Cloud Display", 0, -50, border=True)
        
        if self.pointcloud_data and "points" in self.pointcloud_data:
            points = self.pointcloud_data["points"]
            imgui.text(f"Point Cloud Data: {len(points)} points")
            imgui.text("(3D visualization would be rendered here)")
            # Note: Full 3D rendering would require additional OpenGL setup
        else:
            imgui.text("Waiting for point cloud data...")
        
        imgui.end_child()
        
        imgui.spacing()
        _, self.auto_update_pc = imgui.checkbox("Auto Update", self.auto_update_pc)
        
        imgui.same_line()
        if imgui.button("Fetch Manual", 150, 30):
            pc_data = self.backend.fetch_pointcloud()
            if pc_data:
                self.pointcloud_data = pc_data
                self.pointcloud_info = f"Points: {pc_data.get('count', 0)}"
        
        imgui.same_line()
        imgui.text(self.pointcloud_info)
    
    def render_control_tab(self):
        """Render control tab."""
        imgui.begin_child("Control Settings", 0, -200, border=True)
        
        imgui.text("Topic Name:")
        _, self.control_topic = imgui.input_text("##topic", self.control_topic, 256)
        
        imgui.spacing()
        imgui.text("Topic Type:")
        _, self.control_type = imgui.input_text("##type", self.control_type, 256)
        
        imgui.spacing()
        imgui.separator()
        imgui.spacing()
        
        # Preset commands
        if imgui.button("Takeoff", 100, 30):
            self.control_message = '{\n    "cmd": 1\n}'
        
        imgui.same_line()
        if imgui.button("Land", 100, 30):
            self.control_message = '{\n    "cmd": 2\n}'
        
        imgui.same_line()
        if imgui.button("Return", 100, 30):
            self.control_message = '{\n    "cmd": 3\n}'
        
        imgui.same_line()
        if imgui.button("Hover", 100, 30):
            self.control_message = '{\n    "cmd": 4\n}'
        
        imgui.spacing()
        imgui.separator()
        imgui.spacing()
        
        imgui.text("Message Content (JSON):")
        imgui.spacing()
        
        # Text input for JSON message
        _, self.control_message = imgui.input_text_multiline(
            "##message", self.control_message, 4096, -50, imgui.INPUT_TEXT_ALLOW_TAB_INPUT
        )
        
        imgui.end_child()
        
        imgui.spacing()
        if imgui.button("Send Command", 200, 40):
            try:
                message = json.loads(self.control_message)
                success = self.backend.publish(self.control_topic, self.control_type, message)
                if success:
                    self.command_history.append(f"[{time.strftime('%H:%M:%S')}] {self.control_topic}: {self.control_message[:50]}...")
            except json.JSONDecodeError as e:
                print(f"JSON error: {e}")
        
        imgui.spacing()
        imgui.begin_child("Command History", 0, 0, border=True)
        for entry in self.command_history[-20:]:  # Show last 20 entries
            imgui.text(entry)
        imgui.end_child()
    
    def render_recording_tab(self):
        """Render recording tab."""
        imgui.begin_child("Recording Control", 0, -200, border=True)
        
        if imgui.button("Start Recording", 150, 30):
            self.backend.start_recording()
            self.recording_active = True
        
        imgui.same_line()
        if imgui.button("Stop Recording", 150, 30):
            self.backend.stop_recording()
            self.recording_active = False
        
        imgui.same_line()
        if imgui.button("Save Recording", 150, 30):
            # Note: File dialog would need additional implementation
            print("Save recording - file dialog not implemented")
        
        imgui.spacing()
        imgui.separator()
        imgui.spacing()
        
        # Recording statistics
        if self.recording_stats:
            imgui.text("Recording Statistics:")
            imgui.spacing()
            for key, value in self.recording_stats.items():
                imgui.text(f"{key}: {value}")
        else:
            imgui.text("No recording statistics available")
        
        imgui.end_child()
        
        # Playback controls (Mock Client only)
        imgui.begin_child("Playback Control", 0, 0, border=True)
        imgui.text("Playback Control (Mock Client Only)")
        imgui.spacing()
        
        if imgui.button("Play", 100, 30):
            self.backend.playback_control("play")
        
        imgui.same_line()
        if imgui.button("Pause", 100, 30):
            self.backend.playback_control("pause")
        
        imgui.same_line()
        if imgui.button("Stop", 100, 30):
            self.backend.playback_control("stop")
        
        playback_info = self.backend.get_playback_info()
        if playback_info:
            imgui.spacing()
            imgui.text(f"Progress: {playback_info.get('progress', 0) * 100:.1f}%")
            imgui.text(f"Time: {playback_info.get('current_time', 0):.1f}s")
        
        imgui.end_child()
    
    def render(self):
        """Render main window."""
        imgui.new_frame()
        
        # Main menu bar
        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File", True):
                if imgui.menu_item("Exit", "Ctrl+Q")[0]:
                    self.running = False
                imgui.end_menu()
            imgui.end_main_menu_bar()
        
        # Main window
        imgui.begin("ROS Client GUI", True)
        
        # Tab bar
        for i, tab_name in enumerate(self.tabs):
            if imgui.selectable(tab_name, self.current_tab == i)[0]:
                self.current_tab = i
        
        imgui.separator()
        imgui.spacing()
        
        # Render current tab
        if self.current_tab == 0:
            self.render_connection_tab()
        elif self.current_tab == 1:
            self.render_status_tab()
        elif self.current_tab == 2:
            self.render_image_tab()
        elif self.current_tab == 3:
            self.render_pointcloud_tab()
        elif self.current_tab == 4:
            self.render_control_tab()
        elif self.current_tab == 5:
            self.render_recording_tab()
        
        imgui.end()
        
        imgui.render()
        self.impl.render(imgui.get_draw_data())
    
    def run(self):
        """Run the application."""
        while not glfw.window_should_close(self.window) and self.running:
            glfw.poll_events()
            self.impl.process_inputs()
            
            gl.glClearColor(0.1, 0.1, 0.1, 1.0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            
            self.render()
            
            glfw.swap_buffers(self.window)
        
        self.cleanup()
    
    def cleanup(self):
        """Cleanup resources."""
        self.stop_update.set()
        if self.update_thread:
            self.update_thread.join(timeout=1.0)
        
        self.impl.shutdown()
        glfw.terminate()


def main():
    """Main entry point."""
    if not HAS_IMGUI:
        print("Error: ImGui dependencies not available")
        print("Please install: pip install pyimgui[glfw] PyOpenGL")
        return
    
    if not HAS_REQUESTS:
        print("Error: requests library not available")
        print("Please install: pip install requests")
        return
    
    try:
        app = ImGuiROSClient()
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

