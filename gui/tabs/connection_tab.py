"""Connection tab implementation."""
import pygame
from typing import Dict, Any

from .base_tab import BaseTab
from ..components import Label, Card, Button, TextInput, Checkbox
from ..design.design_system import DesignSystem


class ConnectionTab(BaseTab):
    """Connection configuration tab with multi-drone management."""
    
    def __init__(self, screen: pygame.Surface, screen_width: int, screen_height: int,
                 components: Dict[str, Any]):
        """Initialize connection tab.
        
        Args:
            screen: Pygame surface to draw on
            screen_width: Screen width
            screen_height: Screen height
            components: Dictionary of UI components (inputs, buttons, etc.)
        """
        super().__init__(screen, screen_width, screen_height)
        self.components = components
        
    def draw(self, app_state: Dict[str, Any]):
        """Draw connection tab."""
        y = self.tab_height + DesignSystem.SPACING['lg']
        
        # Title
        title_label = Label(50, y, "Multi-Drone Connection Management", 'title', 
                           DesignSystem.COLORS['text'])
        title_label.draw(self.screen)
        y += 50
        
        # Connection settings card
        settings_card = Card(50, y, self.screen_width - 100, 280, "Add/Connect Drone")
        settings_card.draw(self.screen)
        
        card_y = y + 50
        # Drone name
        name_label = Label(70, card_y, "Drone Name:", 'label',
                         DesignSystem.COLORS['text_label'])
        name_label.draw(self.screen)
        self.components['drone_name_input'].rect.x = 70
        self.components['drone_name_input'].rect.y = card_y + 25
        self.components['drone_name_input'].rect.width = 200
        self.components['drone_name_input'].draw(self.screen)
        
        # Connection URL
        url_label = Label(290, card_y, "WebSocket Address:", 'label',
                         DesignSystem.COLORS['text_label'])
        url_label.draw(self.screen)
        self.components['connection_url_input'].rect.x = 290
        self.components['connection_url_input'].rect.y = card_y + 25
        self.components['connection_url_input'].rect.width = settings_card.rect.width - 310
        self.components['connection_url_input'].draw(self.screen)
        card_y += 70
        
        # Mock checkbox
        self.components['use_mock_checkbox'].rect.x = 70
        self.components['use_mock_checkbox'].rect.y = card_y
        self.components['use_mock_checkbox'].draw(self.screen)
        card_y += 50
        
        # Buttons
        self.components['add_drone_btn'].rect.x = 70
        self.components['add_drone_btn'].rect.y = card_y
        self.components['add_drone_btn'].draw(self.screen)
        self.components['connect_btn'].rect.x = 200
        self.components['connect_btn'].rect.y = card_y
        self.components['connect_btn'].draw(self.screen)
        self.components['disconnect_btn'].rect.x = 330
        self.components['disconnect_btn'].rect.y = card_y
        self.components['disconnect_btn'].draw(self.screen)
        self.components['remove_drone_btn'].rect.x = 460
        self.components['remove_drone_btn'].rect.y = card_y
        self.components['remove_drone_btn'].draw(self.screen)
        
        y += settings_card.rect.height + 20
        
        # Drone list card
        list_card = Card(50, y, self.screen_width - 100, 200, "Connected Drones")
        list_card.draw(self.screen)
        
        list_area = pygame.Rect(70, y + 50, list_card.rect.width - 40, list_card.rect.height - 70)
        pygame.draw.rect(self.screen, DesignSystem.COLORS['bg'], list_area,
                       border_radius=DesignSystem.RADIUS['sm'])
        
        # Draw drone list
        drones = app_state.get('drones', {})
        current_drone_id = app_state.get('current_drone_id')
        font = DesignSystem.get_font('label')
        list_y = list_area.y + DesignSystem.SPACING['sm']
        for i, (drone_id, drone_info) in enumerate(drones.items()):
            if list_y + 30 > list_area.bottom - DesignSystem.SPACING['sm']:
                break
            
            # Highlight selected drone
            if drone_id == current_drone_id:
                highlight_rect = pygame.Rect(list_area.x + 5, list_y - 5, list_area.width - 10, 30)
                pygame.draw.rect(self.screen, DesignSystem.COLORS['primary'], highlight_rect,
                               border_radius=DesignSystem.RADIUS['sm'])
            
            # Drone info
            status = "Connected" if drone_info.get('is_connected') else "Disconnected"
            status_color = DesignSystem.COLORS['success'] if drone_info.get('is_connected') else DesignSystem.COLORS['error']
            text = f"{drone_info['name']} - {drone_info['url']} [{status}]"
            text_surf = font.render(text, True, DesignSystem.COLORS['text'])
            self.screen.blit(text_surf, (list_area.x + DesignSystem.SPACING['md'], list_y))
            list_y += 35
        
        if len(drones) == 0:
            empty_text = font.render("No drones added. Add a drone above.", True, 
                                   DesignSystem.COLORS['text_secondary'])
            self.screen.blit(empty_text, (list_area.x + DesignSystem.SPACING['md'], list_y))
        
        y += list_card.rect.height + 20
        
        # Log display card
        log_card = Card(50, y, self.screen_width - 100, 
                       self.screen_height - y - 20, "Connection Log")
        log_card.draw(self.screen)
        
        log_area = pygame.Rect(70, y + 50, log_card.rect.width - 40, 
                              log_card.rect.height - 70)
        pygame.draw.rect(self.screen, DesignSystem.COLORS['bg'], log_area,
                       border_radius=DesignSystem.RADIUS['sm'])
        
        connection_logs = app_state.get('connection_logs', [])
        if connection_logs:
            font = DesignSystem.get_font('console')
            log_y = log_area.y + DesignSystem.SPACING['sm']
            for log in connection_logs[-20:]:
                log_surf = font.render(log, True, DesignSystem.COLORS['text_console'])
                if log_y + log_surf.get_height() > log_area.bottom - DesignSystem.SPACING['sm']:
                    break
                self.screen.blit(log_surf, (log_area.x + DesignSystem.SPACING['md'], log_y))
                log_y += log_surf.get_height() + DesignSystem.SPACING['xs']
    
    def handle_event(self, event: pygame.event.Event, app_state: Dict[str, Any]) -> bool:
        """Handle connection tab events."""
        # Handle component events
        self.components['drone_name_input'].handle_event(event)
        self.components['connection_url_input'].handle_event(event)
        self.components['use_mock_checkbox'].handle_event(event)
        self.components['add_drone_btn'].handle_event(event)
        self.components['connect_btn'].handle_event(event)
        self.components['disconnect_btn'].handle_event(event)
        self.components['remove_drone_btn'].handle_event(event)
        
        # Handle drone list selection
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            list_card_y = 45 + DesignSystem.SPACING['lg'] + 50 + 280 + 20
            list_area = pygame.Rect(70, list_card_y + 50, self.screen_width - 140, 200)
            if list_area.collidepoint(event.pos):
                # Calculate which drone was clicked
                relative_y = event.pos[1] - list_area.y
                drone_index = relative_y // 35
                drones = app_state.get('drones', {})
                if 0 <= drone_index < len(drones):
                    app_state['current_drone_id'] = list(drones.keys())[drone_index]
                    # Update input fields with selected drone info
                    drone_info = drones[app_state['current_drone_id']]
                    self.components['drone_name_input'].text = drone_info['name']
                    self.components['connection_url_input'].text = drone_info['url']
                    self.components['use_mock_checkbox'].checked = drone_info.get('use_mock', False)
                    return True
        return False
    
    def update(self, dt: float, app_state: Dict[str, Any]):
        """Update connection tab."""
        self.components['connection_url_input'].update(dt)
        self.components['connect_btn'].update(dt)
        self.components['disconnect_btn'].update(dt)

