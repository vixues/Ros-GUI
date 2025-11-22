"""Interactive UI components."""
import pygame
import inspect
from typing import Optional, List, Tuple, Callable

from .base import UIComponent
from ..design.design_system import DesignSystem


class Button(UIComponent):
    """Button component with fighter cockpit styling."""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str,
                 callback: Callable = None, color: Tuple[int, int, int] = None):
        super().__init__(x, y, width, height)
        self.text = text
        self.color = color or DesignSystem.COLORS['primary']
        self.hovered = False
        self.pressed = False
        self.animation_scale = 1.0
        
        # Connect callback to port system if provided
        if callback:
            self.connect_port('on_click', callback)
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle button events with port system integration."""
        if not self.visible or not self.enabled:
            return False
            
        if event.type == pygame.MOUSEMOTION:
            was_hovered = self.hovered
            self.hovered = self.rect.collidepoint(event.pos) if hasattr(event, 'pos') else False
            if was_hovered != self.hovered:
                self.emit_signal('hover', self.hovered)
                self.emit_signal('on_hover', {'hovered': self.hovered, 'text': self.text})
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if hasattr(event, 'pos') and self.rect.collidepoint(event.pos):
                self.pressed = True
                self.emit_signal('click', {'action': 'press', 'text': self.text})
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.pressed:
                self.pressed = False
                if hasattr(event, 'pos') and self.rect.collidepoint(event.pos):
                    # Emit signals through port system
                    self.emit_signal('click', {'action': 'release', 'text': self.text})
                    # Get on_click port and call handlers directly to avoid parameter issues
                    on_click_port = self.get_port('on_click')
                    if on_click_port:
                        for handler in on_click_port.connections:
                            try:
                                # Check if handler is a lambda with default arguments (captured values)
                                is_lambda = (hasattr(handler, '__name__') and 
                                           (handler.__name__ == '<lambda>' or 
                                            handler.__name__ == '<function>'))
                                
                                # Check if handler accepts parameters
                                try:
                                    sig = inspect.signature(handler)
                                    params = list(sig.parameters.values())
                                    if hasattr(handler, '__self__') and params and params[0].name == 'self':
                                        params = params[1:]
                                    
                                    # For lambda functions, check if all params have default values
                                    if is_lambda and params:
                                        all_have_defaults = all(p.default != inspect.Parameter.empty for p in params)
                                        if all_have_defaults:
                                            # Lambda with captured values - call without args
                                            handler()
                                        elif len(params) == 0:
                                            handler()
                                        else:
                                            # Try with dict, fallback to no args
                                            try:
                                                handler({'text': self.text, 'button': self})
                                            except TypeError:
                                                handler()
                                    elif len(params) == 0:
                                        handler()
                                    else:
                                        # Try with dict first, fallback to no args
                                        try:
                                            handler({'text': self.text, 'button': self})
                                        except TypeError:
                                            handler()
                                except (ValueError, TypeError):
                                    # If signature inspection fails, try calling without args first
                                    # (for lambda functions with captured values)
                                    try:
                                        handler()
                                    except TypeError:
                                        try:
                                            handler({'text': self.text, 'button': self})
                                        except TypeError:
                                            handler()
                            except Exception as e:
                                print(f"Error in button on_click handler: {e}")
                return True
        return False
        
    def update(self, dt: float):
        """Update button animation."""
        target_scale = 1.05 if self.hovered else 1.0
        if abs(self.animation_scale - target_scale) > 0.01:
            diff = target_scale - self.animation_scale
            self.animation_scale += diff * dt * 10
            
    def draw(self, surface: pygame.Surface):
        """Draw button with fighter cockpit style."""
        if not self.visible:
            return
            
        # Calculate color based on state
        if self.pressed:
            bg_color = tuple(max(0, c - 40) for c in self.color)
        elif self.hovered:
            bg_color = tuple(min(255, int(c * 1.2)) for c in self.color)
        else:
            bg_color = self.color
            
        # Draw button with scale animation
        scale = self.animation_scale
        scaled_rect = pygame.Rect(
            self.rect.centerx - self.rect.width * scale / 2,
            self.rect.centery - self.rect.height * scale / 2,
            self.rect.width * scale,
            self.rect.height * scale
        )
        
        # Draw shadow
        shadow_rect = scaled_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (*DesignSystem.COLORS['shadow_light'][:3], 100),
                        shadow_surf.get_rect(), border_radius=DesignSystem.RADIUS['md'])
        surface.blit(shadow_surf, shadow_rect)
        
        # Draw button
        pygame.draw.rect(surface, bg_color, scaled_rect,
                        border_radius=DesignSystem.RADIUS['md'])
        pygame.draw.rect(surface, DesignSystem.COLORS['border_light'], scaled_rect,
                        width=1, border_radius=DesignSystem.RADIUS['md'])
        
        # Draw text - ensure contrast with background
        font = DesignSystem.get_font('label')
        # Calculate text color based on background brightness
        bg_brightness = sum(bg_color) / 3.0
        if bg_brightness > 200:  # Light background - use dark text
            text_color = (0, 0, 0)  # Black
        else:  # Dark background - use light text
            text_color = DesignSystem.COLORS['text']
        text_surf = font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=scaled_rect.center)
        surface.blit(text_surf, text_rect)


class TextInput(UIComponent):
    """Text input component with console style."""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 default_text: str = "", placeholder: str = ""):
        super().__init__(x, y, width, height)
        self.text = default_text
        self.placeholder = placeholder
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0.0
        self.cursor_pos = len(self.text)
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle text input events with port system integration."""
        if not self.visible or not self.enabled:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            was_active = self.active
            self.active = self.rect.collidepoint(event.pos) if hasattr(event, 'pos') else False
            if was_active != self.active:
                self.emit_signal('focus', self.active)
            return self.active
        elif event.type == pygame.KEYDOWN and self.active:
            old_text = self.text
            if event.key == pygame.K_BACKSPACE:
                if self.cursor_pos > 0:
                    self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
                    self.cursor_pos = max(0, self.cursor_pos - 1)
            elif event.key == pygame.K_DELETE:
                if self.cursor_pos < len(self.text):
                    self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos+1:]
            elif event.key == pygame.K_LEFT:
                self.cursor_pos = max(0, self.cursor_pos - 1)
            elif event.key == pygame.K_RIGHT:
                self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
            elif event.key == pygame.K_HOME:
                self.cursor_pos = 0
            elif event.key == pygame.K_END:
                self.cursor_pos = len(self.text)
            elif event.unicode and event.unicode.isprintable():
                self.text = self.text[:self.cursor_pos] + event.unicode + self.text[self.cursor_pos:]
                self.cursor_pos += 1
            
            # Emit change signal if text changed
            if self.text != old_text:
                self.emit_signal('change', {'text': self.text, 'old_text': old_text})
                self.emit_signal('on_change', self.text)
                # Update value port
                port = self.get_port('value')
                if port:
                    port.value = self.text
            return True
        return False
        
    def update(self, dt: float):
        """Update cursor blink."""
        self.cursor_timer += dt
        if self.cursor_timer > 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0.0
            
    def draw(self, surface: pygame.Surface):
        """Draw text input with console style."""
        if not self.visible:
            return
        
        # Draw background
        bg_color = DesignSystem.COLORS['surface_active'] if self.active else DesignSystem.COLORS['surface_light']
        pygame.draw.rect(surface, bg_color, self.rect,
                       border_radius=DesignSystem.RADIUS['sm'])
        
        # Draw border with glow when active
        border_color = DesignSystem.COLORS['primary'] if self.active else DesignSystem.COLORS['border']
        pygame.draw.rect(surface, border_color, self.rect,
                       width=2 if self.active else 1, border_radius=DesignSystem.RADIUS['sm'])
        
        # Draw text
        font = DesignSystem.get_font('console')
        display_text = self.text if self.text else self.placeholder
        text_color = DesignSystem.COLORS['text'] if self.text else DesignSystem.COLORS['text_tertiary']
        
        # Clip text if too long
        text_surf = font.render(display_text, True, text_color)
        clip_rect = self.rect.inflate(-DesignSystem.SPACING['md'], 0)
        old_clip = surface.get_clip()
        surface.set_clip(clip_rect)
        
        text_y = self.rect.y + (self.rect.height - text_surf.get_height()) // 2
        surface.blit(text_surf, (clip_rect.x, text_y))
        
        # Draw cursor
        if self.active and self.cursor_visible:
            cursor_text = self.text[:self.cursor_pos]
            cursor_surf = font.render(cursor_text, True, text_color)
            cursor_x = clip_rect.x + cursor_surf.get_width()
            pygame.draw.line(surface, DesignSystem.COLORS['primary'],
                           (cursor_x, self.rect.y + 4),
                           (cursor_x, self.rect.bottom - 4), 2)
        
        surface.set_clip(old_clip)


class Checkbox(UIComponent):
    """Checkbox component."""
    
    def __init__(self, x: int, y: int, text: str, checked: bool = False,
                 callback: Callable = None):
        super().__init__(x, y, 20, 20)
        self.text = text
        self.checked = checked
        self.hovered = False
        
        # Connect callback to port system if provided
        if callback:
            self.connect_port('on_change', callback)
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle checkbox events with port system integration."""
        if not self.visible or not self.enabled:
            return False
            
        if event.type == pygame.MOUSEMOTION:
            was_hovered = self.hovered
            self.hovered = self.rect.collidepoint(event.pos) if hasattr(event, 'pos') else False
            if was_hovered != self.hovered:
                self.emit_signal('hover', self.hovered)
                self.emit_signal('on_hover', {'hovered': self.hovered, 'text': self.text})
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if hasattr(event, 'pos') and self.rect.collidepoint(event.pos):
                old_checked = self.checked
                self.checked = not self.checked
                # Emit signals through port system
                self.emit_signal('click', {'checked': self.checked})
                self.emit_signal('change', {'checked': self.checked, 'old_checked': old_checked})
                self.emit_signal('on_change', self.checked)
                # Update value port
                port = self.get_port('value')
                if port:
                    port.value = self.checked
                return True
        return False
        
    def draw(self, surface: pygame.Surface):
        """Draw checkbox."""
        if not self.visible:
            return
            
        # Draw box
        bg_color = DesignSystem.COLORS['primary'] if self.checked else DesignSystem.COLORS['surface_light']
        pygame.draw.rect(surface, bg_color, self.rect,
                       border_radius=DesignSystem.RADIUS['sm'])
        pygame.draw.rect(surface, DesignSystem.COLORS['border_light'], self.rect,
                       width=1, border_radius=DesignSystem.RADIUS['sm'])
        
        # Draw checkmark
        if self.checked:
            points = [
                (self.rect.x + 5, self.rect.y + 10),
                (self.rect.x + 9, self.rect.y + 14),
                (self.rect.x + 15, self.rect.y + 6)
            ]
            pygame.draw.lines(surface, DesignSystem.COLORS['text'], False, points, 2)
        
        # Draw label
        font = DesignSystem.get_font('label')
        label_surf = font.render(self.text, True, DesignSystem.COLORS['text'])
        label_y = self.rect.y + (self.rect.height - label_surf.get_height()) // 2
        surface.blit(label_surf, (self.rect.right + DesignSystem.SPACING['sm'], label_y))


class Items(UIComponent):
    """List items component with selection."""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height)
        self.items: List[Tuple[str, str]] = []  # List of (name, type) tuples
        self.selected_index = -1
        self.scroll_y = 0
        self.item_height = 32
        self.on_select: Optional[Callable] = None
        
    def set_items(self, items: List[Tuple[str, str]]):
        """Set items list."""
        if items and isinstance(items[0], str):
            self.items = [(item, "") for item in items]
        else:
            self.items = items
            
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle items list events."""
        if not self.visible or not self.enabled:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                rel_y = event.pos[1] - self.rect.y
                index = (rel_y + self.scroll_y) // self.item_height
                if 0 <= index < len(self.items):
                    self.selected_index = index
                    if self.on_select:
                        self.on_select(self.items[index])
                    return True
            elif event.button == 4:  # Scroll up
                self.scroll_y = max(0, self.scroll_y - 20)
            elif event.button == 5:  # Scroll down
                self.scroll_y += 20
        return False
        
    def draw(self, surface: pygame.Surface):
        """Draw items list."""
        if not self.visible:
            return
            
        # Draw background
        pygame.draw.rect(surface, DesignSystem.COLORS['surface'], self.rect,
                       border_radius=DesignSystem.RADIUS['md'])
        pygame.draw.rect(surface, DesignSystem.COLORS['border'], self.rect,
                       width=1, border_radius=DesignSystem.RADIUS['md'])
        
        # Clip to item area
        clip_rect = self.rect.inflate(-DesignSystem.SPACING['sm'], -DesignSystem.SPACING['sm'])
        old_clip = surface.get_clip()
        surface.set_clip(clip_rect)
        
        font = DesignSystem.get_font('console')
        small_font = DesignSystem.get_font('small')
        
        y_offset = clip_rect.y - self.scroll_y
        for i, (name, item_type) in enumerate(self.items):
            item_y = y_offset + i * self.item_height
            if item_y + self.item_height < clip_rect.y:
                continue
            if item_y > clip_rect.bottom:
                break
                
            item_rect = pygame.Rect(clip_rect.x, item_y, clip_rect.width, self.item_height)
            
            # Highlight selected
            if i == self.selected_index:
                pygame.draw.rect(surface, DesignSystem.COLORS['primary'], item_rect,
                               border_radius=DesignSystem.RADIUS['sm'])
                text_color = DesignSystem.COLORS['text']
            else:
                text_color = DesignSystem.COLORS['text_secondary']
            
            # Draw item name
            name_surf = font.render(name, True, text_color)
            surface.blit(name_surf, (item_rect.x + DesignSystem.SPACING['sm'], 
                                   item_rect.y + (self.item_height - name_surf.get_height()) // 2))
            
            # Draw item type if available
            if item_type:
                type_surf = small_font.render(item_type, True, DesignSystem.COLORS['text_tertiary'])
                type_y = item_rect.y + name_surf.get_height() + 2
                if type_y + type_surf.get_height() < item_rect.bottom:
                    surface.blit(type_surf, (item_rect.x + DesignSystem.SPACING['sm'], type_y))
        
        surface.set_clip(old_clip)

