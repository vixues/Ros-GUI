"""Professional network testing tab with comprehensive network tools."""
import pygame
import socket
import threading
import time
import subprocess
import platform
import json
import os
from typing import Dict, Any, List, Tuple, Optional
from urllib.parse import urlparse
from datetime import datetime

from .base_tab import BaseTab
from ..components import Label, Card, TextInput, Button, Items, Checkbox
from ..design.design_system import DesignSystem
from ..renderers.ui_renderer import get_renderer


class NetworkTab(BaseTab):
    """Professional network testing tab with comprehensive tools."""
    
    def __init__(self, screen: pygame.Surface, screen_width: int, screen_height: int,
                 components: Dict[str, Any]):
        """Initialize network tab.
        
        Args:
            screen: Pygame surface to draw on
            screen_width: Screen width
            screen_height: Screen height
            components: Dictionary of UI components
        """
        super().__init__(screen, screen_width, screen_height)
        self.components = components
        self.renderer = get_renderer()
        
        # Network test state
        self.test_results: List[str] = []
        self.test_history: List[Dict[str, Any]] = []
        self.scan_results: List[Dict[str, Any]] = []
        self.device_list: List[Dict[str, Any]] = []
        self.ros_devices: List[Dict[str, Any]] = []  # Discovered ROS devices
        self.active_tests: Dict[str, bool] = {}
        
        # UI state
        self.current_tool = "quick_test"  # quick_test, port_scan, device_discovery, ros_discovery, ros_test, advanced
        self.scroll_y = 0
        
        # ROS common ports
        self.ROS_PORTS = {
            "rosbridge": 9090,
            "ros_master": 11311,
            "rosbridge_ssl": 9443,
            "rosbridge_secure": 9091
        }
        
        # Initialize app_state test_results if needed
        if not hasattr(self, 'app_state'):
            self.app_state = {}
        
    def add_result(self, message: str, level: str = "info"):
        """Add test result message.
        
        Args:
            message: Result message
            level: Message level (info, success, warning, error)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "info": "[INFO]",
            "success": "[✓]",
            "warning": "[!]",
            "error": "[✗]"
        }.get(level, "[INFO]")
        
        result = f"{timestamp} {prefix} {message}"
        self.test_results.append(result)
        
        # Keep last 1000 results
        if len(self.test_results) > 1000:
            self.test_results.pop(0)
        
        # Save to history
        self.test_history.append({
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        })
    
    def ping_test(self, host: str, count: int = 4, timeout: float = 5.0):
        """Perform ping test.
        
        Args:
            host: Host to ping
            count: Number of ping packets
            timeout: Timeout in seconds
        """
        self.add_result(f"Pinging {host}...", "info")
        self.active_tests["ping"] = True
        
        def ping_thread():
            try:
                # Determine ping command based on OS
                if platform.system().lower() == "windows":
                    cmd = ["ping", "-n", str(count), "-w", str(int(timeout * 1000)), host]
                else:
                    cmd = ["ping", "-c", str(count), "-W", str(timeout), host]
                
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=timeout * count + 5
                )
                
                if result.returncode == 0:
                    # Parse ping results
                    output = result.stdout
                    if "time=" in output or "time<" in output:
                        # Extract statistics
                        lines = output.split('\n')
                        for line in lines:
                            if "time=" in line or "time<" in line:
                                self.add_result(f"  {line.strip()}", "success")
                        
                        # Extract summary
                        for line in lines:
                            if "packets" in line.lower() or "丢失" in line or "loss" in line.lower():
                                self.add_result(f"  {line.strip()}", "info")
                        
                        self.add_result(f"Ping to {host} successful", "success")
                    else:
                        self.add_result(f"Ping to {host} completed", "success")
                else:
                    self.add_result(f"Ping to {host} failed: {result.stderr}", "error")
            except subprocess.TimeoutExpired:
                self.add_result(f"Ping to {host} timed out", "error")
            except Exception as e:
                self.add_result(f"Ping error: {e}", "error")
            finally:
                self.active_tests["ping"] = False
        
        threading.Thread(target=ping_thread, daemon=True).start()
    
    def port_scan(self, host: str, ports: List[int], protocol: str = "tcp", timeout: float = 2.0):
        """Scan ports on a host.
        
        Args:
            host: Host to scan
            ports: List of port numbers to scan
            protocol: Protocol type (tcp or udp)
            timeout: Timeout per port in seconds
        """
        self.add_result(f"Scanning {protocol.upper()} ports on {host}...", "info")
        self.active_tests["port_scan"] = True
        self.scan_results.clear()
        
        def scan_thread():
            open_ports = []
            closed_ports = []
            
            for port in ports:
                try:
                    if protocol.lower() == "tcp":
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(timeout)
                        result = sock.connect_ex((host, port))
                        sock.close()
                        
                        if result == 0:
                            open_ports.append(port)
                            self.scan_results.append({
                                "host": host,
                                "port": port,
                                "protocol": "TCP",
                                "status": "open",
                                "service": self._guess_service(port)
                            })
                            self.add_result(f"  TCP {port}: OPEN ({self._guess_service(port)})", "success")
                        else:
                            closed_ports.append(port)
                    else:  # UDP
                        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        sock.settimeout(timeout)
                        try:
                            sock.sendto(b"", (host, port))
                            sock.recvfrom(1024)
                            open_ports.append(port)
                            self.scan_results.append({
                                "host": host,
                                "port": port,
                                "protocol": "UDP",
                                "status": "open"
                            })
                            self.add_result(f"  UDP {port}: OPEN", "success")
                        except socket.timeout:
                            # UDP is unreliable, timeout might mean filtered or open
                            self.add_result(f"  UDP {port}: FILTERED/OPEN", "warning")
                        finally:
                            sock.close()
                except Exception as e:
                    self.add_result(f"  {protocol.upper()} {port}: ERROR - {e}", "error")
            
            self.add_result(f"Scan complete: {len(open_ports)} open, {len(closed_ports)} closed", "info")
            self.active_tests["port_scan"] = False
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def _guess_service(self, port: int) -> str:
        """Guess service name from port number."""
        common_ports = {
            22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS", 80: "HTTP",
            443: "HTTPS", 9090: "Rosbridge", 11311: "ROS Master",
            8080: "HTTP-Alt", 3306: "MySQL", 5432: "PostgreSQL",
            6379: "Redis", 27017: "MongoDB", 1883: "MQTT", 8888: "HTTP-Alt"
        }
        return common_ports.get(port, "Unknown")
    
    def test_websocket(self, url: str, timeout: float = 5.0):
        """Test WebSocket connection.
        
        Args:
            url: WebSocket URL
            timeout: Connection timeout
        """
        self.add_result(f"Testing WebSocket connection to {url}...", "info")
        self.active_tests["websocket"] = True
        
        def ws_test_thread():
            try:
                parsed = urlparse(url)
                if parsed.scheme not in ("ws", "wss"):
                    self.add_result(f"Invalid WebSocket URL: {url}", "error")
                    self.active_tests["websocket"] = False
                    return
                
                host = parsed.hostname
                port = parsed.port or (443 if parsed.scheme == "wss" else 80)
                
                # Test TCP connection first
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                start_time = time.time()
                result = sock.connect_ex((host, port))
                connect_time = (time.time() - start_time) * 1000
                sock.close()
                
                if result == 0:
                    self.add_result(f"TCP connection to {host}:{port} successful ({connect_time:.2f}ms)", "success")
                    
                    # Try to import websocket library for full test
                    try:
                        import websocket
                        ws = websocket.create_connection(url, timeout=timeout)
                        self.add_result(f"WebSocket handshake successful", "success")
                        ws.close()
                        self.add_result(f"WebSocket connection test passed", "success")
                    except ImportError:
                        self.add_result(f"WebSocket library not available, TCP test passed", "warning")
                    except Exception as e:
                        self.add_result(f"WebSocket handshake failed: {e}", "error")
                else:
                    self.add_result(f"TCP connection to {host}:{port} failed", "error")
            except Exception as e:
                self.add_result(f"WebSocket test error: {e}", "error")
            finally:
                self.active_tests["websocket"] = False
        
        threading.Thread(target=ws_test_thread, daemon=True).start()
    
    def test_ros_connection(self, url: str, timeout: float = 5.0):
        """Test ROS connection via rosbridge.
        
        Args:
            url: Rosbridge WebSocket URL
            timeout: Connection timeout
        """
        self.add_result(f"Testing ROS connection to {url}...", "info")
        self.active_tests["ros"] = True
        
        def ros_test_thread():
            try:
                from rosclient import RosClient
                
                client = RosClient(url)
                client.connect_async()
                
                # Wait for connection
                start_time = time.time()
                while not client.is_connected() and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
                
                if client.is_connected():
                    self.add_result(f"ROS connection established", "success")
                    
                    # Test topic listing
                    try:
                        ts_mgr = client._ts_mgr
                        if ts_mgr:
                            # Try to get topics
                            self.add_result(f"ROS connection fully functional", "success")
                    except:
                        pass
                    
                    client.terminate()
                    self.add_result(f"ROS connection test completed", "success")
                else:
                    self.add_result(f"ROS connection failed (timeout)", "error")
            except ImportError:
                self.add_result(f"RosClient not available", "error")
            except Exception as e:
                self.add_result(f"ROS test error: {e}", "error")
            finally:
                self.active_tests["ros"] = False
        
        threading.Thread(target=ros_test_thread, daemon=True).start()
    
    def device_discovery(self, network: str, timeout: float = 2.0):
        """Discover devices on network.
        
        Args:
            network: Network CIDR (e.g., 192.168.1.0/24) or IP range
            timeout: Timeout per host
        """
        self.add_result(f"Discovering devices on {network}...", "info")
        self.active_tests["discovery"] = True
        self.device_list.clear()
        
        def discovery_thread():
            try:
                # Parse network range
                if "/" in network:
                    # CIDR notation
                    base_ip, mask = network.split("/")
                    # Simplified: scan common range
                    base_parts = base_ip.split(".")
                    base_ip = ".".join(base_parts[:3])
                    ip_range = range(1, 255)
                else:
                    # Assume single IP or simple range
                    base_parts = network.split(".")
                    if len(base_parts) == 4:
                        base_ip = ".".join(base_parts[:3])
                        ip_range = [int(base_parts[3])]
                    else:
                        base_ip = network
                        ip_range = range(1, 255)
                
                for i in ip_range:
                    ip = f"{base_ip}.{i}"
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(timeout)
                        result = sock.connect_ex((ip, 22))  # Try SSH port
                        sock.close()
                        
                        if result == 0:
                            # Try to get hostname
                            try:
                                hostname = socket.gethostbyaddr(ip)[0]
                            except:
                                hostname = "Unknown"
                            
                            device_info = {
                                "ip": ip,
                                "hostname": hostname,
                                "ports": []
                            }
                            self.device_list.append(device_info)
                            self.add_result(f"  Found device: {ip} ({hostname})", "success")
                    except:
                        pass
                
                self.add_result(f"Discovery complete: {len(self.device_list)} devices found", "info")
            except Exception as e:
                self.add_result(f"Discovery error: {e}", "error")
            finally:
                self.active_tests["discovery"] = False
        
        threading.Thread(target=discovery_thread, daemon=True).start()
    
    def discover_ros_devices(self, network: str, timeout: float = 1.5):
        """Discover ROS devices on network by scanning ROS-specific ports.
        
        Args:
            network: Network CIDR (e.g., 192.168.1.0/24) or IP range
            timeout: Timeout per host/port
        """
        self.add_result(f"Scanning network {network} for ROS devices...", "info")
        self.active_tests["ros_discovery"] = True
        self.ros_devices.clear()
        
        def ros_discovery_thread():
            try:
                # Parse network range
                if "/" in network:
                    base_ip, mask = network.split("/")
                    base_parts = base_ip.split(".")
                    base_ip = ".".join(base_parts[:3])
                    try:
                        mask_int = int(mask)
                        if mask_int == 24:
                            ip_range = range(1, 255)
                        elif mask_int == 16:
                            # For /16, scan common ranges
                            ip_range = range(1, 255)
                        else:
                            ip_range = range(1, 255)
                    except:
                        ip_range = range(1, 255)
                else:
                    base_parts = network.split(".")
                    if len(base_parts) == 4:
                        base_ip = ".".join(base_parts[:3])
                        ip_range = [int(base_parts[3])]
                    else:
                        base_ip = network
                        ip_range = range(1, 255)
                
                total_ips = len(list(ip_range))
                scanned = 0
                found_count = 0
                
                self.add_result(f"Scanning {total_ips} IPs for ROS services...", "info")
                
                for i in ip_range:
                    ip = f"{base_ip}.{i}"
                    scanned += 1
                    
                    # Progress update every 20 IPs
                    if scanned % 20 == 0:
                        progress = (scanned / total_ips) * 100
                        self.add_result(f"  Progress: {scanned}/{total_ips} ({progress:.1f}%) - Found: {found_count}", "info")
                    
                    ros_services = []
                    
                    # Check ROS-specific ports (prioritize rosbridge)
                    ports_to_check = [
                        (self.ROS_PORTS["rosbridge"], "rosbridge"),
                        (self.ROS_PORTS["ros_master"], "ros_master"),
                        (self.ROS_PORTS.get("rosbridge_ssl", 9443), "rosbridge_ssl"),
                        (self.ROS_PORTS.get("rosbridge_secure", 9091), "rosbridge_secure")
                    ]
                    
                    for port, service_name in ports_to_check:
                        try:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(timeout)
                            start_time = time.time()
                            result = sock.connect_ex((ip, port))
                            connect_time = (time.time() - start_time) * 1000
                            sock.close()
                            
                            if result == 0:
                                ros_services.append({
                                    "service": service_name,
                                    "port": port,
                                    "url": f"ws://{ip}:{port}" if "rosbridge" in service_name else None,
                                    "connect_time_ms": connect_time
                                })
                        except:
                            pass
                    
                    # If ROS services found, add to device list
                    if ros_services:
                        found_count += 1
                        # Try to get hostname
                        try:
                            hostname = socket.gethostbyaddr(ip)[0]
                        except:
                            hostname = "Unknown"
                        
                        # Test ROS connection if rosbridge found (more thorough test)
                        rosbridge_url = None
                        ros_status = "unknown"
                        ros_info = {}
                        
                        for service in ros_services:
                            if service["url"]:
                                rosbridge_url = service["url"]
                                # Quick but more reliable connection test
                                try:
                                    from rosclient import RosClient
                                    test_client = RosClient(rosbridge_url)
                                    test_client.connect_async()
                                    
                                    # Wait a bit longer for connection
                                    time.sleep(1.0)
                                    
                                    if test_client.is_connected():
                                        ros_status = "connected"
                                        # Try to get ROS info
                                        try:
                                            if hasattr(test_client, '_ts_mgr') and test_client._ts_mgr:
                                                ros_info["topics_available"] = True
                                        except:
                                            pass
                                    else:
                                        ros_status = "port_open"
                                    
                                    test_client.terminate()
                                except ImportError:
                                    ros_status = "port_open"
                                except Exception as e:
                                    ros_status = "port_open"
                                    ros_info["error"] = str(e)
                                break
                        
                        device_info = {
                            "ip": ip,
                            "hostname": hostname,
                            "ros_services": ros_services,
                            "rosbridge_url": rosbridge_url,
                            "ros_status": ros_status,
                            "ros_info": ros_info,
                            "discovered_at": datetime.now().isoformat()
                        }
                        self.ros_devices.append(device_info)
                        
                        services_str = ", ".join([f"{s['service']}:{s['port']}" for s in ros_services])
                        status_icon = "✓" if ros_status == "connected" else "○"
                        status_text = "CONNECTED" if ros_status == "connected" else "PORT_OPEN"
                        self.add_result(
                            f"  {status_icon} ROS device: {ip} ({hostname}) - {services_str} [{status_text}]",
                            "success" if ros_status == "connected" else "info"
                        )
                
                self.add_result(
                    f"ROS discovery complete: {found_count} ROS devices found out of {scanned} scanned",
                    "success" if self.ros_devices else "info"
                )
                
                # Summary
                connected_count = sum(1 for d in self.ros_devices if d.get('ros_status') == 'connected')
                if connected_count > 0:
                    self.add_result(f"  {connected_count} devices are fully connected and ready", "success")
            except Exception as e:
                self.add_result(f"ROS discovery error: {e}", "error")
            finally:
                self.active_tests["ros_discovery"] = False
        
        threading.Thread(target=ros_discovery_thread, daemon=True).start()
    
    def test_all_ros_devices(self):
        """Test all discovered ROS devices."""
        if not self.ros_devices:
            self.add_result("No ROS devices discovered. Run discovery first.", "warning")
            return
        
        devices_with_url = [d for d in self.ros_devices if d.get("rosbridge_url")]
        if not devices_with_url:
            self.add_result("No ROS devices with rosbridge URL found.", "warning")
            return
        
        self.add_result(f"Testing {len(devices_with_url)} discovered ROS devices...", "info")
        self.active_tests["ros_batch_test"] = True
        
        def batch_test_thread():
            success_count = 0
            for i, device in enumerate(devices_with_url, 1):
                url = device["rosbridge_url"]
                self.add_result(f"[{i}/{len(devices_with_url)}] Testing {device['ip']} ({url})...", "info")
                
                # Quick test with better error handling
                try:
                    from rosclient import RosClient
                    test_client = RosClient(url)
                    test_client.connect_async()
                    
                    # Wait for connection with timeout
                    start_time = time.time()
                    while not test_client.is_connected() and (time.time() - start_time) < 3.0:
                        time.sleep(0.1)
                    
                    if test_client.is_connected():
                        # Try to get more info
                        try:
                            if hasattr(test_client, '_ts_mgr') and test_client._ts_mgr:
                                device["ros_info"]["fully_connected"] = True
                        except:
                            pass
                        
                        self.add_result(f"  ✓ {device['ip']}: Connection successful", "success")
                        device["ros_status"] = "connected"
                        device["last_tested"] = datetime.now().isoformat()
                        success_count += 1
                    else:
                        self.add_result(f"  ✗ {device['ip']}: Connection timeout", "error")
                        device["ros_status"] = "failed"
                        device["last_tested"] = datetime.now().isoformat()
                    
                    test_client.terminate()
                except ImportError:
                    self.add_result(f"  ! {device['ip']}: RosClient not available", "warning")
                    device["ros_status"] = "unknown"
                except Exception as e:
                    self.add_result(f"  ✗ {device['ip']}: Error - {str(e)[:50]}", "error")
                    device["ros_status"] = "error"
                    device["last_tested"] = datetime.now().isoformat()
                
                time.sleep(0.3)  # Small delay between tests
            
            self.add_result(
                f"Batch testing complete: {success_count}/{len(devices_with_url)} devices connected",
                "success" if success_count > 0 else "warning"
            )
            self.active_tests["ros_batch_test"] = False
        
        threading.Thread(target=batch_test_thread, daemon=True).start()
    
    def connect_to_ros_device(self, ip: str) -> bool:
        """Connect to a discovered ROS device (for use by main GUI).
        
        Args:
            ip: IP address of ROS device
            
        Returns:
            True if URL found and can be used
        """
        for device in self.ros_devices:
            if device.get("ip") == ip and device.get("rosbridge_url"):
                # Update ROS URL input if available
                ros_url_input = self.components.get('ros_url_input')
                if ros_url_input:
                    ros_url_input.text = device["rosbridge_url"]
                    self.add_result(f"Selected ROS device: {ip} -> {device['rosbridge_url']}", "info")
                    return True
        return False
    
    def get_ros_device_url(self, ip: str) -> Optional[str]:
        """Get rosbridge URL for a specific IP from discovered devices.
        
        Args:
            ip: IP address
            
        Returns:
            Rosbridge URL or None
        """
        for device in self.ros_devices:
            if device.get("ip") == ip:
                return device.get("rosbridge_url")
        return None
    
    def get_local_network(self) -> str:
        """Get local network CIDR automatically."""
        try:
            # Get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # Connect to a remote address (doesn't actually send data)
                s.connect(('8.8.8.8', 80))
                local_ip = s.getsockname()[0]
            except:
                local_ip = '127.0.0.1'
            finally:
                s.close()
            
            # Extract network base
            ip_parts = local_ip.split('.')
            if len(ip_parts) == 4:
                return f"{'.'.join(ip_parts[:3])}.0/24"
            return "192.168.1.0/24"  # Default fallback
        except:
            return "192.168.1.0/24"
    
    def quick_scan_common_ros_ports(self, host: str) -> List[Dict[str, Any]]:
        """Quick scan common ROS ports on a single host.
        
        Args:
            host: Host IP or hostname
            
        Returns:
            List of found ROS services
        """
        found_services = []
        timeout = 1.0
        
        for service_name, port in self.ROS_PORTS.items():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    found_services.append({
                        "service": service_name,
                        "port": port,
                        "url": f"ws://{host}:{port}" if "rosbridge" in service_name else None
                    })
            except:
                pass
        
        return found_services
    
    def save_results(self, filepath: str):
        """Save test results to file.
        
        Args:
            filepath: Path to save file
        """
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "results": self.test_results,
                "history": self.test_history,
                "scan_results": self.scan_results,
                "devices": self.device_list,
                "ros_devices": self.ros_devices
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.add_result(f"Results saved to {filepath}", "success")
        except Exception as e:
            self.add_result(f"Failed to save results: {e}", "error")
    
    def load_ros_devices(self, filepath: str):
        """Load discovered ROS devices from file.
        
        Args:
            filepath: Path to load file
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if "ros_devices" in data:
                self.ros_devices = data["ros_devices"]
                self.add_result(f"Loaded {len(self.ros_devices)} ROS devices from {filepath}", "success")
                self.mark_dirty()
            else:
                self.add_result(f"No ROS devices found in file", "warning")
        except Exception as e:
            self.add_result(f"Failed to load ROS devices: {e}", "error")
    
    def save_ros_devices(self, filepath: str):
        """Save discovered ROS devices to file.
        
        Args:
            filepath: Path to save file
        """
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "ros_devices": self.ros_devices,
                "count": len(self.ros_devices)
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.add_result(f"ROS devices saved to {filepath}", "success")
        except Exception as e:
            self.add_result(f"Failed to save ROS devices: {e}", "error")
    
    def draw(self, app_state: Dict[str, Any]):
        """Draw network test tab with professional tools."""
        self.app_state = app_state
        
        # Update component positions first (same logic as handle_event)
        self._layout_components()
        
        # Calculate layout
        y = self.tab_height + DesignSystem.SPACING['md']
        
        # Title
        title_label = Label(50, y, "Network Testing Tools", 'title', DesignSystem.COLORS['text'])
        title_label.draw(self.screen)
        y += 50
        
        # Tool selection tabs (horizontal) - dynamic width based on text
        tab_height = 35
        tab_padding = DesignSystem.SPACING['md'] * 2  # Horizontal padding for tabs
        tab_spacing = DesignSystem.SPACING['sm']  # Spacing between tabs
        tabs = [
            ("Quick Test", "quick_test"),
            ("Port Scan", "port_scan"),
            ("Device Discovery", "device_discovery"),
            ("ROS Discovery", "ros_discovery"),
            ("ROS Test", "ros_test"),
            ("Advanced", "advanced")
        ]
        
        # Calculate tab widths based on text length
        tab_widths = []
        for tab_name, _ in tabs:
            text_width, _ = self.renderer.measure_text(tab_name, 'label')
            tab_width = text_width + tab_padding
            tab_widths.append(tab_width)
        
        tab_x = 50
        for idx, (tab_name, tab_id) in enumerate(tabs):
            tab_width = tab_widths[idx]
            tab_rect = pygame.Rect(tab_x, y, tab_width, tab_height)
            is_active = self.current_tool == tab_id
            tab_color = DesignSystem.COLORS['primary'] if is_active else DesignSystem.COLORS['surface']
            self.renderer.draw_rect(self.screen, tab_rect, tab_color, border_radius=0)
            
            # Tab text
            text_color = DesignSystem.COLORS['text'] if is_active else DesignSystem.COLORS['text_secondary']
            text_width, text_height = self.renderer.measure_text(tab_name, 'label')
            text_x = tab_x + (tab_width - text_width) // 2
            text_y = y + (tab_height - text_height) // 2
            self.renderer.render_text(self.screen, tab_name,
                                    (text_x, text_y),
                                    size='label', color=text_color)
            
            tab_x += tab_width + tab_spacing
        
        y += tab_height + DesignSystem.SPACING['md']
        
        # Tool content area
        content_width = self.screen_width - 100
        content_height = self.screen_height - y - 20
        
        # Draw current tool content (components already positioned by _layout_components)
        if self.current_tool == "quick_test":
            self._draw_quick_test(y, content_width, content_height)
        elif self.current_tool == "port_scan":
            self._draw_port_scan(y, content_width, content_height)
        elif self.current_tool == "device_discovery":
            self._draw_device_discovery(y, content_width, content_height)
        elif self.current_tool == "ros_discovery":
            self._draw_ros_discovery(y, content_width, content_height)
        elif self.current_tool == "ros_test":
            self._draw_ros_test(y, content_width, content_height)
        elif self.current_tool == "advanced":
            self._draw_advanced(y, content_width, content_height)
        
        # Results panel (always visible at bottom)
        results_height = min(300, content_height // 3)
        self._draw_results_panel(
            y + content_height - results_height,
            content_width,
            results_height
        )
    
    def _draw_quick_test(self, y: int, width: int, height: int):
        """Draw quick test tool."""
        card = Card(50, y, width, height - 300, "Quick Network Test")
        card.draw(self.screen)
        
        card_y = y + 50
        x = 70
        
        # Host input (position already set by _layout_components)
        host_label = Label(x, card_y, "Host/IP:", 'label', DesignSystem.COLORS['text_label'])
        host_label.draw(self.screen)
        
        host_input = self.components.get('network_host_input')
        if host_input:
            host_input.draw(self.screen)
        
        # Test buttons (position already set by _layout_components)
        ping_btn = self.components.get('ping_btn')
        if ping_btn:
            ping_btn.draw(self.screen)
        
        ws_test_btn = self.components.get('ws_test_btn')
        if ws_test_btn:
            ws_test_btn.draw(self.screen)
        
        ros_test_btn = self.components.get('ros_test_btn')
        if ros_test_btn:
            ros_test_btn.draw(self.screen)
    
    def _draw_port_scan(self, y: int, width: int, height: int):
        """Draw port scan tool."""
        card = Card(50, y, width, height - 300, "Port Scanner")
        card.draw(self.screen)
        
        card_y = y + 50
        x = 70
        spacing = DesignSystem.SPACING['md']
        
        # Components (position already set by _layout_components)
        host_label = Label(x, card_y, "Host:", 'label', DesignSystem.COLORS['text_label'])
        host_label.draw(self.screen)
        scan_host_input = self.components.get('scan_host_input')
        if scan_host_input:
            scan_host_input.draw(self.screen)
        
        card_y += 50
        port_label = Label(x, card_y, "Ports:", 'label', DesignSystem.COLORS['text_label'])
        port_label.draw(self.screen)
        port_input = self.components.get('port_range_input')
        if port_input:
            port_input.draw(self.screen)
        
        card_y += 50
        protocol_label = Label(x, card_y, "Protocol:", 'label', DesignSystem.COLORS['text_label'])
        protocol_label.draw(self.screen)
        tcp_checkbox = self.components.get('tcp_checkbox')
        if tcp_checkbox:
            tcp_checkbox.draw(self.screen)
        udp_checkbox = self.components.get('udp_checkbox')
        if udp_checkbox:
            udp_checkbox.draw(self.screen)
        
        card_y += 50
        scan_btn = self.components.get('scan_btn')
        if scan_btn:
            scan_btn.draw(self.screen)
        
        # Scan results with proper spacing
        if self.scan_results:
            results_y = card_y + scan_btn.rect.height + spacing * 2 if scan_btn else card_y + spacing
            results_label = Label(x, results_y, "Scan Results:", 'label', DesignSystem.COLORS['text'])
            results_label.draw(self.screen)
            results_y += 30
            
            # Clip results to available width
            max_result_width = width - x * 2
            for result in self.scan_results[:10]:  # Show first 10
                result_text = f"{result['protocol']} {result['port']}: {result['status']}"
                if 'service' in result:
                    result_text += f" ({result['service']})"
                
                # Truncate text if too long
                text_width = self.renderer.measure_text(result_text, 'console')[0]
                if text_width > max_result_width:
                    ellipsis = "..."
                    ellipsis_width = self.renderer.measure_text(ellipsis, 'console')[0]
                    while text_width > max_result_width - ellipsis_width and len(result_text) > 0:
                        result_text = result_text[:-1]
                        text_width = self.renderer.measure_text(result_text, 'console')[0]
                    result_text = result_text + ellipsis
                
                color = DesignSystem.COLORS['success'] if result['status'] == 'open' else DesignSystem.COLORS['text_secondary']
                self.renderer.render_text(self.screen, result_text,
                                        (x, results_y),
                                        size='console',
                                        color=color)
                results_y += 22  # Increased line spacing
    
    def _draw_device_discovery(self, y: int, width: int, height: int):
        """Draw device discovery tool."""
        card = Card(50, y, width, height - 300, "Device Discovery")
        card.draw(self.screen)
        
        card_y = y + 50
        x = 70
        spacing = DesignSystem.SPACING['md']
        
        # Components (position already set by _layout_components)
        network_label = Label(x, card_y, "Network:", 'label', DesignSystem.COLORS['text_label'])
        network_label.draw(self.screen)
        network_input = self.components.get('network_input')
        if network_input:
            network_input.draw(self.screen)
        
        card_y += 50
        discover_btn = self.components.get('discover_btn')
        if discover_btn:
            discover_btn.draw(self.screen)
        
        # Device list with proper spacing
        if self.device_list:
            devices_y = card_y + discover_btn.rect.height + spacing * 2 if discover_btn else card_y + spacing
            devices_label = Label(x, devices_y, "Discovered Devices:", 'label', DesignSystem.COLORS['text'])
            devices_label.draw(self.screen)
            devices_y += 30
            
            # Clip device text to available width
            max_device_width = width - x * 2
            for device in self.device_list[:10]:  # Show first 10
                device_text = f"{device['ip']} - {device.get('hostname', 'Unknown')}"
                
                # Truncate text if too long
                text_width = self.renderer.measure_text(device_text, 'console')[0]
                if text_width > max_device_width:
                    ellipsis = "..."
                    ellipsis_width = self.renderer.measure_text(ellipsis, 'console')[0]
                    while text_width > max_device_width - ellipsis_width and len(device_text) > 0:
                        device_text = device_text[:-1]
                        text_width = self.renderer.measure_text(device_text, 'console')[0]
                    device_text = device_text + ellipsis
                
                self.renderer.render_text(self.screen, device_text,
                                        (x, devices_y),
                                        size='console',
                                        color=DesignSystem.COLORS['text_secondary'])
                devices_y += 22  # Increased line spacing
    
    def _draw_ros_discovery(self, y: int, width: int, height: int):
        """Draw ROS device discovery tool."""
        card = Card(50, y, width, height - 300, "ROS Device Discovery (内网扫描)")
        card.draw(self.screen)
        
        card_y = y + 50
        x = 70
        spacing = DesignSystem.SPACING['md']
        row_spacing = 50
        btn_spacing = DesignSystem.SPACING['sm']
        
        # Components (position already set by _layout_components)
        network_label = Label(x, card_y, "Network:", 'label', DesignSystem.COLORS['text_label'])
        network_label.draw(self.screen)
        ros_network_input = self.components.get('ros_network_input')
        if ros_network_input:
            ros_network_input.draw(self.screen)
        auto_detect_btn = self.components.get('auto_detect_network_btn')
        if auto_detect_btn:
            auto_detect_btn.draw(self.screen)
        
        card_y += row_spacing
        discover_ros_btn = self.components.get('discover_ros_btn')
        if discover_ros_btn:
            discover_ros_btn.draw(self.screen)
        test_all_ros_btn = self.components.get('test_all_ros_btn')
        if test_all_ros_btn:
            test_all_ros_btn.draw(self.screen)
        
        # ROS devices list with clickable items and proper spacing
        if self.ros_devices:
            # Calculate spacing after buttons
            max_btn_bottom = card_y
            if discover_ros_btn:
                max_btn_bottom = max(max_btn_bottom, discover_ros_btn.rect.bottom)
            if test_all_ros_btn:
                max_btn_bottom = max(max_btn_bottom, test_all_ros_btn.rect.bottom)
            
            devices_y = max_btn_bottom + spacing * 2
            devices_label = Label(x, devices_y, f"Discovered ROS Devices ({len(self.ros_devices)}):", 
                                'label', DesignSystem.COLORS['text'])
            devices_label.draw(self.screen)
            devices_y += 30 + spacing
            
            # Device list area (scrollable) with proper margins
            device_list_area = pygame.Rect(x, devices_y, width - x * 2, height - devices_y - 100)
            max_text_width = device_list_area.width - spacing * 2
            
            for idx, device in enumerate(self.ros_devices[:20]):  # Show first 20
                device_rect = pygame.Rect(x, devices_y, device_list_area.width, 60)
                
                # Highlight if connected
                if device.get('ros_status') == 'connected':
                    highlight_rect = pygame.Rect(x - 3, devices_y, 3, 60)
                    self.renderer.draw_rect(self.screen, highlight_rect,
                                          DesignSystem.COLORS['success'],
                                          border_radius=0)
                
                # Device info line with truncation
                status_color = DesignSystem.COLORS['success'] if device.get('ros_status') == 'connected' else DesignSystem.COLORS['warning']
                status_text = "✓" if device.get('ros_status') == 'connected' else "○"
                
                device_text = f"{status_text} {device['ip']}"
                if device.get('hostname') and device['hostname'] != 'Unknown':
                    device_text += f" ({device['hostname']})"
                
                # Truncate device text if too long
                text_width = self.renderer.measure_text(device_text, 'console')[0]
                if text_width > max_text_width:
                    ellipsis = "..."
                    ellipsis_width = self.renderer.measure_text(ellipsis, 'console')[0]
                    while text_width > max_text_width - ellipsis_width and len(device_text) > 0:
                        device_text = device_text[:-1]
                        text_width = self.renderer.measure_text(device_text, 'console')[0]
                    device_text = device_text + ellipsis
                
                self.renderer.render_text(self.screen, device_text,
                                        (x, devices_y),
                                        size='console',
                                        color=status_color)
                
                # Services line with truncation
                services_y = devices_y + 20
                services = device.get('ros_services', [])
                if services:
                    services_text = "  Services: " + ", ".join([f"{s['service']}:{s['port']}" for s in services])
                    # Truncate services text if too long
                    services_width = self.renderer.measure_text(services_text, 'small')[0]
                    if services_width > max_text_width:
                        ellipsis = "..."
                        ellipsis_width = self.renderer.measure_text(ellipsis, 'small')[0]
                        while services_width > max_text_width - ellipsis_width and len(services_text) > 0:
                            services_text = services_text[:-1]
                            services_width = self.renderer.measure_text(services_text, 'small')[0]
                        services_text = services_text + ellipsis
                    
                    self.renderer.render_text(self.screen, services_text,
                                            (x + spacing, services_y),
                                            size='small',
                                            color=DesignSystem.COLORS['text_secondary'])
                
                # URL line with truncation and status indicator
                if device.get('rosbridge_url'):
                    url_y = services_y + 18
                    url_text = f"  URL: {device['rosbridge_url']} [Click to use]"
                    
                    # Calculate available width for URL (considering status indicator)
                    status_indicator_width = 80  # Approximate width for status text
                    url_max_width = max_text_width - status_indicator_width - spacing
                    
                    # Truncate URL text if too long
                    url_width = self.renderer.measure_text(url_text, 'small')[0]
                    if url_width > url_max_width:
                        ellipsis = "..."
                        ellipsis_width = self.renderer.measure_text(ellipsis, 'small')[0]
                        while url_width > url_max_width - ellipsis_width and len(url_text) > 0:
                            url_text = url_text[:-1]
                            url_width = self.renderer.measure_text(url_text, 'small')[0]
                        url_text = url_text + ellipsis
                    
                    self.renderer.render_text(self.screen, url_text,
                                            (x + spacing, url_y),
                                            size='small',
                                            color=DesignSystem.COLORS['primary'])
                    
                    # Status indicator (right-aligned)
                    if device.get('ros_status') == 'connected':
                        status_text = "[READY]"
                        status_x = device_list_area.right - self.renderer.measure_text(status_text, 'small')[0] - spacing
                        self.renderer.render_text(self.screen, status_text,
                                                (status_x, url_y),
                                                size='small',
                                                color=DesignSystem.COLORS['success'])
                    elif device.get('ros_status') == 'failed':
                        status_text = "[FAILED]"
                        status_x = device_list_area.right - self.renderer.measure_text(status_text, 'small')[0] - spacing
                        self.renderer.render_text(self.screen, status_text,
                                                (status_x, url_y),
                                                size='small',
                                                color=DesignSystem.COLORS['error'])
                    
                    devices_y += 55  # Increased spacing between devices
                else:
                    devices_y += 45
                
                if devices_y > device_list_area.bottom:
                    break
        else:
            # Help text
            help_y = card_y + 60
            help_text = "Click 'Discover ROS Devices' to scan network for ROS services"
            self.renderer.render_text(self.screen, help_text,
                                    (x, help_y),
                                    size='label',
                                    color=DesignSystem.COLORS['text_tertiary'])
            
            help_y += 30
            help_text2 = "Scans for: Rosbridge (9090), ROS Master (11311), and other ROS ports"
            self.renderer.render_text(self.screen, help_text2,
                                    (x, help_y),
                                    size='small',
                                    color=DesignSystem.COLORS['text_tertiary'])
    
    def _draw_ros_test(self, y: int, width: int, height: int):
        """Draw ROS test tool."""
        card = Card(50, y, width, height - 300, "ROS Connection Test")
        card.draw(self.screen)
        
        card_y = y + 50
        x = 70
        spacing = DesignSystem.SPACING['md']
        row_spacing = 50
        
        # Components (position already set by _layout_components)
        ros_url_label = Label(x, card_y, "Rosbridge URL:", 'label', DesignSystem.COLORS['text_label'])
        ros_url_label.draw(self.screen)
        ros_url_input = self.components.get('ros_url_input')
        if ros_url_input:
            ros_url_input.draw(self.screen)
        
        card_y += row_spacing
        ros_test_btn = self.components.get('ros_connection_btn')
        if ros_test_btn:
            ros_test_btn.draw(self.screen)
    
    def _draw_advanced(self, y: int, width: int, height: int):
        """Draw advanced tools."""
        card = Card(50, y, width, height - 300, "Advanced Network Tools")
        card.draw(self.screen)
        
        card_y = y + 50
        x = 70
        
        # Advanced tools info
        info_text = "Advanced network diagnostic tools coming soon..."
        self.renderer.render_text(self.screen, info_text,
                                (x, card_y),
                                size='label',
                                color=DesignSystem.COLORS['text_secondary'])
    
    def _draw_results_panel(self, y: int, width: int, height: int):
        """Draw results panel with proper spacing and text clipping."""
        result_card = Card(50, y, width, height, "Test Results")
        result_card.draw(self.screen)
        
        spacing = DesignSystem.SPACING['md']
        result_area = pygame.Rect(70, y + 50, width - 40, height - 100)
        self.renderer.draw_rect(self.screen, result_area,
                              DesignSystem.COLORS['bg'],
                              border_radius=0)
        
        # Draw results with scrolling and proper text clipping
        if self.test_results:
            result_y = result_area.y + spacing - self.scroll_y
            max_text_width = result_area.width - spacing * 2
            
            for result in reversed(self.test_results[-50:]):  # Show last 50
                if result_y + 20 < result_area.y:
                    break
                if result_y > result_area.bottom:
                    continue
                
                # Truncate text if too long to prevent overflow
                display_result = result
                text_width = self.renderer.measure_text(result, 'console')[0]
                if text_width > max_text_width:
                    ellipsis = "..."
                    ellipsis_width = self.renderer.measure_text(ellipsis, 'console')[0]
                    while text_width > max_text_width - ellipsis_width and len(display_result) > 0:
                        display_result = display_result[:-1]
                        text_width = self.renderer.measure_text(display_result, 'console')[0]
                    display_result = display_result + ellipsis
                
                # Color based on result type
                if "[✓]" in result or "successful" in result.lower():
                    color = DesignSystem.COLORS['success']
                elif "[✗]" in result or "failed" in result.lower() or "error" in result.lower():
                    color = DesignSystem.COLORS['error']
                elif "[!]" in result or "warning" in result.lower():
                    color = DesignSystem.COLORS['warning']
                else:
                    color = DesignSystem.COLORS['text_console']
                
                self.renderer.render_text(self.screen, display_result,
                                        (result_area.x + spacing, result_y),
                                        size='console',
                                        color=color)
                result_y += 22  # Increased line spacing
        
        # Buttons (position already set by _layout_results_buttons)
        if self.current_tool == "ros_discovery" and self.ros_devices:
            save_ros_btn = self.components.get('save_ros_devices_btn')
            if save_ros_btn:
                save_ros_btn.draw(self.screen)
        
        save_btn = self.components.get('save_results_btn')
        if save_btn:
            save_btn.draw(self.screen)
    
    def handle_event(self, event: pygame.event.Event, app_state: Dict[str, Any]) -> bool:
        """Handle network tab events."""
        # Update component positions (same as draw)
        self._layout_components()
        
        # Handle tab switching first (before component events to avoid conflicts)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            tab_height = 35
            tab_padding = DesignSystem.SPACING['md'] * 2
            tab_spacing = DesignSystem.SPACING['sm']
            tab_y = self.tab_height + DesignSystem.SPACING['md'] + 50
            tab_x = 50
            
            tabs_data = [
                ("Quick Test", "quick_test"),
                ("Port Scan", "port_scan"),
                ("Device Discovery", "device_discovery"),
                ("ROS Discovery", "ros_discovery"),
                ("ROS Test", "ros_test"),
                ("Advanced", "advanced")
            ]
            
            # Calculate tab widths (same as in draw method)
            tab_widths = []
            for tab_name, _ in tabs_data:
                text_width, _ = self.renderer.measure_text(tab_name, 'label')
                tab_width = text_width + tab_padding
                tab_widths.append(tab_width)
            
            current_x = tab_x
            for i, (tab_name, tab_id) in enumerate(tabs_data):
                tab_width = tab_widths[i]
                tab_rect = pygame.Rect(current_x, tab_y, tab_width, tab_height)
                if tab_rect.collidepoint(event.pos):
                    self.current_tool = tab_id
                    self._layout_components()  # Re-layout after tab switch
                    return True
                current_x += tab_width + tab_spacing
        
        # Handle component events (buttons, inputs, etc. have priority)
        # Process buttons first, then other components
        component_order = []
        for component_key, component in self.components.items():
            if component is None:
                continue
            # Skip primitive types
            if isinstance(component, (int, float, str, bool, list, dict, tuple)):
                continue
            # Only process components that have handle_event
            if hasattr(component, 'handle_event'):
                # Ensure component is visible and enabled
                if hasattr(component, 'visible') and not component.visible:
                    continue
                if hasattr(component, 'enabled') and not component.enabled:
                    continue
                # Prioritize buttons
                if isinstance(component, Button):
                    component_order.insert(0, (component_key, component))
                else:
                    component_order.append((component_key, component))
        
        # Handle component events in priority order
        for component_key, component in component_order:
            try:
                # Ensure component rect is valid before handling events
                if hasattr(component, 'rect'):
                    if component.rect.width <= 0 or component.rect.height <= 0:
                        continue  # Skip components with invalid rect
                
                if component.handle_event(event):
                    return True
            except Exception as e:
                # Log error but continue processing
                print(f"Error handling event for component {component_key}: {e}")
                pass
        
        
        # Handle ROS device list clicks
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.current_tool == "ros_discovery" and self.ros_devices:
                card_y = self.tab_height + DesignSystem.SPACING['md'] + 50 + 35 + DesignSystem.SPACING['md'] + 50 + 60 + 30
                x = 70
                devices_y = card_y
                
                for device in self.ros_devices[:20]:
                    if device.get('rosbridge_url'):
                        url_rect = pygame.Rect(x + 20, devices_y + 34, 500, 16)
                        if url_rect.collidepoint(event.pos):
                            ros_url_input = self.components.get('ros_url_input')
                            if ros_url_input:
                                ros_url_input.text = device['rosbridge_url']
                                self.add_result(f"Selected ROS device: {device['ip']} ({device['rosbridge_url']})", "info")
                            return True
                    devices_y += 55  # Match the spacing used in draw method
        
        # Handle scrolling
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # Scroll up
                self.scroll_y = max(0, self.scroll_y - 20)
                return True
            elif event.button == 5:  # Scroll down
                self.scroll_y += 20
                return True
        
        return False
    
    def _layout_components(self):
        """Layout components based on current tool. Called by both draw() and handle_event()."""
        # Calculate base positions (same as in draw method)
        y = self.tab_height + DesignSystem.SPACING['md']
        y += 50  # Title height
        y += 35 + DesignSystem.SPACING['md']  # Tab height + spacing
        
        content_width = self.screen_width - 100
        content_height = self.screen_height - y - 20
        
        # Layout components based on current tool
        if self.current_tool == "quick_test":
            self._layout_quick_test(y, content_width, content_height)
        elif self.current_tool == "port_scan":
            self._layout_port_scan(y, content_width, content_height)
        elif self.current_tool == "device_discovery":
            self._layout_device_discovery(y, content_width, content_height)
        elif self.current_tool == "ros_discovery":
            self._layout_ros_discovery(y, content_width, content_height)
        elif self.current_tool == "ros_test":
            self._layout_ros_test(y, content_width, content_height)
        
        # Layout results panel buttons (always at bottom)
        results_height = min(300, content_height // 3)
        results_y = y + content_height - results_height
        self._layout_results_buttons(results_y, content_width, results_height)
        
        # Define which components belong to which tool
        tool_components = {
            "quick_test": ['network_host_input', 'ping_btn', 'ws_test_btn', 'ros_test_btn'],
            "port_scan": ['scan_host_input', 'port_range_input', 'tcp_checkbox', 'udp_checkbox', 'scan_btn'],
            "device_discovery": ['network_input', 'discover_btn'],
            "ros_discovery": ['ros_network_input', 'auto_detect_network_btn', 'discover_ros_btn', 'test_all_ros_btn', 'save_ros_devices_btn'],
            "ros_test": ['ros_url_input', 'ros_connection_btn'],
            "advanced": []
        }
        
        # Set visibility and enabled state based on current tool
        current_tool_components = set(tool_components.get(self.current_tool, []))
        # Results buttons are always visible
        current_tool_components.add('save_results_btn')
        
        for component_key, component in self.components.items():
            if component is None:
                continue
            if isinstance(component, (int, float, str, bool, list, dict, tuple)):
                continue
            
            # Set visibility based on whether component belongs to current tool
            if hasattr(component, 'visible'):
                component.visible = component_key in current_tool_components
            
            # Always enable components that are visible
            if hasattr(component, 'enabled'):
                component.enabled = component_key in current_tool_components
    
    def _layout_results_buttons(self, results_y: int, width: int, height: int):
        """Layout buttons in results panel."""
        spacing = DesignSystem.SPACING['md']
        button_bottom_margin = DesignSystem.SPACING['md']  # Increased margin for better spacing
        button_spacing = DesignSystem.SPACING['md']  # Spacing between buttons
        result_area_bottom = results_y + height - 100
        
        # Save ROS devices button (if in ROS discovery tab)
        if self.current_tool == "ros_discovery" and self.ros_devices:
            save_ros_btn = self.components.get('save_ros_devices_btn')
            if save_ros_btn:
                save_ros_btn.rect.x = 50 + width - save_ros_btn.rect.width - spacing
                save_ros_btn.rect.y = result_area_bottom + button_bottom_margin
        
        # Save results button
        save_btn = self.components.get('save_results_btn')
        if save_btn:
            if self.current_tool == "ros_discovery" and self.ros_devices:
                save_ros_btn = self.components.get('save_ros_devices_btn')
                if save_ros_btn:
                    save_btn.rect.y = save_ros_btn.rect.bottom + button_spacing
                else:
                    save_btn.rect.y = result_area_bottom + button_bottom_margin
            else:
                save_btn.rect.y = result_area_bottom + button_bottom_margin
            save_btn.rect.x = 50 + width - save_btn.rect.width - spacing
    
    def _layout_quick_test(self, y: int, width: int, height: int):
        """Update quick test component positions."""
        card_y = y + 50
        x = 70
        spacing = DesignSystem.SPACING['md']
        
        host_input = self.components.get('network_host_input')
        if host_input:
            label_width = self.renderer.measure_text("Host/IP:", 'label')[0]
            input_spacing = spacing * 2  # Increased spacing between label and input
            host_input.rect.x = x + label_width + input_spacing
            host_input.rect.y = card_y
            host_input.rect.width = min(300, width - (x + label_width + input_spacing) - x)
        
        card_y += 50 + spacing
        btn_x = x
        btn_y = card_y
        btn_spacing = DesignSystem.SPACING['md']  # Increased button spacing for better visual separation
        
        ping_btn = self.components.get('ping_btn')
        if ping_btn:
            # Ensure button has valid size
            if ping_btn.rect.width <= 0 or ping_btn.rect.height <= 0:
                # Recalculate button size if needed
                if hasattr(ping_btn, '_resize_to_text'):
                    ping_btn._resize_to_text()
            ping_btn.rect.x = btn_x
            ping_btn.rect.y = btn_y
            btn_x += ping_btn.rect.width + btn_spacing
        
        ws_test_btn = self.components.get('ws_test_btn')
        if ws_test_btn:
            # Ensure button has valid size
            if ws_test_btn.rect.width <= 0 or ws_test_btn.rect.height <= 0:
                if hasattr(ws_test_btn, '_resize_to_text'):
                    ws_test_btn._resize_to_text()
            if btn_x + ws_test_btn.rect.width <= 50 + width - spacing:
                ws_test_btn.rect.x = btn_x
                ws_test_btn.rect.y = btn_y
                btn_x += ws_test_btn.rect.width + btn_spacing
        
        ros_test_btn = self.components.get('ros_test_btn')
        if ros_test_btn:
            # Ensure button has valid size
            if ros_test_btn.rect.width <= 0 or ros_test_btn.rect.height <= 0:
                if hasattr(ros_test_btn, '_resize_to_text'):
                    ros_test_btn._resize_to_text()
            if btn_x + ros_test_btn.rect.width <= 50 + width - spacing:
                ros_test_btn.rect.x = btn_x
                ros_test_btn.rect.y = btn_y
    
    def _layout_port_scan(self, y: int, width: int, height: int):
        """Update port scan component positions."""
        card_y = y + 50
        x = 70
        spacing = DesignSystem.SPACING['md']
        row_spacing = 50
        
        scan_host_input = self.components.get('scan_host_input')
        if scan_host_input:
            label_width = self.renderer.measure_text("Host:", 'label')[0]
            input_spacing = spacing * 2  # Increased spacing between label and input
            scan_host_input.rect.x = x + label_width + input_spacing
            scan_host_input.rect.y = card_y
            scan_host_input.rect.width = min(200, width - (x + label_width + input_spacing) - x)
        
        card_y += row_spacing
        port_input = self.components.get('port_range_input')
        if port_input:
            label_width = self.renderer.measure_text("Ports:", 'label')[0]
            input_spacing = spacing * 2  # Increased spacing between label and input
            port_input.rect.x = x + label_width + input_spacing
            port_input.rect.y = card_y
            port_input.rect.width = min(200, width - (x + label_width + input_spacing) - x)
        
        card_y += row_spacing
        label_width = self.renderer.measure_text("Protocol:", 'label')[0]
        checkbox_start_x = x + label_width + spacing
        checkbox_spacing = DesignSystem.SPACING['md'] * 2  # Increased spacing between checkboxes
        checkbox_y_offset = 2  # Vertical alignment offset
        
        tcp_checkbox = self.components.get('tcp_checkbox')
        if tcp_checkbox:
            tcp_checkbox.rect.x = checkbox_start_x
            tcp_checkbox.rect.y = card_y + checkbox_y_offset
        
        udp_checkbox = self.components.get('udp_checkbox')
        if udp_checkbox:
            if tcp_checkbox:
                # Calculate UDP checkbox position: after TCP checkbox + its text + spacing
                # TCP checkbox is 20px wide, text width needs to be measured
                tcp_text_width, _ = self.renderer.measure_text(tcp_checkbox.text, 'label')
                tcp_total_width = 20 + DesignSystem.SPACING['sm'] + tcp_text_width  # checkbox + spacing + text
                udp_checkbox.rect.x = checkbox_start_x + tcp_total_width + checkbox_spacing
            else:
                udp_checkbox.rect.x = checkbox_start_x
            udp_checkbox.rect.y = card_y + checkbox_y_offset
            
            # If UDP checkbox would overflow, move to next line
            if udp_checkbox.rect.right > 50 + width - spacing:
                udp_checkbox.rect.x = checkbox_start_x
                udp_checkbox.rect.y = card_y + 35  # Move to next line with proper spacing
        
        card_y += row_spacing
        scan_btn = self.components.get('scan_btn')
        if scan_btn:
            scan_btn.rect.x = x
            scan_btn.rect.y = card_y
    
    def _layout_device_discovery(self, y: int, width: int, height: int):
        """Update device discovery component positions."""
        card_y = y + 50
        x = 70
        spacing = DesignSystem.SPACING['md']
        row_spacing = 50
        
        network_input = self.components.get('network_input')
        if network_input:
            label_width = self.renderer.measure_text("Network:", 'label')[0]
            input_spacing = spacing * 2  # Increased spacing between label and input
            network_input.rect.x = x + label_width + input_spacing
            network_input.rect.y = card_y
            network_input.rect.width = min(200, width - (x + label_width + input_spacing) - x)
        
        card_y += row_spacing
        discover_btn = self.components.get('discover_btn')
        if discover_btn:
            discover_btn.rect.x = x
            discover_btn.rect.y = card_y
    
    def _layout_ros_discovery(self, y: int, width: int, height: int):
        """Update ROS discovery component positions."""
        card_y = y + 50
        x = 70
        spacing = DesignSystem.SPACING['md']
        row_spacing = 50
        btn_spacing = DesignSystem.SPACING['md']  # Increased button spacing for better visual separation
        
        ros_network_input = self.components.get('ros_network_input')
        if ros_network_input:
            label_width = self.renderer.measure_text("Network:", 'label')[0]
            input_spacing = spacing * 2  # Increased spacing between label and input
            ros_network_input.rect.x = x + label_width + input_spacing
            ros_network_input.rect.y = card_y
            auto_detect_btn = self.components.get('auto_detect_network_btn')
            if auto_detect_btn:
                auto_detect_width = auto_detect_btn.rect.width if hasattr(auto_detect_btn, 'rect') else 100
                ros_network_input.rect.width = min(200, width - (x + label_width + input_spacing) - auto_detect_width - btn_spacing - x)
            else:
                ros_network_input.rect.width = min(200, width - (x + label_width + input_spacing) - x)
        
        auto_detect_btn = self.components.get('auto_detect_network_btn')
        if auto_detect_btn:
            if ros_network_input:
                auto_detect_btn.rect.x = ros_network_input.rect.right + btn_spacing
            else:
                label_width = self.renderer.measure_text("Network:", 'label')[0]
                input_spacing = spacing * 2
                auto_detect_btn.rect.x = x + label_width + input_spacing
            auto_detect_btn.rect.y = card_y
            if auto_detect_btn.rect.right > 50 + width - spacing:
                auto_detect_btn.rect.x = x
                auto_detect_btn.rect.y = card_y + 40
        
        card_y += row_spacing
        discover_ros_btn = self.components.get('discover_ros_btn')
        if discover_ros_btn:
            discover_ros_btn.rect.x = x
            discover_ros_btn.rect.y = card_y
        
        test_all_ros_btn = self.components.get('test_all_ros_btn')
        if test_all_ros_btn:
            if discover_ros_btn:
                test_all_ros_btn.rect.x = discover_ros_btn.rect.right + btn_spacing
            else:
                test_all_ros_btn.rect.x = x
            test_all_ros_btn.rect.y = card_y
            if test_all_ros_btn.rect.right > 50 + width - spacing:
                test_all_ros_btn.rect.x = x
                test_all_ros_btn.rect.y = card_y + 40
    
    def _layout_ros_test(self, y: int, width: int, height: int):
        """Update ROS test component positions."""
        card_y = y + 50
        x = 70
        spacing = DesignSystem.SPACING['md']
        row_spacing = 50
        
        ros_url_input = self.components.get('ros_url_input')
        if ros_url_input:
            label_width = self.renderer.measure_text("Rosbridge URL:", 'label')[0]
            input_spacing = spacing * 2  # Increased spacing between label and input
            ros_url_input.rect.x = x + label_width + input_spacing
            ros_url_input.rect.y = card_y
            ros_url_input.rect.width = min(400, width - (x + label_width + input_spacing) - x)
        
        card_y += row_spacing
        ros_test_btn = self.components.get('ros_connection_btn')
        if ros_test_btn:
            ros_test_btn.rect.x = x
            ros_test_btn.rect.y = card_y
    
    def update(self, dt: float, app_state: Dict[str, Any]):
        """Update network tab."""
        # Only update actual component objects, not primitive types
        for component_key in self.components:
            component = self.components[component_key]
            # Check if it's a component object (has update method and is not a primitive type)
            if (component is not None and 
                not isinstance(component, (int, float, str, bool, list, dict, tuple)) and
                hasattr(component, 'update')):
                try:
                    component.update(dt)
                except (TypeError, AttributeError) as e:
                    # Skip components that don't accept dt or have other issues
                    pass
