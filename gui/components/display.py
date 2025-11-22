"""Professional display components for images and point clouds."""
import pygame
import math
from typing import Optional, Tuple, List

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

from .base import UIComponent
from ..design.design_system import DesignSystem
from ..renderers.point_cloud import PointCloudRenderer, HAS_POINTCLOUD


class ImageDisplayComponent(UIComponent):
    """Professional image display component with optimized rendering."""
    
    def __init__(self, x: int, y: int, width: int, height: int, title: str = ""):
        super().__init__(x, y, width, height)
        self.title = title
        self.image: Optional[pygame.Surface] = None
        self.placeholder_text = "Waiting for image..."
        
    def set_image(self, image: Optional[pygame.Surface]):
        """Set the image to display."""
        self.image = image
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events."""
        if not self.visible or not self.enabled:
            return False
        return self.rect.collidepoint(event.pos) if hasattr(event, 'pos') else False
        
    def update(self, dt: float):
        """Update component state."""
        pass
        
    def draw(self, surface: pygame.Surface):
        """Draw image display component."""
        if not self.visible:
            return
            
        # Draw background
        pygame.draw.rect(surface, DesignSystem.COLORS['surface'], self.rect,
                        border_radius=DesignSystem.RADIUS['lg'])
        pygame.draw.rect(surface, DesignSystem.COLORS['border'], self.rect,
                        width=1, border_radius=DesignSystem.RADIUS['lg'])
        
        # Draw title if present
        if self.title:
            header_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 36)
            pygame.draw.rect(surface, DesignSystem.COLORS['surface_light'], header_rect,
                           border_radius=DesignSystem.RADIUS['lg'])
            pygame.draw.rect(surface, DesignSystem.COLORS['border_light'], header_rect,
                           width=1, border_radius=DesignSystem.RADIUS['lg'])
            
            font = DesignSystem.get_font('label')
            title_surf = font.render(self.title, True, DesignSystem.COLORS['text'])
            title_y = header_rect.y + (header_rect.height - title_surf.get_height()) // 2
            surface.blit(title_surf, (header_rect.x + DesignSystem.SPACING['md'], title_y))
        
        # Calculate image area (below title if present)
        img_area = pygame.Rect(
            self.rect.x + 10,
            self.rect.y + (36 + 10 if self.title else 10),
            self.rect.width - 20,
            self.rect.height - (36 + 20 if self.title else 20)
        )
        
        # Draw image or placeholder
        if self.image:
            img_rect = self.image.get_rect()
            # Scale to fill area while maintaining aspect ratio
            scale = min(img_area.width / img_rect.width, img_area.height / img_rect.height)
            new_size = (int(img_rect.width * scale), int(img_rect.height * scale))
            scaled_img = pygame.transform.scale(self.image, new_size)
            scaled_rect = scaled_img.get_rect(center=img_area.center)
            surface.blit(scaled_img, scaled_rect)
        else:
            # Draw placeholder
            font = DesignSystem.get_font('label')
            placeholder_surf = font.render(self.placeholder_text, True, 
                                          DesignSystem.COLORS['text_secondary'])
            placeholder_rect = placeholder_surf.get_rect(center=img_area.center)
            surface.blit(placeholder_surf, placeholder_rect)


class PointCloudDisplayComponent(UIComponent):
    """Professional point cloud display component with 3D view controls."""
    
    def __init__(self, x: int, y: int, width: int, height: int, title: str = ""):
        super().__init__(x, y, width, height)
        self.title = title
        self.pc_surface: Optional[pygame.Surface] = None
        self.renderer: Optional[PointCloudRenderer] = None
        
        # Camera controls
        self.camera_angle_x = 0.0
        self.camera_angle_y = 0.0
        self.zoom = 1.0
        
        # 3D cube control (bottom left corner)
        self.cube_size = 80
        self.cube_margin = 15
        self.cube_hovered_face = None
        self.cube_rotation = 0.0
        
        # Drag state for cube rotation
        self.cube_dragging = False
        self.cube_drag_start_pos = None
        self.cube_drag_start_angles = None
        self.cube_drag_initial_pos = None
        self.cube_drag_initial_angles = None
        
        # View presets
        self.view_presets = {
            'front': (0.0, 0.0),
            'top': (-math.pi / 2, 0.0),
            'side': (0.0, math.pi / 2),
            'iso': (-math.pi / 6, math.pi / 4),
            'back': (0.0, math.pi),
            'bottom': (math.pi / 2, 0.0),
        }
        
        if HAS_POINTCLOUD:
            self.renderer = PointCloudRenderer(width=width - 20, height=height - 56)
        
    def set_pointcloud(self, pc_surface: Optional[pygame.Surface]):
        """Set the point cloud surface to display."""
        self.pc_surface = pc_surface
        
    def set_camera(self, angle_x: float, angle_y: float, zoom: float):
        """Set camera parameters with port system notification."""
        old_camera = (self.camera_angle_x, self.camera_angle_y, self.zoom)
        self.camera_angle_x = angle_x
        self.camera_angle_y = angle_y
        self.zoom = zoom
        if self.renderer:
            self.renderer.set_camera(angle_x, angle_y, zoom)
        
        # Emit camera change signal through port system
        new_camera = (angle_x, angle_y, zoom)
        self.emit_signal('change', {'camera': new_camera, 'old_camera': old_camera})
        self.emit_signal('on_change', new_camera)
        # Update value port
        port = self.get_port('value')
        if port:
            port.value = new_camera
            
    def get_camera(self) -> Tuple[float, float, float]:
        """Get current camera parameters."""
        return (self.camera_angle_x, self.camera_angle_y, self.zoom)
        
    def _get_cube_rect(self) -> pygame.Rect:
        """Get the 3D cube control rect (bottom left) - relative to component origin (0,0)."""
        return pygame.Rect(
            self.cube_margin,
            self.rect.height - self.cube_size - self.cube_margin,
            self.cube_size,
            self.cube_size
        )
    
    def _get_cube_geometry(self):
        """Get cube geometry (vertices, faces, normals) in 3D space."""
        if not HAS_NUMPY:
            return None, None, None
            
        size = self.cube_size * 0.25
        
        # Cube vertices in 3D space (relative to center)
        vertices_3d = np.array([
            [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],  # Back face (0-3)
            [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1],     # Front face (4-7)
        ], dtype=np.float32) * size
        
        # Define faces with vertex indices and their normals (before rotation)
        faces_data = [
            ([4, 5, 6, 7], 'front', np.array([0, 0, 1])),   # Front face (positive Z)
            ([0, 3, 2, 1], 'back', np.array([0, 0, -1])),   # Back face (negative Z)
            ([3, 7, 6, 2], 'top', np.array([0, 1, 0])),     # Top face (positive Y)
            ([0, 1, 5, 4], 'bottom', np.array([0, -1, 0])),  # Bottom face (negative Y)
            ([1, 2, 6, 5], 'right', np.array([1, 0, 0])),    # Right face (positive X)
            ([0, 4, 7, 3], 'left', np.array([-1, 0, 0])),   # Left face (negative X)
        ]
        
        # Apply rotation to vertices and normals
        cos_x, sin_x = math.cos(self.camera_angle_x), math.sin(self.camera_angle_x)
        cos_y, sin_y = math.cos(self.camera_angle_y), math.sin(self.camera_angle_y)
        
        # Rotate vertices
        rotated_vertices = []
        for v in vertices_3d:
            x, y, z = v[0], v[1], v[2]
            y_rot = y * cos_x - z * sin_x
            z_rot = y * sin_x + z * cos_x
            x_final = x * cos_y + z_rot * sin_y
            z_final = -x * sin_y + z_rot * cos_y
            rotated_vertices.append(np.array([x_final, y_rot, z_final]))
        
        # Rotate normals
        rotated_faces = []
        for face_indices, face_name, normal in faces_data:
            # Rotate normal vector
            nx, ny, nz = normal[0], normal[1], normal[2]
            ny_rot = ny * cos_x - nz * sin_x
            nz_rot = ny * sin_x + nz * cos_x
            nx_final = nx * cos_y + nz_rot * sin_y
            nz_final = -nx * sin_y + nz_rot * cos_y
            rotated_normal = np.array([nx_final, ny_rot, nz_final])
            rotated_faces.append((face_indices, face_name, rotated_normal))
        
        return rotated_vertices, rotated_faces, (cos_x, sin_x, cos_y, sin_y)
    
    def _project_3d_to_2d(self, vertex_3d, center_x, center_y):
        """Project a 3D vertex to 2D screen coordinates."""
        x, y, z = vertex_3d[0], vertex_3d[1], vertex_3d[2]
        # Simple orthographic projection
        proj_x = int(center_x + x)
        proj_y = int(center_y - y)  # Flip Y axis
        return (proj_x, proj_y)
    
    def _get_face_from_mouse(self, pos: Tuple[int, int]) -> Optional[str]:
        """Accurately determine which cube face is under the mouse using improved 3D ray casting."""
        if not HAS_NUMPY:
            return None
            
        cube_rect = self._get_cube_rect()
        if not cube_rect.collidepoint(pos):
            return None
        
        center_x, center_y = cube_rect.center
        rotated_vertices, rotated_faces, _ = self._get_cube_geometry()
        if rotated_vertices is None:
            return None
        
        # Convert mouse position to relative coordinates (relative to cube center)
        rel_x = pos[0] - center_x
        rel_y = pos[1] - center_y
        
        # Project all faces to 2D and find which one contains the mouse point
        best_face = None
        best_depth = float('inf')
        best_distance = float('inf')
        
        for face_indices, face_name, face_normal in rotated_faces:
            # Only consider faces facing the camera
            if face_normal[2] >= 0:  # Face is not visible (back-facing)
                continue
            
            # Project face vertices to 2D screen coordinates
            face_2d = [self._project_3d_to_2d(rotated_vertices[idx], center_x, center_y) for idx in face_indices]
            mouse_2d = (pos[0], pos[1])
            
            # Check if mouse point is inside the projected face polygon
            if self._point_in_polygon(mouse_2d, face_2d):
                # Calculate face center depth for z-ordering
                face_center = np.mean([rotated_vertices[idx] for idx in face_indices], axis=0)
                depth = face_center[2]  # Z depth (negative is closer to camera)
                
                # Also calculate distance from mouse to face center in 2D for tie-breaking
                face_center_2d = self._project_3d_to_2d(face_center, center_x, center_y)
                distance = ((mouse_2d[0] - face_center_2d[0])**2 + (mouse_2d[1] - face_center_2d[1])**2)**0.5
                
                # Prefer closer faces (more negative depth), and if same depth, prefer closer in 2D
                if depth < best_depth or (abs(depth - best_depth) < 0.1 and distance < best_distance):
                    best_depth = depth
                    best_distance = distance
                    best_face = face_name
        
        return best_face
    
    def _point_in_polygon(self, point: Tuple[int, int], polygon: List[Tuple[int, int]]) -> bool:
        """Check if a point is inside a polygon using improved ray casting algorithm."""
        if len(polygon) < 3:
            return False
            
        x, y = point
        n = len(polygon)
        inside = False
        
        # Use ray casting algorithm with proper edge handling
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            
            # Check if point is on the edge (with small tolerance)
            if abs((yj - yi) * (x - xi) - (xj - xi) * (y - yi)) < 1e-6:
                # Point is on the line segment
                if min(xi, xj) <= x <= max(xi, xj) and min(yi, yj) <= y <= max(yi, yj):
                    return True
            
            # Ray casting: check if ray from point crosses edge
            if ((yi > y) != (yj > y)):  # Edge crosses horizontal line through point
                # Calculate x-coordinate of intersection
                if yj != yi:  # Avoid division by zero
                    x_intersect = (xj - xi) * (y - yi) / (yj - yi) + xi
                    if x < x_intersect:
                        inside = not inside
            
            j = i
        
        return inside
        
    def _draw_3d_cube_control(self, surface: pygame.Surface):
        """Draw 3D cube control with accurate face detection and hover highlighting."""
        if not HAS_NUMPY:
            return
            
        cube_rect = self._get_cube_rect()
        
        # Draw cube background with hover effect
        bg_color = DesignSystem.COLORS['surface_active'] if self.cube_hovered_face else DesignSystem.COLORS['surface_light']
        pygame.draw.rect(surface, bg_color, cube_rect,
                       border_radius=DesignSystem.RADIUS['sm'])
        border_color = DesignSystem.COLORS['primary'] if self.cube_hovered_face else DesignSystem.COLORS['border']
        pygame.draw.rect(surface, border_color, cube_rect,
                       width=2 if self.cube_hovered_face else 1, border_radius=DesignSystem.RADIUS['sm'])
        
        # Get cube geometry
        rotated_vertices, rotated_faces, _ = self._get_cube_geometry()
        if rotated_vertices is None:
            return
        
        center_x, center_y = cube_rect.center
        
        # Project vertices to 2D
        vertices_2d = [self._project_3d_to_2d(v, center_x, center_y) for v in rotated_vertices]
        
        # Define face colors (RGB)
        base_face_colors = {
            'front': (255, 0, 0),      # Red
            'back': (0, 255, 0),       # Green
            'top': (0, 0, 255),        # Blue
            'bottom': (255, 255, 0),   # Yellow
            'right': (255, 0, 255),    # Magenta
            'left': (0, 255, 255),     # Cyan
        }
        
        # Calculate face depths and prepare for rendering
        face_render_data = []
        for face_indices, face_name, face_normal in rotated_faces:
            # Calculate average depth
            face_center = np.mean([rotated_vertices[idx] for idx in face_indices], axis=0)
            depth = face_center[2]
            
            # Only render faces facing camera (normal.z < 0)
            if face_normal[2] < 0:
                face_points = [vertices_2d[idx] for idx in face_indices]
                face_render_data.append((depth, face_indices, face_name, face_points))
        
        # Sort faces by depth (back to front)
        face_render_data.sort(key=lambda x: x[0], reverse=True)
        
        # Draw faces (back to front)
        for depth, face_indices, face_name, face_points in face_render_data:
            base_color = base_face_colors[face_name]
            
            # Highlight hovered face
            if self.cube_hovered_face == face_name:
                # Brighten and add glow effect
                highlight_color = tuple(min(255, int(c * 1.5)) for c in base_color)
                alpha_color = tuple(min(255, int(c * 0.9)) for c in highlight_color)
                border_width = 3
                border_color = highlight_color
            else:
                # Normal appearance
                alpha_color = tuple(int(c * 0.6) for c in base_color)
                border_width = 2
                border_color = base_color
            
            # Draw face fill
            pygame.draw.polygon(surface, alpha_color, face_points)
            # Draw face border
            pygame.draw.polygon(surface, border_color, face_points, width=border_width)
        
        # Draw cube edges for better definition
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # Back face
            (4, 5), (5, 6), (6, 7), (7, 4),  # Front face
            (0, 4), (1, 5), (2, 6), (3, 7),  # Connecting edges
        ]
        
        edge_color = DesignSystem.COLORS['primary'] if self.cube_hovered_face else DesignSystem.COLORS['text']
        for edge in edges:
            pygame.draw.line(surface, edge_color,
                           vertices_2d[edge[0]], vertices_2d[edge[1]], 1)
        
        # Draw face labels
        font = DesignSystem.get_font('small')
        # Determine which face is facing forward based on camera angles
        if abs(self.camera_angle_x + math.pi / 2) < 0.3:
            label = "TOP"
        elif abs(self.camera_angle_x - math.pi / 2) < 0.3:
            label = "BOT"
        elif abs(self.camera_angle_y) < 0.3:
            label = "FRONT"
        elif abs(self.camera_angle_y - math.pi) < 0.3 or abs(self.camera_angle_y + math.pi) < 0.3:
            label = "BACK"
        elif abs(self.camera_angle_y - math.pi / 2) < 0.3:
            label = "RIGHT"
        elif abs(self.camera_angle_y + math.pi / 2) < 0.3:
            label = "LEFT"
        else:
            label = "ISO"
            
        label_color = DesignSystem.COLORS['primary'] if self.cube_hovered_face else DesignSystem.COLORS['text']
        label_surf = font.render(label, True, label_color)
        label_rect = label_surf.get_rect(center=(center_x, center_y))
        surface.blit(label_surf, label_rect)
        
        # Draw instruction hint
        hint_font = DesignSystem.get_font('small')
        hint_text = "Click face to rotate"
        hint_surf = hint_font.render(hint_text, True, DesignSystem.COLORS['text_tertiary'])
        hint_y = cube_rect.bottom + 5
        if hint_y + hint_surf.get_height() < self.rect.bottom:
            surface.blit(hint_surf, (cube_rect.x, hint_y))
            
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events including cube control clicks and drag rotation with port system integration."""
        if not self.visible or not self.enabled:
            return False
            
        cube_rect = self._get_cube_rect()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if hasattr(event, 'pos') and cube_rect.collidepoint(event.pos):
                # Check if it's a drag (middle button or right button) or click (left button)
                if event.button == 1:  # Left button - click to set view
                    # Use accurate face detection
                    face = self._get_face_from_mouse(event.pos)
                    
                    if face:
                        # Map face to view preset
                        view_map = {
                            'front': 'front',
                            'back': 'back',
                            'top': 'top',
                            'bottom': 'bottom',
                            'right': 'side',
                            'left': 'side',  # Both left and right map to side view
                        }
                        preset = view_map.get(face, 'iso')
                        
                        if preset in self.view_presets:
                            angle_x, angle_y = self.view_presets[preset]
                            self.set_camera(angle_x, angle_y, 1.0)
                            
                            # Emit signals through port system
                            self.emit_signal('click', face)
                            self.emit_signal('on_click', {'face': face, 'preset': preset, 
                                                           'camera': (angle_x, angle_y, 1.0)})
                            self.emit_signal('change', {'camera': (angle_x, angle_y, 1.0)})
                            return True
                    else:
                        # Click on cube but not on a face - cycle views
                        current_preset = None
                        for name, (ax, ay) in self.view_presets.items():
                            if abs(self.camera_angle_x - ax) < 0.1 and abs(self.camera_angle_y - ay) < 0.1:
                                current_preset = name
                                break
                        
                        # Cycle to next preset
                        preset_order = ['front', 'top', 'side', 'iso', 'back', 'bottom']
                        if current_preset in preset_order:
                            current_idx = preset_order.index(current_preset)
                            next_idx = (current_idx + 1) % len(preset_order)
                            next_preset = preset_order[next_idx]
                        else:
                            next_preset = 'front'
                        
                        if next_preset in self.view_presets:
                            angle_x, angle_y = self.view_presets[next_preset]
                            self.set_camera(angle_x, angle_y, 1.0)
                            self.emit_signal('click', 'cycle')
                            self.emit_signal('on_click', {'action': 'cycle', 'preset': next_preset})
                            return True
                elif event.button in (2, 3):  # Middle or right button - start drag
                    # Start dragging for rotation
                    self.cube_dragging = True
                    self.cube_drag_start_pos = event.pos
                    self.cube_drag_initial_pos = event.pos
                    self.cube_drag_start_angles = (self.camera_angle_x, self.camera_angle_y)
                    self.cube_drag_initial_angles = (self.camera_angle_x, self.camera_angle_y)
                    return True
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.cube_dragging:
                self.cube_dragging = False
                self.cube_drag_start_pos = None
                self.cube_drag_initial_pos = None
                self.cube_drag_start_angles = None
                self.cube_drag_initial_angles = None
                return True
                    
        elif event.type == pygame.MOUSEMOTION:
            if self.cube_dragging and self.cube_drag_initial_pos and self.cube_drag_initial_angles:
                # Calculate rotation based on mouse movement
                if hasattr(event, 'pos'):
                    # Calculate movement from initial drag position
                    if hasattr(event, 'rel') and event.rel:
                        # Use relative movement for smooth rotation (preferred)
                        dx = event.rel[0]
                        dy = event.rel[1]
                        # Update start angles for next frame (accumulate)
                        new_angle_y = self.cube_drag_start_angles[1] + dx * 0.01
                        new_angle_x = self.cube_drag_start_angles[0] - dy * 0.01
                        self.cube_drag_start_angles = (new_angle_x, new_angle_y)
                    else:
                        # Fallback: calculate from initial position
                        dx = event.pos[0] - self.cube_drag_initial_pos[0]
                        dy = event.pos[1] - self.cube_drag_initial_pos[1]
                        sensitivity = 0.01
                        new_angle_y = self.cube_drag_initial_angles[1] + dx * sensitivity
                        new_angle_x = self.cube_drag_initial_angles[0] - dy * sensitivity
                    
                    # Clamp X angle to prevent flipping
                    new_angle_x = max(-math.pi / 2, min(math.pi / 2, new_angle_x))
                    
                    self.set_camera(new_angle_x, new_angle_y, self.zoom)
                    return True
            elif hasattr(event, 'pos') and cube_rect.collidepoint(event.pos):
                # Use accurate face detection for hover (only when not dragging)
                if not self.cube_dragging:
                    hovered_face = self._get_face_from_mouse(event.pos)
                    if hovered_face != self.cube_hovered_face:
                        self.cube_hovered_face = hovered_face
                        # Emit hover signal
                        self.emit_signal('hover', hovered_face)
                        self.emit_signal('on_hover', {'face': hovered_face})
            else:
                if self.cube_hovered_face is not None:
                    self.cube_hovered_face = None
                    self.emit_signal('hover', None)
            
        return False
        
    def update(self, dt: float):
        """Update component state."""
        self.cube_rotation += dt * 0.5  # Slow rotation animation
        
    def draw(self, surface: pygame.Surface):
        """Draw point cloud display component with enhanced visuals."""
        if not self.visible:
            return
            
        # Draw background with subtle gradient effect
        pygame.draw.rect(surface, DesignSystem.COLORS['bg_panel'], self.rect,
                        border_radius=DesignSystem.RADIUS['md'])
        pygame.draw.rect(surface, DesignSystem.COLORS['border'], self.rect,
                        width=1, border_radius=DesignSystem.RADIUS['md'])
        
        # Draw title if present
        # Note: Card sets child.rect to (0,0) during draw, so use relative coordinates
        if self.title:
            header_rect = pygame.Rect(0, 0, self.rect.width, 36)
            pygame.draw.rect(surface, DesignSystem.COLORS['surface_light'], header_rect,
                           border_radius=DesignSystem.RADIUS['md'])
            pygame.draw.rect(surface, DesignSystem.COLORS['border_light'], header_rect,
                           width=1, border_radius=DesignSystem.RADIUS['md'])
            
            font = DesignSystem.get_font('label')
            title_surf = font.render(self.title, True, DesignSystem.COLORS['text'])
            title_y = header_rect.y + (header_rect.height - title_surf.get_height()) // 2
            surface.blit(title_surf, (header_rect.x + DesignSystem.SPACING['md'], title_y))
        
        # Calculate point cloud area (below title if present, with padding)
        # Use relative coordinates since Card sets rect to (0,0) during draw
        padding = DesignSystem.SPACING['sm']
        header_height = 36 if self.title else 0
        pc_area = pygame.Rect(
            padding,
            header_height + padding,
            self.rect.width - padding * 2,
            self.rect.height - header_height - padding * 2
        )
        
        # Draw point cloud or placeholder
        if self.pc_surface:
            try:
                pc_copy = self.pc_surface.copy()
                pc_rect = pc_copy.get_rect()
                if pc_rect.width > 0 and pc_rect.height > 0:
                    # Scale to fill area completely while maintaining aspect ratio
                    scale_w = pc_area.width / pc_rect.width
                    scale_h = pc_area.height / pc_rect.height
                    scale = max(scale_w, scale_h)  # Fill entire area
                    new_size = (int(pc_rect.width * scale), int(pc_rect.height * scale))
                    if new_size[0] > 0 and new_size[1] > 0:
                        scaled_pc = pygame.transform.scale(pc_copy, new_size)
                        scaled_rect = scaled_pc.get_rect(center=pc_area.center)
                        surface.blit(scaled_pc, scaled_rect)
            except Exception:
                pass
        else:
            # Draw enhanced placeholder with icon-like visual
            center_x, center_y = pc_area.center
            
            # Draw placeholder background
            placeholder_bg = pygame.Rect(
                center_x - 150, center_y - 40,
                300, 80
            )
            pygame.draw.rect(surface, DesignSystem.COLORS['surface_light'], placeholder_bg,
                           border_radius=DesignSystem.RADIUS['md'])
            pygame.draw.rect(surface, DesignSystem.COLORS['border'], placeholder_bg,
                           width=1, border_radius=DesignSystem.RADIUS['md'])
            
            # Draw placeholder text
            font = DesignSystem.get_font('label')
            placeholder_surf = font.render("Waiting for point cloud data...", True,
                                          DesignSystem.COLORS['text_secondary'])
            placeholder_rect = placeholder_surf.get_rect(center=(center_x, center_y))
            surface.blit(placeholder_surf, placeholder_rect)
        
        # Draw 3D cube control (bottom left) - only if there's space
        cube_rect = self._get_cube_rect()
        if cube_rect.bottom <= self.rect.bottom - padding:
            self._draw_3d_cube_control(surface)

