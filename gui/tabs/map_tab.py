"""Map tab implementation with optimized rendering."""
import pygame
from typing import Dict, Any

from .base_tab import BaseTab
from ..components import Label, Card, MapComponent
from ..design.design_system import DesignSystem
from ..renderers.ui_renderer import get_renderer


class MapTab(BaseTab):
    """Map tab showing all drone positions."""
    
    def __init__(self, screen: pygame.Surface, screen_width: int, screen_height: int,
                 components: Dict[str, Any]):
        """Initialize map tab.
        
        Args:
            screen: Pygame surface to draw on
            screen_width: Screen width
            screen_height: Screen height
            components: Dictionary of UI components
        """
        super().__init__(screen, screen_width, screen_height)
        self.components = components
        self.renderer = get_renderer()
        
    def draw(self, app_state: Dict[str, Any]):
        """Draw map tab."""
        y = self.tab_height + DesignSystem.SPACING['lg']
        
        title_label = Label(50, y, "Drone Map View", 'title', DesignSystem.COLORS['text'])
        title_label.draw(self.screen)
        y += 50
        
        # Map display card
        map_card = self.components.get('map_card')
        if not map_card:
            map_card = Card(50, y, self.screen_width - 100, self.screen_height - y - 20, "Drone Positions")
            self.components['map_card'] = map_card
        else:
            map_card.rect.x = 50
            map_card.rect.y = y
            map_card.rect.width = self.screen_width - 100
            map_card.rect.height = self.screen_height - y - 20
            map_card.children.clear()
        
        map_card.draw(self.screen)
        
        # Get card's content area for map component
        card_content_area = map_card.get_content_area()
        
        # Set map component position and size
        component_padding = DesignSystem.SPACING['sm']
        map_display = self.components.get('map_display')
        if map_display:
            map_display.visible = True
            map_display.enabled = True
            map_display.rect.x = component_padding
            map_display.rect.y = component_padding
            map_display.rect.width = card_content_area.width - component_padding * 2
            map_display.rect.height = card_content_area.height - component_padding * 2
            map_display.title = ""
            
            # Update map component with current drones data
            drones = app_state.get('drones', {})
            current_drone_id = app_state.get('current_drone_id')
            map_display.set_drones(drones, current_drone_id)
            
            map_card.add_child(map_display)
        
        # Draw Card
        map_card.draw(self.screen)
    
    def handle_event(self, event: pygame.event.Event, app_state: Dict[str, Any]) -> bool:
        """Handle map tab events."""
        map_card = self.components.get('map_card')
        if map_card and map_card.handle_event(event):
            return True
        
        # Map interactions can be added here (zoom, pan, click to select drone, etc.)
        if hasattr(event, 'pos') and map_card and map_card.rect.collidepoint(event.pos):
            # Could implement click-to-select drone here
            pass
        
        return False
    
    def update(self, dt: float, app_state: Dict[str, Any]):
        """Update map tab."""
        map_display = self.components.get('map_display')
        if map_display:
            map_display.update(dt)

