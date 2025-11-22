"""Advanced UI components for maps, JSON editing, and topic lists."""
import pygame
import json
from typing import Optional, Dict, Any, List, Tuple

from .base import UIComponent
from .interactive import Items
from ..design.design_system import DesignSystem


class MapComponent(UIComponent):
    """Professional map display component for showing drone positions and trajectories."""
    
    def __init__(self, x: int, y: int, width: int, height: int, title: str = ""):
        super().__init__(x, y, width, height)
        self.title = title
        self.drones: Dict[str, Dict[str, Any]] = {}  # Will be set from parent
        self.current_drone_id: Optional[str] = None  # Will be set from parent
        
    def set_drones(self, drones: Dict[str, Dict[str, Any]], current_drone_id: Optional[str]):
        """Set the drones data and current selection."""
        self.drones = drones
        self.current_drone_id = current_drone_id
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events - can be used for clicking on drones to select them."""
        if not self.visible or not self.enabled:
            return False
        if hasattr(event, 'pos') and self.rect.collidepoint(event.pos):
            # Could implement click-to-select drone here
            return True
        return False
    
    def update(self, dt: float):
        """Update component state."""
        pass
    
    def draw(self, surface: pygame.Surface):
        """Draw map component with drone positions and trajectories."""
        if not self.visible:
            return
        
        # Calculate map area (relative to component origin, which Card sets to 0,0)
        padding = DesignSystem.SPACING['md']
        header_height = 36 if self.title else 0
        map_rect = pygame.Rect(
            padding,
            header_height + padding,
            self.rect.width - padding * 2,
            self.rect.height - header_height - padding * 2
        )
        
        # Draw map background
        pygame.draw.rect(surface, DesignSystem.COLORS['bg_secondary'], map_rect,
                       border_radius=DesignSystem.RADIUS['sm'])
        
        # Collect all drone positions
        drone_positions = []
        for drone_id, drone_info in self.drones.items():
            if drone_info.get('client') and drone_info.get('is_connected'):
                try:
                    pos = drone_info['client'].get_position()
                    if len(pos) >= 3 and pos[0] != 0.0 and pos[1] != 0.0:
                        drone_positions.append({
                            'id': drone_id,
                            'name': drone_info['name'],
                            'lat': pos[0],
                            'lon': pos[1],
                            'alt': pos[2],
                            'state': drone_info['client'].get_status(),
                            'trajectory': drone_info.get('trajectory', [])
                        })
                except:
                    pass
        
        if len(drone_positions) == 0:
            # No drones with valid positions
            font = DesignSystem.get_font('label')
            no_data_text = font.render("No drone positions available. Connect drones to see their positions on the map.",
                                     True, DesignSystem.COLORS['text_secondary'])
            text_rect = no_data_text.get_rect(center=map_rect.center)
            surface.blit(no_data_text, text_rect)
        else:
            # Calculate map bounds
            lats = [d['lat'] for d in drone_positions]
            lons = [d['lon'] for d in drone_positions]
            min_lat, max_lat = min(lats), max(lats)
            min_lon, max_lon = min(lons), max(lons)
            
            # Add padding
            lat_range = max(max_lat - min_lat, 0.001)  # Minimum range
            lon_range = max(max_lon - min_lon, 0.001)
            padding_factor = 0.1
            min_lat -= lat_range * padding_factor
            max_lat += lat_range * padding_factor
            min_lon -= lon_range * padding_factor
            max_lon += lon_range * padding_factor
            lat_range = max_lat - min_lat
            lon_range = max_lon - min_lon
            
            # Draw trajectories
            for drone_data in drone_positions:
                if len(drone_data['trajectory']) > 1:
                    points = []
                    for lat, lon, alt in drone_data['trajectory']:
                        x = map_rect.x + int((lon - min_lon) / lon_range * map_rect.width)
                        y = map_rect.y + int((max_lat - lat) / lat_range * map_rect.height)
                        points.append((x, y))
                    
                    if len(points) > 1:
                        # Draw trajectory line
                        color = DesignSystem.COLORS['primary']
                        if drone_data['id'] == self.current_drone_id:
                            color = DesignSystem.COLORS['accent']
                        pygame.draw.lines(surface, color, False, points, 2)
            
            # Draw drone positions
            font = DesignSystem.get_font('small')
            for drone_data in drone_positions:
                x = map_rect.x + int((drone_data['lon'] - min_lon) / lon_range * map_rect.width)
                y = map_rect.y + int((max_lat - drone_data['lat']) / lat_range * map_rect.height)
                
                # Draw drone icon (circle)
                color = DesignSystem.COLORS['success']
                if drone_data['id'] == self.current_drone_id:
                    color = DesignSystem.COLORS['accent']
                    # Draw larger circle for selected drone
                    pygame.draw.circle(surface, color, (x, y), 12, 2)
                
                # Draw drone position
                pygame.draw.circle(surface, color, (x, y), 8)
                pygame.draw.circle(surface, DesignSystem.COLORS['bg'], (x, y), 4)
                
                # Draw drone name and info
                state = drone_data['state']
                info_text = f"{drone_data['name']}"
                if state:
                    info_text += f" | Alt: {drone_data['alt']:.1f}m"
                    if state.armed:
                        info_text += " | ARMED"
                    if state.battery > 0:
                        info_text += f" | Bat: {state.battery:.0f}%"
                
                text_surf = font.render(info_text, True, DesignSystem.COLORS['text'])
                text_rect = text_surf.get_rect()
                text_rect.centerx = x
                text_rect.y = y + 15
                
                # Draw background for text
                bg_rect = text_rect.inflate(10, 5)
                pygame.draw.rect(surface, DesignSystem.COLORS['bg'], bg_rect,
                               border_radius=DesignSystem.RADIUS['sm'])
                pygame.draw.rect(surface, color, bg_rect, 1,
                               border_radius=DesignSystem.RADIUS['sm'])
                surface.blit(text_surf, text_rect)
            
            # Draw legend
            legend_y = map_rect.y + 10
            legend_x = map_rect.x + 10
            legend_font = DesignSystem.get_font('small')
            
            legend_items = [
                ("Selected Drone", DesignSystem.COLORS['accent']),
                ("Other Drones", DesignSystem.COLORS['success']),
                ("Trajectory", DesignSystem.COLORS['primary'])
            ]
            
            for i, (label, color) in enumerate(legend_items):
                pygame.draw.circle(surface, color, (legend_x + 5, legend_y + i * 20 + 5), 5)
                legend_text = legend_font.render(label, True, DesignSystem.COLORS['text'])
                surface.blit(legend_text, (legend_x + 15, legend_y + i * 20))


class JSONEditor(UIComponent):
    """Advanced JSON editor with syntax highlighting, selection, copy/paste, and more."""
    
    def __init__(self, x: int, y: int, width: int, height: int, default_text: str = ""):
        super().__init__(x, y, width, height)
        self.text = default_text
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0.0
        self.scroll_y = 0
        self.scroll_x = 0
        self.cursor_pos = [0, 0]  # [line, col]
        self.selection_start = None  # [line, col] or None
        self.line_height = 18
        self.char_width = 8
        self.line_number_width = 50
        self.undo_stack = []  # History for undo
        self.undo_limit = 50
        self.clipboard = ""
        
    def _save_state(self):
        """Save current state for undo."""
        if len(self.undo_stack) == 0 or self.undo_stack[-1] != (self.text, self.cursor_pos):
            self.undo_stack.append((self.text, self.cursor_pos.copy()))
            if len(self.undo_stack) > self.undo_limit:
                self.undo_stack.pop(0)
    
    def _get_selected_text(self):
        """Get selected text."""
        if self.selection_start is None:
            return ""
        lines = self.text.split('\n')
        start_line, start_col = self.selection_start
        end_line, end_col = self.cursor_pos
        
        if start_line > end_line or (start_line == end_line and start_col > end_col):
            start_line, end_line = end_line, start_line
            start_col, end_col = end_col, start_col
        
        if start_line == end_line:
            return lines[start_line][start_col:end_col]
        else:
            result = [lines[start_line][start_col:]]
            for i in range(start_line + 1, end_line):
                result.append(lines[i])
            result.append(lines[end_line][:end_col])
            return '\n'.join(result)
    
    def _delete_selection(self):
        """Delete selected text."""
        if self.selection_start is None:
            return False
        
        lines = self.text.split('\n')
        start_line, start_col = self.selection_start
        end_line, end_col = self.cursor_pos
        
        if start_line > end_line or (start_line == end_line and start_col > end_col):
            start_line, end_line = end_line, start_line
            start_col, end_col = end_col, start_col
        
        if start_line == end_line:
            lines[start_line] = lines[start_line][:start_col] + lines[start_line][end_col:]
        else:
            lines[start_line] = lines[start_line][:start_col] + lines[end_line][end_col:]
            del lines[start_line + 1:end_line + 1]
        
        self.text = '\n'.join(lines)
        self.cursor_pos = [start_line, start_col]
        self.selection_start = None
        return True
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle JSON editor events with advanced editing capabilities."""
        if not self.visible or not self.enabled:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
                # Calculate cursor position from mouse click
                rel_x = event.pos[0] - (self.rect.x + self.line_number_width + 8) + self.scroll_x
                rel_y = event.pos[1] - (self.rect.y + 4) + self.scroll_y
                click_line = max(0, int(rel_y / self.line_height))
                lines = self.text.split('\n')
                click_line = min(click_line, len(lines) - 1)
                click_col = max(0, min(int(rel_x / self.char_width), len(lines[click_line])))
                self.cursor_pos = [click_line, click_col]
                if event.button == 1:  # Left click
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        if self.selection_start is None:
                            self.selection_start = self.cursor_pos.copy()
                    else:
                        self.selection_start = None
            else:
                self.active = False
            if event.button == 4:  # Scroll up
                self.scroll_y = max(0, self.scroll_y - 20)
            elif event.button == 5:  # Scroll down
                self.scroll_y += 20
            return self.active
        elif event.type == pygame.KEYDOWN and self.active:
            # Handle modifier keys
            mods = pygame.key.get_mods()
            ctrl = mods & (pygame.KMOD_CTRL | pygame.KMOD_META)
            shift = mods & pygame.KMOD_SHIFT
            
            # Save state before modification
            if event.key not in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, 
                                pygame.K_HOME, pygame.K_END, pygame.K_PAGEUP, pygame.K_PAGEDOWN):
                self._save_state()
            
            lines = self.text.split('\n')
            
            # Copy/Cut/Paste
            if ctrl and event.key == pygame.K_c:
                selected = self._get_selected_text()
                if selected:
                    self.clipboard = selected
                return True
            elif ctrl and event.key == pygame.K_x:
                selected = self._get_selected_text()
                if selected:
                    self.clipboard = selected
                    self._delete_selection()
                return True
            elif ctrl and event.key == pygame.K_v:
                if self.clipboard:
                    if self._delete_selection():
                        lines = self.text.split('\n')
                    clipboard_lines = self.clipboard.split('\n')
                    if len(clipboard_lines) == 1:
                        lines[self.cursor_pos[0]] = (lines[self.cursor_pos[0]][:self.cursor_pos[1]] + 
                                                     clipboard_lines[0] + 
                                                     lines[self.cursor_pos[0]][self.cursor_pos[1]:])
                        self.cursor_pos[1] += len(clipboard_lines[0])
                    else:
                        line = lines[self.cursor_pos[0]]
                        lines[self.cursor_pos[0]] = line[:self.cursor_pos[1]] + clipboard_lines[0]
                        for i, clip_line in enumerate(clipboard_lines[1:], 1):
                            lines.insert(self.cursor_pos[0] + i, clip_line)
                        lines[self.cursor_pos[0] + len(clipboard_lines) - 1] += line[self.cursor_pos[1]:]
                        self.cursor_pos[0] += len(clipboard_lines) - 1
                        self.cursor_pos[1] = len(clipboard_lines[-1])
                    self.text = '\n'.join(lines)
                    self.selection_start = None
                return True
            elif ctrl and event.key == pygame.K_a:  # Select all
                self.selection_start = [0, 0]
                lines = self.text.split('\n')
                self.cursor_pos = [len(lines) - 1, len(lines[-1])]
                return True
            elif ctrl and event.key == pygame.K_z:  # Undo
                if self.undo_stack:
                    self.text, self.cursor_pos = self.undo_stack.pop()
                    self.selection_start = None
                return True
            
            # Delete key
            if event.key == pygame.K_DELETE:
                if self._delete_selection():
                    return True
                lines = self.text.split('\n')
                if self.cursor_pos[0] < len(lines):
                    if self.cursor_pos[1] < len(lines[self.cursor_pos[0]]):
                        lines[self.cursor_pos[0]] = (lines[self.cursor_pos[0]][:self.cursor_pos[1]] + 
                                                    lines[self.cursor_pos[0]][self.cursor_pos[1] + 1:])
                    elif self.cursor_pos[0] < len(lines) - 1:
                        lines[self.cursor_pos[0]] += lines.pop(self.cursor_pos[0] + 1)
                self.text = '\n'.join(lines)
                self.selection_start = None
                return True
            
            # Navigation with selection
            if event.key == pygame.K_UP:
                if shift and self.selection_start is None:
                    self.selection_start = self.cursor_pos.copy()
                self.cursor_pos[0] = max(0, self.cursor_pos[0] - 1)
                self.cursor_pos[1] = min(self.cursor_pos[1], len(lines[self.cursor_pos[0]]))
                if not shift:
                    self.selection_start = None
                return True
            elif event.key == pygame.K_DOWN:
                if shift and self.selection_start is None:
                    self.selection_start = self.cursor_pos.copy()
                self.cursor_pos[0] = min(len(lines) - 1, self.cursor_pos[0] + 1)
                self.cursor_pos[1] = min(self.cursor_pos[1], len(lines[self.cursor_pos[0]]))
                if not shift:
                    self.selection_start = None
                return True
            elif event.key == pygame.K_LEFT:
                if shift and self.selection_start is None:
                    self.selection_start = self.cursor_pos.copy()
                if self.cursor_pos[1] > 0:
                    self.cursor_pos[1] -= 1
                elif self.cursor_pos[0] > 0:
                    self.cursor_pos[0] -= 1
                    self.cursor_pos[1] = len(lines[self.cursor_pos[0]])
                if not shift:
                    self.selection_start = None
                return True
            elif event.key == pygame.K_RIGHT:
                if shift and self.selection_start is None:
                    self.selection_start = self.cursor_pos.copy()
                if self.cursor_pos[0] < len(lines):
                    if self.cursor_pos[1] < len(lines[self.cursor_pos[0]]):
                        self.cursor_pos[1] += 1
                    elif self.cursor_pos[0] < len(lines) - 1:
                        self.cursor_pos[0] += 1
                        self.cursor_pos[1] = 0
                if not shift:
                    self.selection_start = None
                return True
            elif event.key == pygame.K_HOME:
                if shift and self.selection_start is None:
                    self.selection_start = self.cursor_pos.copy()
                self.cursor_pos[1] = 0
                if ctrl:
                    self.cursor_pos[0] = 0
                if not shift:
                    self.selection_start = None
                return True
            elif event.key == pygame.K_END:
                if shift and self.selection_start is None:
                    self.selection_start = self.cursor_pos.copy()
                self.cursor_pos[1] = len(lines[self.cursor_pos[0]])
                if ctrl:
                    self.cursor_pos[0] = len(lines) - 1
                    self.cursor_pos[1] = len(lines[-1])
                if not shift:
                    self.selection_start = None
                return True
            elif event.key == pygame.K_PAGEUP:
                self.scroll_y = max(0, self.scroll_y - self.rect.height // 2)
                return True
            elif event.key == pygame.K_PAGEDOWN:
                self.scroll_y += self.rect.height // 2
                return True
            
            # Text editing
            lines = self.text.split('\n')
            if event.key == pygame.K_BACKSPACE:
                if self._delete_selection():
                    return True
                if self.cursor_pos[0] < len(lines):
                    if self.cursor_pos[1] > 0:
                        lines[self.cursor_pos[0]] = (lines[self.cursor_pos[0]][:self.cursor_pos[1]-1] + 
                                                    lines[self.cursor_pos[0]][self.cursor_pos[1]:])
                        self.cursor_pos[1] -= 1
                    elif self.cursor_pos[0] > 0:
                        self.cursor_pos[1] = len(lines[self.cursor_pos[0]-1])
                        lines[self.cursor_pos[0]-1] += lines.pop(self.cursor_pos[0])
                        self.cursor_pos[0] -= 1
                    self.text = '\n'.join(lines)
                self.selection_start = None
                return True
            elif event.key == pygame.K_RETURN:
                if self._delete_selection():
                    lines = self.text.split('\n')
                if self.cursor_pos[0] < len(lines):
                    line = lines[self.cursor_pos[0]]
                    # Preserve indentation
                    indent = len(line) - len(line.lstrip())
                    lines[self.cursor_pos[0]] = line[:self.cursor_pos[1]]
                    lines.insert(self.cursor_pos[0] + 1, " " * indent + line[self.cursor_pos[1]:])
                    self.cursor_pos[0] += 1
                    self.cursor_pos[1] = indent
                    self.text = '\n'.join(lines)
                self.selection_start = None
                return True
            elif event.key == pygame.K_TAB:
                if self._delete_selection():
                    lines = self.text.split('\n')
                if self.cursor_pos[0] < len(lines):
                    lines[self.cursor_pos[0]] = (lines[self.cursor_pos[0]][:self.cursor_pos[1]] + 
                                                "    " + lines[self.cursor_pos[0]][self.cursor_pos[1]:])
                    self.cursor_pos[1] += 4
                    self.text = '\n'.join(lines)
                self.selection_start = None
                return True
            else:
                # Insert text
                if event.unicode and event.unicode.isprintable():
                    if self._delete_selection():
                        lines = self.text.split('\n')
                    if self.cursor_pos[0] < len(lines):
                        line = lines[self.cursor_pos[0]]
                        lines[self.cursor_pos[0]] = (line[:self.cursor_pos[1]] + event.unicode + 
                                                    line[self.cursor_pos[1]:])
                        self.cursor_pos[1] += 1
                        self.text = '\n'.join(lines)
                    self.selection_start = None
                    return True
            return True
        return False
                    
    def update(self, dt: float):
        """Update cursor blink."""
        self.cursor_timer += dt
        if self.cursor_timer > 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0.0
            
    def format_json(self):
        """Format JSON text."""
        try:
            obj = json.loads(self.text)
            self.text = json.dumps(obj, indent=4)
            lines = self.text.split('\n')
            self.cursor_pos = [0, 0]
        except:
            pass
            
    def draw(self, surface: pygame.Surface):
        """Draw JSON editor with console style."""
        if not self.visible:
            return
        
        # Draw background
        bg_color = DesignSystem.COLORS['surface_active'] if self.active else DesignSystem.COLORS['surface']
        pygame.draw.rect(surface, bg_color, self.rect,
                       border_radius=DesignSystem.RADIUS['md'])
        border_color = DesignSystem.COLORS['primary'] if self.active else DesignSystem.COLORS['border']
        pygame.draw.rect(surface, border_color, self.rect,
                       width=2 if self.active else 1, border_radius=DesignSystem.RADIUS['md'])
        
        # Draw line numbers
        line_num_rect = pygame.Rect(self.rect.x + 4, self.rect.y + 4, 
                                   self.line_number_width, self.rect.height - 8)
        pygame.draw.rect(surface, DesignSystem.COLORS['bg'], line_num_rect,
                       border_radius=DesignSystem.RADIUS['sm'])
        
        # Clip to text area
        text_rect = pygame.Rect(
            self.rect.x + self.line_number_width + 8,
            self.rect.y + 4,
            self.rect.width - self.line_number_width - 12,
            self.rect.height - 8
        )
        old_clip = surface.get_clip()
        surface.set_clip(text_rect)
        
        font = DesignSystem.get_font('console')
        # Ensure text is always a string
        text_str = str(self.text) if self.text is not None else ""
        lines = text_str.split('\n') if text_str else [""]
        y_offset = text_rect.y - self.scroll_y
        
        # Draw selection highlight
        if self.selection_start is not None:
            start_line, start_col = self.selection_start
            end_line, end_col = self.cursor_pos
            
            if start_line > end_line or (start_line == end_line and start_col > end_col):
                start_line, end_line = end_line, start_line
                start_col, end_col = end_col, start_col
            
            for line_idx in range(start_line, end_line + 1):
                if 0 <= line_idx < len(lines):
                    line_y = y_offset + line_idx * self.line_height
                    if line_y + self.line_height < text_rect.y or line_y > text_rect.bottom:
                        continue
                    
                    if line_idx == start_line == end_line:
                        sel_x1 = text_rect.x + start_col * self.char_width
                        sel_x2 = text_rect.x + end_col * self.char_width
                    elif line_idx == start_line:
                        sel_x1 = text_rect.x + start_col * self.char_width
                        sel_x2 = text_rect.right
                    elif line_idx == end_line:
                        sel_x1 = text_rect.x
                        sel_x2 = text_rect.x + end_col * self.char_width
                    else:
                        sel_x1 = text_rect.x
                        sel_x2 = text_rect.right
                    
                    sel_rect = pygame.Rect(sel_x1, line_y, sel_x2 - sel_x1, self.line_height)
                    pygame.draw.rect(surface, DesignSystem.COLORS['primary'], sel_rect, 
                                   border_radius=2)
        
        for i, line in enumerate(lines):
            line_y = y_offset + i * self.line_height
            if line_y + self.line_height < text_rect.y:
                continue
            if line_y > text_rect.bottom:
                break
                
            # Draw line number
            line_num_surf = font.render(str(i + 1), True, DesignSystem.COLORS['text_tertiary'])
            surface.blit(line_num_surf, (self.rect.x + 8, line_y))
            
            # Draw line with syntax highlighting
            x_pos = text_rect.x - self.scroll_x
            for j, char in enumerate(line):
                char_x = x_pos + j * self.char_width
                if char_x + self.char_width < text_rect.x:
                    continue
                if char_x > text_rect.right:
                    break
                    
                # Enhanced syntax highlighting
                if char in ['{', '}', '[', ']']:
                    color = DesignSystem.COLORS['primary']
                elif char in [':', ',']:
                    color = DesignSystem.COLORS['text_secondary']
                elif char == '"':
                    color = DesignSystem.COLORS['success']
                elif char.isdigit() or char == '.' or char == '-':
                    color = DesignSystem.COLORS['warning']
                else:
                    color = DesignSystem.COLORS['text']
                    
                char_surf = font.render(char, True, color)
                surface.blit(char_surf, (char_x, line_y))
        
        # Draw cursor
        if self.active and self.cursor_visible:
            cursor_y = text_rect.y - self.scroll_y + self.cursor_pos[0] * self.line_height
            if text_rect.y <= cursor_y <= text_rect.bottom:
                lines = self.text.split('\n')
                cursor_x = text_rect.x - self.scroll_x + self.cursor_pos[1] * self.char_width
                if text_rect.x <= cursor_x <= text_rect.right:
                    pygame.draw.line(surface, DesignSystem.COLORS['text'],
                                       (cursor_x, cursor_y),
                                       (cursor_x, cursor_y + self.line_height), 2)
        
        surface.set_clip(old_clip)


class TopicList(Items):
    """Topic list component (specialized Items)."""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height)

