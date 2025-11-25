"""Control tab implementation with optimized rendering."""
import pygame
from typing import Dict, Any

from .base_tab import BaseTab
from ..components import Label, Card, TopicList, TextInput, JSONEditor, Button
from ..design.design_system import DesignSystem
from ..renderers.ui_renderer import get_renderer


class ControlTab(BaseTab):
    """Control command tab."""
    
    def __init__(self, screen: pygame.Surface, screen_width: int, screen_height: int,
                 components: Dict[str, Any]):
        """Initialize control tab.
        
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
        """Draw control tab."""
        y = self.tab_height + DesignSystem.SPACING['lg']
        
        title_label = Label(50, y, "Control Commands", 'title', DesignSystem.COLORS['text'])
        title_label.draw(self.screen)
        y += 50
        
        # Left panel: Topic list
        topic_card = Card(50, y, 320, 550, "Available Topics")
        topic_card.draw(self.screen)
        
        topic_list = self.components.get('topic_list')
        if topic_list:
            topic_list.rect.x = 70
            topic_list.rect.y = y + 50
            topic_list.rect.width = topic_card.rect.width - 40
            topic_list.rect.height = topic_card.rect.height - 70
            topic_list.draw(self.screen)
        
        # Right panel
        x_right = 50 + topic_card.rect.width + 20
        y_right = y
        
        # Topic configuration
        config_card = Card(x_right, y_right, self.screen_width - x_right - 50, 120, "Topic Configuration")
        config_card.draw(self.screen)
        
        card_y = y_right + 50
        topic_label = Label(x_right + 20, card_y, "Topic Name:", 'label',
                           DesignSystem.COLORS['text_label'])
        topic_label.draw(self.screen)
        
        control_topic_input = self.components.get('control_topic_input')
        if control_topic_input:
            control_topic_input.rect.x = x_right + 20
            control_topic_input.rect.y = card_y + 25
            control_topic_input.rect.width = (config_card.rect.width - 60) // 2
            control_topic_input.draw(self.screen)
        
        type_label = Label(x_right + 20 + (control_topic_input.rect.width if control_topic_input else 200) + 20, card_y,
                          "Topic Type:", 'label', DesignSystem.COLORS['text_label'])
        type_label.draw(self.screen)
        
        control_type_input = self.components.get('control_type_input')
        if control_type_input:
            control_type_input.rect.x = x_right + 20 + (control_topic_input.rect.width if control_topic_input else 200) + 20
            control_type_input.rect.y = card_y + 25
            control_type_input.rect.width = config_card.rect.width - (control_topic_input.rect.width if control_topic_input else 200) - 80
            control_type_input.draw(self.screen)
        
        y_right += config_card.rect.height + 20
        
        # JSON editor
        editor_card = Card(x_right, y_right, self.screen_width - x_right - 50, 380, "Message Content (JSON)")
        editor_card.draw(self.screen)
        
        json_editor = self.components.get('json_editor')
        if json_editor:
            json_editor.rect.x = x_right + 20
            json_editor.rect.y = y_right + 50
            json_editor.rect.width = editor_card.rect.width - 40
            json_editor.rect.height = editor_card.rect.height - 70
            json_editor.draw(self.screen)
        
        y_right += editor_card.rect.height + 20
        
        # Action buttons - use auto-sizing and dynamic positioning
        button_y = y_right
        button_x = x_right + 20
        btn_gap = DesignSystem.SPACING['md']
        current_x = button_x
        
        preset_buttons = self.components.get('preset_buttons', [])
        for btn in preset_buttons:
            btn.rect.x = current_x
            btn.rect.y = button_y
            btn.draw(self.screen)
            current_x = btn.rect.right + btn_gap
        
        format_json_btn = self.components.get('format_json_btn')
        if format_json_btn:
            format_json_btn.rect.x = current_x
            format_json_btn.rect.y = button_y
            format_json_btn.draw(self.screen)
            current_x = format_json_btn.rect.right + btn_gap
        
        send_command_btn = self.components.get('send_command_btn')
        if send_command_btn:
            send_command_btn.rect.x = current_x
            send_command_btn.rect.y = button_y
            send_command_btn.draw(self.screen)
        
        # Command history
        y = y_right + 50
        history_card = Card(50, y, self.screen_width - 100, 
                           self.screen_height - y - 20, "Command History")
        history_card.draw(self.screen)
        
        history_area = pygame.Rect(70, y + 50, history_card.rect.width - 40,
                                   history_card.rect.height - 70)
        self.renderer.draw_rect(self.screen, history_area,
                              DesignSystem.COLORS['bg'],
                              border_radius=DesignSystem.RADIUS['sm'])
        
        command_history = app_state.get('command_history', [])
        if command_history:
            history_y = history_area.y + DesignSystem.SPACING['sm']
            for cmd in command_history[-15:]:
                cmd_height = self.renderer.measure_text(cmd, 'console')[1]
                if history_y + cmd_height > history_area.bottom - DesignSystem.SPACING['sm']:
                    break
                self.renderer.render_text(self.screen, cmd,
                                        (history_area.x + DesignSystem.SPACING['md'], history_y),
                                        size='console',
                                        color=DesignSystem.COLORS['text_console'])
                history_y += cmd_height + DesignSystem.SPACING['xs']
    
    def handle_event(self, event: pygame.event.Event, app_state: Dict[str, Any]) -> bool:
        """Handle control tab events."""
        # Update button positions before handling events
        tab_height = 45
        y = tab_height + DesignSystem.SPACING['lg']
        y += 50  # Title height
        
        x_right = 50 + 320 + 20  # topic_card width is 320
        y_right = y
        
        # Calculate positions same as in draw
        y_right += 120 + 20  # config_card height
        y_right += 380 + 20  # editor_card height
        button_y = y_right
        button_x = x_right + 20
        
        preset_buttons = self.components.get('preset_buttons', [])
        for i, btn in enumerate(preset_buttons):
            btn.rect.x = button_x + i * 140
            btn.rect.y = button_y
        
        format_json_btn = self.components.get('format_json_btn')
        if format_json_btn:
            format_json_btn.rect.x = button_x + len(preset_buttons) * 140
            format_json_btn.rect.y = button_y
        
        send_command_btn = self.components.get('send_command_btn')
        if send_command_btn:
            send_command_btn.rect.x = button_x + len(preset_buttons) * 140 + 150
            send_command_btn.rect.y = button_y
        
        # Handle component events
        topic_list = self.components.get('topic_list')
        if topic_list and topic_list.handle_event(event):
            return True
        
        control_topic_input = self.components.get('control_topic_input')
        if control_topic_input and control_topic_input.handle_event(event):
            return True
        
        control_type_input = self.components.get('control_type_input')
        if control_type_input and control_type_input.handle_event(event):
            return True
        
        json_editor = self.components.get('json_editor')
        if json_editor and json_editor.handle_event(event):
            return True
        
        for btn in preset_buttons:
            if btn.handle_event(event):
                return True
        
        if format_json_btn and format_json_btn.handle_event(event):
            return True
        
        if send_command_btn and send_command_btn.handle_event(event):
            return True
        
        return False
    
    def update(self, dt: float, app_state: Dict[str, Any]):
        """Update control tab."""
        control_topic_input = self.components.get('control_topic_input')
        if control_topic_input:
            control_topic_input.update(dt)
        
        control_type_input = self.components.get('control_type_input')
        if control_type_input:
            control_type_input.update(dt)
        
        json_editor = self.components.get('json_editor')
        if json_editor:
            json_editor.update(dt)
        
        preset_buttons = self.components.get('preset_buttons', [])
        for btn in preset_buttons:
            btn.update(dt)
        
        format_json_btn = self.components.get('format_json_btn')
        if format_json_btn:
            format_json_btn.update(dt)
        
        send_command_btn = self.components.get('send_command_btn')
        if send_command_btn:
            send_command_btn.update(dt)

