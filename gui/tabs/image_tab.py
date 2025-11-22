"""Image tab implementation."""
import pygame
from typing import Dict, Any

from .base_tab import BaseTab
from ..components import Label, ImageDisplayComponent
from ..design.design_system import DesignSystem

# Check for optional dependencies
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


class ImageTab(BaseTab):
    """Image display tab."""
    
    def __init__(self, screen: pygame.Surface, screen_width: int, screen_height: int,
                 components: Dict[str, Any]):
        """Initialize image tab.
        
        Args:
            screen: Pygame surface to draw on
            screen_width: Screen width
            screen_height: Screen height
            components: Dictionary of UI components
        """
        super().__init__(screen, screen_width, screen_height)
        self.components = components
        
    def draw(self, app_state: Dict[str, Any]):
        """Draw image tab."""
        y = self.tab_height + DesignSystem.SPACING['lg']
        
        title_label = Label(50, y, "Image Display", 'title', DesignSystem.COLORS['text'])
        title_label.draw(self.screen)
        y += 50
        
        # Use professional ImageDisplayComponent
        image_display = self.components.get('image_display')
        if image_display:
            image_display.rect.x = 50
            image_display.rect.y = y
            image_display.rect.width = self.screen_width - 100
            image_display.rect.height = self.screen_height - y - 20
            image_display.set_image(app_state.get('current_image'))
            image_display.draw(self.screen)
    
    def handle_event(self, event: pygame.event.Event, app_state: Dict[str, Any]) -> bool:
        """Handle image tab events."""
        image_display = self.components.get('image_display')
        if image_display:
            return image_display.handle_event(event)
        return False
    
    def update(self, dt: float, app_state: Dict[str, Any]):
        """Update image tab."""
        image_display = self.components.get('image_display')
        if image_display:
            image_display.update(dt)

