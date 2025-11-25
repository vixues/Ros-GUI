"""Real-time rendering optimization system.

This module provides optimizations for real-time UI rendering including:
- Dirty rectangle tracking
- Render caching
- Batch operations
- Viewport culling
"""
import pygame
from typing import List, Set, Dict, Optional, Tuple, Any
from collections import deque
import time


class DirtyRegionTracker:
    """Tracks dirty regions for partial screen updates."""
    
    def __init__(self, max_regions: int = 100):
        self._dirty_regions: List[pygame.Rect] = []
        self._max_regions = max_regions
        self._merged_region: Optional[pygame.Rect] = None
        self._needs_merge = True
    
    def add_region(self, rect: pygame.Rect):
        """Add a dirty region.
        
        Args:
            rect: Dirty rectangle
        """
        if rect.width > 0 and rect.height > 0:
            self._dirty_regions.append(rect)
            self._needs_merge = True
            
            # Limit number of regions
            if len(self._dirty_regions) > self._max_regions:
                # Merge oldest regions
                self._merge_regions()
    
    def get_regions(self) -> List[pygame.Rect]:
        """Get all dirty regions.
        
        Returns:
            List of dirty rectangles
        """
        if self._needs_merge:
            self._merge_regions()
        return self._dirty_regions.copy()
    
    def get_merged_region(self) -> Optional[pygame.Rect]:
        """Get a single merged region covering all dirty areas.
        
        Returns:
            Merged rectangle or None if no dirty regions
        """
        if self._needs_merge:
            self._merge_regions()
        return self._merged_region
    
    def clear(self):
        """Clear all dirty regions."""
        self._dirty_regions.clear()
        self._merged_region = None
        self._needs_merge = False
    
    def _merge_regions(self):
        """Merge overlapping dirty regions for efficiency."""
        if not self._dirty_regions:
            self._merged_region = None
            self._needs_merge = False
            return
        
        # Simple merge: find bounding box
        min_x = min(r.x for r in self._dirty_regions)
        min_y = min(r.y for r in self._dirty_regions)
        max_x = max(r.right for r in self._dirty_regions)
        max_y = max(r.bottom for r in self._dirty_regions)
        
        self._merged_region = pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
        
        # Merge overlapping regions
        merged = []
        for rect in self._dirty_regions:
            added = False
            for i, existing in enumerate(merged):
                if existing.colliderect(rect):
                    # Merge with existing
                    merged[i] = existing.union(rect)
                    added = True
                    break
            if not added:
                merged.append(rect)
        
        self._dirty_regions = merged
        self._needs_merge = False


class RenderCache:
    """Cache for rendered surfaces to avoid redundant drawing."""
    
    def __init__(self, max_size: int = 50):
        self._cache: Dict[Any, Tuple[pygame.Surface, float]] = {}
        self._max_size = max_size
        self._access_times: deque = deque()
    
    def get(self, key: Any) -> Optional[pygame.Surface]:
        """Get cached surface.
        
        Args:
            key: Cache key
            
        Returns:
            Cached surface or None
        """
        if key in self._cache:
            surface, _ = self._cache[key]
            # Update access time
            self._cache[key] = (surface, time.time())
            return surface
        return None
    
    def put(self, key: Any, surface: pygame.Surface):
        """Store surface in cache.
        
        Args:
            key: Cache key
            surface: Surface to cache
        """
        # Remove oldest if cache is full
        if len(self._cache) >= self._max_size:
            # Find least recently used
            oldest_key = min(self._cache.keys(),
                           key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
        
        self._cache[key] = (surface, time.time())
    
    def invalidate(self, key: Any):
        """Invalidate a cache entry.
        
        Args:
            key: Cache key to invalidate
        """
        if key in self._cache:
            del self._cache[key]
    
    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        self._access_times.clear()


class ViewportCuller:
    """Viewport culling for off-screen component optimization."""
    
    @staticmethod
    def is_visible(rect: pygame.Rect, viewport: pygame.Rect) -> bool:
        """Check if rectangle is visible in viewport.
        
        Args:
            rect: Rectangle to check
            viewport: Viewport rectangle
            
        Returns:
            True if visible
        """
        return rect.colliderect(viewport)
    
    @staticmethod
    def get_visible_rects(rects: List[pygame.Rect],
                         viewport: pygame.Rect) -> List[pygame.Rect]:
        """Filter rectangles to only those visible in viewport.
        
        Args:
            rects: List of rectangles
            viewport: Viewport rectangle
            
        Returns:
            List of visible rectangles
        """
        return [r for r in rects if ViewportCuller.is_visible(r, viewport)]
    
    @staticmethod
    def clip_rect(rect: pygame.Rect, viewport: pygame.Rect) -> pygame.Rect:
        """Clip rectangle to viewport.
        
        Args:
            rect: Rectangle to clip
            viewport: Viewport rectangle
            
        Returns:
            Clipped rectangle
        """
        return rect.clip(viewport)


class BatchRenderer:
    """Batch renderer for efficient drawing operations."""
    
    def __init__(self):
        self._batches: Dict[str, List[Dict[str, Any]]] = {}
    
    def add_rect(self, batch_id: str, rect: pygame.Rect, color: Tuple[int, int, int],
                 border_radius: int = 0, width: int = 0):
        """Add rectangle to batch.
        
        Args:
            batch_id: Batch identifier
            rect: Rectangle to draw
            color: Fill color
            border_radius: Border radius
            width: Border width
        """
        if batch_id not in self._batches:
            self._batches[batch_id] = []
        
        self._batches[batch_id].append({
            'type': 'rect',
            'rect': rect,
            'color': color,
            'border_radius': border_radius,
            'width': width
        })
    
    def add_text(self, batch_id: str, text: str, pos: Tuple[int, int],
                 font_size: str = 'label', color: Tuple[int, int, int] = None):
        """Add text to batch.
        
        Args:
            batch_id: Batch identifier
            text: Text to render
            pos: Position
            font_size: Font size
            color: Text color
        """
        if batch_id not in self._batches:
            self._batches[batch_id] = []
        
        self._batches[batch_id].append({
            'type': 'text',
            'text': text,
            'pos': pos,
            'font_size': font_size,
            'color': color
        })
    
    def render_batch(self, surface: pygame.Surface, batch_id: str,
                    renderer: Any):
        """Render a batch.
        
        Args:
            surface: Target surface
            batch_id: Batch identifier
            renderer: UIRenderer instance
        """
        if batch_id not in self._batches:
            return
        
        for item in self._batches[batch_id]:
            if item['type'] == 'rect':
                renderer.draw_rect(surface, item['rect'], item['color'],
                                 item['border_radius'], item['width'])
            elif item['type'] == 'text':
                renderer.render_text(surface, item['text'], item['pos'],
                                   item['font_size'], item['color'])
    
    def clear_batch(self, batch_id: str):
        """Clear a batch.
        
        Args:
            batch_id: Batch identifier
        """
        if batch_id in self._batches:
            del self._batches[batch_id]
    
    def clear_all(self):
        """Clear all batches."""
        self._batches.clear()


class RealtimeOptimizer:
    """Main real-time rendering optimizer.
    
    This class combines all optimization techniques for maximum performance.
    """
    
    def __init__(self):
        self.dirty_tracker = DirtyRegionTracker()
        self.render_cache = RenderCache()
        self.batch_renderer = BatchRenderer()
        self.viewport_culler = ViewportCuller()
        self._frame_count = 0
        self._last_fps_time = time.time()
        self._fps = 0.0
    
    def mark_dirty(self, rect: pygame.Rect):
        """Mark a region as dirty.
        
        Args:
            rect: Dirty rectangle
        """
        self.dirty_tracker.add_region(rect)
    
    def get_dirty_regions(self) -> List[pygame.Rect]:
        """Get all dirty regions.
        
        Returns:
            List of dirty rectangles
        """
        return self.dirty_tracker.get_regions()
    
    def clear_dirty(self):
        """Clear all dirty regions."""
        self.dirty_tracker.clear()
    
    def get_cached_surface(self, key: Any) -> Optional[pygame.Surface]:
        """Get cached surface.
        
        Args:
            key: Cache key
            
        Returns:
            Cached surface or None
        """
        return self.render_cache.get(key)
    
    def cache_surface(self, key: Any, surface: pygame.Surface):
        """Cache a surface.
        
        Args:
            key: Cache key
            surface: Surface to cache
        """
        self.render_cache.put(key, surface)
    
    def invalidate_cache(self, key: Any):
        """Invalidate cache entry.
        
        Args:
            key: Cache key
        """
        self.render_cache.invalidate(key)
    
    def is_visible(self, rect: pygame.Rect, viewport: pygame.Rect) -> bool:
        """Check if rectangle is visible.
        
        Args:
            rect: Rectangle to check
            viewport: Viewport rectangle
            
        Returns:
            True if visible
        """
        return self.viewport_culler.is_visible(rect, viewport)
    
    def update_fps(self):
        """Update FPS counter."""
        self._frame_count += 1
        current_time = time.time()
        if current_time - self._last_fps_time >= 1.0:
            self._fps = self._frame_count / (current_time - self._last_fps_time)
            self._frame_count = 0
            self._last_fps_time = current_time
    
    def get_fps(self) -> float:
        """Get current FPS.
        
        Returns:
            Frames per second
        """
        return self._fps
    
    def reset(self):
        """Reset all optimizers."""
        self.dirty_tracker.clear()
        self.render_cache.clear()
        self.batch_renderer.clear_all()
        self._frame_count = 0
        self._last_fps_time = time.time()
        self._fps = 0.0


# Global optimizer instance
_global_optimizer: Optional[RealtimeOptimizer] = None


def get_optimizer() -> RealtimeOptimizer:
    """Get the global optimizer instance.
    
    Returns:
        RealtimeOptimizer instance
    """
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = RealtimeOptimizer()
    return _global_optimizer

