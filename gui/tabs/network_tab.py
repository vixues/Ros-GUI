"""Network test tab implementation with optimized rendering."""
import pygame
from typing import Dict, Any

from .base_tab import BaseTab
from ..components import Label, Card, TextInput, Button
from ..design.design_system import DesignSystem
from ..renderers.ui_renderer import get_renderer


class NetworkTab(BaseTab):
    """Network test tab."""
    
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
        
    def draw(self, app_state: Dict[str, Any]):
        """Draw network test tab."""
        y = self.tab_height + DesignSystem.SPACING['lg']
        
        title_label = Label(50, y, "Network Test", 'title', DesignSystem.COLORS['text'])
        title_label.draw(self.screen)
        y += 50
        
        config_card = Card(50, y, self.screen_width - 100, 200, "Test Configuration")
        config_card.draw(self.screen)
        
        card_y = y + 50
        url_label = Label(70, card_y, "Test Address:", 'label',
                         DesignSystem.COLORS['text_label'])
        url_label.draw(self.screen)
        
        test_url_input = self.components.get('test_url_input')
        if test_url_input:
            test_url_input.rect.x = 70
            test_url_input.rect.y = card_y + 25
            test_url_input.rect.width = config_card.rect.width - 40
            test_url_input.draw(self.screen)
        
        card_y += 70
        
        timeout_label = Label(70, card_y, "Timeout (seconds):", 'label',
                            DesignSystem.COLORS['text_label'])
        timeout_label.draw(self.screen)
        
        test_timeout_input = self.components.get('test_timeout_input')
        if test_timeout_input:
            test_timeout_input.rect.x = 70
            test_timeout_input.rect.y = card_y + 25
            test_timeout_input.rect.width = 200
            test_timeout_input.draw(self.screen)
        
        test_btn = self.components.get('test_btn')
        if test_btn:
            test_btn.rect.x = 280
            test_btn.rect.y = card_y + 25
            test_btn.draw(self.screen)
        
        y += config_card.rect.height + 20
        
        result_card = Card(50, y, self.screen_width - 100,
                          self.screen_height - y - 20, "Test Results")
        result_card.draw(self.screen)
        
        result_area = pygame.Rect(70, y + 50, result_card.rect.width - 40,
                                 result_card.rect.height - 70)
        self.renderer.draw_rect(self.screen, result_area,
                              DesignSystem.COLORS['bg'],
                              border_radius=0)  # No rounded corners
        
        test_results = app_state.get('test_results', [])
        if test_results:
            result_y = result_area.y + DesignSystem.SPACING['sm']
            for result in test_results[-25:]:
                result_height = self.renderer.measure_text(result, 'console')[1]
                if result_y + result_height > result_area.bottom - DesignSystem.SPACING['sm']:
                    break
                self.renderer.render_text(self.screen, result,
                                        (result_area.x + DesignSystem.SPACING['md'], result_y),
                                        size='console',
                                        color=DesignSystem.COLORS['text_console'])
                result_y += result_height + DesignSystem.SPACING['xs']
    
    def handle_event(self, event: pygame.event.Event, app_state: Dict[str, Any]) -> bool:
        """Handle network tab events."""
        test_url_input = self.components.get('test_url_input')
        if test_url_input and test_url_input.handle_event(event):
            return True
        
        test_timeout_input = self.components.get('test_timeout_input')
        if test_timeout_input and test_timeout_input.handle_event(event):
            return True
        
        test_btn = self.components.get('test_btn')
        if test_btn and test_btn.handle_event(event):
            return True
        
        return False
    
    def update(self, dt: float, app_state: Dict[str, Any]):
        """Update network tab."""
        test_url_input = self.components.get('test_url_input')
        if test_url_input:
            test_url_input.update(dt)
        
        test_timeout_input = self.components.get('test_timeout_input')
        if test_timeout_input:
            test_timeout_input.update(dt)
        
        test_btn = self.components.get('test_btn')
        if test_btn:
            test_btn.update(dt)

