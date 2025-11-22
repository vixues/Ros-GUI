"""Base class for tab implementations."""
import pygame
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from ..components import Label
from ..design.design_system import DesignSystem


class BaseTab(ABC):
    """Base class for all tabs."""
    
    def __init__(self, screen: pygame.Surface, screen_width: int, screen_height: int):
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.tab_height = 45
        
    @abstractmethod
    def draw(self, app_state: Dict[str, Any]):
        """Draw the tab content.
        
        Args:
            app_state: Dictionary containing application state (drones, current_drone_id, etc.)
        """
        pass
    
    @abstractmethod
    def handle_event(self, event: pygame.event.Event, app_state: Dict[str, Any]) -> bool:
        """Handle events for this tab.
        
        Args:
            event: Pygame event
            app_state: Dictionary containing application state
            
        Returns:
            True if event was handled, False otherwise
        """
        return False
    
    @abstractmethod
    def update(self, dt: float, app_state: Dict[str, Any]):
        """Update tab state.
        
        Args:
            dt: Delta time since last update
            app_state: Dictionary containing application state
        """
        pass

