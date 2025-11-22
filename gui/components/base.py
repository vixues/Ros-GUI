"""Base UI components with port-based message passing."""
import pygame
import inspect
from typing import Optional, Dict, Any, List, Tuple, Callable

from ..design.design_system import DesignSystem


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
    """Base class for all UI components with port-based message passing."""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.visible = True
        self.enabled = True
        
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
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame event. Returns True if event was handled."""
        return False
        
    def update(self, dt: float):
        """Update component state."""
        pass
        
    def draw(self, surface: pygame.Surface):
        """Draw component to surface."""
        pass


class Panel(UIComponent):
    """Panel container component with fighter cockpit styling."""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 title: str = "", show_border: bool = True):
        super().__init__(x, y, width, height)
        self.title = title
        self.show_border = show_border
        self.children: List[UIComponent] = []
        
    def add_child(self, child: UIComponent):
        """Add child component."""
        self.children.append(child)
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events for panel and children."""
        if not self.visible or not self.enabled:
            return False
            
        # Transform event position relative to panel
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            if self.rect.collidepoint(event.pos):
                # Create relative event
                rel_event = pygame.event.Event(event.type)
                rel_event.pos = (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)
                rel_event.button = getattr(event, 'button', None)
                
                # Pass to children
                for child in reversed(self.children):  # Reverse for z-order
                    if child.handle_event(rel_event):
                        return True
        return False
        
    def update(self, dt: float):
        """Update panel and children."""
        for child in self.children:
            child.update(dt)
            
    def draw(self, surface: pygame.Surface):
        """Draw panel with fighter cockpit style."""
        if not self.visible:
            return
            
        # Draw panel background
        pygame.draw.rect(surface, DesignSystem.COLORS['bg_panel'], self.rect, 
                        border_radius=DesignSystem.RADIUS['md'])
        
        # Draw border with glow effect
        if self.show_border:
            # Outer border
            pygame.draw.rect(surface, DesignSystem.COLORS['border'], self.rect, 
                           width=1, border_radius=DesignSystem.RADIUS['md'])
            # Inner glow line
            inner_rect = self.rect.inflate(-2, -2)
            pygame.draw.rect(surface, DesignSystem.COLORS['border_light'], inner_rect, 
                           width=1, border_radius=DesignSystem.RADIUS['sm'])
        
        # Draw title if present
        if self.title:
            font = DesignSystem.get_font('label')
            title_surf = font.render(self.title, True, DesignSystem.COLORS['text_label'])
            title_rect = title_surf.get_rect(topleft=(self.rect.x + DesignSystem.SPACING['md'], 
                                                      self.rect.y + DesignSystem.SPACING['sm']))
            surface.blit(title_surf, title_rect)
            
            # Draw title underline
            underline_y = title_rect.bottom + 2
            pygame.draw.line(surface, DesignSystem.COLORS['primary'], 
                           (title_rect.left, underline_y),
                           (title_rect.right, underline_y), 1)
        
        # Draw children
        for child in self.children:
            # Create subsurface for clipping
            child_surface = surface.subsurface(
                pygame.Rect(child.rect.x + self.rect.x, 
                           child.rect.y + self.rect.y,
                           child.rect.width, child.rect.height)
            )
            child.draw(child_surface)


class Card(UIComponent):
    """Card component with shadow and border."""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 title: str = "", show_shadow: bool = True):
        super().__init__(x, y, width, height)
        self.title = title
        self.show_shadow = show_shadow
        self.children: List[UIComponent] = []
        
    def add_child(self, child: UIComponent):
        """Add child component."""
        self.children.append(child)
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events for card and children."""
        if not self.visible or not self.enabled:
            return False
            
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            if hasattr(event, 'pos') and self.rect.collidepoint(event.pos):
                # Get content area (below title)
                header_height = 36 if self.title else 0
                content_area = pygame.Rect(
                    self.rect.x,
                    self.rect.y + header_height,
                    self.rect.width,
                    self.rect.height - header_height
                )
                
                # Convert event position to content area coordinates (relative to content area start)
                rel_event = pygame.event.Event(event.type)
                rel_event.pos = (event.pos[0] - content_area.x, event.pos[1] - content_area.y)
                rel_event.button = getattr(event, 'button', None)
                rel_event.buttons = getattr(event, 'buttons', None)
                rel_event.rel = getattr(event, 'rel', None)
                
                for child in reversed(self.children):
                    if child.handle_event(rel_event):
                        return True
        return False
        
    def update(self, dt: float):
        """Update card and children."""
        for child in self.children:
            child.update(dt)
            
    def draw(self, surface: pygame.Surface):
        """Draw card with fighter cockpit styling and proper children space control."""
        if not self.visible:
            return
            
        # Draw shadow
        if self.show_shadow:
            shadow_rect = self.rect.copy()
            shadow_rect.x += DesignSystem.SHADOW_OFFSET
            shadow_rect.y += DesignSystem.SHADOW_OFFSET
            shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            shadow_color = (*DesignSystem.COLORS['shadow'][:3], 
                          DesignSystem.COLORS['shadow'][3] if len(DesignSystem.COLORS['shadow']) > 3 
                          else DesignSystem.COLORS['shadow'][0])
            pygame.draw.rect(shadow_surf, shadow_color, shadow_surf.get_rect(), 
                           border_radius=DesignSystem.RADIUS['lg'])
            surface.blit(shadow_surf, shadow_rect)
        
        # Draw card background
        pygame.draw.rect(surface, DesignSystem.COLORS['surface'], self.rect,
                        border_radius=DesignSystem.RADIUS['lg'])
        
        # Draw border with subtle glow
        pygame.draw.rect(surface, DesignSystem.COLORS['border'], self.rect,
                        width=1, border_radius=DesignSystem.RADIUS['lg'])
        
        # Calculate title header height
        header_height = 36 if self.title else 0
        
        # Draw title header if present
        if self.title:
            header_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, header_height)
            pygame.draw.rect(surface, DesignSystem.COLORS['surface_light'], header_rect,
                           border_radius=DesignSystem.RADIUS['lg'])
            pygame.draw.rect(surface, DesignSystem.COLORS['border_light'], header_rect,
                           width=1, border_radius=DesignSystem.RADIUS['lg'])
            
            font = DesignSystem.get_font('label')
            title_surf = font.render(self.title, True, DesignSystem.COLORS['text'])
            title_y = header_rect.y + (header_rect.height - title_surf.get_height()) // 2
            surface.blit(title_surf, (header_rect.x + DesignSystem.SPACING['md'], title_y))
        
        # Calculate content area (below title) - absolute coordinates for clipping
        content_area_abs = pygame.Rect(
            self.rect.x,
            self.rect.y + header_height,
            self.rect.width,
            self.rect.height - header_height
        )
        
        # Draw children with clipping to prevent covering title
        old_clip = surface.get_clip()
        # Set clip region to content area (below title) - use absolute coordinates
        surface.set_clip(content_area_abs)
        
        for child in self.children:
            # Child coordinates are relative to card's content area
            # Calculate absolute position for drawing
            child_abs_rect = pygame.Rect(
                self.rect.x + child.rect.x,
                self.rect.y + header_height + child.rect.y,
                child.rect.width,
                child.rect.height
            )
            
            # Only draw if child intersects with content area
            if child_abs_rect.colliderect(content_area_abs):
                # Create subsurface for child (relative to content area)
                child_surface = surface.subsurface(child_abs_rect)
                # Save child's original position temporarily
                orig_x, orig_y = child.rect.x, child.rect.y
                # Set child position to 0,0 relative to its surface
                child.rect.x = 0
                child.rect.y = 0
                child.draw(child_surface)
                # Restore original position
                child.rect.x, child.rect.y = orig_x, orig_y
        
        # Restore original clip
        surface.set_clip(old_clip)
    
    def get_content_area(self) -> pygame.Rect:
        """Get the content area rect (below title) for children placement.
        Returns rect with coordinates relative to card's position (0,0 at content area start)."""
        header_height = 36 if self.title else 0
        return pygame.Rect(
            0,  # Relative to card's content area start
            0,  # Relative to card's content area start
            self.rect.width,
            self.rect.height - header_height
        )


class Label(UIComponent):
    """Text label component."""
    
    def __init__(self, x: int, y: int, text: str, 
                 font_size: str = 'label', color: Tuple[int, int, int] = None,
                 align: str = 'left'):
        super().__init__(x, y, 0, 0)
        self.text = text
        self.font_size = font_size
        self.color = color or DesignSystem.COLORS['text']
        self.align = align  # 'left', 'center', 'right'
        self._update_size()
        
    def _update_size(self):
        """Update label size based on text."""
        font = DesignSystem.get_font(self.font_size)
        text_surf = font.render(self.text, True, self.color)
        self.rect.width = text_surf.get_width()
        self.rect.height = text_surf.get_height()
        
    def set_text(self, text: str):
        """Update label text."""
        self.text = text
        self._update_size()
        
    def draw(self, surface: pygame.Surface):
        """Draw label."""
        if not self.visible:
            return
            
        font = DesignSystem.get_font(self.font_size)
        text_surf = font.render(self.text, True, self.color)
        
        if self.align == 'center':
            pos = (self.rect.centerx - text_surf.get_width() // 2, self.rect.y)
        elif self.align == 'right':
            pos = (self.rect.right - text_surf.get_width(), self.rect.y)
        else:
            pos = (self.rect.x, self.rect.y)
            
        surface.blit(text_surf, pos)


class Field(UIComponent):
    """Field component (label + value display)."""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 label: str, value: str = "", value_color: Tuple[int, int, int] = None):
        super().__init__(x, y, width, height)
        self.label = label
        self.value = value
        self.value_color = value_color or DesignSystem.COLORS['text']
        
    def set_value(self, value: str, color: Tuple[int, int, int] = None):
        """Update field value."""
        self.value = value
        if color:
            self.value_color = color
            
    def draw(self, surface: pygame.Surface):
        """Draw field."""
        if not self.visible:
            return
            
        # Draw background
        pygame.draw.rect(surface, DesignSystem.COLORS['surface_light'], self.rect,
                       border_radius=DesignSystem.RADIUS['sm'])
        pygame.draw.rect(surface, DesignSystem.COLORS['border'], self.rect,
                       width=1, border_radius=DesignSystem.RADIUS['sm'])
        
        font = DesignSystem.get_font('label')
        
        # Draw label
        label_surf = font.render(f"{self.label}:", True, DesignSystem.COLORS['text_label'])
        label_y = self.rect.y + (self.rect.height - label_surf.get_height()) // 2
        surface.blit(label_surf, (self.rect.x + DesignSystem.SPACING['md'], label_y))
        
        # Draw value
        value_surf = font.render(str(self.value), True, self.value_color)
        value_x = self.rect.right - value_surf.get_width() - DesignSystem.SPACING['md']
        value_y = self.rect.y + (self.rect.height - value_surf.get_height()) // 2
        surface.blit(value_surf, (value_x, value_y))

