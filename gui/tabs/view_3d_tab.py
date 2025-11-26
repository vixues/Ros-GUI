"""3D view tab implementation using Open3D with optimized rendering."""
import pygame
import time
from typing import Dict, Any, Optional, Tuple
import math

from .base_tab import BaseTab
from ..components import Label, Card
from ..design.design_system import DesignSystem
from ..renderers.ui_renderer import get_renderer
from ..renderers.realtime_optimizer import get_optimizer

# Check for optional dependencies
try:
    import open3d as o3d
    import numpy as np
    HAS_OPEN3D = True
    HAS_NUMPY = True
except ImportError:
    HAS_OPEN3D = False
    HAS_NUMPY = False
    np = None


class View3DTab(BaseTab):
    """3D view tab using Open3D offscreen rendering with high-performance optimizations."""
    
    def __init__(self, screen: pygame.Surface, screen_width: int, screen_height: int,
                 components: Dict[str, Any]):
        """Initialize 3D view tab.
        
        Args:
            screen: Pygame surface to draw on
            screen_width: Screen width
            screen_height: Screen height
            components: Dictionary of UI components
        """
        super().__init__(screen, screen_width, screen_height)
        self.components = components
        self.renderer = get_renderer()
        self.optimizer = get_optimizer()
        
        # Performance optimization: cached surfaces
        self._cached_surface: Optional[pygame.Surface] = None
        self._cached_view_area: Optional[pygame.Rect] = None
        self._last_surface_update: float = 0.0
        
        # Interaction state
        self._is_dragging = False
        self._drag_start_pos: Optional[Tuple[int, int]] = None
        self._last_mouse_pos: Optional[Tuple[int, int]] = None
        
        # Performance stats
        self._fps_history = []
        self._render_times = []
        self._last_fps_update = time.time()
        self._current_fps = 0.0
        
        # View area cache
        self._view_area_cache: Optional[pygame.Rect] = None
        self._view_area_cache_time = 0.0
        
        # Interaction throttling
        self._interaction_throttle = 0.008  # ~120 Hz for smooth interaction
        self._last_interaction_time = 0.0
        
        # Keyboard shortcuts state
        self._key_states = {}
        
    def _get_view_area(self, y: int) -> pygame.Rect:
        """Get view area rectangle with caching."""
        current_time = time.time()
        # Cache view area for 1 second
        if (self._view_area_cache is None or 
            current_time - self._view_area_cache_time > 1.0):
            view_card_width = self.screen_width - 100
            view_card_height = self.screen_height - y - 20
            self._view_area_cache = pygame.Rect(
                70, y + 50, view_card_width - 40, view_card_height - 70
            )
            self._view_area_cache_time = current_time
        return self._view_area_cache
    
    def _update_fps(self):
        """Update FPS counter."""
        current_time = time.time()
        if current_time - self._last_fps_update >= 0.5:  # Update every 0.5 seconds
            if self._render_times:
                avg_render_time = sum(self._render_times) / len(self._render_times)
                self._current_fps = 1.0 / avg_render_time if avg_render_time > 0 else 0.0
                self._render_times.clear()
            self._last_fps_update = current_time
    
    def _should_throttle_interaction(self) -> bool:
        """Check if interaction should be throttled."""
        current_time = time.time()
        if current_time - self._last_interaction_time < self._interaction_throttle:
            return True
        self._last_interaction_time = current_time
        return False
    
    def draw(self, app_state: Dict[str, Any]):
        """Draw 3D view tab with performance optimizations."""
        render_start = time.time()
        
        y = self.tab_height + DesignSystem.SPACING['lg']
        
        # Title
        title_label = Label(50, y, "3D Point Cloud View (Open3D)", 'title', DesignSystem.COLORS['text'])
        title_label.draw(self.screen)
        y += 50
        
        if not HAS_OPEN3D:
            error_card = Card(50, y, self.screen_width - 100, 200, "Open3D Not Available")
            error_card.draw(self.screen)
            
            error_label = Label(self.screen_width // 2 - 200, y + 100,
                              "Open3D is not installed. Please install it with: pip install open3d",
                              'label', DesignSystem.COLORS['error'])
            error_label.align = 'center'
            error_label.draw(self.screen)
            return
        
        # 3D view area
        view_card = Card(50, y, self.screen_width - 100, 
                        self.screen_height - y - 20, "3D Point Cloud")
        view_card.draw(self.screen)
        
        view_area = self._get_view_area(y)
        
        # Get point cloud surface from app state
        pc_surface_o3d = app_state.get('pc_surface_o3d')
        
        # Performance optimization: only update cached surface if changed
        surface_changed = (pc_surface_o3d is not None and 
                          (self._cached_surface is None or 
                           pc_surface_o3d != self._cached_surface))
        
        if surface_changed:
            self._cached_surface = pc_surface_o3d
            self._cached_view_area = view_area.copy()
            self._last_surface_update = time.time()
        
        # Draw point cloud or placeholder
        if pc_surface_o3d and self._cached_surface:
            # Use cached scaled image if view area hasn't changed
            if (self._cached_view_area and 
                self._cached_view_area.size == view_area.size):
                # Reuse cached scaled image
                img_rect = pc_surface_o3d.get_rect()
                scale = min(view_area.width / img_rect.width, view_area.height / img_rect.height)
                new_size = (int(img_rect.width * scale), int(img_rect.height * scale))
                
                # Only rescale if size changed
                if not hasattr(self, '_scaled_img_cache') or self._scaled_img_cache.get_size() != new_size:
                    self._scaled_img_cache = pygame.transform.scale(pc_surface_o3d, new_size)
                
                scaled_rect = self._scaled_img_cache.get_rect(center=view_area.center)
                self.screen.blit(self._scaled_img_cache, scaled_rect)
            else:
                # Scale and display Open3D rendered image
                img_rect = pc_surface_o3d.get_rect()
                scale = min(view_area.width / img_rect.width, view_area.height / img_rect.height)
                new_size = (int(img_rect.width * scale), int(img_rect.height * scale))
                scaled_img = pygame.transform.scale(pc_surface_o3d, new_size)
                scaled_rect = scaled_img.get_rect(center=view_area.center)
                self.screen.blit(scaled_img, scaled_rect)
                # Cache for next frame
                self._scaled_img_cache = scaled_img
        else:
            placeholder_label = Label(view_area.centerx - 150, view_area.centery - 10,
                                     "Waiting for point cloud data...", 'label',
                                     DesignSystem.COLORS['text_secondary'])
            placeholder_label.align = 'center'
            placeholder_label.draw(self.screen)
        
        # Performance stats overlay
        self._update_fps()
        o3d_vis = app_state.get('o3d_vis')
        if o3d_vis:
            # Get point cloud info
            o3d_geometry = app_state.get('o3d_geometry')
            point_count = 0
            if o3d_geometry and hasattr(o3d_geometry, 'points'):
                point_count = len(o3d_geometry.points)
            
            # Display stats
            stats_text = f"FPS: {self._current_fps:.1f} | Points: {point_count:,}"
            self.renderer.render_text(self.screen, stats_text,
                                    (view_area.left + 10, view_area.top + 10),
                                    size='small',
                                    color=DesignSystem.COLORS['text_secondary'])
        
        # Instructions overlay (only show when not interacting)
        if not self._is_dragging:
            instructions = [
                "Mouse Drag: Rotate view",
                "Scroll: Zoom in/out",
                "Middle Mouse: Pan view",
                "R: Reset view",
                "Space: Toggle stats"
            ]
            
            inst_y = y + 60
            for inst in instructions:
                self.renderer.render_text(self.screen, inst,
                                        (self.screen_width - 200, inst_y),
                                        size='small',
                                        color=DesignSystem.COLORS['text'])
                inst_y += 18
        
        # Track render time
        render_time = time.time() - render_start
        self._render_times.append(render_time)
        if len(self._render_times) > 60:  # Keep last 60 frames
            self._render_times.pop(0)
    
    def handle_event(self, event: pygame.event.Event, app_state: Dict[str, Any]) -> bool:
        """Handle 3D view tab events with optimized interaction."""
        if not HAS_OPEN3D:
            return False
        
        o3d_vis = app_state.get('o3d_vis')
        if not o3d_vis:
            return False
        
        # Calculate view area
        y = self.tab_height + DesignSystem.SPACING['lg'] + 50
        view_area = self._get_view_area(y)
        
        # Handle keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:  # Reset view
                ctr = o3d_vis.get_view_control()
                ctr.set_zoom(0.7)
                ctr.set_lookat([0, 0, 0])
                ctr.set_up([0, 0, 1])
                ctr.set_front([0, -1, 0])
                return True
            elif event.key == pygame.K_SPACE:  # Toggle stats (could be extended)
                pass  # Placeholder for future feature
        
        # Handle mouse events in view area
        if hasattr(event, 'pos') and view_area.collidepoint(event.pos):
            # Throttle interactions for performance
            if self._should_throttle_interaction():
                return False
            
            ctr = o3d_vis.get_view_control()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse - start rotation
                    self._is_dragging = True
                    self._drag_start_pos = event.pos
                    self._last_mouse_pos = event.pos
                    return True
                elif event.button == 2:  # Middle mouse - pan
                    self._is_dragging = True
                    self._drag_start_pos = event.pos
                    self._last_mouse_pos = event.pos
                    return True
                elif event.button == 4:  # Scroll up - zoom in
                    ctr.scale(0.9)
                    return True
                elif event.button == 5:  # Scroll down - zoom out
                    ctr.scale(1.1)
                    return True
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button in (1, 2):  # Left or middle mouse
                    self._is_dragging = False
                    self._drag_start_pos = None
                    self._last_mouse_pos = None
                    return True
            
            elif event.type == pygame.MOUSEMOTION:
                if self._is_dragging and self._last_mouse_pos:
                    buttons = event.buttons
                    rel_x = event.pos[0] - self._last_mouse_pos[0]
                    rel_y = event.pos[1] - self._last_mouse_pos[1]
                    
                    if buttons[0]:  # Left mouse - rotate
                        # Smooth rotation with sensitivity adjustment
                        sensitivity = 0.5
                        ctr.rotate(rel_x * sensitivity, rel_y * sensitivity)
                        self._last_mouse_pos = event.pos
                        return True
                    elif buttons[1]:  # Middle mouse - pan
                        # Pan view
                        pan_sensitivity = 0.01
                        ctr.translate(rel_x * pan_sensitivity, -rel_y * pan_sensitivity, 0)
                        self._last_mouse_pos = event.pos
                        return True
        
        return False
    
    def update(self, dt: float, app_state: Dict[str, Any]):
        """Update 3D view tab state."""
        # Update FPS counter
        self._update_fps()
        
        # Invalidate cache if point cloud changed
        current_pc = app_state.get('pc_surface_o3d')
        if current_pc != self._cached_surface:
            self._cached_surface = None
            if hasattr(self, '_scaled_img_cache'):
                delattr(self, '_scaled_img_cache')
        
        # Clear drag state if mouse is released (safety check)
        if self._is_dragging:
            # Check if mouse is still pressed
            mouse_buttons = pygame.mouse.get_pressed()
            if not mouse_buttons[0] and not mouse_buttons[1]:
                self._is_dragging = False
                self._drag_start_pos = None
                self._last_mouse_pos = None
