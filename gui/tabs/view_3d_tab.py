"""3D view tab implementation using Open3D."""
import pygame
from typing import Dict, Any

from .base_tab import BaseTab
from ..components import Label, Card
from ..design.design_system import DesignSystem

# Check for optional dependencies
try:
    import open3d as o3d
    HAS_OPEN3D = True
except ImportError:
    HAS_OPEN3D = False


class View3DTab(BaseTab):
    """3D view tab using Open3D offscreen rendering."""
    
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
        
    def draw(self, app_state: Dict[str, Any]):
        """Draw 3D view tab."""
        y = self.tab_height + DesignSystem.SPACING['lg']
        
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
        
        view_area = pygame.Rect(70, y + 50, view_card.rect.width - 40,
                               view_card.rect.height - 70)
        
        pc_surface_o3d = app_state.get('pc_surface_o3d')
        if pc_surface_o3d:
            # Scale and display Open3D rendered image
            img_rect = pc_surface_o3d.get_rect()
            scale = min(view_area.width / img_rect.width, view_area.height / img_rect.height)
            new_size = (int(img_rect.width * scale), int(img_rect.height * scale))
            scaled_img = pygame.transform.scale(pc_surface_o3d, new_size)
            scaled_rect = scaled_img.get_rect(center=view_area.center)
            self.screen.blit(scaled_img, scaled_rect)
        else:
            placeholder_label = Label(view_area.centerx - 150, view_area.centery - 10,
                                     "Waiting for point cloud data...", 'label',
                                     DesignSystem.COLORS['text_secondary'])
            placeholder_label.align = 'center'
            placeholder_label.draw(self.screen)
        
        # Instructions overlay
        instructions = [
            "Mouse Drag: Rotate view",
            "Scroll: Zoom in/out",
        ]
        
        font = DesignSystem.get_font('small')
        inst_y = y + 60
        for inst in instructions:
            inst_surf = font.render(inst, True, DesignSystem.COLORS['text'])
            self.screen.blit(inst_surf, (self.screen_width - 200, inst_y))
            inst_y += 20
    
    def handle_event(self, event: pygame.event.Event, app_state: Dict[str, Any]) -> bool:
        """Handle 3D view tab events."""
        if not HAS_OPEN3D:
            return False
        
        o3d_vis = app_state.get('o3d_vis')
        if not o3d_vis:
            return False
        
        if hasattr(event, 'pos'):
            view_area = pygame.Rect(70, 110, self.screen_width - 140, self.screen_height - 130)
            if view_area.collidepoint(event.pos):
                pc_last_interaction_time = app_state.get('pc_last_interaction_time', 0.0)
                pc_interaction_throttle = app_state.get('pc_interaction_throttle', 0.016)
                current_time = pygame.time.get_ticks() / 1000.0
                
                if current_time - pc_last_interaction_time < pc_interaction_throttle:
                    return False
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:  # Scroll up - zoom in
                        ctr = o3d_vis.get_view_control()
                        ctr.scale(0.9)
                        app_state['pc_last_interaction_time'] = current_time
                        return True
                    elif event.button == 5:  # Scroll down - zoom out
                        ctr = o3d_vis.get_view_control()
                        ctr.scale(1.1)
                        app_state['pc_last_interaction_time'] = current_time
                        return True
                elif event.type == pygame.MOUSEMOTION and hasattr(event, 'buttons') and event.buttons[0]:
                    if hasattr(event, 'rel'):
                        ctr = o3d_vis.get_view_control()
                        ctr.rotate(event.rel[0] * 0.5, event.rel[1] * 0.5)
                        app_state['pc_last_interaction_time'] = current_time
                        return True
        
        return False
    
    def update(self, dt: float, app_state: Dict[str, Any]):
        """Update 3D view tab."""
        pass

