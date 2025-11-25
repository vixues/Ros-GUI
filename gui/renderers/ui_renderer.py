"""Professional UI rendering system with optimized drawing primitives.

This module provides a high-performance rendering system optimized for real-time
UI updates. It includes specialized rectangle drawing, color management, and
font rendering with caching and batch operations.
"""
import pygame
from typing import Tuple, Optional, Dict, List, Any
from collections import defaultdict
import weakref

from ..design.design_system import DesignSystem
from .realtime_optimizer import get_optimizer


class ColorManager:
    """Centralized color management with caching and blending support."""
    
    _color_cache: Dict[Tuple[int, int, int, Optional[int]], pygame.Color] = {}
    
    @staticmethod
    def get_color(rgb: Tuple[int, int, int], alpha: Optional[int] = None) -> pygame.Color:
        """Get pygame.Color with caching.
        
        Args:
            rgb: RGB tuple (r, g, b)
            alpha: Optional alpha value (0-255)
            
        Returns:
            pygame.Color object
        """
        key = (*rgb, alpha)
        if key not in ColorManager._color_cache:
            if alpha is not None:
                ColorManager._color_cache[key] = pygame.Color(*rgb, alpha)
            else:
                ColorManager._color_cache[key] = pygame.Color(*rgb)
        return ColorManager._color_cache[key]
    
    @staticmethod
    def blend(color1: Tuple[int, int, int], color2: Tuple[int, int, int], 
             factor: float) -> Tuple[int, int, int]:
        """Blend two colors.
        
        Args:
            color1: First color (r, g, b)
            color2: Second color (r, g, b)
            factor: Blend factor (0.0 = color1, 1.0 = color2)
            
        Returns:
            Blended color (r, g, b)
        """
        factor = max(0.0, min(1.0, factor))
        return (
            int(color1[0] * (1 - factor) + color2[0] * factor),
            int(color1[1] * (1 - factor) + color2[1] * factor),
            int(color1[2] * (1 - factor) + color2[2] * factor)
        )
    
    @staticmethod
    def darken(color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """Darken a color.
        
        Args:
            color: Color (r, g, b)
            factor: Darkening factor (0.0 = no change, 1.0 = black)
            
        Returns:
            Darkened color
        """
        factor = max(0.0, min(1.0, factor))
        return (
            int(color[0] * (1 - factor)),
            int(color[1] * (1 - factor)),
            int(color[2] * (1 - factor))
        )
    
    @staticmethod
    def lighten(color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """Lighten a color.
        
        Args:
            color: Color (r, g, b)
            factor: Lightening factor (0.0 = no change, 1.0 = white)
            
        Returns:
            Lightened color
        """
        factor = max(0.0, min(1.0, factor))
        return (
            int(color[0] + (255 - color[0]) * factor),
            int(color[1] + (255 - color[1]) * factor),
            int(color[2] + (255 - color[2]) * factor)
        )


class FontRenderer:
    """Optimized font rendering with caching and text measurement."""
    
    _text_cache: Dict[Tuple[str, str, Tuple[int, int, int], bool], pygame.Surface] = {}
    _font_cache: Dict[str, pygame.font.Font] = {}
    
    @staticmethod
    def get_font(size: str = 'label') -> pygame.font.Font:
        """Get font with caching.
        
        Args:
            size: Font size name ('console', 'label', 'title', 'small')
            
        Returns:
            pygame.font.Font object
        """
        if size not in FontRenderer._font_cache:
            FontRenderer._font_cache[size] = DesignSystem.get_font(size)
        return FontRenderer._font_cache[size]
    
    @staticmethod
    def render_text(text: str, size: str = 'label', 
                   color: Tuple[int, int, int] = None,
                   antialias: bool = True) -> pygame.Surface:
        """Render text with caching.
        
        Args:
            text: Text to render
            size: Font size name
            color: Text color (r, g, b)
            antialias: Whether to use antialiasing
            
        Returns:
            Rendered text surface
        """
        if color is None:
            color = DesignSystem.COLORS['text']
        
        key = (text, size, color, antialias)
        if key not in FontRenderer._text_cache:
            font = FontRenderer.get_font(size)
            surface = font.render(text, antialias, color)
            FontRenderer._text_cache[key] = surface
        return FontRenderer._text_cache[key]
    
    @staticmethod
    def measure_text(text: str, size: str = 'label') -> Tuple[int, int]:
        """Measure text dimensions without rendering.
        
        Args:
            text: Text to measure
            size: Font size name
            
        Returns:
            (width, height) tuple
        """
        font = FontRenderer.get_font(size)
        return font.size(text)
    
    @staticmethod
    def clear_cache():
        """Clear text rendering cache."""
        FontRenderer._text_cache.clear()


class RectangleRenderer:
    """Optimized rectangle drawing with batch operations and effects."""
    
    @staticmethod
    def draw_rect(surface: pygame.Surface, rect: pygame.Rect,
                 color: Tuple[int, int, int],
                 border_radius: int = 0,
                 width: int = 0,
                 alpha: Optional[int] = None) -> None:
        """Draw a rectangle with optional border radius and alpha.
        
        Args:
            surface: Target surface
            rect: Rectangle to draw
            color: Fill color (r, g, b)
            border_radius: Border radius (0 = no rounding)
            width: Border width (0 = filled)
            alpha: Optional alpha value
        """
        if alpha is not None and alpha < 255:
            # Use alpha blending
            temp_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            if width == 0:
                pygame.draw.rect(temp_surface, (*color, alpha), temp_surface.get_rect(),
                                border_radius=border_radius)
            else:
                pygame.draw.rect(temp_surface, (*color, alpha), temp_surface.get_rect(),
                                width=width, border_radius=border_radius)
            surface.blit(temp_surface, rect.topleft)
        else:
            if width == 0:
                pygame.draw.rect(surface, color, rect, border_radius=border_radius)
            else:
                pygame.draw.rect(surface, color, rect, width=width, border_radius=border_radius)
    
    @staticmethod
    def draw_rect_with_shadow(surface: pygame.Surface, rect: pygame.Rect,
                             color: Tuple[int, int, int],
                             shadow_color: Tuple[int, int, int, int] = None,
                             shadow_offset: int = None,
                             border_radius: int = 0) -> None:
        """Draw rectangle with shadow effect.
        
        Args:
            surface: Target surface
            rect: Rectangle to draw
            color: Fill color
            shadow_color: Shadow color with alpha (r, g, b, a)
            shadow_offset: Shadow offset in pixels
            border_radius: Border radius
        """
        if shadow_color is None:
            shadow_color = (*DesignSystem.COLORS['shadow'][:3], 
                          DesignSystem.COLORS['shadow'][3] if len(DesignSystem.COLORS['shadow']) > 3 
                          else 220)
        if shadow_offset is None:
            shadow_offset = DesignSystem.SHADOW_OFFSET
        
        # Draw shadow
        shadow_rect = rect.copy()
        shadow_rect.x += shadow_offset
        shadow_rect.y += shadow_offset
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, shadow_color, shadow_surf.get_rect(),
                        border_radius=border_radius)
        surface.blit(shadow_surf, shadow_rect.topleft)
        
        # Draw main rectangle
        RectangleRenderer.draw_rect(surface, rect, color, border_radius=border_radius)
    
    @staticmethod
    def draw_rect_with_border(surface: pygame.Surface, rect: pygame.Rect,
                             fill_color: Tuple[int, int, int],
                             border_color: Tuple[int, int, int],
                             border_width: int = 1,
                             border_radius: int = 0) -> None:
        """Draw rectangle with border.
        
        Args:
            surface: Target surface
            rect: Rectangle to draw
            fill_color: Fill color
            border_color: Border color
            border_width: Border width
            border_radius: Border radius
        """
        # Draw fill
        if fill_color:
            RectangleRenderer.draw_rect(surface, rect, fill_color, 
                                       border_radius=border_radius)
        
        # Draw border
        if border_width > 0:
            RectangleRenderer.draw_rect(surface, rect, border_color,
                                       border_radius=border_radius, width=border_width)
    
    @staticmethod
    def draw_rect_with_glow(surface: pygame.Surface, rect: pygame.Rect,
                           color: Tuple[int, int, int],
                           glow_color: Tuple[int, int, int, int] = None,
                           glow_width: int = 2,
                           border_radius: int = 0) -> None:
        """Draw rectangle with glow effect.
        
        Args:
            surface: Target surface
            rect: Rectangle to draw
            color: Fill color
            glow_color: Glow color with alpha
            glow_width: Glow width
            border_radius: Border radius
        """
        if glow_color is None:
            glow_color = DesignSystem.COLORS.get('primary_glow', (64, 224, 255, 60))
        
        # Draw main rectangle
        RectangleRenderer.draw_rect(surface, rect, color, border_radius=border_radius)
        
        # Draw glow (multiple layers for smooth effect)
        for i in range(glow_width):
            glow_rect = rect.inflate(i * 2, i * 2)
            alpha = glow_color[3] // (i + 1) if len(glow_color) > 3 else 60 // (i + 1)
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*glow_color[:3], alpha), glow_surf.get_rect(),
                           border_radius=border_radius + i)
            surface.blit(glow_surf, glow_rect.topleft, special_flags=pygame.BLEND_ALPHA_SDL2)


class UIRenderer:
    """Unified UI renderer combining all rendering primitives.
    
    This class provides a high-level interface for all UI rendering operations
    with optimizations for real-time performance.
    """
    
    def __init__(self):
        self.color_manager = ColorManager()
        self.font_renderer = FontRenderer()
        self.rect_renderer = RectangleRenderer()
        self._optimizer = get_optimizer()
        self._dirty_regions: List[pygame.Rect] = []
        self._batch_operations: List[Dict[str, Any]] = []
    
    def clear_dirty_regions(self):
        """Clear the dirty regions list."""
        self._dirty_regions.clear()
    
    def add_dirty_region(self, rect: pygame.Rect):
        """Add a dirty region for partial updates.
        
        Args:
            rect: Dirty region rectangle
        """
        self._dirty_regions.append(rect)
        self._optimizer.mark_dirty(rect)
    
    def get_dirty_regions(self) -> List[pygame.Rect]:
        """Get all dirty regions.
        
        Returns:
            List of dirty rectangles
        """
        return self._dirty_regions.copy()
    
    def draw_rect(self, surface: pygame.Surface, rect: pygame.Rect,
                 color: Tuple[int, int, int],
                 border_radius: int = 0,
                 width: int = 0,
                 alpha: Optional[int] = None) -> None:
        """Draw rectangle using optimized renderer."""
        self.rect_renderer.draw_rect(surface, rect, color, border_radius, width, alpha)
    
    def draw_rect_with_shadow(self, surface: pygame.Surface, rect: pygame.Rect,
                             color: Tuple[int, int, int],
                             shadow_color: Tuple[int, int, int, int] = None,
                             shadow_offset: int = None,
                             border_radius: int = 0) -> None:
        """Draw rectangle with shadow."""
        self.rect_renderer.draw_rect_with_shadow(surface, rect, color, 
                                                shadow_color, shadow_offset, border_radius)
    
    def draw_rect_with_border(self, surface: pygame.Surface, rect: pygame.Rect,
                             fill_color: Tuple[int, int, int],
                             border_color: Tuple[int, int, int],
                             border_width: int = 1,
                             border_radius: int = 0) -> None:
        """Draw rectangle with border."""
        self.rect_renderer.draw_rect_with_border(surface, rect, fill_color,
                                                 border_color, border_width, border_radius)
    
    def draw_rect_with_glow(self, surface: pygame.Surface, rect: pygame.Rect,
                           color: Tuple[int, int, int],
                           glow_color: Tuple[int, int, int, int] = None,
                           glow_width: int = 2,
                           border_radius: int = 0) -> None:
        """Draw rectangle with glow effect."""
        self.rect_renderer.draw_rect_with_glow(surface, rect, color,
                                             glow_color, glow_width, border_radius)
    
    def render_text(self, surface: pygame.Surface, text: str,
                   pos: Tuple[int, int],
                   size: str = 'label',
                   color: Tuple[int, int, int] = None,
                   antialias: bool = True) -> None:
        """Render text at position.
        
        Args:
            surface: Target surface
            text: Text to render
            pos: Position (x, y)
            size: Font size name
            color: Text color
            antialias: Whether to use antialiasing
        """
        text_surface = self.font_renderer.render_text(text, size, color, antialias)
        surface.blit(text_surface, pos)
    
    def measure_text(self, text: str, size: str = 'label') -> Tuple[int, int]:
        """Measure text dimensions."""
        return self.font_renderer.measure_text(text, size)
    
    def get_color(self, rgb: Tuple[int, int, int], alpha: Optional[int] = None) -> pygame.Color:
        """Get color with caching."""
        return self.color_manager.get_color(rgb, alpha)
    
    def blend_colors(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int],
                    factor: float) -> Tuple[int, int, int]:
        """Blend two colors."""
        return self.color_manager.blend(color1, color2, factor)
    
    def darken_color(self, color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """Darken a color."""
        return self.color_manager.darken(color, factor)
    
    def lighten_color(self, color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """Lighten a color."""
        return self.color_manager.lighten(color, factor)


# Global renderer instance
_global_renderer: Optional[UIRenderer] = None


def get_renderer() -> UIRenderer:
    """Get the global UI renderer instance.
    
    Returns:
        UIRenderer instance
    """
    global _global_renderer
    if _global_renderer is None:
        _global_renderer = UIRenderer()
    return _global_renderer

