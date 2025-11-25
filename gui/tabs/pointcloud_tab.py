"""Point cloud tab implementation with optimized rendering."""
import pygame
import math
from typing import Dict, Any

from .base_tab import BaseTab
from ..components import Label, Card, PointCloudDisplayComponent
from ..layout import LayoutManager
from ..renderers import PointCloudRenderer, HAS_POINTCLOUD
from ..design.design_system import DesignSystem
from ..renderers.ui_renderer import get_renderer


class PointCloudTab(BaseTab):
    """Point cloud display tab."""
    
    def __init__(self, screen: pygame.Surface, screen_width: int, screen_height: int,
                 components: Dict[str, Any]):
        """Initialize point cloud tab.
        
        Args:
            screen: Pygame surface to draw on
            screen_width: Screen width
            screen_height: Screen height
            components: Dictionary of UI components
        """
        super().__init__(screen, screen_width, screen_height)
        self.components = components
        self.layout = LayoutManager(screen_width, screen_height)
        self.renderer = get_renderer()
        
    def draw(self, app_state: Dict[str, Any]):
        """Draw point cloud tab."""
        # Get content area using layout manager
        content_area = self.layout.get_content_area()
        
        # Calculate header area with title and subtitle
        subtitle_text = "Use mouse to rotate, scroll to zoom, click cube to change view"
        header_rect, header_height = self.layout.calculate_header_area(
            content_area, 
            "Point Cloud Display",
            subtitle_text
        )
        
        # Draw title and subtitle
        title_label = Label(header_rect.x, header_rect.y, "Point Cloud Display", 
                           'title', DesignSystem.COLORS['text'])
        title_label.draw(self.screen)
        
        title_height = self.renderer.measure_text("Point Cloud Display", 'title')[1]
        subtitle_label = Label(header_rect.x, 
                              header_rect.y + title_height + DesignSystem.SPACING['sm'],
                              subtitle_text, 'small', DesignSystem.COLORS['text_tertiary'])
        subtitle_label.draw(self.screen)
        
        # Calculate component area
        component_rect = self.layout.calculate_component_area(content_area, header_height, min_height=200)
        
        if not HAS_POINTCLOUD:
            # Enhanced error display using Card
            error_card_height = 200
            error_card = Card(component_rect.x, component_rect.y, component_rect.width, 
                            error_card_height, "Point Cloud Not Available")
            error_card.draw(self.screen)
            
            # Calculate error message positions using layout
            error_content_area = self.layout.calculate_inner_content_area(
                error_card.rect, has_title=True, padding='md'
            )
            error_center_x = error_content_area.centerx
            error_y = error_content_area.y + DesignSystem.SPACING['lg']
            
            error_label = Label(error_center_x, error_y,
                              "Point cloud display requires numpy and point cloud data",
                              'label', DesignSystem.COLORS['error'])
            error_label.align = 'center'
            error_label.draw(self.screen)
            
            label_height = self.renderer.measure_text("Point cloud display requires numpy and point cloud data", 'label')[1]
            install_label = Label(error_center_x, 
                                error_y + label_height + DesignSystem.SPACING['sm'],
                                "Please ensure numpy is installed: pip install numpy",
                                'small', DesignSystem.COLORS['text_tertiary'])
            install_label.align = 'center'
            install_label.draw(self.screen)
            return
        
        # Create Card to manage point cloud component
        pc_card = self.components.get('pc_card')
        if not pc_card:
            pc_card = Card(component_rect.x, component_rect.y, component_rect.width, 
                          component_rect.height, "Point Cloud 3D View")
            self.components['pc_card'] = pc_card
        else:
            pc_card.rect.x = component_rect.x
            pc_card.rect.y = component_rect.y
            pc_card.rect.width = component_rect.width
            pc_card.rect.height = component_rect.height
            pc_card.children.clear()
        
        # Get Card's content area
        card_content_area = pc_card.get_content_area()
        
        # Set point cloud component position and size
        component_padding = DesignSystem.SPACING['sm']
        pointcloud_display = self.components.get('pointcloud_display')
        if pointcloud_display:
            pointcloud_display.visible = True
            pointcloud_display.enabled = True
            pointcloud_display.rect.x = component_padding
            pointcloud_display.rect.y = component_padding
            pointcloud_display.rect.width = card_content_area.width - component_padding * 2
            pointcloud_display.rect.height = card_content_area.height - component_padding * 2
            pointcloud_display.title = ""
            
            # Update point cloud data and camera
            pc_camera = app_state.get('pc_camera', (0.0, 0.0, 1.0))
            pointcloud_display.set_pointcloud(app_state.get('pc_surface_simple'))
            pointcloud_display.set_camera(pc_camera[0], pc_camera[1], pc_camera[2])
            
            # Calculate renderer size
            if pointcloud_display.rect.width > 0 and pointcloud_display.rect.height > 0:
                component_inner_area = self.layout.calculate_inner_content_area(
                    pygame.Rect(0, 0, pointcloud_display.rect.width, pointcloud_display.rect.height),
                    has_title=False, 
                    padding='sm'
                )
                renderer_width, renderer_height = self.layout.calculate_renderer_size(component_inner_area)
                
                # Create or update renderer if needed
                if pointcloud_display.renderer is None:
                    from ..renderers import PointCloudRenderer
                    pointcloud_display.renderer = PointCloudRenderer(
                        width=renderer_width, 
                        height=renderer_height
                    )
                elif (pointcloud_display.renderer.width != renderer_width or 
                      pointcloud_display.renderer.height != renderer_height):
                    pointcloud_display.renderer.width = renderer_width
                    pointcloud_display.renderer.height = renderer_height
            
            pc_card.add_child(pointcloud_display)
        
        # Draw Card
        pc_card.draw(self.screen)
        
        # Draw status indicator overlay
        indicator_height = 24
        indicator_width = 90
        indicator_y = component_padding + DesignSystem.SPACING['sm']
        
        if indicator_y + indicator_height <= card_content_area.height:
            indicator_abs_x = pc_card.rect.right - DesignSystem.SPACING['md'] - indicator_width
            indicator_abs_y = pc_card.rect.y + LayoutManager.CARD_TITLE_HEIGHT + indicator_y
            
            if (indicator_abs_x >= pc_card.rect.x and 
                indicator_abs_y >= pc_card.rect.y + LayoutManager.CARD_TITLE_HEIGHT and
                indicator_abs_x + indicator_width <= pc_card.rect.right and
                indicator_abs_y + indicator_height <= pc_card.rect.bottom):
                
                pc_surface_simple = app_state.get('pc_surface_simple')
                if pc_surface_simple is not None:
                    # Draw "Live" indicator
                    indicator_rect = pygame.Rect(indicator_abs_x, indicator_abs_y, indicator_width, indicator_height)
                    self.renderer.draw_rect(self.screen, indicator_rect,
                                           DesignSystem.COLORS['success'],
                                           border_radius=DesignSystem.RADIUS['sm'],
                                           alpha=180)
                    self.renderer.draw_rect(self.screen, indicator_rect,
                                           DesignSystem.COLORS['success'],
                                           border_radius=DesignSystem.RADIUS['sm'],
                                           width=1)
                    
                    live_text = "● LIVE"
                    live_width, live_height = self.renderer.measure_text(live_text, 'small')
                    live_x = indicator_rect.centerx - live_width // 2
                    live_y = indicator_rect.centery - live_height // 2
                    self.renderer.render_text(self.screen, live_text,
                                            (live_x, live_y),
                                            size='small',
                                            color=DesignSystem.COLORS['text'])
                else:
                    # Draw "Waiting" indicator
                    indicator_rect = pygame.Rect(indicator_abs_x, indicator_abs_y, indicator_width, indicator_height)
                    self.renderer.draw_rect(self.screen, indicator_rect,
                                           DesignSystem.COLORS['text_tertiary'],
                                           border_radius=DesignSystem.RADIUS['sm'],
                                           alpha=180)
                    self.renderer.draw_rect(self.screen, indicator_rect,
                                           DesignSystem.COLORS['border'],
                                           border_radius=DesignSystem.RADIUS['sm'],
                                           width=1)
                    
                    wait_text = "WAITING"
                    wait_width, wait_height = self.renderer.measure_text(wait_text, 'small')
                    wait_x = indicator_rect.centerx - wait_width // 2
                    wait_y = indicator_rect.centery - wait_height // 2
                    self.renderer.render_text(self.screen, wait_text,
                                            (wait_x, wait_y),
                                            size='small',
                                            color=DesignSystem.COLORS['text_tertiary'])
    
    def handle_event(self, event: pygame.event.Event, app_state: Dict[str, Any]) -> bool:
        """Handle point cloud tab events."""
        # Handle events through Card first
        pc_card = self.components.get('pc_card')
        if pc_card and pc_card.handle_event(event):
            # Sync camera angles from component
            pointcloud_display = self.components.get('pointcloud_display')
            if pointcloud_display:
                angle_x, angle_y, zoom = pointcloud_display.get_camera()
                app_state['pc_camera'] = (angle_x, angle_y, zoom)
            return True
        
        # Handle mouse interactions
        if hasattr(event, 'pos') and pc_card and pc_card.rect.collidepoint(event.pos):
            pc_last_interaction_time = app_state.get('pc_last_interaction_time', 0.0)
            pc_interaction_throttle = app_state.get('pc_interaction_throttle', 0.016)
            current_time = pygame.time.get_ticks() / 1000.0
            
            if current_time - pc_last_interaction_time < pc_interaction_throttle:
                return False
            
            pointcloud_display = self.components.get('pointcloud_display')
            if not pointcloud_display:
                return False
            
            # Convert event position to component's coordinate system
            card_content_area = pc_card.get_content_area()
            rel_x = event.pos[0] - card_content_area.x
            rel_y = event.pos[1] - card_content_area.y
            
            if pointcloud_display.rect.collidepoint((rel_x, rel_y)):
                pc_camera = app_state.get('pc_camera', (0.0, 0.0, 1.0))
                angle_x, angle_y, zoom = pc_camera
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:  # Scroll up - zoom in
                        zoom = min(3.0, zoom * 1.1)
                        pointcloud_display.set_camera(angle_x, angle_y, zoom)
                        app_state['pc_camera'] = (angle_x, angle_y, zoom)
                        app_state['pc_last_interaction_time'] = current_time
                        return True
                    elif event.button == 5:  # Scroll down - zoom out
                        zoom = max(0.1, zoom / 1.1)
                        pointcloud_display.set_camera(angle_x, angle_y, zoom)
                        app_state['pc_camera'] = (angle_x, angle_y, zoom)
                        app_state['pc_last_interaction_time'] = current_time
                        return True
                elif event.type == pygame.MOUSEMOTION and hasattr(event, 'buttons') and event.buttons[0]:
                    if hasattr(event, 'rel'):
                        angle_y += event.rel[0] * 0.01
                        angle_x += event.rel[1] * 0.01
                        angle_x = max(-math.pi/2, min(math.pi/2, angle_x))
                        pointcloud_display.set_camera(angle_x, angle_y, zoom)
                        app_state['pc_camera'] = (angle_x, angle_y, zoom)
                        app_state['pc_last_interaction_time'] = current_time
                        return True
        
        return False
    
    def update(self, dt: float, app_state: Dict[str, Any]):
        """Update point cloud tab."""
        pointcloud_display = self.components.get('pointcloud_display')
        if pointcloud_display:
            pointcloud_display.update(dt)

