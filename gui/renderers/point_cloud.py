"""Professional point cloud renderer with optimized performance and features.

This renderer uses the new UI rendering framework for optimal performance
and integrates with the real-time optimization system.
"""
import pygame
import math
import time
from typing import Optional, Tuple

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

from ..design.design_system import DesignSystem
from .ui_renderer import get_renderer
from .realtime_optimizer import get_optimizer

# Point cloud rendering using simple 3D projection
HAS_POINTCLOUD = True


class PointCloudRenderer:
    """Professional point cloud renderer with optimized performance and features."""
    
    def __init__(self, width: int = 800, height: int = 600):
        if not HAS_NUMPY:
            raise ImportError("numpy is required for PointCloudRenderer")
            
        self.width = width
        self.height = height
        self.camera_angle_x = 0.0
        self.camera_angle_y = 0.0
        self.zoom = 1.0
        
        # Rendering system integration
        self.renderer = get_renderer()
        self.optimizer = get_optimizer()
        
        # Rendering settings
        self.max_points = 20000  # Adaptive based on performance
        self.point_size = 1  # Pixels per point
        self.color_scheme = 'depth'  # 'depth', 'height', 'intensity', 'uniform'
        self.show_axes = True
        self.show_info = True
        
        # Filtering settings
        self.distance_filter_min = 0.0
        self.distance_filter_max = float('inf')
        self.use_voxel_downsample = False
        self.voxel_size = 0.1
        
        # Performance stats
        self.render_stats = {
            'total_points': 0,
            'rendered_points': 0,
            'render_time': 0.0,
            'fps': 0.0
        }
        
        # Enhanced cache with hash-based invalidation
        self._last_points_hash = None
        self._last_render_params = None
        self._cached_surface = None
        self._cache_key = None
        
    def set_camera(self, angle_x: float, angle_y: float, zoom: float):
        """Update camera parameters and invalidate cache if changed."""
        old_params = (self.camera_angle_x, self.camera_angle_y, self.zoom)
        self.camera_angle_x = angle_x
        self.camera_angle_y = angle_y
        self.zoom = zoom
        
        # Invalidate cache if camera changed
        new_params = (angle_x, angle_y, zoom)
        if old_params != new_params:
            self._last_render_params = None
            self._cached_surface = None
        
    def filter_points(self, points):
        """Apply filtering to point cloud."""
        if len(points) == 0:
            return points
            
        # Distance filter
        distances = np.linalg.norm(points, axis=1)
        mask = (distances >= self.distance_filter_min) & (distances <= self.distance_filter_max)
        points = points[mask]
        
        # Voxel downsampling (simple grid-based)
        if self.use_voxel_downsample and len(points) > 1000:
            points = self._voxel_downsample(points, self.voxel_size)
            
        return points
    
    def _voxel_downsample(self, points, voxel_size: float):
        """Simple voxel grid downsampling."""
        # Calculate voxel indices
        voxel_indices = np.floor(points / voxel_size).astype(np.int32)
        
        # Use dictionary to keep first point in each voxel
        voxel_dict = {}
        for i, idx in enumerate(voxel_indices):
            idx_tuple = tuple(idx)
            if idx_tuple not in voxel_dict:
                voxel_dict[idx_tuple] = i
        
        # Return downsampled points
        indices = list(voxel_dict.values())
        return points[indices]
    
    def adaptive_sample(self, points):
        """Adaptive sampling based on point count and zoom level."""
        if len(points) <= self.max_points:
            return points
            
        # Adjust max_points based on zoom (closer = more points)
        effective_max = int(self.max_points * (1.0 + self.zoom * 0.5))
        
        if len(points) <= effective_max:
            return points
            
        # Use stratified sampling for better distribution
        # Divide into spatial bins and sample from each
        num_bins = min(100, len(points) // 1000)
        if num_bins < 2:
            # Simple uniform sampling
            step = len(points) // effective_max
            return points[::step]
        
        # Spatial binning
        min_coords = np.min(points, axis=0)
        max_coords = np.max(points, axis=0)
        bin_size = (max_coords - min_coords) / num_bins
        
        sampled_indices = []
        points_per_bin = effective_max // num_bins
        
        for i in range(num_bins):
            for j in range(num_bins):
                for k in range(num_bins):
                    bin_min = min_coords + np.array([i, j, k]) * bin_size
                    bin_max = bin_min + bin_size
                    
                    mask = np.all((points >= bin_min) & (points < bin_max), axis=1)
                    bin_points = np.where(mask)[0]
                    
                    if len(bin_points) > 0:
                        if len(bin_points) <= points_per_bin:
                            sampled_indices.extend(bin_points)
                        else:
                            # Random sample from bin
                            selected = np.random.choice(bin_points, points_per_bin, replace=False)
                            sampled_indices.extend(selected)
        
        if len(sampled_indices) == 0:
            # Fallback to uniform sampling
            step = len(points) // effective_max
            return points[::step]
            
        return points[sampled_indices]
    
    def compute_colors(self, points, z_final, max_dist: float):
        """Compute colors based on color scheme using color manager."""
        primary_color = DesignSystem.COLORS['primary']
        
        if self.color_scheme == 'uniform':
            return np.full((len(points), 3), primary_color, dtype=np.uint8)
        
        # Depth-based coloring with enhanced gradient
        z_normalized = np.clip((z_final + max_dist) / (2 * max_dist), 0.0, 1.0)
        
        colors = np.zeros((len(points), 3), dtype=np.uint8)
        
        if self.color_scheme == 'height':
            # Height-based coloring (Z coordinate) with smooth gradient
            z_coords = points[:, 2]
            z_min, z_max = np.min(z_coords), np.max(z_coords)
            if z_max > z_min:
                height_normalized = (z_coords - z_min) / (z_max - z_min)
                # Use color manager for smooth blending
                for i, h_norm in enumerate(height_normalized):
                    blended = self.renderer.blend_colors(
                        DesignSystem.COLORS['primary_dark'],
                        DesignSystem.COLORS['primary_light'],
                        h_norm
                    )
                    colors[i] = blended
            else:
                colors[:] = primary_color
        else:
            # Depth-based coloring with smooth gradient
            for i, z_norm in enumerate(z_normalized):
                blended = self.renderer.blend_colors(
                    DesignSystem.COLORS['primary_dark'],
                    DesignSystem.COLORS['primary_light'],
                    z_norm
                )
                colors[i] = blended
        
        return colors
    
    def render(self, points) -> Optional[pygame.Surface]:
        """Render point cloud to pygame surface with optimizations and caching."""
        start_time = time.time()
        
        if not HAS_POINTCLOUD:
            return None
            
        if points is None:
            return None
            
        if len(points) == 0:
            # Return empty surface instead of None
            surface = pygame.Surface((self.width, self.height))
            surface.fill(DesignSystem.COLORS['bg'])
            return surface
        
        # Check cache first
        current_params = (self.camera_angle_x, self.camera_angle_y, self.zoom, 
                        self.width, self.height, self.color_scheme)
        
        # Simple hash for points (use first/last/middle points for quick comparison)
        if isinstance(points, np.ndarray) and len(points) > 0:
            points_hash = hash((len(points), 
                              tuple(points[0]) if len(points) > 0 else None,
                              tuple(points[-1]) if len(points) > 1 else None,
                              tuple(points[len(points)//2]) if len(points) > 2 else None))
        else:
            points_hash = hash(str(points)[:100])  # Simple hash for non-array
        
        cache_key = (points_hash, current_params)
        
        # Check if we can use cached surface
        if (self._cache_key == cache_key and 
            self._cached_surface is not None and
            self._cached_surface.get_width() == self.width and
            self._cached_surface.get_height() == self.height):
            return self._cached_surface
            
        try:
            # Validate input
            if not isinstance(points, np.ndarray):
                points = np.array(points, dtype=np.float32)
            
            if points.ndim != 2 or points.shape[1] < 3:
                print(f"Warning: Invalid point cloud shape: {points.shape if hasattr(points, 'shape') else type(points)}")
                # Return empty surface
                surface = pygame.Surface((self.width, self.height))
                surface.fill(DesignSystem.COLORS['bg'])
                return surface
            
            original_count = len(points)
            
            # Apply filters (but don't filter too aggressively)
            points = self.filter_points(points)
            if len(points) == 0:
                # Return empty surface instead of None
                surface = pygame.Surface((self.width, self.height))
                surface.fill(DesignSystem.COLORS['bg'])
                return surface
            
            # Adaptive sampling (preserve more points for better visualization)
            points = self.adaptive_sample(points)
            
            # Create surface
            surface = pygame.Surface((self.width, self.height))
            surface.fill(DesignSystem.COLORS['bg'])
            
            # Calculate center and scale
            center = np.mean(points, axis=0)
            points_centered = points - center
            distances = np.linalg.norm(points_centered, axis=1)
            max_dist = np.max(distances) if len(distances) > 0 else 1.0
            if max_dist == 0:
                max_dist = 1.0
            
            scale = min(self.width, self.height) * 0.4 / max_dist * self.zoom
            
            # Pre-compute rotation matrices
            cos_x, sin_x = math.cos(self.camera_angle_x), math.sin(self.camera_angle_x)
            cos_y, sin_y = math.cos(self.camera_angle_y), math.sin(self.camera_angle_y)
            
            # Vectorized rotation
            x, y, z = points_centered[:, 0], points_centered[:, 1], points_centered[:, 2]
            
            # Rotate around X axis
            y_rot = y * cos_x - z * sin_x
            z_rot = y * sin_x + z * cos_x
            
            # Rotate around Y axis
            x_final = x * cos_y + z_rot * sin_y
            z_final = -x * sin_y + z_rot * cos_y
            
            # Frustum culling (filter points in front) - less aggressive
            # Allow more points behind camera to be visible
            front_mask = z_final > -max_dist * 0.5  # Changed from 0.1 to 0.5 for more visibility
            x_final = x_final[front_mask]
            y_final = y_rot[front_mask]
            z_final = z_final[front_mask]
            
            if len(x_final) == 0:
                # Still return surface even if no points visible
                return surface
            
            # Perspective projection (vectorized)
            z_scale = 1.0 + z_final / max_dist
            proj_x_float = self.width / 2 + x_final * scale / z_scale
            proj_y_float = self.height / 2 - y_final * scale / z_scale
            
            # Convert to integer coordinates and clip to bounds FIRST
            # This ensures all coordinates are always within valid range
            proj_x = np.clip(proj_x_float.astype(np.int32), 0, self.width - 1)
            proj_y = np.clip(proj_y_float.astype(np.int32), 0, self.height - 1)
            
            # Get the corresponding original points for color computation
            filtered_points = points[front_mask] if len(points) == len(front_mask) else points
            
            # Compute colors for all points (they're all valid after clip)
            colors = self.compute_colors(filtered_points, z_final, max_dist)
            
            # Vectorized point drawing using pixel array with optimized access
            # Note: pygame.surfarray.pixels3d uses [y, x] indexing
            pixel_array = pygame.surfarray.pixels3d(surface)
            
            # Draw points (vectorized for better performance)
            # All coordinates are guaranteed to be in valid range after clip
            if len(proj_x) > 0 and len(proj_y) > 0:
                try:
                    if self.point_size == 1:
                        # Single pixel - fastest method with direct vectorized assignment
                        # Since we already clipped, all points are valid
                        min_len = min(len(proj_x), len(proj_y), len(colors))
                        if min_len > 0:
                            # Direct assignment - fastest for single pixel points
                            pixel_array[proj_y[:min_len], proj_x[:min_len]] = colors[:min_len]
                    else:
                        # Multi-pixel points with optimized batch drawing
                        # Limit processing for performance
                        max_points_to_draw = min(5000, len(proj_x))
                        half_size = self.point_size // 2
                        
                        # Process in batches for better performance
                        batch_size = 100
                        for batch_start in range(0, max_points_to_draw, batch_size):
                            batch_end = min(batch_start + batch_size, max_points_to_draw)
                            batch_x = proj_x[batch_start:batch_end]
                            batch_y = proj_y[batch_start:batch_end]
                            batch_colors = colors[batch_start:batch_end]
                            
                            for i, (px, py, color) in enumerate(zip(batch_x, batch_y, batch_colors)):
                                px, py = int(px), int(py)
                                # Draw square of pixels with bounds checking
                                y_min = max(0, py - half_size)
                                y_max = min(self.height, py + half_size + 1)
                                x_min = max(0, px - half_size)
                                x_max = min(self.width, px + half_size + 1)
                                
                                if y_max > y_min and x_max > x_min:
                                    pixel_array[y_min:y_max, x_min:x_max] = color
                except (IndexError, ValueError, MemoryError) as e:
                    # Fallback: draw points one by one if vectorized method fails
                    print(f"Vectorized drawing failed, using fallback: {e}")
                    max_points = min(5000, len(proj_x))  # Limit fallback points
                    for i in range(min(max_points, len(proj_x), len(proj_y), len(colors))):
                        px, py = int(proj_x[i]), int(proj_y[i])
                        if 0 <= px < self.width and 0 <= py < self.height:
                            try:
                                pixel_array[py, px] = colors[i]
                            except (IndexError, ValueError):
                                continue
            
            del pixel_array  # Unlock surface
            
            # Draw axes with fixed world coordinate length (relative to point cloud scale)
            if self.show_axes:
                # Use fixed world coordinate length based on point cloud scale
                axis_world_length = max_dist * 0.2  # 20% of point cloud extent
                
                # Origin is at point cloud center (which is at screen center after centering)
                origin_x, origin_y = self.width // 2, self.height // 2
                
                # World coordinate axes (relative to point cloud center)
                axis_points = np.array([
                    [axis_world_length, 0, 0],  # X axis (red)
                    [0, axis_world_length, 0],  # Y axis (green)
                    [0, 0, axis_world_length],  # Z axis (blue)
                ], dtype=np.float32)
                
                axis_colors = [
                    DesignSystem.COLORS['error'],    # X - Red
                    DesignSystem.COLORS['success'],  # Y - Green
                    DesignSystem.COLORS['primary'],  # Z - Blue/White
                ]
                
                axis_labels = ['X', 'Y', 'Z']
                
                # Project axes using the same center and scale as point cloud
                for idx, (axis_point, color) in enumerate(zip(axis_points, axis_colors)):
                    # Project axis endpoint using same transformation as points
                    axis_centered = axis_point  # Already relative to center
                    
                    # Apply same rotation as point cloud
                    x, y, z = axis_centered[0], axis_centered[1], axis_centered[2]
                    y_rot = y * cos_x - z * sin_x
                    z_rot = y * sin_x + z * cos_x
                    x_final = x * cos_y + z_rot * sin_y
                    z_final = -x * sin_y + z_rot * cos_y
                    
                    # Apply same perspective projection as points
                    z_scale = 1.0 + z_final / max_dist
                    axis_proj_x = int(self.width / 2 + x_final * scale / z_scale)
                    axis_proj_y = int(self.height / 2 - y_rot * scale / z_scale)
                    
                    # Only draw if axis endpoint is visible
                    if 0 <= axis_proj_x < self.width and 0 <= axis_proj_y < self.height:
                        # Draw axis line from origin to endpoint
                        pygame.draw.line(surface, color, 
                                       (origin_x, origin_y), 
                                       (axis_proj_x, axis_proj_y), 3)
                        
                        # Draw axis label at endpoint using optimized renderer
                        if idx < len(axis_labels):
                            label_text = axis_labels[idx]
                            label_width, label_height = self.renderer.measure_text(label_text, 'small')
                            label_x = axis_proj_x + 5
                            label_y = axis_proj_y - 5
                            self.renderer.render_text(surface, label_text,
                                                    (label_x, label_y),
                                                    size='small',
                                                    color=color)
            
            # Draw info text using optimized renderer
            if self.show_info:
                render_time = (time.time() - start_time) * 1000
                info_text = (f"Points: {original_count} → {len(proj_x)} | "
                           f"Zoom: {self.zoom:.2f} | "
                           f"Time: {render_time:.1f}ms")
                self.renderer.render_text(surface, info_text,
                                        (10, 10),
                                        size='small',
                                        color=DesignSystem.COLORS['text_secondary'])
            
            # Update stats
            render_time = time.time() - start_time
            self.render_stats = {
                'total_points': original_count,
                'rendered_points': len(proj_x) if 'proj_x' in locals() else 0,
                'render_time': render_time,
                'fps': 1.0 / render_time if render_time > 0 else 0
            }
            
            # Cache the rendered surface
            self._cache_key = cache_key
            self._cached_surface = surface.copy() if surface else None
            self._last_render_params = current_params
            self._last_points_hash = points_hash
            
            # Store in global cache for reuse
            if surface:
                self.optimizer.cache_surface(cache_key, surface)
            
            return surface
            
        except Exception as e:
            print(f"Point cloud render error: {e}")
            import traceback
            traceback.print_exc()
            # Return empty surface instead of None to prevent display issues
            try:
                surface = pygame.Surface((self.width, self.height))
                surface.fill(DesignSystem.COLORS['bg'])
                # Mark dirty region for optimization
                self.optimizer.mark_dirty(pygame.Rect(0, 0, self.width, self.height))
                return surface
            except:
                return None
    
    def invalidate_cache(self):
        """Invalidate render cache."""
        self._cache_key = None
        self._cached_surface = None
        self._last_render_params = None
        self._last_points_hash = None
    
    def set_size(self, width: int, height: int):
        """Update renderer size and invalidate cache."""
        if self.width != width or self.height != height:
            self.width = width
            self.height = height
            self.invalidate_cache()
    
    def get_stats(self) -> dict:
        """Get rendering statistics."""
        return self.render_stats.copy()

