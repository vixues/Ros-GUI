"""Interactive UI components with optimized rendering."""
import pygame
import inspect
from typing import Optional, List, Tuple, Callable

from .base import UIComponent
from ..design.design_system import DesignSystem
from ..renderers.ui_renderer import get_renderer


class Button(UIComponent):
    """Button component with fighter cockpit styling and auto-sizing based on text."""
    
    def __init__(self, x: int, y: int, width: int = None, height: int = None, 
                 text: str = "", callback: Callable = None, 
                 color: Tuple[int, int, int] = None,
                 padding: Tuple[int, int] = None, min_width: int = None, min_height: int = None):
        """
        Initialize button component.
        
        Args:
            x: X position
            y: Y position
            width: Button width (None for auto-size based on text)
            height: Button height (None for auto-size based on text)
            text: Button text
            callback: Click callback function
            color: Button color (default: primary color)
            padding: (horizontal, vertical) padding in pixels (default: from DesignSystem)
            min_width: Minimum button width (default: 80)
            min_height: Minimum button height (default: 32)
        """
        # Calculate size based on text if not provided
        if width is None or height is None:
            renderer = get_renderer()
            text_width, text_height = renderer.measure_text(text, 'label')
            
            # Use provided padding or default from DesignSystem
            if padding is None:
                h_padding = DesignSystem.SPACING['md'] * 2
                v_padding = DesignSystem.SPACING['sm'] * 2
            else:
                h_padding, v_padding = padding
            
            # Calculate auto size
            auto_width = text_width + h_padding
            auto_height = text_height + v_padding
            
            # Apply minimums
            if min_width is None:
                min_width = 80
            if min_height is None:
                min_height = 32
            
            # Use provided size or auto-calculated size
            final_width = width if width is not None else max(auto_width, min_width)
            final_height = height if height is not None else max(auto_height, min_height)
        else:
            final_width = width
            final_height = height
        
        super().__init__(x, y, final_width, final_height)
        self.text = text
        self.color = color or DesignSystem.COLORS['primary']
        self.hovered = False
        self.pressed = False
        self.animation_scale = 1.0
        self.padding = padding or (DesignSystem.SPACING['md'] * 2, DesignSystem.SPACING['sm'] * 2)
        self.min_width = min_width or 80
        self.min_height = min_height or 32
        
        # Connect callback to port system if provided
        if callback:
            self.connect_port('on_click', callback)
    
    def set_text(self, text: str, auto_resize: bool = True):
        """
        Set button text and optionally resize button.
        
        Args:
            text: New button text
            auto_resize: If True, automatically resize button to fit new text
        """
        if self.text != text:
            self.text = text
            if auto_resize:
                self._resize_to_text()
            self.mark_dirty()
    
    def _resize_to_text(self):
        """Resize button to fit current text."""
        renderer = self._renderer
        text_width, text_height = renderer.measure_text(self.text, 'label')
        
        h_padding, v_padding = self.padding
        new_width = max(text_width + h_padding, self.min_width)
        new_height = max(text_height + v_padding, self.min_height)
        
        # Update rect size while maintaining position
        old_x, old_y = self.rect.x, self.rect.y
        self.rect.width = new_width
        self.rect.height = new_height
        self.rect.x, self.rect.y = old_x, old_y  # Keep top-left position
        
        # Mark dirty to trigger redraw
        self.mark_dirty()
    
    def get_preferred_size(self) -> Tuple[int, int]:
        """
        Get the preferred size of the button based on current text.
        
        Returns:
            (width, height) tuple
        """
        renderer = self._renderer
        text_width, text_height = renderer.measure_text(self.text, 'label')
        
        h_padding, v_padding = self.padding
        width = max(text_width + h_padding, self.min_width)
        height = max(text_height + v_padding, self.min_height)
        
        return (width, height)
    
    def set_size(self, width: int = None, height: int = None, keep_position: str = 'top-left'):
        """
        Set button size manually.
        
        Args:
            width: New width (None to keep current or auto-calculate)
            height: New height (None to keep current or auto-calculate)
            keep_position: How to maintain position - 'top-left', 'center', 'bottom-right'
        """
        if width is None:
            width = self.rect.width
        if height is None:
            height = self.rect.height
        
        # Store old position based on keep_position
        if keep_position == 'center':
            old_center = self.rect.center
        elif keep_position == 'bottom-right':
            old_bottom = self.rect.bottom
            old_right = self.rect.right
        else:  # top-left
            old_x, old_y = self.rect.x, self.rect.y
        
        # Update size
        self.rect.width = width
        self.rect.height = height
        
        # Restore position
        if keep_position == 'center':
            self.rect.center = old_center
        elif keep_position == 'bottom-right':
            self.rect.right = old_right
            self.rect.bottom = old_bottom
        # else: top-left - already correct
        
        self.mark_dirty()
        
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
        super().update(dt)
        target_scale = 1.05 if self.hovered else 1.0
        if abs(self.animation_scale - target_scale) > 0.01:
            diff = target_scale - self.animation_scale
            self.animation_scale += diff * dt * 10
            self.mark_dirty()
            
    def _draw_self(self, surface: pygame.Surface):
        """Draw modern flat button - no borders, no rounded corners."""
        renderer = self._renderer
        
        # Calculate color based on state
        if self.pressed:
            bg_color = renderer.darken_color(self.color, 0.15)
        elif self.hovered:
            bg_color = renderer.lighten_color(self.color, 0.1)
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
        
        # Draw flat background - no shadow, no border, no rounded corners
        renderer.draw_rect(surface, scaled_rect, bg_color,
                         border_radius=0)  # No rounded corners
        
        # Optional: subtle bottom accent line when hovered (modern flat design)
        if self.hovered and not self.pressed:
            accent_color = renderer.lighten_color(self.color, 0.2)
            pygame.draw.line(surface, accent_color,
                           (scaled_rect.x, scaled_rect.bottom - 1),
                           (scaled_rect.right, scaled_rect.bottom - 1), 2)
        
        # Draw text - ensure contrast with background
        # Calculate text color based on background brightness
        bg_brightness = sum(bg_color) / 3.0
        if bg_brightness > 200:  # Light background - use dark text
            text_color = (0, 0, 0)  # Black
        else:  # Dark background - use light text
            text_color = DesignSystem.COLORS['text']
        
        # Calculate text position (centered)
        text_width, text_height = renderer.measure_text(self.text, 'label')
        text_x = scaled_rect.centerx - text_width // 2
        text_y = scaled_rect.centery - text_height // 2
        renderer.render_text(surface, self.text, (text_x, text_y),
                           size='label', color=text_color)


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
                self.mark_dirty()
            return True
        return False
        
    def update(self, dt: float):
        """Update cursor blink."""
        super().update(dt)
        self.cursor_timer += dt
        if self.cursor_timer > 0.5:
            was_visible = self.cursor_visible
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0.0
            if was_visible != self.cursor_visible:
                self.mark_dirty()
            
    def _draw_self(self, surface: pygame.Surface):
        """Draw modern flat text input - no borders, no rounded corners."""
        renderer = self._renderer
        
        # Modern flat design: subtle background change on focus, no border
        if self.active:
            # Slightly brighter background when active
            bg_color = tuple(min(255, c + 5) for c in DesignSystem.COLORS['surface'])
        else:
            bg_color = DesignSystem.COLORS['surface']
        
        # Draw flat background - no border, no rounded corners
        renderer.draw_rect(surface, self.rect,
                         bg_color,
                         border_radius=0)  # No rounded corners
        
        # Optional: subtle bottom border line for modern flat design
        if self.active:
            # Active state: primary color accent line at bottom
            accent_color = DesignSystem.COLORS['primary']
            pygame.draw.line(surface, accent_color,
                           (self.rect.x, self.rect.bottom - 1),
                           (self.rect.right, self.rect.bottom - 1), 2)
        else:
            # Inactive state: subtle divider line
            divider_color = tuple(max(0, c - 15) for c in DesignSystem.COLORS['surface'])
            pygame.draw.line(surface, divider_color,
                           (self.rect.x, self.rect.bottom - 1),
                           (self.rect.right, self.rect.bottom - 1), 1)
        
        # Draw text
        display_text = self.text if self.text else self.placeholder
        text_color = DesignSystem.COLORS['text'] if self.text else DesignSystem.COLORS['text_tertiary']
        
        # Clip text if too long
        padding = DesignSystem.SPACING['sm']
        clip_rect = pygame.Rect(
            self.rect.x + padding,
            self.rect.y,
            self.rect.width - padding * 2,
            self.rect.height
        )
        old_clip = surface.get_clip()
        surface.set_clip(clip_rect)
        
        text_height = renderer.measure_text(display_text, 'label')[1]
        text_y = self.rect.y + (self.rect.height - text_height) // 2
        renderer.render_text(surface, display_text, (clip_rect.x, text_y),
                           size='label', color=text_color)
        
        # Draw cursor - modern thin line
        if self.active and self.cursor_visible:
            cursor_text = self.text[:self.cursor_pos]
            cursor_width = renderer.measure_text(cursor_text, 'label')[0]
            cursor_x = clip_rect.x + cursor_width
            if clip_rect.x <= cursor_x <= clip_rect.right:
                # Modern thin cursor line
                cursor_color = DesignSystem.COLORS['primary']
                pygame.draw.line(surface, cursor_color,
                               (cursor_x, self.rect.y + 4),
                               (cursor_x, self.rect.bottom - 4), 1)
        
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
                self.mark_dirty()
                return True
        return False
        
    def _draw_self(self, surface: pygame.Surface):
        """Draw checkbox using optimized renderer."""
        renderer = self._renderer
        
        # Draw modern flat checkbox - no border, no rounded corners
        bg_color = DesignSystem.COLORS['primary'] if self.checked else DesignSystem.COLORS['surface_light']
        renderer.draw_rect(surface, self.rect,
                         bg_color,
                         border_radius=0)  # No rounded corners
        
        # Optional: subtle border line when not checked
        if not self.checked:
            border_color = tuple(max(0, c - 20) for c in DesignSystem.COLORS['surface_light'])
            pygame.draw.rect(surface, border_color, self.rect, width=1)
        
        # Draw checkmark
        if self.checked:
            points = [
                (self.rect.x + 5, self.rect.y + 10),
                (self.rect.x + 9, self.rect.y + 14),
                (self.rect.x + 15, self.rect.y + 6)
            ]
            pygame.draw.lines(surface, DesignSystem.COLORS['text'], False, points, 2)
        
        # Draw label
        label_height = renderer.measure_text(self.text, 'label')[1]
        label_y = self.rect.y + (self.rect.height - label_height) // 2
        renderer.render_text(surface, self.text,
                           (self.rect.right + DesignSystem.SPACING['sm'], label_y),
                           size='label',
                           color=DesignSystem.COLORS['text'])


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
        self.mark_dirty()
            
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
                    self.mark_dirty()
                    return True
            elif event.button == 4:  # Scroll up
                self.scroll_y = max(0, self.scroll_y - 20)
                self.mark_dirty()
            elif event.button == 5:  # Scroll down
                self.scroll_y += 20
                self.mark_dirty()
        return False
        
    def _draw_self(self, surface: pygame.Surface):
        """Draw items list using optimized renderer."""
        renderer = self._renderer
        
        # Draw modern flat background - no border, no rounded corners
        renderer.draw_rect(surface, self.rect,
                         DesignSystem.COLORS['surface'],
                         border_radius=0)  # No rounded corners
        
        # Clip to item area
        clip_rect = self.rect.inflate(-DesignSystem.SPACING['sm'], -DesignSystem.SPACING['sm'])
        old_clip = surface.get_clip()
        surface.set_clip(clip_rect)
        
        y_offset = clip_rect.y - self.scroll_y
        for i, (name, item_type) in enumerate(self.items):
            item_y = y_offset + i * self.item_height
            if item_y + self.item_height < clip_rect.y:
                continue
            if item_y > clip_rect.bottom:
                break
                
            item_rect = pygame.Rect(clip_rect.x, item_y, clip_rect.width, self.item_height)
            
            # Highlight selected - modern flat style
            if i == self.selected_index:
                # Selected: primary color background, no rounded corners
                renderer.draw_rect(surface, item_rect,
                                 DesignSystem.COLORS['primary'],
                                 border_radius=0)  # No rounded corners
                text_color = DesignSystem.COLORS['text']
            else:
                # Optional: subtle hover effect on even rows
                if i % 2 == 0:
                    hover_bg = tuple(max(0, c - 3) for c in DesignSystem.COLORS['surface'])
                    renderer.draw_rect(surface, item_rect,
                                     hover_bg,
                                     border_radius=0)
                text_color = DesignSystem.COLORS['text_secondary']
            
            # Draw item name
            name_height = renderer.measure_text(name, 'console')[1]
            name_y = item_rect.y + (self.item_height - name_height) // 2
            renderer.render_text(surface, name,
                               (item_rect.x + DesignSystem.SPACING['sm'], name_y),
                               size='console',
                               color=text_color)
            
            # Draw item type if available
            if item_type:
                type_height = renderer.measure_text(item_type, 'small')[1]
                type_y = item_rect.y + name_height + 2
                if type_y + type_height < item_rect.bottom:
                    renderer.render_text(surface, item_type,
                                       (item_rect.x + DesignSystem.SPACING['sm'], type_y),
                                       size='small',
                                       color=DesignSystem.COLORS['text_tertiary'])
        
        surface.set_clip(old_clip)

