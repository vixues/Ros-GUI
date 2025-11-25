"""Advanced layout system with professional layout algorithms.

This module provides a comprehensive layout system inspired by CSS Flexbox
and Grid layouts, optimized for real-time UI updates.
"""
import pygame
from typing import Optional, List, Tuple, Dict, Any, Callable
from enum import Enum

from ..design.design_system import DesignSystem
from ..components.base import UIComponent


class LayoutDirection(Enum):
    """Layout direction for flex containers."""
    ROW = "row"  # Horizontal
    COLUMN = "column"  # Vertical


class JustifyContent(Enum):
    """Main axis alignment."""
    START = "start"
    END = "end"
    CENTER = "center"
    SPACE_BETWEEN = "space-between"
    SPACE_AROUND = "space-around"
    SPACE_EVENLY = "space-evenly"


class AlignItems(Enum):
    """Cross axis alignment."""
    START = "start"
    END = "end"
    CENTER = "center"
    STRETCH = "stretch"
    BASELINE = "baseline"


class LayoutConstraint:
    """Layout constraints for components."""
    
    def __init__(self,
                 min_width: Optional[int] = None,
                 max_width: Optional[int] = None,
                 min_height: Optional[int] = None,
                 max_height: Optional[int] = None,
                 flex: float = 0.0,  # Flex grow factor
                 flex_shrink: float = 1.0,
                 align_self: Optional[AlignItems] = None):
        self.min_width = min_width
        self.max_width = max_width
        self.min_height = min_height
        self.max_height = max_height
        self.flex = flex
        self.flex_shrink = flex_shrink
        self.align_self = align_self


class FlexContainer:
    """Flexbox-style container for layout management.
    
    This class implements a simplified Flexbox layout algorithm optimized
    for real-time UI updates.
    """
    
    def __init__(self,
                 direction: LayoutDirection = LayoutDirection.ROW,
                 justify_content: JustifyContent = JustifyContent.START,
                 align_items: AlignItems = AlignItems.START,
                 gap: int = 0,
                 padding: Tuple[int, int, int, int] = (0, 0, 0, 0),  # top, right, bottom, left
                 wrap: bool = False):
        self.direction = direction
        self.justify_content = justify_content
        self.align_items = align_items
        self.gap = gap
        self.padding = padding  # (top, right, bottom, left)
        self.wrap = wrap
        self._children: List[Tuple[UIComponent, LayoutConstraint]] = []
    
    def add_child(self, child: UIComponent, constraint: Optional[LayoutConstraint] = None):
        """Add a child component with optional layout constraints.
        
        Args:
            child: UI component to add
            constraint: Optional layout constraints
        """
        if constraint is None:
            constraint = LayoutConstraint()
        self._children.append((child, constraint))
    
    def remove_child(self, child: UIComponent):
        """Remove a child component.
        
        Args:
            child: Component to remove
        """
        self._children = [(c, const) for c, const in self._children if c != child]
    
    def layout(self, container_rect: pygame.Rect) -> List[pygame.Rect]:
        """Calculate layout for all children.
        
        Args:
            container_rect: Container rectangle
            
        Returns:
            List of calculated rectangles for children
        """
        if not self._children:
            return []
        
        # Calculate available space (accounting for padding)
        available_rect = pygame.Rect(
            container_rect.x + self.padding[3],  # left
            container_rect.y + self.padding[0],  # top
            container_rect.width - self.padding[1] - self.padding[3],  # width
            container_rect.height - self.padding[0] - self.padding[2]  # height
        )
        
        if self.direction == LayoutDirection.ROW:
            return self._layout_row(available_rect)
        else:
            return self._layout_column(available_rect)
    
    def _layout_row(self, available_rect: pygame.Rect) -> List[pygame.Rect]:
        """Layout children in a row."""
        if not self._children:
            return []
        
        # Calculate base sizes for all children
        base_sizes = []
        total_flex = 0.0
        total_base_size = 0
        
        for child, constraint in self._children:
            if not child.visible:
                base_sizes.append((0, 0))
                continue
            
            # Get preferred size
            pref_width = child.rect.width if child.rect.width > 0 else 100
            pref_height = child.rect.height if child.rect.height > 0 else 100
            
            # Apply constraints
            if constraint.min_width:
                pref_width = max(pref_width, constraint.min_width)
            if constraint.max_width:
                pref_width = min(pref_width, constraint.max_width)
            if constraint.min_height:
                pref_height = max(pref_height, constraint.min_height)
            if constraint.max_height:
                pref_height = min(pref_height, constraint.max_height)
            
            base_sizes.append((pref_width, pref_height))
            total_flex += constraint.flex
            total_base_size += pref_width
        
        # Calculate available space for flex items
        available_width = available_rect.width - (len(self._children) - 1) * self.gap
        flex_space = max(0, available_width - total_base_size)
        
        # Calculate final positions
        results = []
        x = available_rect.x
        y = available_rect.y
        
        for i, ((child, constraint), (base_w, base_h)) in enumerate(zip(self._children, base_sizes)):
            if not child.visible:
                results.append(pygame.Rect(0, 0, 0, 0))
                continue
            
            # Calculate width
            if constraint.flex > 0:
                flex_ratio = constraint.flex / total_flex if total_flex > 0 else 0
                width = base_w + int(flex_space * flex_ratio)
            else:
                width = base_w
            
            # Calculate height based on align_items
            if constraint.align_self:
                align = constraint.align_self
            else:
                align = self.align_items
            
            if align == AlignItems.STRETCH:
                height = available_rect.height
            elif align == AlignItems.CENTER:
                height = base_h
                y = available_rect.y + (available_rect.height - base_h) // 2
            elif align == AlignItems.END:
                height = base_h
                y = available_rect.y + available_rect.height - base_h
            else:  # START
                height = base_h
                y = available_rect.y
            
            # Apply height constraints
            if constraint.min_height:
                height = max(height, constraint.min_height)
            if constraint.max_height:
                height = min(height, constraint.max_height)
            
            results.append(pygame.Rect(x, y, width, height))
            
            # Move x position for next item
            x += width + self.gap
        
        # Apply justify_content
        if self.justify_content != JustifyContent.START:
            results = self._apply_justify_content(results, available_rect, LayoutDirection.ROW)
        
        return results
    
    def _layout_column(self, available_rect: pygame.Rect) -> List[pygame.Rect]:
        """Layout children in a column."""
        if not self._children:
            return []
        
        # Similar to row layout but vertical
        base_sizes = []
        total_flex = 0.0
        total_base_size = 0
        
        for child, constraint in self._children:
            if not child.visible:
                base_sizes.append((0, 0))
                continue
            
            pref_width = child.rect.width if child.rect.width > 0 else 100
            pref_height = child.rect.height if child.rect.height > 0 else 100
            
            if constraint.min_width:
                pref_width = max(pref_width, constraint.min_width)
            if constraint.max_width:
                pref_width = min(pref_width, constraint.max_width)
            if constraint.min_height:
                pref_height = max(pref_height, constraint.min_height)
            if constraint.max_height:
                pref_height = min(pref_height, constraint.max_height)
            
            base_sizes.append((pref_width, pref_height))
            total_flex += constraint.flex
            total_base_size += pref_height
        
        available_height = available_rect.height - (len(self._children) - 1) * self.gap
        flex_space = max(0, available_height - total_base_size)
        
        results = []
        x = available_rect.x
        y = available_rect.y
        
        for i, ((child, constraint), (base_w, base_h)) in enumerate(zip(self._children, base_sizes)):
            if not child.visible:
                results.append(pygame.Rect(0, 0, 0, 0))
                continue
            
            # Calculate height
            if constraint.flex > 0:
                flex_ratio = constraint.flex / total_flex if total_flex > 0 else 0
                height = base_h + int(flex_space * flex_ratio)
            else:
                height = base_h
            
            # Calculate width based on align_items
            if constraint.align_self:
                align = constraint.align_self
            else:
                align = self.align_items
            
            if align == AlignItems.STRETCH:
                width = available_rect.width
            elif align == AlignItems.CENTER:
                width = base_w
                x = available_rect.x + (available_rect.width - base_w) // 2
            elif align == AlignItems.END:
                width = base_w
                x = available_rect.x + available_rect.width - base_w
            else:  # START
                width = base_w
                x = available_rect.x
            
            # Apply width constraints
            if constraint.min_width:
                width = max(width, constraint.min_width)
            if constraint.max_width:
                width = min(width, constraint.max_width)
            
            results.append(pygame.Rect(x, y, width, height))
            
            # Move y position for next item
            y += height + self.gap
        
        # Apply justify_content
        if self.justify_content != JustifyContent.START:
            results = self._apply_justify_content(results, available_rect, LayoutDirection.COLUMN)
        
        return results
    
    def _apply_justify_content(self, rects: List[pygame.Rect],
                               container_rect: pygame.Rect,
                               direction: LayoutDirection) -> List[pygame.Rect]:
        """Apply justify-content alignment.
        
        Args:
            rects: List of child rectangles
            container_rect: Container rectangle
            direction: Layout direction
            
        Returns:
            Adjusted rectangles
        """
        if not rects:
            return rects
        
        visible_rects = [r for r in rects if r.width > 0 and r.height > 0]
        if not visible_rects:
            return rects
        
        if direction == LayoutDirection.ROW:
            total_width = sum(r.width for r in visible_rects) + (len(visible_rects) - 1) * self.gap
            available_space = container_rect.width - total_width
            offset_x = 0
            
            if self.justify_content == JustifyContent.END:
                offset_x = available_space
            elif self.justify_content == JustifyContent.CENTER:
                offset_x = available_space // 2
            elif self.justify_content == JustifyContent.SPACE_BETWEEN:
                if len(visible_rects) > 1:
                    gap = available_space / (len(visible_rects) - 1)
                else:
                    gap = 0
                # Adjust positions
                current_x = container_rect.x
                for i, rect in enumerate(rects):
                    if rect.width > 0:
                        rect.x = current_x
                        current_x += rect.width + gap + self.gap
                return rects
            elif self.justify_content == JustifyContent.SPACE_AROUND:
                if len(visible_rects) > 0:
                    gap = available_space / (len(visible_rects) * 2)
                else:
                    gap = 0
                current_x = container_rect.x + gap
                for rect in rects:
                    if rect.width > 0:
                        rect.x = current_x
                        current_x += rect.width + gap * 2 + self.gap
                return rects
            elif self.justify_content == JustifyContent.SPACE_EVENLY:
                if len(visible_rects) > 0:
                    gap = available_space / (len(visible_rects) + 1)
                else:
                    gap = 0
                current_x = container_rect.x + gap
                for rect in rects:
                    if rect.width > 0:
                        rect.x = current_x
                        current_x += rect.width + gap + self.gap
                return rects
            
            # Apply offset
            for rect in rects:
                if rect.width > 0:
                    rect.x += offset_x
        
        else:  # COLUMN
            total_height = sum(r.height for r in visible_rects) + (len(visible_rects) - 1) * self.gap
            available_space = container_rect.height - total_height
            offset_y = 0
            
            if self.justify_content == JustifyContent.END:
                offset_y = available_space
            elif self.justify_content == JustifyContent.CENTER:
                offset_y = available_space // 2
            elif self.justify_content == JustifyContent.SPACE_BETWEEN:
                if len(visible_rects) > 1:
                    gap = available_space / (len(visible_rects) - 1)
                else:
                    gap = 0
                current_y = container_rect.y
                for rect in rects:
                    if rect.height > 0:
                        rect.y = current_y
                        current_y += rect.height + gap + self.gap
                return rects
            elif self.justify_content == JustifyContent.SPACE_AROUND:
                if len(visible_rects) > 0:
                    gap = available_space / (len(visible_rects) * 2)
                else:
                    gap = 0
                current_y = container_rect.y + gap
                for rect in rects:
                    if rect.height > 0:
                        rect.y = current_y
                        current_y += rect.height + gap * 2 + self.gap
                return rects
            elif self.justify_content == JustifyContent.SPACE_EVENLY:
                if len(visible_rects) > 0:
                    gap = available_space / (len(visible_rects) + 1)
                else:
                    gap = 0
                current_y = container_rect.y + gap
                for rect in rects:
                    if rect.height > 0:
                        rect.y = current_y
                        current_y += rect.height + gap + self.gap
                return rects
            
            # Apply offset
            for rect in rects:
                if rect.height > 0:
                    rect.y += offset_y
        
        return rects


class AdvancedLayoutManager:
    """Advanced layout manager with Flexbox-style algorithms.
    
    This manager provides professional layout capabilities optimized for
    real-time UI updates with computer vision-inspired optimizations.
    """
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self._containers: Dict[str, FlexContainer] = {}
    
    def create_flex_container(self, name: str, **kwargs) -> FlexContainer:
        """Create a flex container.
        
        Args:
            name: Container identifier
            **kwargs: FlexContainer parameters
            
        Returns:
            Created FlexContainer
        """
        container = FlexContainer(**kwargs)
        self._containers[name] = container
        return container
    
    def get_container(self, name: str) -> Optional[FlexContainer]:
        """Get a container by name.
        
        Args:
            name: Container identifier
            
        Returns:
            FlexContainer or None
        """
        return self._containers.get(name)
    
    def layout_container(self, name: str, container_rect: pygame.Rect) -> List[pygame.Rect]:
        """Calculate layout for a container.
        
        Args:
            name: Container identifier
            container_rect: Container rectangle
            
        Returns:
            List of calculated rectangles
        """
        container = self._containers.get(name)
        if container:
            return container.layout(container_rect)
        return []
    
    # Backward compatibility methods
    def get_content_area(self) -> pygame.Rect:
        """Get the main content area below tab bar with standard padding."""
        content_padding = DesignSystem.SPACING['md']
        start_y = 45 + DesignSystem.SPACING['lg']  # TAB_BAR_HEIGHT
        return pygame.Rect(
            content_padding,
            start_y,
            self.screen_width - content_padding * 2,
            self.screen_height - start_y - content_padding
        )
    
    def calculate_header_area(self, content_area: pygame.Rect,
                             title: str, subtitle: str = None) -> Tuple[pygame.Rect, int]:
        """Calculate header area (title + optional subtitle)."""
        from ..renderers.ui_renderer import get_renderer
        renderer = get_renderer()
        
        y = content_area.y
        title_height = renderer.measure_text(title, 'title')[1]
        
        header_height = title_height
        if subtitle:
            subtitle_height = renderer.measure_text(subtitle, 'small')[1]
            header_height += DesignSystem.SPACING['sm'] + subtitle_height
        
        header_height += DesignSystem.SPACING['md']
        
        return pygame.Rect(
            content_area.x, y, content_area.width, header_height
        ), header_height
    
    def calculate_component_area(self, content_area: pygame.Rect,
                                 header_height: int,
                                 min_height: int = 200) -> pygame.Rect:
        """Calculate component area below header."""
        component_y = content_area.y + header_height
        component_height = content_area.height - header_height
        component_height = max(min_height, component_height)
        max_height = self.screen_height - component_y - DesignSystem.SPACING['md']
        component_height = min(component_height, max_height)
        
        return pygame.Rect(
            content_area.x, component_y, content_area.width, component_height
        )
    
    def calculate_inner_content_area(self, component_rect: pygame.Rect,
                                     has_title: bool = True,
                                     padding: str = 'sm') -> pygame.Rect:
        """Calculate inner content area within a component."""
        padding_value = DesignSystem.SPACING[padding]
        title_offset = 36 if has_title else 0
        
        return pygame.Rect(
            component_rect.x + padding_value,
            component_rect.y + title_offset + padding_value,
            component_rect.width - padding_value * 2,
            component_rect.height - title_offset - padding_value * 2
        )

