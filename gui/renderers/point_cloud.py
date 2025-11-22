"""Professional point cloud renderer with optimized performance and features."""
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
        
        # Cache
        self._last_points_hash = None
        self._last_render_params = None
        self._cached_surface = None
        
    def set_camera(self, angle_x: float, angle_y: float, zoom: float):
        """Update camera parameters."""
        self.camera_angle_x = angle_x
        self.camera_angle_y = angle_y
        self.zoom = zoom
        
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
        """Compute colors based on color scheme."""
        if self.color_scheme == 'uniform':
            primary_r, primary_g, primary_b = DesignSystem.COLORS['primary']
            return np.full((len(points), 3), [primary_r, primary_g, primary_b], dtype=np.uint8)
        
        # Depth-based coloring
        z_normalized = np.clip((z_final + max_dist) / (2 * max_dist), 0.0, 1.0)
        primary_r, primary_g, primary_b = DesignSystem.COLORS['primary']
        
        colors = np.zeros((len(points), 3), dtype=np.uint8)
        colors[:, 0] = (primary_r * z_normalized).astype(np.uint8)
        colors[:, 1] = (primary_g * z_normalized).astype(np.uint8)
        colors[:, 2] = primary_b
        
        if self.color_scheme == 'height':
            # Height-based coloring (Z coordinate)
            z_coords = points[:, 2]
            z_min, z_max = np.min(z_coords), np.max(z_coords)
            if z_max > z_min:
                height_normalized = (z_coords - z_min) / (z_max - z_min)
                colors[:, 0] = (primary_r * height_normalized).astype(np.uint8)
                colors[:, 1] = (primary_g * height_normalized).astype(np.uint8)
                colors[:, 2] = (primary_b * height_normalized).astype(np.uint8)
        
        return colors
    
    def render(self, points) -> Optional[pygame.Surface]:
        """Render point cloud to pygame surface with optimizations."""
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
            
            # Vectorized point drawing using pixel array
            # Note: pygame.surfarray.pixels3d uses [y, x] indexing
            pixel_array = pygame.surfarray.pixels3d(surface)
            
            # Draw points (vectorized for better performance)
            # All coordinates are guaranteed to be in valid range after clip
            if len(proj_x) > 0 and len(proj_y) > 0:
                try:
                    if self.point_size == 1:
                        # Single pixel - fastest method
                        min_len = min(len(proj_x), len(proj_y), len(colors))
                        if min_len > 0:
                            pixel_array[proj_y[:min_len], proj_x[:min_len]] = colors[:min_len]
                    else:
                        # Multi-pixel points with bounds checking
                        for i in range(len(proj_x)):
                            px, py = int(proj_x[i]), int(proj_y[i])
                            # Double-check bounds (shouldn't be needed after clip, but safety)
                            if 0 <= px < self.width and 0 <= py < self.height:
                                color = colors[i]
                                size = self.point_size
                                half_size = size // 2
                                # Draw square of pixels
                                for dy in range(-half_size, half_size + 1):
                                    for dx in range(-half_size, half_size + 1):
                                        x_pos, y_pos = px + dx, py + dy
                                        if 0 <= x_pos < self.width and 0 <= y_pos < self.height:
                                            pixel_array[y_pos, x_pos] = color
                except (IndexError, ValueError) as e:
                    # Fallback: draw points one by one if vectorized method fails
                    print(f"Vectorized drawing failed, using fallback: {e}")
                    for i in range(min(len(proj_x), len(proj_y), len(colors))):
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
                
                # Project axes using the same center and scale as point cloud
                for axis_point, color in zip(axis_points, axis_colors):
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
                        
                        # Draw axis label at endpoint
                        font = DesignSystem.get_font('small')
                        axis_labels = ['X', 'Y', 'Z']
                        label_idx = list(axis_colors).index(color)
                        if label_idx < len(axis_labels):
                            label_surf = font.render(axis_labels[label_idx], True, color)
                            # Position label slightly offset from endpoint
                            label_pos = (axis_proj_x + 5, axis_proj_y - 5)
                            surface.blit(label_surf, label_pos)
            
            # Draw info text
            if self.show_info:
                font = DesignSystem.get_font('small')
                render_time = (time.time() - start_time) * 1000
                info_text = (f"Points: {original_count} → {len(proj_x)} | "
                           f"Zoom: {self.zoom:.2f} | "
                           f"Time: {render_time:.1f}ms")
                text_surf = font.render(info_text, True, DesignSystem.COLORS['text_secondary'])
                surface.blit(text_surf, (10, 10))
            
            # Update stats
            render_time = time.time() - start_time
            self.render_stats = {
                'total_points': original_count,
                'rendered_points': len(proj_x) if 'proj_x' in locals() else 0,
                'render_time': render_time,
                'fps': 1.0 / render_time if render_time > 0 else 0
            }
            
            return surface
            
        except Exception as e:
            print(f"Point cloud render error: {e}")
            import traceback
            traceback.print_exc()
            # Return empty surface instead of None to prevent display issues
            try:
                surface = pygame.Surface((self.width, self.height))
                surface.fill(DesignSystem.COLORS['bg'])
                return surface
            except:
                return None

