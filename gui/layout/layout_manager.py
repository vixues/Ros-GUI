"""Unified layout manager for automatic component sizing and padding calculation."""
import pygame
from typing import Optional, Tuple

from ..design.design_system import DesignSystem


class LayoutManager:
    """Unified layout manager for automatic component sizing and padding calculation."""
    
    # Constants
    TAB_BAR_HEIGHT = 45
    CARD_TITLE_HEIGHT = 36
    COMPONENT_TITLE_HEIGHT = 36
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
    def get_content_area(self) -> pygame.Rect:
        """Get the main content area below tab bar with standard padding."""
        content_padding = DesignSystem.SPACING['md']
        start_y = self.TAB_BAR_HEIGHT + DesignSystem.SPACING['lg']
        return pygame.Rect(
            content_padding,
            start_y,
            self.screen_width - content_padding * 2,
            self.screen_height - start_y - content_padding
        )
    
    def calculate_header_area(self, content_area: pygame.Rect, 
                             title: str, subtitle: str = None) -> Tuple[pygame.Rect, int]:
        """Calculate header area (title + optional subtitle) and return header rect and total height."""
        y = content_area.y
        title_font = DesignSystem.get_font('title')
        title_height = title_font.get_height()
        
        # Calculate total header height
        header_height = title_height
        if subtitle:
            subtitle_font = DesignSystem.get_font('small')
            subtitle_height = subtitle_font.get_height()
            header_height += DesignSystem.SPACING['sm'] + subtitle_height
        
        header_height += DesignSystem.SPACING['md']  # Spacing after header
        
        header_rect = pygame.Rect(
            content_area.x,
            y,
            content_area.width,
            header_height
        )
        
        return header_rect, header_height
    
    def calculate_component_area(self, content_area: pygame.Rect, 
                                 header_height: int,
                                 min_height: int = 200) -> pygame.Rect:
        """Calculate component area below header with proper padding."""
        component_y = content_area.y + header_height
        component_height = content_area.height - header_height
        
        # Ensure minimum height
        component_height = max(min_height, component_height)
        
        # Ensure doesn't exceed screen
        max_height = self.screen_height - component_y - DesignSystem.SPACING['md']
        component_height = min(component_height, max_height)
        
        return pygame.Rect(
            content_area.x,
            component_y,
            content_area.width,
            component_height
        )
    
    def calculate_inner_content_area(self, component_rect: pygame.Rect,
                                     has_title: bool = True,
                                     padding: str = 'sm') -> pygame.Rect:
        """Calculate inner content area within a component (accounting for title and padding)."""
        padding_value = DesignSystem.SPACING[padding]
        title_offset = self.COMPONENT_TITLE_HEIGHT if has_title else 0
        
        return pygame.Rect(
            component_rect.x + padding_value,
            component_rect.y + title_offset + padding_value,
            component_rect.width - padding_value * 2,
            component_rect.height - title_offset - padding_value * 2
        )
    
    def calculate_indicator_position(self, component_rect: pygame.Rect,
                                    indicator_width: int = 90,
                                    indicator_height: int = 24) -> Optional[pygame.Rect]:
        """Calculate status indicator position (top-right of component, below title)."""
        indicator_y = component_rect.y + self.COMPONENT_TITLE_HEIGHT + DesignSystem.SPACING['sm']
        
        # Check if indicator fits within component
        if indicator_y + indicator_height <= component_rect.bottom:
            return pygame.Rect(
                self.screen_width - DesignSystem.SPACING['md'] - indicator_width,
                indicator_y,
                indicator_width,
                indicator_height
            )
        return None
    
    def calculate_renderer_size(self, inner_content_area: pygame.Rect,
                               min_size: int = 100) -> Tuple[int, int]:
        """Calculate renderer size from inner content area."""
        return (
            max(min_size, inner_content_area.width),
            max(min_size, inner_content_area.height)
        )

