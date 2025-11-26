"""Base UI components with tree-based hierarchy and port-based message passing.

This module provides a tree-structured UI component system with optimized
rendering and real-time update capabilities.
"""
import pygame
import inspect
from typing import Optional, Dict, Any, List, Tuple, Callable

from ..design.design_system import DesignSystem
from ..renderers.ui_renderer import get_renderer, UIRenderer


class ComponentPort:
    """Port system for component communication and message passing."""
    
    def __init__(self, name: str, port_type: str = 'signal'):
        """
        Initialize a component port.
        
        Args:
            name: Port name/identifier
            port_type: Type of port - 'signal' (control signals), 
                      'callback' (callback functions), 'param' (parameters)
        """
        self.name = name
        self.port_type = port_type
        self.connections: List[Callable] = []
        self.value = None
        self.last_value = None
        
    def connect(self, handler: Callable):
        """Connect a handler function to this port."""
        if handler not in self.connections:
            self.connections.append(handler)
    
    def disconnect(self, handler: Callable):
        """Disconnect a handler from this port."""
        if handler in self.connections:
            self.connections.remove(handler)
    
    def emit(self, value: Any = None):
        """Emit a signal/value through this port."""
        self.value = value
        for handler in self.connections:
            try:
                if self.port_type == 'callback':
                    # Check if handler accepts parameters
                    try:
                        sig = inspect.signature(handler)
                        # Get parameters excluding 'self' for bound methods
                        params = list(sig.parameters.values())
                        # Remove 'self' if it's a bound method
                        if hasattr(handler, '__self__') and params and params[0].name == 'self':
                            params = params[1:]
                        
                        # Check if handler accepts any parameters (excluding self)
                        if len(params) == 0:
                            # Handler doesn't accept parameters
                            handler()
                        else:
                            # Handler accepts parameters, pass the value
                            handler(value)
                    except (ValueError, TypeError):
                        # If signature inspection fails, try calling with value
                        # and fall back to no args if it fails
                        try:
                            handler(value)
                        except TypeError:
                            handler()
                elif self.port_type == 'signal':
                    handler()
                elif self.port_type == 'param':
                    handler(self.name, value)
            except Exception as e:
                print(f"Error in port {self.name} handler: {e}")
    
    def get(self) -> Any:
        """Get current port value."""
        return self.value


class UIComponent:
    """Base class for all UI components with tree-based hierarchy.
    
    This class provides:
    - Tree structure for parent-child relationships
    - Port-based message passing system
    - Optimized rendering with dirty region tracking
    - Unified event handling and coordinate transformation
    """
    
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.visible = True
        self.enabled = True
        
        # Tree structure for parent-child relationships
        self.parent: Optional['UIComponent'] = None
        self.children: List['UIComponent'] = []
        self._z_order: int = 0  # For rendering order
        
        # Rendering optimization
        self._dirty: bool = True  # Component needs redraw
        self._renderer: UIRenderer = get_renderer()
        
        # Port system for message passing
        self.ports: Dict[str, ComponentPort] = {}
        self._setup_ports()
        
    def _setup_ports(self):
        """Setup default ports. Override in subclasses for custom ports."""
        # Control signal ports
        self.add_port('click', 'signal')
        self.add_port('hover', 'signal')
        self.add_port('focus', 'signal')
        self.add_port('change', 'signal')
        
        # Callback ports
        self.add_port('on_click', 'callback')
        self.add_port('on_hover', 'callback')
        self.add_port('on_change', 'callback')
        
        # Parameter ports
        self.add_port('value', 'param')
        self.add_port('config', 'param')
        
    def add_port(self, name: str, port_type: str = 'signal') -> ComponentPort:
        """Add a new port to this component."""
        port = ComponentPort(name, port_type)
        self.ports[name] = port
        return port
    
    def get_port(self, name: str) -> Optional[ComponentPort]:
        """Get a port by name."""
        return self.ports.get(name)
    
    def connect_port(self, port_name: str, handler: Callable):
        """Connect a handler to a port."""
        port = self.get_port(port_name)
        if port:
            port.connect(handler)
        else:
            # Auto-create port if it doesn't exist
            port = self.add_port(port_name, 'callback')
            port.connect(handler)
    
    def emit_signal(self, port_name: str, value: Any = None):
        """Emit a signal through a port."""
        port = self.get_port(port_name)
        if port:
            port.emit(value)
    
    # Tree structure methods
    def add_child(self, child: 'UIComponent', z_order: Optional[int] = None):
        """Add a child component to the tree.
        
        Args:
            child: Child component to add
            z_order: Optional z-order (higher = rendered later/on top)
        """
        if child.parent is not None:
            child.parent.remove_child(child)
        
        child.parent = self
        if z_order is not None:
            child._z_order = z_order
        
        self.children.append(child)
        self.children.sort(key=lambda c: c._z_order)
        self.mark_dirty()
    
    def remove_child(self, child: 'UIComponent'):
        """Remove a child component from the tree.
        
        Args:
            child: Child component to remove
        """
        if child in self.children:
            self.children.remove(child)
            child.parent = None
            self.mark_dirty()
    
    def get_root(self) -> 'UIComponent':
        """Get the root component of the tree.
        
        Returns:
            Root component (self if no parent)
        """
        current = self
        while current.parent is not None:
            current = current.parent
        return current
    
    def get_absolute_rect(self) -> pygame.Rect:
        """Get absolute rectangle position in screen coordinates.
        
        Returns:
            Absolute rectangle
        """
        abs_rect = self.rect.copy()
        current = self.parent
        while current is not None:
            abs_rect.x += current.rect.x
            abs_rect.y += current.rect.y
            current = current.parent
        return abs_rect
    
    def mark_dirty(self):
        """Mark this component and all parents as dirty (needs redraw)."""
        self._dirty = True
        if self.parent is not None:
            self.parent.mark_dirty()
    
    def is_dirty(self) -> bool:
        """Check if component needs redraw.
        
        Returns:
            True if dirty
        """
        return self._dirty
    
    def clear_dirty(self):
        """Clear dirty flag."""
        self._dirty = False
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame event with coordinate transformation.
        
        Args:
            event: Pygame event (pos should be relative to this component)
            
        Returns:
            True if event was handled
        """
        if not self.visible or not self.enabled:
            return False
        
        # Handle events in reverse z-order (top components first)
        for child in reversed(self.children):
            if child.handle_event(event):
                return True
        
        return False
    
    def update(self, dt: float):
        """Update component state and children.
        
        Args:
            dt: Delta time since last update
        """
        for child in self.children:
            child.update(dt)
    
    def draw(self, surface: pygame.Surface):
        """Draw component and children with optimized rendering.
        
        Args:
            surface: Target surface (coordinates relative to this component)
        """
        if not self.visible:
            return
        
        # Draw this component
        self._draw_self(surface)
        
        # Draw children in z-order
        for child in self.children:
            if child.visible:
                # Create clipping surface for child
                child_abs_rect = pygame.Rect(
                    self.rect.x + child.rect.x,
                    self.rect.y + child.rect.y,
                    child.rect.width,
                    child.rect.height
                )
                
                # Only draw if child is within bounds
                if child_abs_rect.colliderect(surface.get_rect()):
                    # Save original position
                    orig_x, orig_y = child.rect.x, child.rect.y
                    
                    # Create subsurface for child
                    try:
                        child_surface = surface.subsurface(child_abs_rect)
                        # Set child position relative to its surface
                        child.rect.x = 0
                        child.rect.y = 0
                        child.draw(child_surface)
                        # Restore original position
                        child.rect.x, child.rect.y = orig_x, orig_y
                    except ValueError:
                        # Subsurface creation failed (out of bounds)
                        pass
        
        self.clear_dirty()
    
    def _draw_self(self, surface: pygame.Surface):
        """Draw this component itself (override in subclasses).
        
        Args:
            surface: Target surface
        """
        pass


class Panel(UIComponent):
    """Modern panel container component with flat design - no borders, no rounded corners."""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 title: str = "", show_border: bool = False):
        super().__init__(x, y, width, height)
        self.title = title
        self.show_border = show_border  # Optional subtle border line
        
    def _draw_self(self, surface: pygame.Surface):
        """Draw modern flat panel - no rounded corners."""
        renderer = self._renderer
        
        # Draw panel background - flat, no rounded corners
        renderer.draw_rect(surface, self.rect, 
                          DesignSystem.COLORS['bg_panel'],
                          border_radius=0)  # No rounded corners
        
        # Optional subtle border line (modern flat design)
        if self.show_border:
            # Single subtle line at edges
            divider_color = tuple(max(0, c - 10) for c in DesignSystem.COLORS['bg_panel'])
            # Top line
            pygame.draw.line(surface, divider_color,
                           (self.rect.x, self.rect.y),
                           (self.rect.right, self.rect.y), 1)
            # Bottom line
            pygame.draw.line(surface, divider_color,
                           (self.rect.x, self.rect.bottom - 1),
                           (self.rect.right, self.rect.bottom - 1), 1)
        
        # Draw title if present
        if self.title:
            renderer.render_text(surface, self.title,
                               (self.rect.x + DesignSystem.SPACING['md'],
                                self.rect.y + DesignSystem.SPACING['sm']),
                               size='label',
                               color=DesignSystem.COLORS['text_label'])
            
            # Draw title underline
            title_width = renderer.measure_text(self.title, 'label')[0]
            underline_y = self.rect.y + DesignSystem.SPACING['sm'] + \
                         renderer.measure_text(self.title, 'label')[1] + 2
            underline_x = self.rect.x + DesignSystem.SPACING['md']
            pygame.draw.line(surface, DesignSystem.COLORS['primary'],
                           (underline_x, underline_y),
                           (underline_x + title_width, underline_y), 1)


class Card(UIComponent):
    """Modern card component with clean flat design and automatic layout management for children."""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 title: str = "", show_shadow: bool = False,
                 layout_direction: str = 'column',  # 'column' or 'row'
                 content_padding: str = 'md',  # 'sm', 'md', 'lg'
                 child_gap: int = None,  # None for auto from DesignSystem
                 auto_layout: bool = True):  # Enable automatic layout
        super().__init__(x, y, width, height)
        self.title = title
        self.show_shadow = show_shadow
        self._header_height = 40 if title else 0
        self.layout_direction = layout_direction  # 'column' or 'row'
        self.content_padding = content_padding
        self.child_gap = child_gap if child_gap is not None else DesignSystem.SPACING['sm']
        self.auto_layout = auto_layout
        self._layout_dirty = True  # Track if layout needs recalculation
        
    def add_child(self, child: 'UIComponent', z_order: Optional[int] = None):
        """Add a child component and mark layout as dirty."""
        super().add_child(child, z_order)
        self._layout_dirty = True
    
    def remove_child(self, child: 'UIComponent'):
        """Remove a child component and mark layout as dirty."""
        super().remove_child(child)
        self._layout_dirty = True
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events for card and children with coordinate transformation."""
        if not self.visible or not self.enabled:
            return False
        
        # Transform event position relative to card's content area
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            if hasattr(event, 'pos') and self.rect.collidepoint(event.pos):
                # Convert to content area coordinates
                rel_event = pygame.event.Event(event.type)
                rel_event.pos = (event.pos[0] - self.rect.x, 
                               event.pos[1] - self.rect.y - self._header_height)
                rel_event.button = getattr(event, 'button', None)
                rel_event.buttons = getattr(event, 'buttons', None)
                rel_event.rel = getattr(event, 'rel', None)
                
                # Pass to children (handled by parent class)
                return super().handle_event(rel_event)
        return False
    
    def _draw_self(self, surface: pygame.Surface):
        """Draw modern flat card with no borders and no rounded corners."""
        renderer = self._renderer
        
        # Draw card background - flat, no border, no rounded corners
        renderer.draw_rect(surface, self.rect,
                         DesignSystem.COLORS['surface'],
                         border_radius=0)  # No rounded corners
        
        # Draw subtle shadow if enabled (optional, modern flat design)
        if self.show_shadow:
            # Subtle shadow effect using a darker rectangle offset
            shadow_rect = pygame.Rect(
                self.rect.x + 2,
                self.rect.y + 2,
                self.rect.width,
                self.rect.height
            )
            shadow_color = tuple(max(0, c - 20) for c in DesignSystem.COLORS['surface'])
            renderer.draw_rect(surface, shadow_rect,
                             shadow_color,
                             border_radius=0)
            # Draw main card on top
            renderer.draw_rect(surface, self.rect,
                             DesignSystem.COLORS['surface'],
                             border_radius=0)
        
        # Draw title header if present - modern flat style
        if self.title:
            header_rect = pygame.Rect(self.rect.x, self.rect.y, 
                                     self.rect.width, self._header_height)
            # Slightly darker background for header
            header_bg = tuple(max(0, c - 10) for c in DesignSystem.COLORS['surface'])
            renderer.draw_rect(surface, header_rect,
                             header_bg,
                             border_radius=0)  # No rounded corners
            
            # Draw title text
            title_height = renderer.measure_text(self.title, 'label')[1]
            title_y = header_rect.y + (header_rect.height - title_height) // 2
            renderer.render_text(surface, self.title,
                               (header_rect.x + DesignSystem.SPACING['md'], title_y),
                               size='label',
                               color=DesignSystem.COLORS['text'])
    
    def _update_children_layout(self):
        """Update children layout positions based on layout settings."""
        if not self.auto_layout or not self.children:
            return
        
        # Get content area
        content_area = self.get_content_area()
        padding = DesignSystem.SPACING[self.content_padding]
        
        # Calculate available space
        available_rect = pygame.Rect(
            padding,
            padding,
            content_area.width - padding * 2,
            content_area.height - padding * 2
        )
        
        if self.layout_direction == 'row':
            # Horizontal layout
            current_x = available_rect.x
            max_height = 0
            
            for child in self.children:
                if not child.visible:
                    continue
                
                # Position child
                child.rect.x = current_x
                child.rect.y = available_rect.y
                
                # Update max height for alignment
                max_height = max(max_height, child.rect.height)
                
                # Move to next position
                current_x += child.rect.width + self.child_gap
            
            # Center align vertically if needed
            for child in self.children:
                if child.visible and child.rect.height < max_height:
                    child.rect.y = available_rect.y + (max_height - child.rect.height) // 2
        else:
            # Vertical layout (default)
            current_y = available_rect.y
            
            for child in self.children:
                if not child.visible:
                    continue
                
                # Position child
                child.rect.x = available_rect.x
                child.rect.y = current_y
                
                # Auto-width: fill available width if child width is 0 or very small
                if child.rect.width < 50:
                    child.rect.width = available_rect.width
                else:
                    # Ensure child doesn't exceed available width
                    child.rect.width = min(child.rect.width, available_rect.width)
                
                # Move to next position
                current_y += child.rect.height + self.child_gap
        
        self._layout_dirty = False
    
    def draw(self, surface: pygame.Surface):
        """Override draw to handle content area clipping and automatic layout."""
        if not self.visible:
            return
        
        # Update layout if dirty
        if self._layout_dirty:
            self._update_children_layout()
        
        # Draw card itself
        self._draw_self(surface)
        
        # Calculate content area (below title)
        content_area_abs = pygame.Rect(
            self.rect.x,
            self.rect.y + self._header_height,
            self.rect.width,
            self.rect.height - self._header_height
        )
        
        # Draw children with clipping
        old_clip = surface.get_clip()
        surface.set_clip(content_area_abs)
        
        # Draw children (parent class handles this, but we need coordinate adjustment)
        for child in self.children:
            if child.visible:
                child_abs_rect = pygame.Rect(
                    self.rect.x + child.rect.x,
                    self.rect.y + self._header_height + child.rect.y,
                    child.rect.width,
                    child.rect.height
                )
                
                if child_abs_rect.colliderect(content_area_abs):
                    orig_x, orig_y = child.rect.x, child.rect.y
                    try:
                        child_surface = surface.subsurface(child_abs_rect)
                        child.rect.x = 0
                        child.rect.y = 0
                        child.draw(child_surface)
                        child.rect.x, child.rect.y = orig_x, orig_y
                    except ValueError:
                        pass
        
        surface.set_clip(old_clip)
        self.clear_dirty()
    
    def set_layout(self, direction: str = None, padding: str = None, gap: int = None):
        """Update layout settings and mark layout as dirty.
        
        Args:
            direction: 'column' or 'row'
            padding: 'sm', 'md', or 'lg'
            gap: Gap between children in pixels
        """
        if direction is not None:
            self.layout_direction = direction
        if padding is not None:
            self.content_padding = padding
        if gap is not None:
            self.child_gap = gap
        self._layout_dirty = True
        self.mark_dirty()
    
    def get_content_area(self) -> pygame.Rect:
        """Get the content area rect (below title) for children placement.
        
        Returns:
            Rect with coordinates relative to card's content area start (0,0)
        """
        return pygame.Rect(
            0, 0,
            self.rect.width,
            self.rect.height - self._header_height
        )


class Label(UIComponent):
    """Modern text label component with optimized rendering and flexible layout.
    
    Features:
    - Automatic text truncation with ellipsis
    - Smart text wrapping
    - Performance-optimized with caching
    - Flexible alignment and styling
    - Auto-sizing based on content
    """
    
    def __init__(self, x: int, y: int, text: str, 
                 font_size: str = 'label', color: Tuple[int, int, int] = None,
                 align: str = 'left', max_width: int = None, wrap: bool = False,
                 truncate: bool = True, ellipsis: str = "...", 
                 auto_size: bool = True, min_width: int = None, min_height: int = None):
        """
        Initialize label component.
        
        Args:
            x: X position
            y: Y position
            text: Label text
            font_size: Font size key ('small', 'label', 'title', etc.)
            color: Text color
            align: Text alignment ('left', 'center', 'right')
            max_width: Maximum width for text wrapping/truncation
            wrap: Whether to wrap text if it exceeds max_width
            truncate: Whether to truncate text with ellipsis if exceeds max_width (when wrap=False)
            ellipsis: Ellipsis string for truncation
            auto_size: Automatically size based on text content
            min_width: Minimum width (when auto_size=True)
            min_height: Minimum height (when auto_size=True)
        """
        super().__init__(x, y, 0, 0)
        self.text = text
        self.font_size = font_size
        self.color = color or DesignSystem.COLORS['text']
        self.align = align  # 'left', 'center', 'right'
        self.max_width = max_width
        self.wrap = wrap
        self.truncate = truncate
        self.ellipsis = ellipsis
        self.auto_size = auto_size
        self.min_width = min_width
        self.min_height = min_height
        
        # Performance optimization: cache text measurements
        self._cached_measurements = {}
        self._cached_text_hash = None
        self._display_text = None  # Cached display text (after truncation/wrapping)
        self._display_lines = None  # Cached wrapped lines
        
        self._update_size()
        
    def _get_text_hash(self) -> str:
        """Get hash for current text state for caching."""
        return f"{self.text}|{self.max_width}|{self.wrap}|{self.truncate}"
    
    def _measure_text_cached(self, text: str) -> Tuple[int, int]:
        """Measure text with caching for performance."""
        cache_key = f"{text}|{self.font_size}"
        if cache_key not in self._cached_measurements:
            self._cached_measurements[cache_key] = self._renderer.measure_text(text, self.font_size)
        return self._cached_measurements[cache_key]
    
    def _update_size(self):
        """Update label size based on text with performance optimization."""
        renderer = self._renderer
        text_hash = self._get_text_hash()
        
        # Use cached display text if available
        if self._cached_text_hash == text_hash and self._display_text is not None:
            if self.wrap and self._display_lines:
                line_height = self._measure_text_cached('A')[1]
                width = min(self.max_width, max(line[0] for line in self._display_lines)) if self.max_width else max(line[0] for line in self._display_lines)
                height = line_height * len(self._display_lines)
            else:
                width, height = self._measure_text_cached(self._display_text)
            self.rect.width = width
            self.rect.height = height
            return
        
        # Calculate display text and size
        width, height = self._measure_text_cached(self.text)
        
        # Handle text wrapping if enabled
        if self.wrap and self.max_width and width > self.max_width:
            # Smart word wrapping with caching
            words = self.text.split(' ')
            lines = []
            current_line = []
            current_width = 0
            
            for word in words:
                word_width = self._measure_text_cached(word + ' ')[0]
                if current_width + word_width <= self.max_width or not current_line:
                    current_line.append(word)
                    current_width += word_width
                else:
                    line_text = ' '.join(current_line)
                    lines.append((self._measure_text_cached(line_text)[0], line_text))
                    current_line = [word]
                    current_width = word_width
            
            if current_line:
                line_text = ' '.join(current_line)
                lines.append((self._measure_text_cached(line_text)[0], line_text))
            
            # Cache wrapped lines
            self._display_lines = lines
            
            # Calculate total height for wrapped text
            line_height = self._measure_text_cached('A')[1]
            height = line_height * len(lines)
            width = min(width, self.max_width) if self.max_width else max(line[0] for line in lines)
            self._display_text = self.text  # Full text for wrapped display
        elif self.truncate and self.max_width and width > self.max_width:
            # Smart truncation with ellipsis
            ellipsis_width = self._measure_text_cached(self.ellipsis)[0]
            available_width = self.max_width - ellipsis_width
            
            # Binary search for optimal truncation point
            low, high = 0, len(self.text)
            best_text = self.text
            
            while low < high:
                mid = (low + high + 1) // 2
                test_text = self.text[:mid]
                test_width = self._measure_text_cached(test_text)[0]
                
                if test_width <= available_width:
                    best_text = test_text
                    low = mid
                else:
                    high = mid - 1
            
            self._display_text = best_text + self.ellipsis
            width = self.max_width
            height = self._measure_text_cached(self._display_text)[1]
            self._display_lines = None
        else:
            if self.max_width:
                width = min(width, self.max_width)
            self._display_text = self.text
            self._display_lines = None
        
        # Apply auto-sizing constraints
        if self.auto_size:
            if self.min_width:
                width = max(width, self.min_width)
            if self.min_height:
                height = max(height, self.min_height)
        
        self.rect.width = width
        self.rect.height = height
        
        # Cache results
        self._cached_text_hash = text_hash
        self.mark_dirty()
        
    def set_text(self, text: str):
        """Update label text."""
        if self.text != text:
            self.text = text
            self._cached_text_hash = None  # Invalidate cache
            self._update_size()
    
    def set_max_width(self, max_width: int):
        """Update maximum width."""
        if self.max_width != max_width:
            self.max_width = max_width
            self._cached_text_hash = None  # Invalidate cache
            self._update_size()
    
    def clear_cache(self):
        """Clear measurement cache (useful when font sizes change)."""
        self._cached_measurements.clear()
        self._cached_text_hash = None
        self._update_size()
        
    def _draw_self(self, surface: pygame.Surface):
        """Draw modern label using optimized renderer with cached display text."""
        renderer = self._renderer
        
        # Use cached display text/lines for performance
        if self._display_lines:
            # Draw wrapped lines
            line_height = self._measure_text_cached('A')[1]
            for i, (line_width, line_text) in enumerate(self._display_lines):
                # Calculate position based on alignment
                if self.align == 'center':
                    x_pos = self.rect.centerx - line_width // 2
                elif self.align == 'right':
                    x_pos = self.rect.right - line_width
                else:
                    x_pos = self.rect.x
                
                y_pos = self.rect.y + i * line_height
                renderer.render_text(surface, line_text, (x_pos, y_pos),
                                   size=self.font_size,
                                   color=self.color)
        else:
            # Single line text (use cached display text if available)
            display_text = self._display_text if self._display_text else self.text
            text_width = self._measure_text_cached(display_text)[0]
            
            # Calculate position based on alignment
            if self.align == 'center':
                pos = (self.rect.centerx - text_width // 2, self.rect.y)
            elif self.align == 'right':
                pos = (self.rect.right - text_width, self.rect.y)
            else:
                pos = (self.rect.x, self.rect.y)
            
            renderer.render_text(surface, display_text, pos,
                               size=self.font_size,
                               color=self.color)


class Field(UIComponent):
    """Modern field component (label + value display) with optimized rendering.
    
    Features:
    - Automatic layout optimization
    - Smart text truncation
    - Performance-optimized with caching
    - Flexible alignment and styling
    - Auto-sizing based on content
    """
    
    def __init__(self, x: int, y: int, width: int = None, height: int = None,
                 label: str = "", value: str = "", value_color: Tuple[int, int, int] = None,
                 show_background: bool = False, label_width: int = None,
                 label_align: str = 'left', value_align: str = 'right',
                 spacing: int = None, truncate_value: bool = True):
        """
        Initialize field component.
        
        Args:
            x: X position
            y: Y position
            width: Field width (None for auto-size)
            height: Field height (None for auto-size based on text)
            label: Label text
            value: Value text
            value_color: Value text color
            show_background: Whether to show subtle background
            label_width: Fixed width for label (None for auto-size)
            label_align: Label alignment ('left', 'center', 'right')
            value_align: Value alignment ('left', 'center', 'right')
            spacing: Spacing between label and value (None for auto from DesignSystem)
            truncate_value: Whether to truncate value text if it exceeds available space
        """
        self.label = label
        self.value = str(value)
        self.value_color = value_color or DesignSystem.COLORS['text']
        self.show_background = show_background
        self.label_width = label_width
        self.label_align = label_align
        self.value_align = value_align
        self.spacing = spacing if spacing is not None else DesignSystem.SPACING['md']
        self.truncate_value = truncate_value
        
        # Performance optimization: cache measurements
        self._cached_measurements = {}
        self._cached_label_hash = None
        self._cached_value_hash = None
        self._display_value = None
        
        # Auto-calculate size if not provided
        if width is None or height is None:
            renderer = get_renderer()
            label_text = f"{label}:" if label else ""
            label_width_actual, label_height = renderer.measure_text(label_text, 'label')
            value_width, value_height = renderer.measure_text(self.value, 'label')
            
            if self.label_width:
                label_width_actual = self.label_width
            
            total_width = label_width_actual + self.spacing + value_width
            total_height = max(label_height, value_height)
            
            final_width = width if width is not None else total_width + DesignSystem.SPACING['md'] * 2
            final_height = height if height is not None else total_height + DesignSystem.SPACING['sm'] * 2
        else:
            final_width = width
            final_height = height
        
        super().__init__(x, y, final_width, final_height)
        self._update_display_value()
        
    def _measure_text_cached(self, text: str) -> Tuple[int, int]:
        """Measure text with caching for performance."""
        cache_key = text
        if cache_key not in self._cached_measurements:
            self._cached_measurements[cache_key] = self._renderer.measure_text(text, 'label')
        return self._cached_measurements[cache_key]
    
    def _update_display_value(self):
        """Update display value with truncation if needed."""
        if not self.truncate_value or not self.rect.width:
            self._display_value = self.value
            return
        
        renderer = self._renderer
        label_text = f"{self.label}:" if self.label else ""
        label_width_actual = self.label_width if self.label_width else self._measure_text_cached(label_text)[0]
        
        # Calculate available width for value
        padding = DesignSystem.SPACING['sm'] * 2
        available_width = self.rect.width - label_width_actual - self.spacing - padding
        
        value_width = self._measure_text_cached(self.value)[0]
        if value_width <= available_width:
            self._display_value = self.value
        else:
            # Truncate with ellipsis
            ellipsis = "..."
            ellipsis_width = self._measure_text_cached(ellipsis)[0]
            available_width -= ellipsis_width
            
            # Binary search for optimal truncation
            low, high = 0, len(self.value)
            best_text = ""
            
            while low < high:
                mid = (low + high + 1) // 2
                test_text = self.value[:mid]
                test_width = self._measure_text_cached(test_text)[0]
                
                if test_width <= available_width:
                    best_text = test_text
                    low = mid
                else:
                    high = mid - 1
            
            self._display_value = best_text + ellipsis
        
    def set_value(self, value: str, color: Tuple[int, int, int] = None):
        """Update field value."""
        new_value = str(value)
        if self.value != new_value:
            self.value = new_value
            self._cached_value_hash = None  # Invalidate cache
            if color:
                self.value_color = color
            self._update_display_value()
            self.mark_dirty()
    
    def set_label(self, label: str):
        """Update field label."""
        if self.label != label:
            self.label = label
            self._cached_label_hash = None  # Invalidate cache
            self._update_display_value()
            self.mark_dirty()
    
    def set_size(self, width: int = None, height: int = None):
        """Update field size."""
        if width is not None:
            self.rect.width = width
        if height is not None:
            self.rect.height = height
        self._update_display_value()
        self.mark_dirty()
    
    def clear_cache(self):
        """Clear measurement cache."""
        self._cached_measurements.clear()
        self._cached_label_hash = None
        self._cached_value_hash = None
        self._update_display_value()
            
    def _draw_self(self, surface: pygame.Surface):
        """Draw modern flat field with optimized rendering."""
        renderer = self._renderer
        
        # Optional subtle background
        if self.show_background:
            bg_color = tuple(max(0, c - 5) for c in DesignSystem.COLORS['surface'])
            renderer.draw_rect(surface, self.rect,
                             bg_color,
                             border_radius=0)  # No rounded corners
        
        padding = DesignSystem.SPACING['sm']
        label_text = f"{self.label}:" if self.label else ""
        
        # Calculate label width
        if self.label_width:
            label_width_actual = self.label_width
        elif label_text:
            label_width_actual = self._measure_text_cached(label_text)[0]
        else:
            label_width_actual = 0
        
        # Draw label with alignment
        if label_text:
            label_height = self._measure_text_cached(label_text)[1]
            label_y = self.rect.y + (self.rect.height - label_height) // 2
            
            if self.label_align == 'center':
                label_x = self.rect.x + padding + (label_width_actual - self._measure_text_cached(label_text)[0]) // 2
            elif self.label_align == 'right':
                label_x = self.rect.x + padding + label_width_actual - self._measure_text_cached(label_text)[0]
            else:  # left
                label_x = self.rect.x + padding
            
            renderer.render_text(surface, label_text,
                               (label_x, label_y),
                               size='label',
                               color=DesignSystem.COLORS['text_label'])
        
        # Draw value with alignment and truncation
        value_text = self._display_value if self._display_value else str(self.value)
        if value_text:
            value_width, value_height = self._measure_text_cached(value_text)
            value_y = self.rect.y + (self.rect.height - value_height) // 2
            
            # Calculate available space for value
            value_start_x = self.rect.x + padding + label_width_actual + self.spacing
            
            if self.value_align == 'center':
                available_width = self.rect.width - padding * 2 - label_width_actual - self.spacing
                value_x = value_start_x + (available_width - value_width) // 2
            elif self.value_align == 'right':
                value_x = self.rect.right - value_width - padding
            else:  # left
                value_x = value_start_x
            
            renderer.render_text(surface, value_text,
                               (value_x, value_y),
                               size='label',
                               color=self.value_color)

