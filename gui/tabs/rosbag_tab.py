"""ROS bag playback tab implementation with optimized rendering and professional layout."""
import pygame
import os
from typing import Dict, Any, Optional

from .base_tab import BaseTab
from ..components import Label, Card, Button, TextInput
from ..design.design_system import DesignSystem
from ..renderers.ui_renderer import get_renderer
from ..layout.layout_manager import LayoutManager

try:
    from rosclient import RosbagClient, HAS_ROSBAG
except ImportError:
    HAS_ROSBAG = False
    RosbagClient = None


class RosbagTab(BaseTab):
    """ROS bag file playback tab."""
    
    def __init__(self, screen: pygame.Surface, screen_width: int, screen_height: int,
                 components: Dict[str, Any]):
        """Initialize rosbag tab.
        
        Args:
            screen: Pygame surface to draw on
            screen_width: Screen width
            screen_height: Screen height
            components: Dictionary of UI components
        """
        super().__init__(screen, screen_width, screen_height)
        self.components = components
        self.renderer = get_renderer()
        self.layout = LayoutManager(screen_width, screen_height)
        self.rosbag_client: Optional[RosbagClient] = None
        self.bag_path = ""
        self.playback_speed = 1.0
        
    def draw(self, app_state: Dict[str, Any]):
        """Draw rosbag tab with professional layout management."""
        # Get content area using layout manager
        content_area = self.layout.get_content_area()
        
        # Calculate header area
        header_rect, header_height = self.layout.calculate_header_area(
            content_area, "ROS Bag Playback", "Playback and analyze ROS bag files"
        )
        
        # Draw title
        title_label = Label(header_rect.x, header_rect.y, "ROS Bag Playback", 'title',
                           DesignSystem.COLORS['text'])
        title_label.draw(self.screen)
        
        # Draw subtitle if space available
        if header_height > 40:
            subtitle_label = Label(header_rect.x, header_rect.y + 35,
                                 "Playback and analyze ROS bag files", 'small',
                                 DesignSystem.COLORS['text_tertiary'])
            subtitle_label.draw(self.screen)
        
        # Calculate main component area
        component_area = self.layout.calculate_component_area(content_area, header_height, min_height=400)
        
        if not HAS_ROSBAG:
            # Error display
            error_card = Card(component_area.x, component_area.y, 
                            component_area.width, 200, "ROS Bag Not Available")
            error_card.draw(self.screen)
            
            error_content = error_card.get_content_area()
            error_center_x = error_content.centerx
            
            error_label = Label(error_center_x, error_content.centery - 30,
                              "rosbag module not available",
                              'label', DesignSystem.COLORS['error'])
            error_label.align = 'center'
            error_label.draw(self.screen)
            
            install_label = Label(error_center_x, error_content.centery + 10,
                                "Install with: pip install rospy",
                                'small', DesignSystem.COLORS['text_tertiary'])
            install_label.align = 'center'
            install_label.draw(self.screen)
            return
        
        # File selection card - positioned at top of component area
        file_card_height = 100
        file_card = Card(component_area.x, component_area.y, 
                        component_area.width, file_card_height, "Bag File")
        file_card.draw(self.screen)
        
        file_content = self.layout.calculate_inner_content_area(
            file_card.rect, has_title=True, padding='md'
        )
        
        # File path input and browse button - horizontal layout
        input_y = file_content.y + DesignSystem.SPACING['sm']
        input_height = 36
        
        # Browse button (auto-sized)
        browse_btn = self.components.get('browse_bag_btn')
        if not browse_btn:
            browse_btn = Button(0, 0, None, input_height, "Browse", self.browse_bag_file)
            self.components['browse_bag_btn'] = browse_btn
        
        browse_btn.rect.x = file_content.right - browse_btn.rect.width - DesignSystem.SPACING['sm']
        browse_btn.rect.y = input_y
        browse_btn.draw(self.screen)
        
        # File path input (fills remaining space)
        bag_path_input = self.components.get('bag_path_input')
        if not bag_path_input:
            bag_path_input = TextInput(0, 0, 0, input_height, "")
            self.components['bag_path_input'] = bag_path_input
        
        input_width = browse_btn.rect.x - file_content.x - DesignSystem.SPACING['md']
        bag_path_input.rect.x = file_content.x + DesignSystem.SPACING['sm']
        bag_path_input.rect.y = input_y
        bag_path_input.rect.width = max(200, input_width)
        bag_path_input.text = self.bag_path
        bag_path_input.draw(self.screen)
        
        # Calculate next card position
        next_card_y = file_card.rect.bottom + DesignSystem.SPACING['md']
        
        # Playback controls card - positioned below file card
        controls_card_height = 240
        controls_card = Card(component_area.x, next_card_y,
                           component_area.width, controls_card_height, "Playback Controls")
        controls_card.draw(self.screen)
        
        controls_content = self.layout.calculate_inner_content_area(
            controls_card.rect, has_title=True, padding='md'
        )
        controls_y = controls_content.y + DesignSystem.SPACING['sm']
        
        # Play/Pause/Stop buttons - horizontal layout with auto-sizing
        btn_height = 40
        btn_gap = DesignSystem.SPACING['md']
        btn_x = controls_content.x + DesignSystem.SPACING['sm']
        
        play_btn = self.components.get('play_btn')
        if not play_btn:
            play_btn = Button(0, 0, None, btn_height, "Play", self.play_bag)
            self.components['play_btn'] = play_btn
        play_btn.rect.x = btn_x
        play_btn.rect.y = controls_y
        play_btn.draw(self.screen)
        
        pause_btn = self.components.get('pause_btn')
        if not pause_btn:
            pause_btn = Button(0, 0, None, btn_height, "Pause", self.pause_bag)
            self.components['pause_btn'] = pause_btn
        pause_btn.rect.x = play_btn.rect.right + btn_gap
        pause_btn.rect.y = controls_y
        pause_btn.draw(self.screen)
        
        stop_btn = self.components.get('stop_btn')
        if not stop_btn:
            stop_btn = Button(0, 0, None, btn_height, "Stop", self.stop_bag)
            self.components['stop_btn'] = stop_btn
            stop_btn.color = DesignSystem.COLORS['error']
        stop_btn.rect.x = pause_btn.rect.right + btn_gap
        stop_btn.rect.y = controls_y
        stop_btn.draw(self.screen)
        
        # Speed control - positioned below buttons
        speed_y = controls_y + btn_height + DesignSystem.SPACING['lg']
        speed_label = Label(btn_x, speed_y, "Speed:", 'label', DesignSystem.COLORS['text'])
        speed_label.draw(self.screen)
        
        speed_input = self.components.get('speed_input')
        if not speed_input:
            speed_input = TextInput(0, 0, 80, 36, "1.0")
            self.components['speed_input'] = speed_input
        speed_input.rect.x = btn_x + 70
        speed_input.rect.y = speed_y - 2
        speed_input.text = f"{self.playback_speed:.1f}"
        speed_input.draw(self.screen)
        
        # Progress bar - positioned below speed control
        progress_y = speed_y + 45
        progress_label = Label(btn_x, progress_y, "Progress:", 'label', DesignSystem.COLORS['text'])
        progress_label.draw(self.screen)
        
        progress_bar_x = btn_x
        progress_bar_y = progress_y + 28
        progress_bar_width = controls_content.width - DesignSystem.SPACING['sm'] * 2
        progress_bar_height = 24
        
        # Draw progress bar background - modern flat style
        progress_rect = pygame.Rect(progress_bar_x, progress_bar_y, progress_bar_width, progress_bar_height)
        self.renderer.draw_rect(self.screen, progress_rect,
                              DesignSystem.COLORS['surface'],
                              border_radius=0)  # No rounded corners
        # Subtle divider line
        divider_color = tuple(max(0, c - 15) for c in DesignSystem.COLORS['surface'])
        pygame.draw.line(self.screen, divider_color,
                       (progress_rect.x, progress_rect.bottom - 1),
                       (progress_rect.right, progress_rect.bottom - 1), 1)
        
        # Draw progress fill - modern flat style
        if self.rosbag_client:
            progress = self.rosbag_client.get_progress()
            fill_width = int(progress_bar_width * progress)
            if fill_width > 0:
                fill_rect = pygame.Rect(progress_bar_x, progress_bar_y, fill_width, progress_bar_height)
                self.renderer.draw_rect(self.screen, fill_rect,
                                      DesignSystem.COLORS['playback_active'],
                                      border_radius=0)  # No rounded corners
        
        # Draw time info - below progress bar
        time_y = progress_bar_y + progress_bar_height + DesignSystem.SPACING['sm']
        if self.rosbag_client:
            current_time = self.rosbag_client.get_current_time()
            duration = self.rosbag_client.get_duration()
            time_text = f"{current_time:.1f}s / {duration:.1f}s"
        else:
            time_text = "0.0s / 0.0s"
        
        time_label = Label(btn_x, time_y, time_text, 'small', DesignSystem.COLORS['text_secondary'])
        time_label.draw(self.screen)
        
        # Status display card - positioned below controls card
        status_card_y = controls_card.rect.bottom + DesignSystem.SPACING['md']
        status_card_height = 140
        status_card = Card(component_area.x, status_card_y,
                          component_area.width, status_card_height, "Status")
        status_card.draw(self.screen)
        
        status_content = self.layout.calculate_inner_content_area(
            status_card.rect, has_title=True, padding='md'
        )
        status_y = status_content.y + DesignSystem.SPACING['sm']
        status_x = status_content.x + DesignSystem.SPACING['sm']
        
        # Status text
        if self.rosbag_client and self.rosbag_client.is_connected():
            status_text = "Connected"
            status_color = DesignSystem.COLORS['success']
            if hasattr(self.rosbag_client, '_playback_thread') and self.rosbag_client._playback_thread and self.rosbag_client._playback_thread.is_alive():
                if self.rosbag_client._playback_paused.is_set():
                    status_text = "Paused"
                    status_color = DesignSystem.COLORS['playback_paused']
                else:
                    status_text = f"Playing ({self.playback_speed:.1f}x)"
                    status_color = DesignSystem.COLORS['playback_active']
        else:
            status_text = "Not Connected"
            status_color = DesignSystem.COLORS['text_tertiary']
        
        status_label = Label(status_x, status_y,
                           f"Status: {status_text}", 'label', status_color)
        status_label.draw(self.screen)
        
        # Bag info - positioned below status
        if self.rosbag_client:
            bag_path = self.rosbag_client.bag_path
            bag_name = bag_path.name if bag_path else "No file"
            bag_label = Label(status_x, status_y + 32,
                            f"File: {bag_name}", 'small', DesignSystem.COLORS['text_secondary'])
            bag_label.draw(self.screen)
            
            topics = self.rosbag_client.get_topics()
            topics_label = Label(status_x, status_y + 52,
                               f"Topics: {len(topics)}", 'small', DesignSystem.COLORS['text_secondary'])
            topics_label.draw(self.screen)
    
    def browse_bag_file(self):
        """Open file dialog to select bag file."""
        # Simple file selection using tkinter
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()  # Hide main window
            
            file_path = filedialog.askopenfilename(
                title="Select ROS Bag File",
                filetypes=[("ROS Bag files", "*.bag"), ("All files", "*.*")]
            )
            
            root.destroy()
            
            if file_path:
                self.bag_path = file_path
                self.components['bag_path_input'].text = file_path
                self.load_bag_file()
        except ImportError:
            # Fallback: manual path entry
            pass
        except Exception as e:
            print(f"Error opening file dialog: {e}")
    
    def load_bag_file(self):
        """Load the selected bag file."""
        if not self.bag_path or not os.path.exists(self.bag_path):
            return
        
        try:
            if self.rosbag_client:
                self.rosbag_client.terminate()
            
            self.rosbag_client = RosbagClient(self.bag_path)
            self.rosbag_client.connect_async()
            
            # Subscribe to common topics
            if self.rosbag_client.is_connected():
                # Subscribe to topics that might be in the bag
                topics = self.rosbag_client.get_topics()
                for topic in topics:
                    if 'image' in topic.lower() or 'camera' in topic.lower():
                        self.rosbag_client.subscribe(topic, lambda msg: None)
                    elif 'point' in topic.lower() and 'cloud' in topic.lower():
                        self.rosbag_client.subscribe(topic, lambda msg: None)
        except Exception as e:
            print(f"Error loading bag file: {e}")
    
    def play_bag(self):
        """Start or resume playback."""
        if not self.rosbag_client or not self.rosbag_client.is_connected():
            if self.bag_path:
                self.load_bag_file()
            else:
                return
        
        try:
            speed = float(self.components['speed_input'].text)
            self.playback_speed = speed
            self.rosbag_client.set_playback_speed(speed)
            
            if self.rosbag_client._playback_thread and self.rosbag_client._playback_thread.is_alive():
                self.rosbag_client.resume_playback()
            else:
                self.rosbag_client.start_playback(speed)
        except ValueError:
            pass
        except Exception as e:
            print(f"Error playing bag: {e}")
    
    def pause_bag(self):
        """Pause playback."""
        if self.rosbag_client:
            self.rosbag_client.pause_playback()
    
    def stop_bag(self):
        """Stop playback."""
        if self.rosbag_client:
            self.rosbag_client.stop_playback()
    
    def handle_event(self, event: pygame.event.Event, app_state: Dict[str, Any]) -> bool:
        """Handle rosbag tab events."""
        # Handle component events
        for component_name in ['bag_path_input', 'browse_bag_btn', 'play_btn', 
                               'pause_btn', 'stop_btn', 'speed_input']:
            component = self.components.get(component_name)
            if component and component.handle_event(event):
                if component_name == 'bag_path_input':
                    self.bag_path = component.text
                elif component_name == 'speed_input':
                    try:
                        self.playback_speed = float(component.text)
                    except ValueError:
                        pass
                return True
        
        return False
    
    def update(self, dt: float, app_state: Dict[str, Any]):
        """Update rosbag tab."""
        # Update bag path from input
        bag_path_input = self.components.get('bag_path_input')
        if bag_path_input:
            if bag_path_input.text != self.bag_path:
                self.bag_path = bag_path_input.text
                if self.bag_path and os.path.exists(self.bag_path):
                    self.load_bag_file()
        
        # Update app state with rosbag client
        if self.rosbag_client and self.rosbag_client.is_connected():
            app_state['rosbag_client'] = self.rosbag_client
            # Update image from bag (convert to pygame surface if needed)
            try:
                import cv2
                import numpy as np
                image_data = self.rosbag_client.get_latest_image()
                if image_data:
                    frame, timestamp = image_data
                    if frame is not None:
                        # Convert numpy array to pygame surface
                        max_width, max_height = 800, 600
                        h, w = frame.shape[:2]
                        scale = min(max_width / w, max_height / h)
                        new_w, new_h = int(w * scale), int(h * scale)
                        frame_resized = cv2.resize(frame, (new_w, new_h))
                        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
                        frame_rotated = np.rot90(frame_rgb, k=3)
                        frame_flipped = np.fliplr(frame_rotated)
                        pygame_image = pygame.surfarray.make_surface(frame_flipped)
                        app_state['current_image'] = pygame_image
            except Exception as e:
                pass
            
            # Update point cloud from bag
            try:
                pointcloud_data = self.rosbag_client.get_latest_point_cloud()
                if pointcloud_data:
                    points, timestamp = pointcloud_data
                    if points is not None and len(points) > 0:
                        # Update point cloud cache
                        app_state['rosbag_pointcloud'] = points
                        # Also update the main point cloud if no active drone connection
                        if not app_state.get('current_drone_id') or not any(
                            drone.get('is_connected', False) 
                            for drone in app_state.get('drones', {}).values()
                        ):
                            # Use rosbag point cloud if no active connection
                            app_state['pc_cache'] = points
            except Exception as e:
                pass

