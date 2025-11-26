"""Interactive UI components with optimized rendering."""
import pygame
import inspect
from typing import Optional, List, Tuple, Callable

from .base import UIComponent
from ..design.design_system import DesignSystem
from ..renderers.ui_renderer import get_renderer

# Try to import clipboard support (optional)
try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False


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
            # Measure text - use space if text is empty to get proper height
            measure_text = text if text else " "
            text_width, text_height = renderer.measure_text(measure_text, 'label')
            # If text is empty, width should be 0 but keep height
            if not text:
                text_width = 0
            
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
        
        # Ensure minimum dimensions
        if final_width <= 0:
            final_width = min_width if min_width else 80
        if final_height <= 0:
            final_height = min_height if min_height else 32
        
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
        # Measure text - use space if text is empty to get proper height
        measure_text = self.text if self.text else " "
        text_width, text_height = renderer.measure_text(measure_text, 'label')
        # If text is empty, width should be 0 but keep height
        if not self.text:
            text_width = 0
        
        h_padding, v_padding = self.padding
        new_width = max(text_width + h_padding, self.min_width)
        new_height = max(text_height + v_padding, self.min_height)
        
        # Ensure minimum dimensions
        if new_width <= 0:
            new_width = self.min_width
        if new_height <= 0:
            new_height = self.min_height
        
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
        # Skip drawing if rect has zero dimensions
        if self.rect.width <= 0 or self.rect.height <= 0:
            return
        
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
        # Ensure scale is valid
        if scale <= 0:
            scale = 1.0
        
        scaled_rect = pygame.Rect(
            self.rect.centerx - self.rect.width * scale / 2,
            self.rect.centery - self.rect.height * scale / 2,
            self.rect.width * scale,
            self.rect.height * scale
        )
        
        # Ensure scaled rect has valid dimensions
        if scaled_rect.width <= 0 or scaled_rect.height <= 0:
            return
        
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
        if self.text:  # Only draw text if it exists
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
    """Text input component with enhanced editing capabilities and optimized rendering.
    
    Features:
    - Performance-optimized with text measurement caching
    - Smart text scrolling and display
    - Enhanced editing capabilities (copy, paste, select all, etc.)
    - Flexible styling and configuration
    - Auto-sizing support
    """
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 default_text: str = "", placeholder: str = "",
                 auto_size: bool = False, min_width: int = None, max_width: int = None,
                 padding: int = None, align: str = 'left'):
        """
        Initialize text input component.
        
        Args:
            x: X position
            y: Y position
            width: Input width (None for auto-size if auto_size=True)
            height: Input height
            default_text: Default text value
            placeholder: Placeholder text when empty
            auto_size: Automatically size based on text content
            min_width: Minimum width (when auto_size=True)
            max_width: Maximum width (when auto_size=True)
            padding: Internal padding (None for auto from DesignSystem)
            align: Text alignment ('left', 'center', 'right')
        """
        # Handle auto-sizing
        if auto_size and width is None:
            renderer = get_renderer()
            text_width, text_height = renderer.measure_text(default_text or placeholder, 'label')
            padding_val = padding if padding is not None else DesignSystem.SPACING['sm'] * 2
            width = text_width + padding_val * 2
            if min_width:
                width = max(width, min_width)
            if max_width:
                width = min(width, max_width)
        
        super().__init__(x, y, width, height)
        self.text = default_text
        self.placeholder = placeholder
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0.0
        self.cursor_pos = len(self.text)
        self.selection_start = -1  # Selection start position (-1 means no selection)
        self.scroll_offset = 0  # Horizontal scroll offset for long text
        self.modifiers = {'ctrl': False, 'shift': False}  # Track modifier keys
        self.auto_size = auto_size
        self.min_width = min_width
        self.max_width = max_width
        self.padding = padding if padding is not None else DesignSystem.SPACING['sm']
        self.align = align
        
        # Performance optimization: cache text measurements
        self._cached_measurements = {}
        self._cached_text_hash = None
        
    def _find_word_boundary(self, pos: int, direction: int) -> int:
        """Find word boundary for Ctrl+Left/Right navigation.
        
        Args:
            pos: Current cursor position
            direction: -1 for left, 1 for right
            
        Returns:
            New cursor position
        """
        if direction < 0:  # Moving left
            if pos == 0:
                return 0
            # Skip whitespace
            while pos > 0 and self.text[pos - 1].isspace():
                pos -= 1
            # Skip word characters
            while pos > 0 and not self.text[pos - 1].isspace():
                pos -= 1
            return pos
        else:  # Moving right
            if pos >= len(self.text):
                return len(self.text)
            # Skip word characters
            while pos < len(self.text) and not self.text[pos].isspace():
                pos += 1
            # Skip whitespace
            while pos < len(self.text) and self.text[pos].isspace():
                pos += 1
            return pos
    
    def _get_selection_range(self) -> Tuple[int, int]:
        """Get selection range (start, end) with start <= end."""
        if self.selection_start == -1:
            return (self.cursor_pos, self.cursor_pos)
        start = min(self.selection_start, self.cursor_pos)
        end = max(self.selection_start, self.cursor_pos)
        return (start, end)
    
    def _get_selected_text(self) -> str:
        """Get currently selected text."""
        start, end = self._get_selection_range()
        return self.text[start:end]
    
    def _delete_selection(self):
        """Delete selected text and update cursor."""
        if self.selection_start == -1:
            return
        start, end = self._get_selection_range()
        self.text = self.text[:start] + self.text[end:]
        self.cursor_pos = start
        self.selection_start = -1
    
    def _measure_text_cached(self, text: str) -> Tuple[int, int]:
        """Measure text with caching for performance."""
        cache_key = text
        if cache_key not in self._cached_measurements:
            self._cached_measurements[cache_key] = self._renderer.measure_text(text, 'label')
        return self._cached_measurements[cache_key]
    
    def _update_cursor_from_mouse(self, mouse_x: int):
        """Update cursor position based on mouse click position with optimized search."""
        text_area_x = self.rect.x + self.padding
        
        # Binary search for optimal cursor position (more efficient than linear)
        best_pos = len(self.text)
        best_dist = float('inf')
        
        # Use binary search for better performance with long text
        low, high = 0, len(self.text)
        
        while low <= high:
            mid = (low + high) // 2
            test_text = self.text[:mid]
            text_width = self._measure_text_cached(test_text)[0]
            char_x = text_area_x + text_width - self.scroll_offset
            dist = abs(mouse_x - char_x)
            
            if dist < best_dist:
                best_dist = dist
                best_pos = mid
            
            if char_x < mouse_x:
                low = mid + 1
            else:
                high = mid - 1
        
        # Fine-tune with nearby positions
        for offset in [-1, 1, -2, 2]:
            test_pos = best_pos + offset
            if 0 <= test_pos <= len(self.text):
                test_text = self.text[:test_pos]
                text_width = self._measure_text_cached(test_text)[0]
                char_x = text_area_x + text_width - self.scroll_offset
                dist = abs(mouse_x - char_x)
                if dist < best_dist:
                    best_dist = dist
                    best_pos = test_pos
        
        self.cursor_pos = best_pos
        self.selection_start = -1  # Clear selection on click
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle text input events with enhanced editing capabilities."""
        if not self.visible or not self.enabled:
            return False
        
        # Track modifier keys
        keys = pygame.key.get_pressed()
        self.modifiers['ctrl'] = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]
        self.modifiers['shift'] = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            was_active = self.active
            self.active = self.rect.collidepoint(event.pos) if hasattr(event, 'pos') else False
            if was_active != self.active:
                self.emit_signal('focus', self.active)
            
            if self.active and hasattr(event, 'pos'):
                # Update cursor position based on mouse click
                self._update_cursor_from_mouse(event.pos[0])
                self.selection_start = self.cursor_pos  # Start selection
                self.mark_dirty()
            
            return self.active
        elif event.type == pygame.MOUSEMOTION:
            if self.active and hasattr(event, 'pos') and self.rect.collidepoint(event.pos):
                # Extend selection while dragging
                if pygame.mouse.get_pressed()[0]:  # Left button held
                    self._update_cursor_from_mouse(event.pos[0])
                    if self.selection_start == -1:
                        self.selection_start = self.cursor_pos
                    self.mark_dirty()
        elif event.type == pygame.KEYDOWN and self.active:
            old_text = self.text
            handled = False
            
            # Handle Ctrl combinations
            if self.modifiers['ctrl']:
                if event.key == pygame.K_a:  # Ctrl+A: Select all
                    self.selection_start = 0
                    self.cursor_pos = len(self.text)
                    self.mark_dirty()
                    return True
                elif event.key == pygame.K_c:  # Ctrl+C: Copy
                    selected = self._get_selected_text()
                    if selected and HAS_CLIPBOARD:
                        try:
                            pyperclip.copy(selected)
                        except:
                            pass  # Clipboard not available
                    return True
                elif event.key == pygame.K_v:  # Ctrl+V: Paste
                    if HAS_CLIPBOARD:
                        try:
                            paste_text = pyperclip.paste()
                            if paste_text:
                                self._delete_selection()
                                self.text = self.text[:self.cursor_pos] + paste_text + self.text[self.cursor_pos:]
                                self.cursor_pos += len(paste_text)
                                handled = True
                        except:
                            pass  # Clipboard not available
                elif event.key == pygame.K_x:  # Ctrl+X: Cut
                    selected = self._get_selected_text()
                    if selected:
                        if HAS_CLIPBOARD:
                            try:
                                pyperclip.copy(selected)
                            except:
                                pass
                        self._delete_selection()
                        handled = True
                elif event.key == pygame.K_LEFT:  # Ctrl+Left: Word left
                    self.cursor_pos = self._find_word_boundary(self.cursor_pos, -1)
                    if not self.modifiers['shift']:
                        self.selection_start = -1
                    handled = True
                elif event.key == pygame.K_RIGHT:  # Ctrl+Right: Word right
                    self.cursor_pos = self._find_word_boundary(self.cursor_pos, 1)
                    if not self.modifiers['shift']:
                        self.selection_start = -1
                    handled = True
            
            # Handle regular keys
            if not handled:
                if event.key == pygame.K_BACKSPACE:
                    if self.selection_start != -1:
                        self._delete_selection()
                        handled = True
                    elif self.cursor_pos > 0:
                        self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
                        self.cursor_pos = max(0, self.cursor_pos - 1)
                        handled = True
                elif event.key == pygame.K_DELETE:
                    if self.selection_start != -1:
                        self._delete_selection()
                        handled = True
                    elif self.cursor_pos < len(self.text):
                        self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos+1:]
                        handled = True
                elif event.key == pygame.K_LEFT:
                    if self.modifiers['shift']:
                        if self.selection_start == -1:
                            self.selection_start = self.cursor_pos
                        self.cursor_pos = max(0, self.cursor_pos - 1)
                    else:
                        self.selection_start = -1
                        self.cursor_pos = max(0, self.cursor_pos - 1)
                    handled = True
                elif event.key == pygame.K_RIGHT:
                    if self.modifiers['shift']:
                        if self.selection_start == -1:
                            self.selection_start = self.cursor_pos
                        self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
                    else:
                        self.selection_start = -1
                        self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
                    handled = True
                elif event.key == pygame.K_HOME:
                    if self.modifiers['shift']:
                        if self.selection_start == -1:
                            self.selection_start = self.cursor_pos
                        self.cursor_pos = 0
                    else:
                        self.selection_start = -1
                        self.cursor_pos = 0
                    handled = True
                elif event.key == pygame.K_END:
                    if self.modifiers['shift']:
                        if self.selection_start == -1:
                            self.selection_start = self.cursor_pos
                        self.cursor_pos = len(self.text)
                    else:
                        self.selection_start = -1
                        self.cursor_pos = len(self.text)
                    handled = True
                elif event.unicode and event.unicode.isprintable():
                    self._delete_selection()  # Delete selection if any
                    self.text = self.text[:self.cursor_pos] + event.unicode + self.text[self.cursor_pos:]
                    self.cursor_pos += 1
                    handled = True
            
            # Update scroll offset to keep cursor visible (optimized)
            if handled:
                text_area_width = self.rect.width - self.padding * 2
                cursor_text = self.text[:self.cursor_pos]
                cursor_width = self._measure_text_cached(cursor_text)[0]
                cursor_x = cursor_width - self.scroll_offset
                
                if cursor_x < 0:
                    self.scroll_offset = cursor_width
                elif cursor_x > text_area_width:
                    self.scroll_offset = cursor_width - text_area_width + self.padding
                
                # Update size if auto-sizing
                if self.auto_size:
                    self._update_size_from_text()
            
            # Emit change signal if text changed
            if self.text != old_text:
                self._cached_text_hash = None  # Invalidate cache
                self.emit_signal('change', {'text': self.text, 'old_text': old_text})
                self.emit_signal('on_change', self.text)
                # Update value port
                port = self.get_port('value')
                if port:
                    port.value = self.text
                
                # Update size if auto-sizing
                if self.auto_size:
                    self._update_size_from_text()
                
                self.mark_dirty()
            
            if handled:
                self.mark_dirty()
            return handled
        return False
    
    def _update_size_from_text(self):
        """Update input size based on text content (for auto-sizing)."""
        if not self.auto_size:
            return
        
        text_to_measure = self.text if self.text else self.placeholder
        text_width, text_height = self._measure_text_cached(text_to_measure)
        new_width = text_width + self.padding * 2
        
        if self.min_width:
            new_width = max(new_width, self.min_width)
        if self.max_width:
            new_width = min(new_width, self.max_width)
        
        if self.rect.width != new_width:
            old_right = self.rect.right
            self.rect.width = new_width
            # Keep right edge aligned if it was at a specific position
            # (This is a simple approach; can be enhanced with alignment options)
            self.mark_dirty()
    
    def set_text(self, text: str):
        """Set text programmatically."""
        if self.text != text:
            self.text = text
            self.cursor_pos = len(self.text)
            self._cached_text_hash = None  # Invalidate cache
            if self.auto_size:
                self._update_size_from_text()
            self.mark_dirty()
    
    def clear_cache(self):
        """Clear measurement cache (useful when font sizes change)."""
        self._cached_measurements.clear()
        self._cached_text_hash = None
        
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
        """Draw modern flat text input with selection highlighting."""
        # Skip drawing if rect has zero dimensions
        if self.rect.width <= 0 or self.rect.height <= 0:
            return
        
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
        
        # Clip text area
        padding = DesignSystem.SPACING['sm']
        clip_rect = pygame.Rect(
            self.rect.x + padding,
            self.rect.y,
            self.rect.width - padding * 2,
            self.rect.height
        )
        old_clip = surface.get_clip()
        surface.set_clip(clip_rect)
        
        # Draw selection highlight if any (optimized with caching)
        if self.selection_start != -1 and self.selection_start != self.cursor_pos:
            start, end = self._get_selection_range()
            start_text = self.text[:start]
            end_text = self.text[:end]
            start_width = self._measure_text_cached(start_text)[0]
            end_width = self._measure_text_cached(end_text)[0]
            
            if self.align == 'center':
                text_width = self._measure_text_cached(self.text)[0]
                base_x = clip_rect.centerx - text_width // 2
                start_x = base_x + start_width
                end_x = base_x + end_width
            elif self.align == 'right':
                text_width = self._measure_text_cached(self.text)[0]
                base_x = clip_rect.right - text_width
                start_x = base_x + start_width
                end_x = base_x + end_width
            else:  # left
                start_x = clip_rect.x + start_width - self.scroll_offset
                end_x = clip_rect.x + end_width - self.scroll_offset
            
            if start_x < clip_rect.right and end_x > clip_rect.x:
                # Clip selection rect to visible area
                sel_x = max(clip_rect.x, start_x)
                sel_width = min(clip_rect.right, end_x) - sel_x
                if sel_width > 0:
                    sel_rect = pygame.Rect(sel_x, clip_rect.y + 2, sel_width, clip_rect.height - 4)
                    # Draw selection background with semi-transparent primary color
                    selection_color = tuple(min(255, c + 30) for c in DesignSystem.COLORS['primary'])
                    renderer.draw_rect(surface, sel_rect, selection_color, border_radius=0)
        
        # Draw text with proper scrolling and alignment (optimized)
        display_text = self.text if self.text else self.placeholder
        text_color = DesignSystem.COLORS['text'] if self.text else DesignSystem.COLORS['text_tertiary']
        
        text_width, text_height = self._measure_text_cached(display_text)
        text_y = self.rect.y + (self.rect.height - text_height) // 2
        
        # Calculate text position based on alignment
        if self.align == 'center':
            text_x = clip_rect.centerx - text_width // 2
        elif self.align == 'right':
            text_x = clip_rect.right - text_width
        else:  # left
            text_x = clip_rect.x - self.scroll_offset
        
        renderer.render_text(surface, display_text, (text_x, text_y),
                           size='label', color=text_color)
        
        # Draw cursor - modern thin line (optimized)
        if self.active and self.cursor_visible:
            cursor_text = self.text[:self.cursor_pos]
            cursor_width = self._measure_text_cached(cursor_text)[0]
            
            if self.align == 'center':
                cursor_x = clip_rect.centerx - text_width // 2 + cursor_width
            elif self.align == 'right':
                cursor_x = clip_rect.right - text_width + cursor_width
            else:  # left
                cursor_x = clip_rect.x + cursor_width - self.scroll_offset
            
            if clip_rect.x <= cursor_x <= clip_rect.right:
                # Modern thin cursor line
                cursor_color = DesignSystem.COLORS['primary']
                cursor_height = self.rect.height - 8
                pygame.draw.line(surface, cursor_color,
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
                self.mark_dirty()
                return True
        return False
        
    def _draw_self(self, surface: pygame.Surface):
        """Draw checkbox using optimized renderer."""
        # Skip drawing if rect has zero dimensions
        if self.rect.width <= 0 or self.rect.height <= 0:
            return
        
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
            # Ensure checkmark fits within rect
            check_size = min(self.rect.width - 4, self.rect.height - 4, 10)
            offset_x = (self.rect.width - check_size) // 2
            offset_y = (self.rect.height - check_size) // 2
            points = [
                (self.rect.x + offset_x, self.rect.y + offset_y + check_size * 0.6),
                (self.rect.x + offset_x + check_size * 0.4, self.rect.y + offset_y + check_size),
                (self.rect.x + offset_x + check_size, self.rect.y + offset_y)
            ]
            pygame.draw.lines(surface, DesignSystem.COLORS['text'], False, points, 2)
        
        # Draw label if text exists
        if self.text:
            label_height = renderer.measure_text(self.text, 'label')[1]
            label_y = self.rect.y + (self.rect.height - label_height) // 2
            renderer.render_text(surface, self.text,
                               (self.rect.right + DesignSystem.SPACING['sm'], label_y),
                               size='label',
                               color=DesignSystem.COLORS['text'])


class Items(UIComponent):
    """Enhanced list items component with selection, search, and improved display."""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height)
        self.items: List[Tuple[str, str]] = []  # List of (name, type) tuples
        self.filtered_items: List[Tuple[str, str]] = []  # Filtered items for display
        self.selected_index = -1
        self.scroll_y = 0
        self.item_height = 36  # Increased for better readability
        self.on_select: Optional[Callable] = None
        self.search_text = ""  # Search filter
        self.show_search = False  # Show search box
        self.hovered_index = -1  # Hovered item index
        
    def set_items(self, items: List[Tuple[str, str]]):
        """Set items list."""
        if items and isinstance(items[0], str):
            self.items = [(item, "") for item in items]
        else:
            self.items = items
        self._update_filtered_items()
        self.mark_dirty()
    
    def _update_filtered_items(self):
        """Update filtered items based on search text."""
        if not self.search_text:
            self.filtered_items = self.items
        else:
            search_lower = self.search_text.lower()
            self.filtered_items = [
                item for item in self.items
                if search_lower in item[0].lower() or (item[1] and search_lower in item[1].lower())
            ]
        # Reset selection if current selection is out of bounds
        if self.selected_index >= len(self.filtered_items):
            self.selected_index = -1
        self.mark_dirty()
    
    def set_search(self, search_text: str):
        """Set search filter text."""
        if self.search_text != search_text:
            self.search_text = search_text
            self._update_filtered_items()
    
    def clear_search(self):
        """Clear search filter."""
        self.set_search("")
            
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle items list events with enhanced interaction."""
        if not self.visible or not self.enabled:
            return False
        
        # Calculate content area (excluding search box if shown)
        content_y = self.rect.y + (40 if self.show_search else 0)
        content_height = self.rect.height - (40 if self.show_search else 0)
        content_rect = pygame.Rect(self.rect.x, content_y, self.rect.width, content_height)
            
        if event.type == pygame.MOUSEMOTION:
            if content_rect.collidepoint(event.pos):
                rel_y = event.pos[1] - content_rect.y
                index = (rel_y + self.scroll_y) // self.item_height
                if 0 <= index < len(self.filtered_items):
                    self.hovered_index = index
                    self.mark_dirty()
                else:
                    self.hovered_index = -1
                    self.mark_dirty()
            else:
                if self.hovered_index != -1:
                    self.hovered_index = -1
                    self.mark_dirty()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if content_rect.collidepoint(event.pos):
                rel_y = event.pos[1] - content_rect.y
                index = (rel_y + self.scroll_y) // self.item_height
                if 0 <= index < len(self.filtered_items):
                    self.selected_index = index
                    # Emit selection signal
                    self.emit_signal('select', {'index': index, 'item': self.filtered_items[index]})
                    self.emit_signal('on_select', self.filtered_items[index])
                    if self.on_select:
                        self.on_select(self.filtered_items[index])
                    self.mark_dirty()
                    return True
            elif event.button == 4:  # Scroll up
                if content_rect.collidepoint(event.pos):
                    self.scroll_y = max(0, self.scroll_y - self.item_height * 2)
                    self.mark_dirty()
                    return True
            elif event.button == 5:  # Scroll down
                if content_rect.collidepoint(event.pos):
                    max_scroll = max(0, len(self.filtered_items) * self.item_height - content_height)
                    self.scroll_y = min(max_scroll, self.scroll_y + self.item_height * 2)
                    self.mark_dirty()
                    return True
        elif event.type == pygame.KEYDOWN:
            # Keyboard navigation
            if self.selected_index >= 0:
                if event.key == pygame.K_UP:
                    self.selected_index = max(0, self.selected_index - 1)
                    self._ensure_visible(self.selected_index)
                    self.mark_dirty()
                    return True
                elif event.key == pygame.K_DOWN:
                    self.selected_index = min(len(self.filtered_items) - 1, self.selected_index + 1)
                    self._ensure_visible(self.selected_index)
                    self.mark_dirty()
                    return True
                elif event.key == pygame.K_RETURN:
                    if 0 <= self.selected_index < len(self.filtered_items):
                        self.emit_signal('select', {'index': self.selected_index, 'item': self.filtered_items[self.selected_index]})
                        if self.on_select:
                            self.on_select(self.filtered_items[self.selected_index])
                        return True
        return False
    
    def _ensure_visible(self, index: int):
        """Ensure selected item is visible by adjusting scroll."""
        content_height = self.rect.height - (40 if self.show_search else 0)
        item_y = index * self.item_height
        visible_top = self.scroll_y
        visible_bottom = self.scroll_y + content_height
        
        if item_y < visible_top:
            self.scroll_y = item_y
        elif item_y + self.item_height > visible_bottom:
            self.scroll_y = item_y + self.item_height - content_height
        
    def _draw_self(self, surface: pygame.Surface):
        """Draw enhanced items list with improved styling, spacing, and search."""
        renderer = self._renderer
        
        # Draw modern flat background - no border, no rounded corners
        renderer.draw_rect(surface, self.rect,
                         DesignSystem.COLORS['surface'],
                         border_radius=0)  # No rounded corners
        
        # Draw search box if enabled
        content_y = self.rect.y
        content_height = self.rect.height
        if self.show_search:
            search_rect = pygame.Rect(
                self.rect.x + DesignSystem.SPACING['sm'],
                self.rect.y + DesignSystem.SPACING['sm'],
                self.rect.width - DesignSystem.SPACING['sm'] * 2,
                32
            )
            # Search box background
            renderer.draw_rect(surface, search_rect,
                             DesignSystem.COLORS['bg_panel'],
                             border_radius=0)
            # Search text
            search_display = self.search_text if self.search_text else "Search..."
            search_color = DesignSystem.COLORS['text'] if self.search_text else DesignSystem.COLORS['text_tertiary']
            renderer.render_text(surface, search_display,
                               (search_rect.x + DesignSystem.SPACING['sm'], 
                                search_rect.y + (search_rect.height - 16) // 2),
                               size='small',
                               color=search_color)
            content_y = search_rect.bottom + DesignSystem.SPACING['sm']
            content_height = self.rect.bottom - content_y
        
        # Clip to item area with proper padding
        horizontal_padding = DesignSystem.SPACING['md']
        clip_rect = pygame.Rect(
            self.rect.x + horizontal_padding,
            content_y,
            self.rect.width - horizontal_padding * 2,
            content_height
        )
        old_clip = surface.get_clip()
        surface.set_clip(clip_rect)
        
        # Draw items count if filtered (positioned to avoid overlap)
        count_text_surf = None
        if self.search_text and len(self.filtered_items) != len(self.items):
            count_text = f"{len(self.filtered_items)}/{len(self.items)}"
            count_text_surf = renderer.font_renderer.get_font('small').render(
                count_text, True, DesignSystem.COLORS['text_tertiary']
            )
            # Position at top-right, with padding
            count_x = clip_rect.right - count_text_surf.get_width() - DesignSystem.SPACING['xs']
            count_y = clip_rect.y + DesignSystem.SPACING['xs']
            surface.blit(count_text_surf, (count_x, count_y))
        
        # Calculate item layout with proper spacing
        item_padding = DesignSystem.SPACING['sm']  # Padding inside each item
        type_badge_min_width = 80  # Minimum space for type badge
        type_badge_padding = DesignSystem.SPACING['sm']  # Space between name and type
        
        y_offset = clip_rect.y - self.scroll_y
        for i, (name, item_type) in enumerate(self.filtered_items):
            item_y = y_offset + i * self.item_height
            if item_y + self.item_height < clip_rect.y:
                continue
            if item_y > clip_rect.bottom:
                break
                
            item_rect = pygame.Rect(clip_rect.x, item_y, clip_rect.width, self.item_height)
            
            # Determine item background color
            if i == self.selected_index:
                # Selected: primary color with subtle glow
                bg_color = DesignSystem.COLORS['primary']
                text_color = DesignSystem.COLORS['text']
                # Draw selection indicator line on left
                indicator_rect = pygame.Rect(item_rect.x, item_rect.y, 3, item_rect.height)
                renderer.draw_rect(surface, indicator_rect,
                                 DesignSystem.COLORS['primary_light'],
                                 border_radius=0)
            elif i == self.hovered_index:
                # Hovered: lighter background
                bg_color = DesignSystem.COLORS['surface_hover']
                text_color = DesignSystem.COLORS['text']
            else:
                # Normal: alternating row colors for better readability
                if i % 2 == 0:
                    bg_color = DesignSystem.COLORS['surface']
                else:
                    bg_color = DesignSystem.COLORS['surface_light']
                text_color = DesignSystem.COLORS['text_secondary']
            
            # Draw item background
            renderer.draw_rect(surface, item_rect, bg_color, border_radius=0)
            
            # Calculate available space for name (accounting for type badge if present)
            available_width = item_rect.width - item_padding * 2
            if item_type:
                # Reserve space for type badge + padding
                type_font = renderer.font_renderer.get_font('small')
                type_width = type_font.size(item_type)[0]
                type_total_width = type_width + type_badge_padding * 2
                available_width -= max(type_total_width, type_badge_min_width)
            
            # Draw item name with proper truncation
            name_x = item_rect.x + item_padding
            name_height = renderer.measure_text(name, 'label')[1]
            name_y = item_rect.y + (self.item_height - name_height) // 2
            
            # Truncate name if too long, ensuring no overlap
            display_name = name
            name_width = renderer.measure_text(name, 'label')[0]
            if name_width > available_width:
                # Truncate with ellipsis
                ellipsis_width = renderer.measure_text("...", 'label')[0]
                max_name_width = available_width - ellipsis_width
                display_name = name
                while renderer.measure_text(display_name, 'label')[0] > max_name_width and len(display_name) > 0:
                    display_name = display_name[:-1]
                display_name = display_name + "..."
            
            renderer.render_text(surface, display_name,
                               (name_x, name_y),
                               size='label',
                               color=text_color)
            
            # Draw item type badge if available (right-aligned with proper spacing)
            if item_type:
                type_font = renderer.font_renderer.get_font('small')
                type_surf = type_font.render(item_type, True, DesignSystem.COLORS['text_tertiary'])
                type_x = item_rect.right - type_surf.get_width() - item_padding
                type_y = item_rect.y + (self.item_height - type_surf.get_height()) // 2
                
                # Ensure type badge doesn't overlap with name
                name_end_x = name_x + renderer.measure_text(display_name, 'label')[0]
                if type_x < name_end_x + type_badge_padding:
                    # If overlap, don't draw type badge or adjust position
                    type_x = max(name_end_x + type_badge_padding, item_rect.right - type_surf.get_width() - item_padding)
                
                surface.blit(type_surf, (type_x, type_y))
        
        surface.set_clip(old_clip)
        
        # Draw scroll indicator if needed
        if len(self.filtered_items) * self.item_height > content_height:
            scrollbar_width = 6
            scrollbar_x = self.rect.right - scrollbar_width - 2
            total_content_height = len(self.filtered_items) * self.item_height
            scrollbar_height = max(20, int(content_height * (content_height / total_content_height)))
            scrollbar_y = content_y + int(self.scroll_y / total_content_height * content_height)
            scrollbar_rect = pygame.Rect(scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height)
            renderer.draw_rect(surface, scrollbar_rect,
                             DesignSystem.COLORS['border'],
                             border_radius=0)

