"""Status tab implementation."""
import pygame
from typing import Dict, Any

from .base_tab import BaseTab
from ..components import Label, Card, Field, ImageDisplayComponent, PointCloudDisplayComponent
from ..design.design_system import DesignSystem

# Check for optional dependencies
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    import numpy as np
    HAS_POINTCLOUD = True
except ImportError:
    HAS_POINTCLOUD = False


class StatusTab(BaseTab):
    """Status monitoring tab with camera and point cloud."""
    
    def __init__(self, screen: pygame.Surface, screen_width: int, screen_height: int,
                 components: Dict[str, Any]):
        """Initialize status tab.
        
        Args:
            screen: Pygame surface to draw on
            screen_width: Screen width
            screen_height: Screen height
            components: Dictionary of UI components
        """
        super().__init__(screen, screen_width, screen_height)
        self.components = components
        
    def draw(self, app_state: Dict[str, Any]):
        """Draw status tab."""
        y = self.tab_height + DesignSystem.SPACING['lg']
        
        # Title with connection indicator
        title_label = Label(50, y, "Status Monitoring", 'title',
                           DesignSystem.COLORS['text'])
        title_label.draw(self.screen)
        
        # Connection indicator
        current_drone_id = app_state.get('current_drone_id')
        drones = app_state.get('drones', {})
        current_connected = False
        if current_drone_id:
            drone_info = drones.get(current_drone_id)
            if drone_info:
                current_connected = drone_info.get('is_connected', False)
        
        indicator_color = (DesignSystem.COLORS['success'] if current_connected 
                          else DesignSystem.COLORS['error'])
        indicator_text = "Connected" if current_connected else "Disconnected"
        indicator_label = Label(self.screen_width - 200, y, indicator_text, 'label', indicator_color)
        indicator_label.draw(self.screen)
        y += 50
        
        # Status fields
        status_fields_data = [
            ("Connection", "connected"),
            ("Armed", "armed"),
            ("Mode", "mode"),
            ("Battery", "battery"),
            ("Latitude", "latitude"),
            ("Longitude", "longitude"),
            ("Altitude", "altitude"),
            ("Roll", "roll"),
            ("Pitch", "pitch"),
            ("Yaw", "yaw"),
            ("Landed", "landed"),
            ("Reached", "reached"),
            ("Returned", "returned"),
            ("Tookoff", "tookoff"),
        ]
        
        x_start = 50
        x_offset = (self.screen_width - 100) // 2
        card_width = x_offset - DesignSystem.SPACING['md']
        card_height = 40
        
        status_y = y
        status_fields = self.components.get('status_fields', {})
        status_data = app_state.get('status_data', {})
        
        for i, (label, field_key) in enumerate(status_fields_data):
            x = x_start if i % 2 == 0 else x_start + x_offset
            row = i // 2
            card_y = status_y + row * (card_height + DesignSystem.SPACING['sm'])
            
            if field_key not in status_fields:
                value, color = self._get_status_value(field_key, status_data)
                status_fields[field_key] = Field(x, card_y, card_width, card_height, label, value, color)
            else:
                value, color = self._get_status_value(field_key, status_data)
                status_fields[field_key].set_value(value, color)
            
            status_fields[field_key].draw(self.screen)
        
        # Calculate bottom of status fields
        status_bottom = status_y + ((len(status_fields_data) + 1) // 2) * (card_height + DesignSystem.SPACING['sm'])
        y = status_bottom + DesignSystem.SPACING['xl']
        
        # Camera and Point Cloud display (side by side)
        display_height = self.screen_height - y - 20
        gap = DesignSystem.SPACING['lg']
        total_width = self.screen_width - 100
        display_width = (total_width - gap) // 2
        
        # Camera display (left)
        if HAS_CV2:
            camera_card = Card(50, y, display_width, display_height, "Camera Feed")
            content_area = camera_card.get_content_area()
            
            img_padding = DesignSystem.SPACING['md']
            image_display = self.components.get('status_image_display')
            if image_display:
                image_display.rect.x = img_padding
                image_display.rect.y = img_padding
                image_display.rect.width = content_area.width - img_padding * 2
                image_display.rect.height = content_area.height - img_padding * 2
                image_display.set_image(app_state.get('current_image'))
                camera_card.add_child(image_display)
            
            camera_card.draw(self.screen)
        
        # Point Cloud display (right)
        if HAS_POINTCLOUD:
            pc_x = 50 + display_width + gap
            status_pc_card = self.components.get('status_pc_card')
            if not status_pc_card:
                status_pc_card = Card(pc_x, y, display_width, display_height, "Point Cloud")
                self.components['status_pc_card'] = status_pc_card
            else:
                status_pc_card.rect.x = pc_x
                status_pc_card.rect.y = y
                status_pc_card.rect.width = display_width
                status_pc_card.rect.height = display_height
                status_pc_card.children.clear()
            
            content_area = status_pc_card.get_content_area()
            pc_padding = DesignSystem.SPACING['md']
            pointcloud_display = self.components.get('status_pointcloud_display')
            if pointcloud_display:
                pointcloud_display.rect.x = pc_padding
                pointcloud_display.rect.y = pc_padding
                pointcloud_display.rect.width = content_area.width - pc_padding * 2
                pointcloud_display.rect.height = content_area.height - pc_padding * 2
                pointcloud_display.title = ""
                pointcloud_display.set_pointcloud(app_state.get('pc_surface_simple'))
                pc_camera = app_state.get('pc_camera', (0.0, 0.0, 1.0))
                pointcloud_display.set_camera(pc_camera[0], pc_camera[1], pc_camera[2])
                status_pc_card.add_child(pointcloud_display)
            
            status_pc_card.draw(self.screen)
    
    def _get_status_value(self, field_key: str, status_data: Dict[str, Any]):
        """Get status value and color for a field."""
        if field_key in status_data:
            return status_data[field_key]
        defaults = {
            "connected": ("N/A", DesignSystem.COLORS['text_tertiary']),
            "armed": ("N/A", DesignSystem.COLORS['text_tertiary']),
            "mode": ("N/A", DesignSystem.COLORS['text_tertiary']),
            "battery": ("N/A", DesignSystem.COLORS['text_tertiary']),
            "latitude": ("N/A", DesignSystem.COLORS['text_tertiary']),
            "longitude": ("N/A", DesignSystem.COLORS['text_tertiary']),
            "altitude": ("N/A", DesignSystem.COLORS['text_tertiary']),
            "roll": ("N/A", DesignSystem.COLORS['text_tertiary']),
            "pitch": ("N/A", DesignSystem.COLORS['text_tertiary']),
            "yaw": ("N/A", DesignSystem.COLORS['text_tertiary']),
            "landed": ("N/A", DesignSystem.COLORS['text_tertiary']),
            "reached": ("N/A", DesignSystem.COLORS['text_tertiary']),
            "returned": ("N/A", DesignSystem.COLORS['text_tertiary']),
            "tookoff": ("N/A", DesignSystem.COLORS['text_tertiary']),
        }
        return defaults.get(field_key, ("N/A", DesignSystem.COLORS['text_tertiary']))
    
    def handle_event(self, event: pygame.event.Event, app_state: Dict[str, Any]) -> bool:
        """Handle status tab events."""
        # Handle point cloud controls through Card
        if HAS_POINTCLOUD:
            status_pc_card = self.components.get('status_pc_card')
            if status_pc_card and status_pc_card.handle_event(event):
                # Sync camera angles from component
                pointcloud_display = self.components.get('status_pointcloud_display')
                if pointcloud_display:
                    angle_x, angle_y, zoom = pointcloud_display.get_camera()
                    app_state['pc_camera'] = (angle_x, angle_y, zoom)
                return True
        return False
    
    def update(self, dt: float, app_state: Dict[str, Any]):
        """Update status tab."""
        if HAS_POINTCLOUD:
            pointcloud_display = self.components.get('status_pointcloud_display')
            if pointcloud_display:
                pointcloud_display.update(dt)

