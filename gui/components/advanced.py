"""Advanced UI components for maps, JSON editing, and topic lists with optimized rendering."""
import pygame
import json
import os
import math
from typing import Optional, Dict, Any, List, Tuple

from .base import UIComponent
from .interactive import Items
from ..design.design_system import DesignSystem
from ..renderers.ui_renderer import get_renderer
from rosclient.models.drone import Waypoint


class MapComponent(UIComponent):
    """Advanced radar-style map component with waypoint editing, terrain import, and UAV integration."""
    
    def __init__(self, x: int, y: int, width: int, height: int, title: str = ""):
        super().__init__(x, y, width, height)
        self.title = title
        self.drones: Dict[str, Dict[str, Any]] = {}  # Will be set from parent
        self.current_drone_id: Optional[str] = None  # Will be set from parent
        
        # Waypoint management
        self.waypoints: List[Waypoint] = []
        self.selected_waypoint: Optional[int] = None  # Index of selected waypoint
        self.editing_waypoint: Optional[int] = None  # Index of waypoint being edited
        self.waypoint_counter = 0
        
        # Map settings
        self.radar_style = True  # Enable radar-style display
        self.show_grid = True
        self.show_terrain = True
        self.terrain_image: Optional[pygame.Surface] = None
        self.terrain_bounds: Optional[Tuple[float, float, float, float]] = None  # (min_lat, min_lon, max_lat, max_lon)
        
        # Map view settings
        self.map_center: Optional[Tuple[float, float]] = None  # (lat, lon)
        self.map_zoom = 1.0
        self.map_rotation = 0.0  # Rotation angle in degrees
        
        # Interaction state
        self.dragging_waypoint: Optional[int] = None
        self.drag_start_pos: Optional[Tuple[int, int]] = None
        
    def set_drones(self, drones: Dict[str, Dict[str, Any]], current_drone_id: Optional[str]):
        """Set the drones data and current selection."""
        self.drones = drones
        self.current_drone_id = current_drone_id
    
    def import_terrain_map(self, image_path: str, bounds: Tuple[float, float, float, float]):
        """
        Import terrain map image.
        
        Args:
            image_path: Path to terrain image file
            bounds: (min_latitude, min_longitude, max_latitude, max_longitude)
        """
        try:
            if os.path.exists(image_path):
                terrain_surf = pygame.image.load(image_path)
                # Convert to format compatible with current surface
                self.terrain_image = terrain_surf.convert_alpha()
                self.terrain_bounds = bounds
                self.mark_dirty()
        except Exception as e:
            print(f"Failed to load terrain map: {e}")
    
    def add_waypoint(self, latitude: float, longitude: float, altitude: float = 10.0) -> Waypoint:
        """Add a new waypoint at the specified coordinates."""
        waypoint = Waypoint(
            id=self.waypoint_counter,
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            name=f"WP{self.waypoint_counter + 1}"
        )
        self.waypoint_counter += 1
        self.waypoints.append(waypoint)
        self.selected_waypoint = len(self.waypoints) - 1
        self.mark_dirty()
        return waypoint
    
    def remove_waypoint(self, index: int):
        """Remove waypoint at index."""
        if 0 <= index < len(self.waypoints):
            self.waypoints.pop(index)
            if self.selected_waypoint == index:
                self.selected_waypoint = None
            elif self.selected_waypoint > index:
                self.selected_waypoint -= 1
            self.mark_dirty()
    
    def clear_waypoints(self):
        """Clear all waypoints."""
        self.waypoints.clear()
        self.selected_waypoint = None
        self.waypoint_counter = 0
        self.mark_dirty()
    
    def save_waypoints(self, filepath: str):
        """Save waypoints to JSON file."""
        try:
            data = {
                "waypoints": [wp.to_dict() for wp in self.waypoints],
                "metadata": {
                    "count": len(self.waypoints),
                    "version": "1.0"
                }
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save waypoints: {e}")
    
    def load_waypoints(self, filepath: str):
        """Load waypoints from JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.waypoints = [Waypoint.from_dict(wp) for wp in data.get("waypoints", [])]
            if self.waypoints:
                self.waypoint_counter = max(wp.id for wp in self.waypoints) + 1
            else:
                self.waypoint_counter = 0
            self.mark_dirty()
        except Exception as e:
            print(f"Failed to load waypoints: {e}")
    
    def save_trajectory(self, filepath: str, drone_id: Optional[str] = None):
        """
        Save drone trajectory to JSON file.
        
        Args:
            filepath: Path to save trajectory file
            drone_id: ID of drone to save trajectory for. If None, uses current_drone_id.
        """
        target_id = drone_id or self.current_drone_id
        if not target_id:
            return False
        
        drone_info = self.drones.get(target_id)
        if not drone_info:
            return False
        
        trajectory = drone_info.get('trajectory', [])
        if not trajectory:
            return False
        
        try:
            data = {
                "drone_id": target_id,
                "drone_name": drone_info.get('name', 'Unknown'),
                "trajectory": [
                    {
                        "latitude": float(lat),
                        "longitude": float(lon),
                        "altitude": float(alt),
                        "timestamp": i  # Sequential index as timestamp
                    }
                    for i, (lat, lon, alt) in enumerate(trajectory)
                ],
                "metadata": {
                    "point_count": len(trajectory),
                    "version": "1.0"
                }
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Failed to save trajectory: {e}")
            return False
    
    def load_trajectory(self, filepath: str, drone_id: Optional[str] = None):
        """
        Load drone trajectory from JSON file.
        
        Args:
            filepath: Path to trajectory file
            drone_id: ID of drone to load trajectory for. If None, uses current_drone_id.
        """
        target_id = drone_id or self.current_drone_id
        if not target_id:
            return False
        
        drone_info = self.drones.get(target_id)
        if not drone_info:
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            trajectory_data = data.get("trajectory", [])
            trajectory = [
                (float(point["latitude"]), float(point["longitude"]), float(point.get("altitude", 0.0)))
                for point in trajectory_data
            ]
            
            drone_info['trajectory'] = trajectory
            self.mark_dirty()
            return True
        except Exception as e:
            print(f"Failed to load trajectory: {e}")
            return False
    
    def send_waypoints_to_uav(self, drone_id: Optional[str] = None) -> bool:
        """
        Send waypoints to UAV client.
        
        Args:
            drone_id: ID of drone to send waypoints to. If None, uses current_drone_id.
        
        Returns:
            True if successful, False otherwise
        """
        target_id = drone_id or self.current_drone_id
        if not target_id:
            return False
        
        drone_info = self.drones.get(target_id)
        if not drone_info or not drone_info.get('client') or not drone_info.get('is_connected'):
            return False
        
        client = drone_info['client']
        
        # Check if client has waypoint sending capability
        if hasattr(client, 'send_waypoints'):
            try:
                client.send_waypoints(self.waypoints)
                return True
            except Exception as e:
                print(f"Failed to send waypoints: {e}")
                return False
        else:
            # Fallback: try to publish waypoints via ROS topic
            try:
                waypoint_data = {
                    "waypoints": [wp.to_dict() for wp in self.waypoints],
                    "count": len(self.waypoints)
                }
                # Try to publish to common waypoint topics
                if hasattr(client, 'safe_publish'):
                    client.safe_publish("/mission/waypoints", "std_msgs/String", 
                                       {"data": json.dumps(waypoint_data)})
                    return True
            except Exception as e:
                print(f"Failed to publish waypoints: {e}")
                return False
        
        return False
    
    def _latlon_to_screen(self, lat: float, lon: float, map_rect: pygame.Rect, 
                         min_lat: float, max_lat: float, min_lon: float, max_lon: float) -> Tuple[int, int]:
        """Convert latitude/longitude to screen coordinates."""
        lat_range = max(max_lat - min_lat, 0.001)
        lon_range = max(max_lon - min_lon, 0.001)
        x = map_rect.x + int((lon - min_lon) / lon_range * map_rect.width)
        y = map_rect.y + int((max_lat - lat) / lat_range * map_rect.height)
        return (x, y)
    
    def _screen_to_latlon(self, x: int, y: int, map_rect: pygame.Rect,
                          min_lat: float, max_lat: float, min_lon: float, max_lon: float) -> Tuple[float, float]:
        """Convert screen coordinates to latitude/longitude."""
        lat_range = max(max_lat - min_lat, 0.001)
        lon_range = max(max_lon - min_lon, 0.001)
        lon = min_lon + (x - map_rect.x) / map_rect.width * lon_range
        lat = max_lat - (y - map_rect.y) / map_rect.height * lat_range
        return (lat, lon)
    
    def _get_map_bounds(self, drone_positions: List[Dict], include_waypoints: bool = True) -> Tuple[float, float, float, float]:
        """Calculate map bounds from drones and waypoints."""
        lats = [d['lat'] for d in drone_positions] if drone_positions else []
        lons = [d['lon'] for d in drone_positions] if drone_positions else []
        
        if include_waypoints:
            for wp in self.waypoints:
                lats.append(wp.latitude)
                lons.append(wp.longitude)
        
        if not lats:
            # Default bounds (example: around a common location like origin or a default location)
            # Use a reasonable default range for adding waypoints
            default_center_lat = 40.0  # Example: New York area
            default_center_lon = -74.0
            default_range = 0.01  # ~1km range
            return (default_center_lat - default_range, 
                   default_center_lon - default_range,
                   default_center_lat + default_range,
                   default_center_lon + default_range)
        
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        
        # Add padding
        lat_range = max(max_lat - min_lat, 0.001)
        lon_range = max(max_lon - min_lon, 0.001)
        padding_factor = 0.1
        min_lat -= lat_range * padding_factor
        max_lat += lat_range * padding_factor
        min_lon -= lon_range * padding_factor
        max_lon += lon_range * padding_factor
        
        return (min_lat, min_lon, max_lat, max_lon)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events for waypoint editing and map interaction."""
        if not self.visible or not self.enabled:
            return False
        
        if not hasattr(event, 'pos'):
            return False
        
        # Check if event is within component bounds
        # event.pos is already relative to component (transformed by Card)
        if not self.rect.collidepoint(event.pos):
            return False
        
        # Calculate map area (relative to component)
        padding = DesignSystem.SPACING['md']
        header_height = 36 if self.title else 0
        map_rect = pygame.Rect(
            padding,
            header_height + padding,
            self.rect.width - padding * 2,
            self.rect.height - header_height - padding * 2
        )
        
        # Check if click is within map area
        # Convert event.pos to map_rect coordinates
        map_x = event.pos[0] - map_rect.x
        map_y = event.pos[1] - map_rect.y
        
        if not (0 <= map_x < map_rect.width and 0 <= map_y < map_rect.height):
            return False
        
        # Get map bounds
        drone_positions = []
        for drone_id, drone_info in self.drones.items():
            if drone_info.get('client') and drone_info.get('is_connected'):
                try:
                    pos = drone_info['client'].get_position()
                    if len(pos) >= 3 and pos[0] != 0.0 and pos[1] != 0.0:
                        drone_positions.append({
                            'lat': pos[0],
                            'lon': pos[1]
                        })
                except:
                    pass
        
        min_lat, min_lon, max_lat, max_lon = self._get_map_bounds(drone_positions)
        
        # Create map-relative event position
        map_event_pos = (map_x, map_y)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check if clicking on waypoint
                clicked_waypoint = None
                for i, wp in enumerate(self.waypoints):
                    # Get waypoint screen position (absolute coordinates)
                    wp_x, wp_y = self._latlon_to_screen(wp.latitude, wp.longitude, map_rect, 
                                                       min_lat, max_lat, min_lon, max_lon)
                    # Convert to map-relative coordinates for comparison
                    wp_rel_x = wp_x - map_rect.x
                    wp_rel_y = wp_y - map_rect.y
                    # Calculate distance using map-relative coordinates
                    dist = math.sqrt((map_event_pos[0] - wp_rel_x)**2 + 
                                   (map_event_pos[1] - wp_rel_y)**2)
                    if dist < 15:  # Increased click radius for easier selection
                        clicked_waypoint = i
                        break
                
                if clicked_waypoint is not None:
                    self.selected_waypoint = clicked_waypoint
                    self.dragging_waypoint = clicked_waypoint
                    self.drag_start_pos = map_event_pos
                    self.mark_dirty()
                elif pygame.key.get_mods() & pygame.KMOD_CTRL:
                    # Ctrl+Click to add waypoint
                    # map_event_pos is already relative to map_rect, use it directly
                    lat, lon = self._screen_to_latlon(
                        map_rect.x + map_event_pos[0], 
                        map_rect.y + map_event_pos[1], 
                        map_rect,
                        min_lat, max_lat, min_lon, max_lon
                    )
                    self.add_waypoint(lat, lon)
                    self.mark_dirty()
                else:
                    self.selected_waypoint = None
                    self.mark_dirty()
                
                return True
            elif event.button == 3:  # Right click
                # Right click to remove waypoint
                if self.selected_waypoint is not None:
                    self.remove_waypoint(self.selected_waypoint)
                    self.mark_dirty()
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.dragging_waypoint is not None:
                    self.dragging_waypoint = None
                    self.drag_start_pos = None
                    self.mark_dirty()
                return True
        
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_waypoint is not None and self.drag_start_pos:
                # Update waypoint position
                # map_event_pos is relative to map_rect, convert to absolute for latlon conversion
                lat, lon = self._screen_to_latlon(
                    map_rect.x + map_event_pos[0],
                    map_rect.y + map_event_pos[1],
                    map_rect,
                    min_lat, max_lat, min_lon, max_lon
                )
                if 0 <= self.dragging_waypoint < len(self.waypoints):
                    self.waypoints[self.dragging_waypoint].latitude = lat
                    self.waypoints[self.dragging_waypoint].longitude = lon
                    self.mark_dirty()
                return True
        
        return False
    
    def update(self, dt: float):
        """Update component state."""
        super().update(dt)
    
    def _draw_radar_grid(self, surface: pygame.Surface, map_rect: pygame.Rect, 
                         center_x: int, center_y: int, radius: int):
        """Draw radar-style grid."""
        # Draw concentric circles
        for i in range(1, 6):
            r = radius * i / 5
            pygame.draw.circle(surface, DesignSystem.COLORS['border'], (center_x, center_y), int(r), 1)
        
        # Draw crosshair lines
        pygame.draw.line(surface, DesignSystem.COLORS['border'],
                         (center_x - radius, center_y), (center_x + radius, center_y), 1)
        pygame.draw.line(surface, DesignSystem.COLORS['border'],
                         (center_x, center_y - radius), (center_x, center_y + radius), 1)
        
        # Draw cardinal directions
        font = self._renderer.font_renderer.get_font('small')
        directions = [("N", 0, -radius - 15), ("E", radius + 15, 0), 
                     ("S", 0, radius + 15), ("W", -radius - 15, 0)]
        for label, dx, dy in directions:
            text_surf = font.render(label, True, DesignSystem.COLORS['text_secondary'])
            text_rect = text_surf.get_rect(center=(center_x + dx, center_y + dy))
            surface.blit(text_surf, text_rect)
    
    def _draw_self(self, surface: pygame.Surface):
        """Draw radar-style map with waypoints, terrain, and drones."""
        renderer = self._renderer
        
        # Calculate map area
        padding = DesignSystem.SPACING['md']
        header_height = 36 if self.title else 0
        map_rect = pygame.Rect(
            padding,
            header_height + padding,
            self.rect.width - padding * 2,
            self.rect.height - header_height - padding * 2
        )
        
        # Draw radar-style background
        if self.radar_style:
            # Dark green/black radar background
            radar_bg = (0, 20, 0)
            renderer.draw_rect(surface, map_rect, radar_bg, border_radius=0)
            
            # Draw radar grid
            center_x, center_y = map_rect.centerx, map_rect.centery
            radius = min(map_rect.width, map_rect.height) // 2 - 10
            self._draw_radar_grid(surface, map_rect, center_x, center_y, radius)
        else:
            # Standard map background
            renderer.draw_rect(surface, map_rect,
                             DesignSystem.COLORS['bg_secondary'],
                             border_radius=0)
        
        # Draw terrain map if available
        if self.show_terrain and self.terrain_image and self.terrain_bounds:
            try:
                # Scale terrain image to fit map bounds
                min_lat, min_lon, max_lat, max_lon = self.terrain_bounds
                terrain_scaled = pygame.transform.scale(self.terrain_image, 
                                                       (map_rect.width, map_rect.height))
                # Apply transparency
                terrain_scaled.set_alpha(128)
                surface.blit(terrain_scaled, map_rect.topleft)
            except:
                pass
        
        # Collect drone positions
        drone_positions = []
        for drone_id, drone_info in self.drones.items():
            if drone_info.get('client') and drone_info.get('is_connected'):
                try:
                    pos = drone_info['client'].get_position()
                    if len(pos) >= 3 and pos[0] != 0.0 and pos[1] != 0.0:
                        drone_positions.append({
                            'id': drone_id,
                            'name': drone_info['name'],
                            'lat': pos[0],
                            'lon': pos[1],
                            'alt': pos[2],
                            'state': drone_info['client'].get_status(),
                            'trajectory': drone_info.get('trajectory', [])
                        })
                except:
                    pass
        
        # Get map bounds
        min_lat, min_lon, max_lat, max_lon = self._get_map_bounds(drone_positions)
        
        # Draw waypoint paths
        if len(self.waypoints) > 1:
            waypoint_points = []
            for wp in self.waypoints:
                x, y = self._latlon_to_screen(wp.latitude, wp.longitude, map_rect,
                                              min_lat, max_lat, min_lon, max_lon)
                waypoint_points.append((x, y))
            
            if len(waypoint_points) > 1:
                # Draw waypoint path
                pygame.draw.lines(surface, DesignSystem.COLORS['warning'], 
                                False, waypoint_points, 2)
        
        # Draw waypoints
        for i, wp in enumerate(self.waypoints):
            x, y = self._latlon_to_screen(wp.latitude, wp.longitude, map_rect,
                                         min_lat, max_lat, min_lon, max_lon)
            
            # Draw waypoint
            color = DesignSystem.COLORS['primary'] if i == self.selected_waypoint else DesignSystem.COLORS['warning']
            pygame.draw.circle(surface, color, (x, y), 8, 2)
            pygame.draw.circle(surface, color, (x, y), 4)
            
            # Draw waypoint label
            label = wp.name or f"WP{i+1}"
            font = renderer.font_renderer.get_font('small')
            label_surf = font.render(label, True, color)
            surface.blit(label_surf, (x + 10, y - 8))
        
        if len(drone_positions) == 0 and len(self.waypoints) == 0:
            # No data message with instructions
            no_data_text = "No data available. Ctrl+Click to add waypoints."
            text_width, text_height = renderer.measure_text(no_data_text, 'label')
            text_x = map_rect.centerx - text_width // 2
            text_y = map_rect.centery - text_height // 2
            renderer.render_text(surface, no_data_text,
                               (text_x, text_y),
                               size='label',
                               color=DesignSystem.COLORS['text_secondary'])
            
            # Additional instructions
            hint_text = "Right-click waypoint to delete | Drag to move"
            hint_width, hint_height = renderer.measure_text(hint_text, 'small')
            hint_x = map_rect.centerx - hint_width // 2
            hint_y = map_rect.centery + text_height + 10
            renderer.render_text(surface, hint_text,
                               (hint_x, hint_y),
                               size='small',
                               color=DesignSystem.COLORS['text_tertiary'])
        else:
            # Draw trajectories
            for drone_data in drone_positions:
                if len(drone_data.get('trajectory', [])) > 1:
                    points = []
                    for lat, lon, alt in drone_data['trajectory']:
                        x, y = self._latlon_to_screen(lat, lon, map_rect,
                                                     min_lat, max_lat, min_lon, max_lon)
                        points.append((x, y))
                    
                    if len(points) > 1:
                        color = DesignSystem.COLORS['primary']
                        if drone_data['id'] == self.current_drone_id:
                            color = DesignSystem.COLORS['accent']
                        pygame.draw.lines(surface, color, False, points, 2)
            
            # Draw drone positions
            for drone_data in drone_positions:
                x, y = self._latlon_to_screen(drone_data['lat'], drone_data['lon'], map_rect,
                                             min_lat, max_lat, min_lon, max_lon)
                
                # Draw drone with radar-style indicator
                color = DesignSystem.COLORS['success']
                if drone_data['id'] == self.current_drone_id:
                    color = DesignSystem.COLORS['accent']
                    # Draw larger circle for selected drone
                    pygame.draw.circle(surface, color, (x, y), 12, 2)
                
                # Draw drone position
                pygame.draw.circle(surface, color, (x, y), 8)
                pygame.draw.circle(surface, DesignSystem.COLORS['bg'], (x, y), 4)
                
                # Draw direction indicator (if yaw available)
                state = drone_data.get('state')
                if state and hasattr(state, 'yaw'):
                    yaw_rad = math.radians(state.yaw)
                    dx = math.sin(yaw_rad) * 15
                    dy = -math.cos(yaw_rad) * 15
                    pygame.draw.line(surface, color, (x, y), (int(x + dx), int(y + dy)), 2)
    
    def draw(self, surface: pygame.Surface):
        """Override draw to handle coordinate transformation from Card."""
        if not self.visible:
            return
        self._draw_self(surface)
        super().draw(surface)  # Draw children if any


class JSONEditor(UIComponent):
    """Advanced JSON editor with syntax highlighting, selection, copy/paste, and more."""
    
    def __init__(self, x: int, y: int, width: int, height: int, default_text: str = ""):
        super().__init__(x, y, width, height)
        self.text = default_text
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0.0
        self.scroll_y = 0
        self.scroll_x = 0
        self.cursor_pos = [0, 0]  # [line, col]
        self.selection_start = None  # [line, col] or None
        
        # Initialize typography based on font metrics
        self._init_typography()
        
        self.line_number_width = 60  # Wider for better alignment
        self.undo_stack = []  # History for undo
        self.undo_limit = 100  # Increased undo limit
        self.clipboard = ""
        # Advanced JSON editing features
        self.auto_indent = True  # Smart indentation
        self.auto_brackets = True  # Auto-complete brackets
        self.json_error_line = None  # Track JSON syntax errors
        self.search_text = ""  # Search functionality
        self.search_positions = []  # Search result positions
        self.current_search_index = -1
        # Collapsible sections (for future expansion)
        self.collapsed_lines = set()  # Lines that are collapsed
    
    def _init_typography(self):
        """Initialize typography settings based on font metrics."""
        # Get font to measure character width
        try:
            renderer = get_renderer()
            font = renderer.font_renderer.get_font('console')
            # Measure character width using a typical character
            test_char = font.render('M', True, (255, 255, 255))
            self.char_width = test_char.get_width()
            # Line height with proper spacing
            self.line_height = max(22, test_char.get_height() + 4)  # At least 22px with 4px spacing
            self.char_spacing = 1  # Additional spacing between characters for better readability
        except:
            # Fallback values if font not available
            self.line_height = 22
            self.char_width = 9
            self.char_spacing = 1
        
    def _save_state(self):
        """Save current state for undo."""
        if len(self.undo_stack) == 0 or self.undo_stack[-1] != (self.text, self.cursor_pos):
            self.undo_stack.append((self.text, self.cursor_pos.copy()))
            if len(self.undo_stack) > self.undo_limit:
                self.undo_stack.pop(0)
    
    def _parse_json_token(self, text: str, pos: int) -> Tuple[str, int, str]:
        """Parse JSON token at position. Returns (token_type, end_pos, token_value)."""
        if pos >= len(text):
            return ("eof", pos, "")
        
        char = text[pos]
        
        # String
        if char == '"':
            end = pos + 1
            escaped = False
            while end < len(text):
                if escaped:
                    escaped = False
                    end += 1
                    continue
                if text[end] == '\\':
                    escaped = True
                    end += 1
                    continue
                if text[end] == '"':
                    return ("string", end + 1, text[pos:end+1])
                end += 1
            return ("string", len(text), text[pos:])
        
        # Number
        if char.isdigit() or char == '-' or char == '.':
            end = pos + 1
            has_dot = (char == '.')
            while end < len(text):
                c = text[end]
                if c.isdigit():
                    end += 1
                elif c == '.' and not has_dot:
                    has_dot = True
                    end += 1
                elif c in ['e', 'E']:
                    end += 1
                    if end < len(text) and text[end] in ['+', '-']:
                        end += 1
                elif c in [' ', '\n', '\t', ',', '}', ']', ':']:
                    break
                else:
                    end += 1
            return ("number", end, text[pos:end])
        
        # Boolean true
        if text[pos:pos+4] == "true" and (pos + 4 >= len(text) or text[pos+4] in [' ', '\n', '\t', ',', '}', ']']):
            return ("boolean", pos + 4, "true")
        
        # Boolean false
        if text[pos:pos+5] == "false" and (pos + 5 >= len(text) or text[pos+5] in [' ', '\n', '\t', ',', '}', ']']):
            return ("boolean", pos + 5, "false")
        
        # Null
        if text[pos:pos+4] == "null" and (pos + 4 >= len(text) or text[pos+4] in [' ', '\n', '\t', ',', '}', ']']):
            return ("null", pos + 4, "null")
        
        # Brackets and braces
        if char in ['{', '}', '[', ']']:
            return ("bracket", pos + 1, char)
        
        # Colon and comma
        if char == ':':
            return ("colon", pos + 1, char)
        if char == ',':
            return ("comma", pos + 1, char)
        
        # Whitespace
        if char in [' ', '\t']:
            end = pos + 1
            while end < len(text) and text[end] in [' ', '\t']:
                end += 1
            return ("whitespace", end, text[pos:end])
        
        # Default
        return ("text", pos + 1, char)
    
    def _get_token_color(self, token_type: str) -> Tuple[int, int, int]:
        """Get color for token type."""
        colors = {
            "string": DesignSystem.COLORS['success'],  # Green for strings
            "number": DesignSystem.COLORS['warning'],  # Amber for numbers
            "boolean": DesignSystem.COLORS['primary_light'],  # Cyan for booleans
            "null": DesignSystem.COLORS['text_tertiary'],  # Gray for null
            "bracket": DesignSystem.COLORS['primary'],  # Cyan for brackets
            "colon": DesignSystem.COLORS['text_secondary'],  # Light gray for colon
            "comma": DesignSystem.COLORS['text_tertiary'],  # Gray for comma
            "whitespace": DesignSystem.COLORS['text'],  # White for whitespace
            "text": DesignSystem.COLORS['text'],  # White for other text
        }
        return colors.get(token_type, DesignSystem.COLORS['text'])
    
    def _validate_json(self) -> Tuple[bool, Optional[int]]:
        """Validate JSON and return (is_valid, error_line)."""
        try:
            json.loads(self.text)
            return (True, None)
        except json.JSONDecodeError as e:
            # Try to extract line number from error
            lines = self.text.split('\n')
            if e.lineno and e.lineno > 0:
                return (False, e.lineno - 1)
            return (False, 0)
    
    def _get_smart_indent(self, line: str) -> int:
        """Calculate smart indentation based on JSON structure."""
        if not self.auto_indent:
            return len(line) - len(line.lstrip())
        
        # Count opening brackets and subtract closing brackets
        indent = 0
        for char in line:
            if char in ['{', '[']:
                indent += 1
            elif char in ['}', ']']:
                indent -= 1
        
        # Base indent from previous line
        base_indent = len(line) - len(line.lstrip())
        if line.rstrip().endswith(('{', '[', ':')):
            return base_indent + 4
        elif line.rstrip().endswith((',', '}')):
            return max(0, base_indent - 4)
        return base_indent
    
    def _get_selected_text(self):
        """Get selected text."""
        if self.selection_start is None:
            return ""
        lines = self.text.split('\n')
        start_line, start_col = self.selection_start
        end_line, end_col = self.cursor_pos
        
        if start_line > end_line or (start_line == end_line and start_col > end_col):
            start_line, end_line = end_line, start_line
            start_col, end_col = end_col, start_col
        
        if start_line == end_line:
            return lines[start_line][start_col:end_col]
        else:
            result = [lines[start_line][start_col:]]
            for i in range(start_line + 1, end_line):
                result.append(lines[i])
            result.append(lines[end_line][:end_col])
            return '\n'.join(result)
    
    def _delete_selection(self):
        """Delete selected text."""
        if self.selection_start is None:
            return False
        
        lines = self.text.split('\n')
        start_line, start_col = self.selection_start
        end_line, end_col = self.cursor_pos
        
        if start_line > end_line or (start_line == end_line and start_col > end_col):
            start_line, end_line = end_line, start_line
            start_col, end_col = end_col, start_col
        
        if start_line == end_line:
            lines[start_line] = lines[start_line][:start_col] + lines[start_line][end_col:]
        else:
            lines[start_line] = lines[start_line][:start_col] + lines[end_line][end_col:]
            del lines[start_line + 1:end_line + 1]
        
        self.text = '\n'.join(lines)
        self.cursor_pos = [start_line, start_col]
        self.selection_start = None
        return True
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle JSON editor events with advanced editing capabilities."""
        if not self.visible or not self.enabled:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
                # Calculate cursor position from mouse click with improved accuracy
                text_start_x = self.rect.x + self.line_number_width + DesignSystem.SPACING['sm'] * 2
                rel_x = event.pos[0] - text_start_x + self.scroll_x
                rel_y = event.pos[1] - (self.rect.y + DesignSystem.SPACING['sm']) + self.scroll_y
                click_line = max(0, int(rel_y / self.line_height))
                lines = self.text.split('\n')
                click_line = min(click_line, len(lines) - 1) if lines else 0
                
                # More accurate column calculation with character spacing
                char_width_with_spacing = self.char_width + self.char_spacing
                click_col = max(0, min(int(rel_x / char_width_with_spacing), len(lines[click_line]) if click_line < len(lines) else 0))
                self.cursor_pos = [click_line, click_col]
                
                if event.button == 1:  # Left click
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        if self.selection_start is None:
                            self.selection_start = self.cursor_pos.copy()
                    else:
                        self.selection_start = None
                elif event.button == 3:  # Right click - could add context menu
                    pass
            else:
                self.active = False
            
            # Improved mouse wheel scrolling
            if event.button == 4:  # Scroll up
                if self.rect.collidepoint(event.pos):
                    self.scroll_y = max(0, self.scroll_y - self.line_height * 3)  # Scroll 3 lines
                    self.mark_dirty()
                    return True
            elif event.button == 5:  # Scroll down
                if self.rect.collidepoint(event.pos):
                    max_scroll = max(0, len(self.text.split('\n')) * self.line_height - self.rect.height)
                    self.scroll_y = min(max_scroll, self.scroll_y + self.line_height * 3)  # Scroll 3 lines
                    self.mark_dirty()
                    return True
            return self.active
        elif event.type == pygame.KEYDOWN and self.active:
            # Handle modifier keys
            mods = pygame.key.get_mods()
            ctrl = mods & (pygame.KMOD_CTRL | pygame.KMOD_META)
            shift = mods & pygame.KMOD_SHIFT
            
            # Save state before modification
            if event.key not in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, 
                                pygame.K_HOME, pygame.K_END, pygame.K_PAGEUP, pygame.K_PAGEDOWN):
                self._save_state()
            
            lines = self.text.split('\n')
            
            # Copy/Cut/Paste
            if ctrl and event.key == pygame.K_c:
                selected = self._get_selected_text()
                if selected:
                    self.clipboard = selected
                return True
            elif ctrl and event.key == pygame.K_x:
                selected = self._get_selected_text()
                if selected:
                    self.clipboard = selected
                    self._delete_selection()
                return True
            elif ctrl and event.key == pygame.K_v:
                if self.clipboard:
                    if self._delete_selection():
                        lines = self.text.split('\n')
                    clipboard_lines = self.clipboard.split('\n')
                    if len(clipboard_lines) == 1:
                        lines[self.cursor_pos[0]] = (lines[self.cursor_pos[0]][:self.cursor_pos[1]] + 
                                                     clipboard_lines[0] + 
                                                     lines[self.cursor_pos[0]][self.cursor_pos[1]:])
                        self.cursor_pos[1] += len(clipboard_lines[0])
                    else:
                        line = lines[self.cursor_pos[0]]
                        lines[self.cursor_pos[0]] = line[:self.cursor_pos[1]] + clipboard_lines[0]
                        for i, clip_line in enumerate(clipboard_lines[1:], 1):
                            lines.insert(self.cursor_pos[0] + i, clip_line)
                        lines[self.cursor_pos[0] + len(clipboard_lines) - 1] += line[self.cursor_pos[1]:]
                        self.cursor_pos[0] += len(clipboard_lines) - 1
                        self.cursor_pos[1] = len(clipboard_lines[-1])
                    self.text = '\n'.join(lines)
                    self.selection_start = None
                return True
            elif ctrl and event.key == pygame.K_a:  # Select all
                self.selection_start = [0, 0]
                lines = self.text.split('\n')
                self.cursor_pos = [len(lines) - 1, len(lines[-1])]
                return True
            elif ctrl and event.key == pygame.K_z:  # Undo
                if self.undo_stack:
                    self.text, self.cursor_pos = self.undo_stack.pop()
                    self.selection_start = None
                return True
            
            # Delete key
            if event.key == pygame.K_DELETE:
                if self._delete_selection():
                    return True
                lines = self.text.split('\n')
                if self.cursor_pos[0] < len(lines):
                    if self.cursor_pos[1] < len(lines[self.cursor_pos[0]]):
                        lines[self.cursor_pos[0]] = (lines[self.cursor_pos[0]][:self.cursor_pos[1]] + 
                                                    lines[self.cursor_pos[0]][self.cursor_pos[1] + 1:])
                    elif self.cursor_pos[0] < len(lines) - 1:
                        lines[self.cursor_pos[0]] += lines.pop(self.cursor_pos[0] + 1)
                self.text = '\n'.join(lines)
                self.selection_start = None
                return True
            
            # Navigation with selection
            if event.key == pygame.K_UP:
                if shift and self.selection_start is None:
                    self.selection_start = self.cursor_pos.copy()
                self.cursor_pos[0] = max(0, self.cursor_pos[0] - 1)
                self.cursor_pos[1] = min(self.cursor_pos[1], len(lines[self.cursor_pos[0]]))
                if not shift:
                    self.selection_start = None
                return True
            elif event.key == pygame.K_DOWN:
                if shift and self.selection_start is None:
                    self.selection_start = self.cursor_pos.copy()
                self.cursor_pos[0] = min(len(lines) - 1, self.cursor_pos[0] + 1)
                self.cursor_pos[1] = min(self.cursor_pos[1], len(lines[self.cursor_pos[0]]))
                if not shift:
                    self.selection_start = None
                return True
            elif event.key == pygame.K_LEFT:
                if shift and self.selection_start is None:
                    self.selection_start = self.cursor_pos.copy()
                if self.cursor_pos[1] > 0:
                    self.cursor_pos[1] -= 1
                elif self.cursor_pos[0] > 0:
                    self.cursor_pos[0] -= 1
                    self.cursor_pos[1] = len(lines[self.cursor_pos[0]])
                if not shift:
                    self.selection_start = None
                return True
            elif event.key == pygame.K_RIGHT:
                if shift and self.selection_start is None:
                    self.selection_start = self.cursor_pos.copy()
                if self.cursor_pos[0] < len(lines):
                    if self.cursor_pos[1] < len(lines[self.cursor_pos[0]]):
                        self.cursor_pos[1] += 1
                    elif self.cursor_pos[0] < len(lines) - 1:
                        self.cursor_pos[0] += 1
                        self.cursor_pos[1] = 0
                if not shift:
                    self.selection_start = None
                return True
            elif event.key == pygame.K_HOME:
                if shift and self.selection_start is None:
                    self.selection_start = self.cursor_pos.copy()
                self.cursor_pos[1] = 0
                if ctrl:
                    self.cursor_pos[0] = 0
                if not shift:
                    self.selection_start = None
                return True
            elif event.key == pygame.K_END:
                if shift and self.selection_start is None:
                    self.selection_start = self.cursor_pos.copy()
                self.cursor_pos[1] = len(lines[self.cursor_pos[0]])
                if ctrl:
                    self.cursor_pos[0] = len(lines) - 1
                    self.cursor_pos[1] = len(lines[-1])
                if not shift:
                    self.selection_start = None
                return True
            elif event.key == pygame.K_PAGEUP:
                self.scroll_y = max(0, self.scroll_y - self.rect.height // 2)
                return True
            elif event.key == pygame.K_PAGEDOWN:
                self.scroll_y += self.rect.height // 2
                return True
            
            # Text editing
            lines = self.text.split('\n')
            if event.key == pygame.K_BACKSPACE:
                if self._delete_selection():
                    return True
                if self.cursor_pos[0] < len(lines):
                    if self.cursor_pos[1] > 0:
                        lines[self.cursor_pos[0]] = (lines[self.cursor_pos[0]][:self.cursor_pos[1]-1] + 
                                                    lines[self.cursor_pos[0]][self.cursor_pos[1]:])
                        self.cursor_pos[1] -= 1
                    elif self.cursor_pos[0] > 0:
                        self.cursor_pos[1] = len(lines[self.cursor_pos[0]-1])
                        lines[self.cursor_pos[0]-1] += lines.pop(self.cursor_pos[0])
                        self.cursor_pos[0] -= 1
                    self.text = '\n'.join(lines)
                self.selection_start = None
                return True
            elif event.key == pygame.K_RETURN:
                if self._delete_selection():
                    lines = self.text.split('\n')
                if self.cursor_pos[0] < len(lines):
                    line = lines[self.cursor_pos[0]]
                    # Smart indentation based on JSON structure
                    indent = self._get_smart_indent(line[:self.cursor_pos[1]])
                    lines[self.cursor_pos[0]] = line[:self.cursor_pos[1]]
                    lines.insert(self.cursor_pos[0] + 1, " " * indent + line[self.cursor_pos[1]:])
                    self.cursor_pos[0] += 1
                    self.cursor_pos[1] = indent
                    self.text = '\n'.join(lines)
                self.selection_start = None
                return True
            elif event.key == pygame.K_TAB:
                if self._delete_selection():
                    lines = self.text.split('\n')
                if self.cursor_pos[0] < len(lines):
                    lines[self.cursor_pos[0]] = (lines[self.cursor_pos[0]][:self.cursor_pos[1]] + 
                                                "    " + lines[self.cursor_pos[0]][self.cursor_pos[1]:])
                    self.cursor_pos[1] += 4
                    self.text = '\n'.join(lines)
                self.selection_start = None
                return True
            else:
                # Insert text with auto-bracket completion
                if event.unicode and event.unicode.isprintable():
                    if self._delete_selection():
                        lines = self.text.split('\n')
                    if self.cursor_pos[0] < len(lines):
                        line = lines[self.cursor_pos[0]]
                        char = event.unicode
                        
                        # Auto-complete brackets
                        if self.auto_brackets:
                            bracket_pairs = {'{': '}', '[': ']', '"': '"', "'": "'"}
                            if char in bracket_pairs:
                                # Check if we're in a string
                                before_cursor = line[:self.cursor_pos[1]]
                                in_string = False
                                escape = False
                                for c in before_cursor:
                                    if escape:
                                        escape = False
                                        continue
                                    if c == '\\':
                                        escape = True
                                        continue
                                    if c == '"':
                                        in_string = not in_string
                                
                                if not in_string or char == '"':
                                    closing = bracket_pairs[char]
                                    lines[self.cursor_pos[0]] = (line[:self.cursor_pos[1]] + char + closing + 
                                                                line[self.cursor_pos[1]:])
                                    self.cursor_pos[1] += 1  # Position cursor between brackets
                                else:
                                    lines[self.cursor_pos[0]] = (line[:self.cursor_pos[1]] + char + 
                                                                line[self.cursor_pos[1]:])
                                    self.cursor_pos[1] += 1
                            else:
                                lines[self.cursor_pos[0]] = (line[:self.cursor_pos[1]] + char + 
                                                            line[self.cursor_pos[1]:])
                                self.cursor_pos[1] += 1
                        else:
                            lines[self.cursor_pos[0]] = (line[:self.cursor_pos[1]] + char + 
                                                        line[self.cursor_pos[1]:])
                            self.cursor_pos[1] += 1
                        
                        self.text = '\n'.join(lines)
                    self.selection_start = None
                    return True
            return True
        return False
                    
    def update(self, dt: float):
        """Update cursor blink."""
        super().update(dt)
        self.cursor_timer += dt
        if self.cursor_timer > 0.5:
            was_visible = self.cursor_visible
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0.0
            if was_visible != self.cursor_visible:
                self.mark_dirty()
            
    def format_json(self):
        """Format JSON text with proper indentation and validation."""
        try:
            obj = json.loads(self.text)
            # Format with 4-space indentation and ensure_ascii=False for better Unicode support
            self.text = json.dumps(obj, indent=4, ensure_ascii=False, sort_keys=False)
            # Preserve cursor position if possible
            try:
                # Try to maintain approximate cursor position
                lines = self.text.split('\n')
                if self.cursor_pos[0] < len(lines):
                    self.cursor_pos[1] = min(self.cursor_pos[1], len(lines[self.cursor_pos[0]]))
                else:
                    self.cursor_pos = [0, 0]
            except:
                self.cursor_pos = [0, 0]
            self.json_error_line = None
            self.mark_dirty()
        except json.JSONDecodeError as e:
            # Keep the error line for highlighting
            if hasattr(e, 'lineno') and e.lineno:
                self.json_error_line = e.lineno - 1
            self.mark_dirty()
        except Exception:
            self.json_error_line = 0
            self.mark_dirty()
    
    def minify_json(self):
        """Minify JSON text (remove all whitespace)."""
        try:
            obj = json.loads(self.text)
            self.text = json.dumps(obj, separators=(',', ':'), ensure_ascii=False)
            self.cursor_pos = [0, len(self.text)]
            self.mark_dirty()
        except:
            pass
    
    def validate_json(self) -> Tuple[bool, Optional[str]]:
        """Validate JSON and return (is_valid, error_message)."""
        try:
            json.loads(self.text)
            return (True, None)
        except json.JSONDecodeError as e:
            return (False, str(e))
        except Exception as e:
            return (False, str(e))
            
    def _draw_self(self, surface: pygame.Surface):
        """Draw JSON editor with enhanced syntax highlighting, better typography, and beautiful UI."""
        renderer = self._renderer
        
        # Enhanced background with subtle gradient effect
        bg_color = DesignSystem.COLORS['surface_active'] if self.active else DesignSystem.COLORS['surface']
        
        # Draw main background with subtle border
        renderer.draw_rect(surface, self.rect, bg_color, border_radius=0)
        
        # Draw elegant border with glow effect when active
        if self.active:
            # Subtle glow border
            border_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, self.rect.height)
            pygame.draw.rect(surface, DesignSystem.COLORS['primary'], border_rect, 2)
            # Accent line at bottom
            accent_color = DesignSystem.COLORS['primary']
            pygame.draw.line(surface, accent_color,
                           (self.rect.x, self.rect.bottom - 2),
                           (self.rect.right, self.rect.bottom - 2), 3)
        else:
            # Subtle border when inactive
            pygame.draw.rect(surface, DesignSystem.COLORS['border'], self.rect, 1)
        
        # Draw line numbers area with better styling
        line_num_padding = DesignSystem.SPACING['sm']
        line_num_rect = pygame.Rect(
            self.rect.x + line_num_padding, 
            self.rect.y + line_num_padding, 
            self.line_number_width, 
            self.rect.height - line_num_padding * 2
        )
        # Darker background for line numbers
        renderer.draw_rect(surface, line_num_rect, DesignSystem.COLORS['bg_panel'], border_radius=0)
        
        # Separator line between line numbers and text
        separator_x = self.rect.x + self.line_number_width + line_num_padding
        pygame.draw.line(surface, DesignSystem.COLORS['border'],
                         (separator_x, self.rect.y + line_num_padding),
                         (separator_x, self.rect.bottom - line_num_padding), 1)
        
        # Text area with proper padding
        text_padding = DesignSystem.SPACING['sm']
        text_rect = pygame.Rect(
            separator_x + text_padding,
            self.rect.y + text_padding,
            self.rect.width - self.line_number_width - text_padding * 3,
            self.rect.height - text_padding * 2
        )
        old_clip = surface.get_clip()
        surface.set_clip(text_rect)
        
        # Ensure text is always a string
        text_str = str(self.text) if self.text is not None else ""
        lines = text_str.split('\n') if text_str else [""]
        y_offset = text_rect.y - self.scroll_y
        
        # Validate JSON and highlight error line
        is_valid, error_line = self._validate_json()
        
        # Draw selection highlight with better visibility
        if self.selection_start is not None:
            start_line, start_col = self.selection_start
            end_line, end_col = self.cursor_pos
            
            if start_line > end_line or (start_line == end_line and start_col > end_col):
                start_line, end_line = end_line, start_line
                start_col, end_col = end_col, start_col
            
            for line_idx in range(start_line, end_line + 1):
                if 0 <= line_idx < len(lines):
                    line_y = y_offset + line_idx * self.line_height
                    if line_y + self.line_height < text_rect.y or line_y > text_rect.bottom:
                        continue
                    
                    if line_idx == start_line == end_line:
                        sel_x1 = text_rect.x - self.scroll_x + start_col * (self.char_width + self.char_spacing)
                        sel_x2 = text_rect.x - self.scroll_x + end_col * (self.char_width + self.char_spacing)
                    elif line_idx == start_line:
                        sel_x1 = text_rect.x - self.scroll_x + start_col * (self.char_width + self.char_spacing)
                        sel_x2 = text_rect.right
                    elif line_idx == end_line:
                        sel_x1 = text_rect.x - self.scroll_x
                        sel_x2 = text_rect.x - self.scroll_x + end_col * (self.char_width + self.char_spacing)
                    else:
                        sel_x1 = text_rect.x - self.scroll_x
                        sel_x2 = text_rect.right
                    
                    sel_rect = pygame.Rect(sel_x1, line_y, sel_x2 - sel_x1, self.line_height)
                    # Use semi-transparent selection color
                    sel_color = (*DesignSystem.COLORS['primary'][:3], 100)
                    sel_surf = pygame.Surface((sel_rect.width, sel_rect.height), pygame.SRCALPHA)
                    sel_surf.fill(sel_color)
                    surface.blit(sel_surf, sel_rect.topleft)
        
        # Get font for rendering
        font = renderer.font_renderer.get_font('console')
        
        # Render each line with intelligent syntax highlighting
        for i, line in enumerate(lines):
            line_y = y_offset + i * self.line_height
            if line_y + self.line_height < text_rect.y:
                continue
            if line_y > text_rect.bottom:
                break
            
            # Highlight error line
            if not is_valid and error_line == i:
                error_bg = pygame.Rect(
                    text_rect.x - self.scroll_x, line_y,
                    text_rect.width, self.line_height
                )
                error_surf = pygame.Surface((error_bg.width, error_bg.height), pygame.SRCALPHA)
                error_surf.fill((*DesignSystem.COLORS['error'][:3], 30))
                surface.blit(error_surf, error_bg.topleft)
            
            # Draw line number with better alignment
            line_num_text = str(i + 1)
            line_num_surf = font.render(line_num_text, True, DesignSystem.COLORS['text_tertiary'])
            # Right-align line numbers
            line_num_x = self.rect.x + self.line_number_width - line_num_padding - line_num_surf.get_width()
            surface.blit(line_num_surf, (line_num_x, line_y))
            
            # Render line with intelligent token-based syntax highlighting
            x_pos = text_rect.x - self.scroll_x
            pos = 0
            
            while pos < len(line):
                token_type, end_pos, token_value = self._parse_json_token(line, pos)
                
                # Calculate token position
                token_start_x = x_pos + pos * (self.char_width + self.char_spacing)
                token_end_x = x_pos + end_pos * (self.char_width + self.char_spacing)
                
                # Skip if token is outside visible area
                if token_end_x < text_rect.x:
                    pos = end_pos
                    continue
                if token_start_x > text_rect.right:
                    break
                
                # Get color for token
                color = self._get_token_color(token_type)
                
                # Render token with proper spacing
                if token_type == "whitespace":
                    # Render whitespace as-is
                    for char in token_value:
                        char_surf = font.render(char, True, color)
                        surface.blit(char_surf, (x_pos + pos * (self.char_width + self.char_spacing), line_y))
                        pos += 1
                else:
                    # Render token as a whole for better performance
                    token_surf = font.render(token_value, True, color)
                    surface.blit(token_surf, (token_start_x, line_y))
                    pos = end_pos
        
        # Draw cursor with better visibility
        if self.active and self.cursor_visible:
            cursor_y = text_rect.y - self.scroll_y + self.cursor_pos[0] * self.line_height
            if text_rect.y <= cursor_y <= text_rect.bottom:
                cursor_x = text_rect.x - self.scroll_x + self.cursor_pos[1] * (self.char_width + self.char_spacing)
                if text_rect.x <= cursor_x <= text_rect.right:
                    # Draw thicker, more visible cursor
                    pygame.draw.line(surface, DesignSystem.COLORS['text'],
                                   (cursor_x, cursor_y + 2),
                                   (cursor_x, cursor_y + self.line_height - 2), 2)
        
        surface.set_clip(old_clip)
        
        # Draw JSON validation status indicator
        if not is_valid:
            status_text = "Invalid JSON"
            status_surf = font.render(status_text, True, DesignSystem.COLORS['error'])
            status_x = self.rect.right - status_surf.get_width() - DesignSystem.SPACING['sm']
            status_y = self.rect.y + DesignSystem.SPACING['sm']
            surface.blit(status_surf, (status_x, status_y))


class TopicList(Items):
    """Enhanced topic list component with optimized display for ROS topics."""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height)
        # Topic-specific properties
        self.topic_info: Dict[str, Dict[str, Any]] = {}  # Additional info per topic
        self.show_topic_type = True  # Show message type
        self.show_topic_status = True  # Show subscription status
        self.item_height = 48  # Increased height for better readability
        self.name_width_ratio = 0.45  # 45% for topic name
        self.type_width_ratio = 0.50  # 50% for message type
        self.status_width_ratio = 0.05  # 5% for status indicator
        self.header_height = 28  # Header height for topic list
    
    def set_topic_info(self, topic_name: str, info: Dict[str, Any]):
        """Set additional information for a topic.
        
        Args:
            topic_name: Name of the topic
            info: Dictionary with keys like 'subscribed', 'message_count', 'last_update', etc.
        """
        self.topic_info[topic_name] = info
        self.mark_dirty()
    
    def _get_topic_category(self, topic_name: str) -> str:
        """Get topic category for color coding."""
        if not topic_name:
            return "unknown"
        
        topic_lower = topic_name.lower()
        
        # Common ROS topic categories
        if any(x in topic_lower for x in ['cmd', 'command', 'control']):
            return "control"
        elif any(x in topic_lower for x in ['status', 'state', 'health']):
            return "status"
        elif any(x in topic_lower for x in ['image', 'camera', 'video']):
            return "image"
        elif any(x in topic_lower for x in ['point', 'cloud', 'lidar']):
            return "pointcloud"
        elif any(x in topic_lower for x in ['pose', 'position', 'odom']):
            return "pose"
        elif any(x in topic_lower for x in ['goal', 'target', 'waypoint']):
            return "goal"
        elif any(x in topic_lower for x in ['battery', 'power', 'voltage']):
            return "battery"
        elif any(x in topic_lower for x in ['gps', 'nav', 'location']):
            return "navigation"
        else:
            return "default"
    
    def _get_category_color(self, category: str) -> Tuple[int, int, int]:
        """Get color for topic category."""
        colors = {
            "control": DesignSystem.COLORS['primary'],
            "status": DesignSystem.COLORS['success'],
            "image": DesignSystem.COLORS['accent'],
            "pointcloud": DesignSystem.COLORS['warning'],
            "pose": DesignSystem.COLORS['primary_light'],
            "goal": DesignSystem.COLORS['error'],
            "battery": DesignSystem.COLORS['warning'],
            "navigation": DesignSystem.COLORS['success'],
            "default": DesignSystem.COLORS['text_secondary'],
            "unknown": DesignSystem.COLORS['text_tertiary']
        }
        return colors.get(category, DesignSystem.COLORS['text_secondary'])
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle topic list events with correct click position calculation."""
        if not self.visible or not self.enabled:
            return False
        
        # Calculate content area (excluding search box if shown)
        search_height = 0
        if self.show_search:
            search_height = 32 + DesignSystem.SPACING['sm'] * 2
        
        # Calculate header height (only if there are items)
        header_height = 0
        if self.filtered_items:
            header_height = self.header_height + DesignSystem.SPACING['xs']
        
        # Calculate padding offsets
        horizontal_padding = DesignSystem.SPACING['md']
        vertical_padding = DesignSystem.SPACING['sm']
        
        # Calculate actual content area where items are drawn
        content_y = self.rect.y + search_height + vertical_padding + header_height
        content_height = self.rect.height - search_height - vertical_padding * 2 - header_height
        content_rect = pygame.Rect(
            self.rect.x + horizontal_padding,
            content_y,
            self.rect.width - horizontal_padding * 2,
            content_height
        )
        
        if event.type == pygame.MOUSEMOTION:
            if content_rect.collidepoint(event.pos):
                rel_y = event.pos[1] - content_rect.y
                index = (rel_y + self.scroll_y) // self.item_height
                if 0 <= index < len(self.filtered_items):
                    self.hovered_index = index
                    self.mark_dirty()
                else:
                    self.hovered_index = -1
                    self.mark_dirty()
            else:
                if self.hovered_index != -1:
                    self.hovered_index = -1
                    self.mark_dirty()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if content_rect.collidepoint(event.pos):
                rel_y = event.pos[1] - content_rect.y
                index = (rel_y + self.scroll_y) // self.item_height
                if 0 <= index < len(self.filtered_items):
                    self.selected_index = index
                    # Emit selection signal
                    self.emit_signal('select', {'index': index, 'item': self.filtered_items[index]})
                    self.emit_signal('on_select', self.filtered_items[index])
                    if self.on_select:
                        self.on_select(self.filtered_items[index])
                    self.mark_dirty()
                    return True
            elif event.button == 4:  # Scroll up
                if self.rect.collidepoint(event.pos):
                    self.scroll_y = max(0, self.scroll_y - self.item_height * 2)
                    self.mark_dirty()
                    return True
            elif event.button == 5:  # Scroll down
                if self.rect.collidepoint(event.pos):
                    max_scroll = max(0, len(self.filtered_items) * self.item_height - content_height)
                    self.scroll_y = min(max_scroll, self.scroll_y + self.item_height * 2)
                    self.mark_dirty()
                    return True
        elif event.type == pygame.KEYDOWN:
            # Keyboard navigation
            if self.selected_index >= 0:
                if event.key == pygame.K_UP:
                    self.selected_index = max(0, self.selected_index - 1)
                    self._ensure_visible(self.selected_index)
                    self.mark_dirty()
                    return True
                elif event.key == pygame.K_DOWN:
                    self.selected_index = min(len(self.filtered_items) - 1, self.selected_index + 1)
                    self._ensure_visible(self.selected_index)
                    self.mark_dirty()
                    return True
                elif event.key == pygame.K_RETURN:
                    if 0 <= self.selected_index < len(self.filtered_items):
                        self.emit_signal('select', {'index': self.selected_index, 'item': self.filtered_items[self.selected_index]})
                        if self.on_select:
                            self.on_select(self.filtered_items[self.selected_index])
                        return True
        return False
    
    def _ensure_visible(self, index: int):
        """Ensure selected item is visible by adjusting scroll, accounting for header."""
        # Calculate content area (excluding search box if shown)
        search_height = 0
        if self.show_search:
            search_height = 32 + DesignSystem.SPACING['sm'] * 2
        
        # Calculate header height (only if there are items)
        header_height = 0
        if self.filtered_items:
            header_height = self.header_height + DesignSystem.SPACING['xs']
        
        # Calculate padding offsets
        vertical_padding = DesignSystem.SPACING['sm']
        
        # Calculate actual content height
        content_height = self.rect.height - search_height - vertical_padding * 2 - header_height
        
        item_y = index * self.item_height
        visible_top = self.scroll_y
        visible_bottom = self.scroll_y + content_height
        
        if item_y < visible_top:
            self.scroll_y = item_y
        elif item_y + self.item_height > visible_bottom:
            self.scroll_y = item_y + self.item_height - content_height
    
    def _draw_self(self, surface: pygame.Surface):
        """Draw enhanced topic list with optimized layout and spacing."""
        renderer = self._renderer
        
        # Draw modern flat background
        renderer.draw_rect(surface, self.rect,
                         DesignSystem.COLORS['surface'],
                         border_radius=0)
        
        # Draw search box if enabled
        content_y = self.rect.y
        content_height = self.rect.height
        if self.show_search:
            search_rect = pygame.Rect(
                self.rect.x + DesignSystem.SPACING['sm'],
                self.rect.y + DesignSystem.SPACING['sm'],
                self.rect.width - DesignSystem.SPACING['sm'] * 2,
                32
            )
            renderer.draw_rect(surface, search_rect,
                             DesignSystem.COLORS['bg_panel'],
                             border_radius=0)
            search_display = self.search_text if self.search_text else "Search topics..."
            search_color = DesignSystem.COLORS['text'] if self.search_text else DesignSystem.COLORS['text_tertiary']
            renderer.render_text(surface, search_display,
                               (search_rect.x + DesignSystem.SPACING['sm'], 
                                search_rect.y + (search_rect.height - 16) // 2),
                               size='small',
                               color=search_color)
            content_y = search_rect.bottom + DesignSystem.SPACING['sm']
            content_height = self.rect.bottom - content_y
        
        # Clip to item area with proper padding
        horizontal_padding = DesignSystem.SPACING['md']
        vertical_padding = DesignSystem.SPACING['sm']
        clip_rect = pygame.Rect(
            self.rect.x + horizontal_padding,
            content_y + vertical_padding,
            self.rect.width - horizontal_padding * 2,
            content_height - vertical_padding * 2
        )
        old_clip = surface.get_clip()
        surface.set_clip(clip_rect)
        
        # Draw header if there are items
        if self.filtered_items:
            header_y = clip_rect.y
            header_height = 28
            header_rect = pygame.Rect(clip_rect.x, header_y, clip_rect.width, header_height)
            
            # Header background
            renderer.draw_rect(surface, header_rect,
                             DesignSystem.COLORS['bg_panel'],
                             border_radius=0)
            
            # Header text
            header_font = renderer.font_renderer.get_font('small')
            name_header = "Topic Name"
            type_header = "Message Type"
            
            name_header_surf = header_font.render(name_header, True, DesignSystem.COLORS['text_tertiary'])
            type_header_surf = header_font.render(type_header, True, DesignSystem.COLORS['text_tertiary'])
            
            name_header_x = clip_rect.x + DesignSystem.SPACING['sm']
            type_header_x = clip_rect.x + int(clip_rect.width * self.name_width_ratio) + DesignSystem.SPACING['md']
            
            surface.blit(name_header_surf, (name_header_x, header_y + (header_height - name_header_surf.get_height()) // 2))
            surface.blit(type_header_surf, (type_header_x, header_y + (header_height - type_header_surf.get_height()) // 2))
            
            # Separator line
            separator_y = header_rect.bottom
            pygame.draw.line(surface, DesignSystem.COLORS['border'],
                           (clip_rect.x, separator_y),
                           (clip_rect.right, separator_y), 1)
            
            clip_rect.y += header_height + DesignSystem.SPACING['xs']
            clip_rect.height -= header_height + DesignSystem.SPACING['xs']
        
        # Draw items count if filtered
        if self.search_text and len(self.filtered_items) != len(self.items):
            count_text = f"{len(self.filtered_items)}/{len(self.items)}"
            count_surf = renderer.font_renderer.get_font('small').render(
                count_text, True, DesignSystem.COLORS['text_tertiary']
            )
            count_x = clip_rect.right - count_surf.get_width() - DesignSystem.SPACING['xs']
            count_y = clip_rect.y + DesignSystem.SPACING['xs']
            surface.blit(count_surf, (count_x, count_y))
        
        # Calculate layout with proper spacing
        item_padding = DesignSystem.SPACING['sm']
        name_area_width = int(clip_rect.width * self.name_width_ratio)
        type_area_width = int(clip_rect.width * self.type_width_ratio)
        status_area_width = clip_rect.width - name_area_width - type_area_width - item_padding * 3
        
        y_offset = clip_rect.y - self.scroll_y
        for i, (topic_name, topic_type) in enumerate(self.filtered_items):
            item_y = y_offset + i * self.item_height
            if item_y + self.item_height < clip_rect.y:
                continue
            if item_y > clip_rect.bottom:
                break
            
            item_rect = pygame.Rect(clip_rect.x, item_y, clip_rect.width, self.item_height)
            
            # Determine item background color
            if i == self.selected_index:
                bg_color = DesignSystem.COLORS['primary']
                text_color = DesignSystem.COLORS['text']
                # Draw selection indicator
                indicator_rect = pygame.Rect(item_rect.x, item_rect.y, 3, item_rect.height)
                renderer.draw_rect(surface, indicator_rect,
                                 DesignSystem.COLORS['primary_light'],
                                 border_radius=0)
            elif i == self.hovered_index:
                bg_color = DesignSystem.COLORS['surface_hover']
                text_color = DesignSystem.COLORS['text']
            else:
                # Alternating row colors
                if i % 2 == 0:
                    bg_color = DesignSystem.COLORS['surface']
                else:
                    bg_color = DesignSystem.COLORS['surface_light']
                text_color = DesignSystem.COLORS['text_secondary']
            
            # Draw item background
            renderer.draw_rect(surface, item_rect, bg_color, border_radius=0)
            
            # Draw topic name with category color indicator
            name_x = item_rect.x + item_padding
            name_y = item_rect.y + DesignSystem.SPACING['xs']
            
            # Category color indicator (small square)
            category = self._get_topic_category(topic_name)
            category_color = self._get_category_color(category)
            indicator_size = 4
            indicator_rect = pygame.Rect(name_x, name_y, indicator_size, indicator_size)
            renderer.draw_rect(surface, indicator_rect, category_color, border_radius=0)
            
            # Topic name
            name_text_x = name_x + indicator_size + DesignSystem.SPACING['xs']
            name_max_width = name_area_width - indicator_size - DesignSystem.SPACING['xs'] - item_padding
            
            # Truncate topic name if too long
            display_name = topic_name
            name_width = renderer.measure_text(topic_name, 'label')[0]
            if name_width > name_max_width:
                ellipsis_width = renderer.measure_text("...", 'label')[0]
                max_name_width = name_max_width - ellipsis_width
                while renderer.measure_text(display_name, 'label')[0] > max_name_width and len(display_name) > 0:
                    display_name = display_name[:-1]
                display_name = display_name + "..."
            
            renderer.render_text(surface, display_name,
                               (name_text_x, name_y),
                               size='label',
                               color=text_color)
            
            # Message type (if available)
            if self.show_topic_type and topic_type:
                type_x = item_rect.x + name_area_width + item_padding
                type_y = item_rect.y + DesignSystem.SPACING['xs']
                type_max_width = type_area_width - item_padding
                
                # Truncate type if too long
                display_type = topic_type
                type_width = renderer.measure_text(topic_type, 'small')[0]
                if type_width > type_max_width:
                    ellipsis_width = renderer.measure_text("...", 'small')[0]
                    max_type_width = type_max_width - ellipsis_width
                    while renderer.measure_text(display_type, 'small')[0] > max_type_width and len(display_type) > 0:
                        display_type = display_type[:-1]
                    display_type = display_type + "..."
                
                type_font = renderer.font_renderer.get_font('small')
                type_surf = type_font.render(display_type, True, DesignSystem.COLORS['text_tertiary'])
                surface.blit(type_surf, (type_x, type_y))
            
            # Status indicator (if subscribed/active)
            if self.show_topic_status:
                status_x = item_rect.right - status_area_width - item_padding
                status_y = item_rect.y + (self.item_height - 8) // 2
                
                topic_info = self.topic_info.get(topic_name, {})
                is_subscribed = topic_info.get('subscribed', False)
                is_active = topic_info.get('active', False)
                
                if is_subscribed or is_active:
                    # Draw active indicator (small circle)
                    status_color = DesignSystem.COLORS['success'] if is_active else DesignSystem.COLORS['warning']
                    pygame.draw.circle(surface, status_color, (status_x, status_y), 4)
                else:
                    # Draw inactive indicator (hollow circle)
                    pygame.draw.circle(surface, DesignSystem.COLORS['text_tertiary'], (status_x, status_y), 3, 1)
            
            # Subtle separator line between items
            if i < len(self.filtered_items) - 1:
                separator_y = item_rect.bottom
                separator_color = tuple(max(0, c - 10) for c in bg_color)
                pygame.draw.line(surface, separator_color,
                               (item_rect.x + item_padding, separator_y),
                               (item_rect.right - item_padding, separator_y), 1)
        
        surface.set_clip(old_clip)
        
        # Draw scrollbar if needed
        if len(self.filtered_items) * self.item_height > clip_rect.height:
            scrollbar_width = 6
            scrollbar_x = self.rect.right - scrollbar_width - 2
            total_content_height = len(self.filtered_items) * self.item_height
            scrollbar_height = max(20, int(clip_rect.height * (clip_rect.height / total_content_height)))
            scrollbar_y = content_y + int(self.scroll_y / total_content_height * clip_rect.height)
            scrollbar_rect = pygame.Rect(scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height)
            renderer.draw_rect(surface, scrollbar_rect,
                             DesignSystem.COLORS['border'],
                             border_radius=0)
        
        # Draw empty state message
        if not self.filtered_items:
            empty_text = "No topics available"
            if self.search_text:
                empty_text = f"No topics match '{self.search_text}'"
            
            text_width, text_height = renderer.measure_text(empty_text, 'label')
            text_x = self.rect.centerx - text_width // 2
            text_y = self.rect.centery - text_height // 2
            renderer.render_text(surface, empty_text,
                               (text_x, text_y),
                               size='label',
                               color=DesignSystem.COLORS['text_tertiary'])

