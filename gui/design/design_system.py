"""Industrial fighter cockpit design system with console typography and DPI support."""
import pygame
import os
import sys


class DesignSystem:
    """Industrial fighter cockpit design system with console typography and DPI awareness."""
    
    # DPI scaling factor (will be calculated based on system DPI)
    _dpi_scale = 1.0
    _base_dpi = 96.0  # Standard DPI
    
    @staticmethod
    def init_dpi():
        """Initialize DPI scaling based on system settings."""
        try:
            # Windows DPI awareness
            if sys.platform == 'win32':
                try:
                    import ctypes
                    # Set DPI awareness
                    ctypes.windll.shcore.SetProcessDpiAwareness(1)  # PROCESS_PER_MONITOR_DPI_AWARE
                    # Get DPI
                    hdc = ctypes.windll.user32.GetDC(0)
                    dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
                    ctypes.windll.user32.ReleaseDC(0, hdc)
                    if dpi > 0:
                        DesignSystem._dpi_scale = dpi / DesignSystem._base_dpi
                except:
                    pass
            # Linux DPI (X11)
            elif sys.platform.startswith('linux'):
                try:
                    dpi_str = os.popen('xrdb -query | grep Xft.dpi').read()
                    if dpi_str:
                        dpi = float(dpi_str.split(':')[1].strip())
                        DesignSystem._dpi_scale = dpi / DesignSystem._base_dpi
                except:
                    pass
            # macOS
            elif sys.platform == 'darwin':
                try:
                    # macOS typically uses 72 DPI as base, but Retina displays are 2x
                    # Check for Retina display
                    import subprocess
                    result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], 
                                          capture_output=True, text=True)
                    if 'Retina' in result.stdout:
                        DesignSystem._dpi_scale = 0.8
                except:
                    pass
        except:
            # Fallback to 1.0 if detection fails
            DesignSystem._dpi_scale = 1.0
    
    @staticmethod
    def get_dpi_scale() -> float:
        """Get current DPI scaling factor."""
        return DesignSystem._dpi_scale
    
    @staticmethod
    def scale(value: float) -> float:
        """Scale a value by DPI factor."""
        return value * DesignSystem._dpi_scale
    
    @staticmethod
    def scale_int(value: float) -> int:
        """Scale a value by DPI factor and return as integer."""
        return int(value * DesignSystem._dpi_scale)
    
    # Enhanced Color Palette - Modern dark theme with better contrast
    COLORS = {
        # Background layers - Deep dark tones with subtle blue tint
        'bg': (8, 12, 18),              # Deep dark blue-black
        'bg_secondary': (12, 16, 22),   # Slightly lighter
        'bg_panel': (16, 20, 28),       # Panel background with blue tint
        
        # Surface layers - Dark grays with blue tint
        'surface': (24, 28, 36),        # Main surface
        'surface_light': (32, 36, 44),  # Light surface
        'surface_hover': (40, 44, 52),  # Hover state
        'surface_active': (48, 52, 60), # Active state
        
        # Primary colors - Cyan/Blue accent (modern tech look)
        'primary': (64, 224, 255),      # Bright cyan
        'primary_dark': (32, 192, 224), # Darker cyan
        'primary_light': (128, 240, 255), # Light cyan
        'primary_glow': (64, 224, 255, 60), # Glow effect
        
        # Status colors - Enhanced visibility
        'success': (76, 255, 76),      # Bright green (operational)
        'success_glow': (76, 255, 76, 40),
        'success_dark': (0, 200, 0),    # Darker green
        'warning': (255, 200, 0),       # Amber (caution)
        'warning_glow': (255, 200, 0, 40),
        'warning_dark': (200, 150, 0),  # Darker amber
        'error': (255, 64, 64),         # Bright red (critical)
        'error_glow': (255, 64, 64, 40),
        'error_dark': (200, 0, 0),      # Darker red
        
        # Text colors - High contrast white/gray scale
        'text': (255, 255, 255),        # Pure white
        'text_secondary': (200, 200, 210), # Light gray with blue tint
        'text_tertiary': (140, 144, 152),   # Medium gray
        'text_console': (76, 255, 76),      # Green console (better visibility)
        'text_label': (220, 224, 232),      # Light gray label
        'text_disabled': (100, 104, 112),   # Disabled text
        
        # Border and accent - Enhanced visibility
        'border': (64, 72, 88),         # Medium gray-blue border
        'border_light': (96, 104, 120), # Light gray-blue border
        'border_glow': (64, 224, 255, 80), # Cyan glowing border
        'accent': (128, 192, 255),       # Blue accent
        'accent_glow': (128, 192, 255, 40),
        
        # Shadow and overlay
        'shadow': (0, 0, 0, 220),       # Strong black shadow
        'shadow_light': (0, 0, 0, 140),  # Light black shadow
        'overlay': (0, 0, 0, 180),      # Black overlay
        
        # Special colors for rosbag playback
        'playback_active': (64, 224, 255),  # Cyan for active playback
        'playback_paused': (255, 200, 0),   # Amber for paused
        'playback_stopped': (140, 144, 152), # Gray for stopped
    }
    
    # Typography - Console monospace style (will be scaled by DPI)
    FONTS = {
        'console': None,  # Will be initialized with monospace
        'label': None,     # Medium size
        'title': None,     # Large size
        'small': None,     # Small size
    }
    
    # Base font sizes (will be scaled by DPI)
    FONT_SIZES = {
        'console': 14,
        'label': 16,
        'title': 24,
        'small': 12,
    }
    
    # Spacing system (will be scaled by DPI)
    SPACING_BASE = {
        'xs': 4,
        'sm': 8,
        'md': 12,
        'lg': 16,
        'xl': 24,
        'xxl': 32,
    }
    
    # Computed spacing (DPI-scaled)
    SPACING = None
    
    # Border radius (will be scaled by DPI)
    RADIUS_BASE = {
        'none': 0,
        'sm': 4,
        'md': 6,
        'lg': 8,
        'xl': 12,
    }
    
    # Computed radius (DPI-scaled)
    RADIUS = None
    
    # Shadow offsets (will be scaled by DPI)
    SHADOW_OFFSET_BASE = 3
    SHADOW_OFFSET = None
    
    @staticmethod
    def init_fonts():
        """Initialize fonts with console monospace style, scaled by DPI."""
        # Initialize DPI first
        DesignSystem.init_dpi()
        
        # Calculate scaled spacing and radius
        DesignSystem.SPACING = {
            k: DesignSystem.scale_int(v) 
            for k, v in DesignSystem.SPACING_BASE.items()
        }
        DesignSystem.RADIUS = {
            k: DesignSystem.scale_int(v) 
            for k, v in DesignSystem.RADIUS_BASE.items()
        }
        DesignSystem.SHADOW_OFFSET = DesignSystem.scale_int(DesignSystem.SHADOW_OFFSET_BASE)
        
        # Try to load monospace font, fallback to default
        try:
            # Try common monospace fonts
            font_paths = [
                'consola.ttf', 'consolas.ttf', 'Courier New.ttf',
                'DejaVuSansMono.ttf', 'LiberationMono-Regular.ttf'
            ]
            font_found_path = None
            for path in font_paths:
                try:
                    test_font = pygame.font.Font(path, 14)
                    font_found_path = path
                    break
                except:
                    continue
            
            # Initialize fonts with DPI-scaled sizes
            if font_found_path:
                DesignSystem.FONTS['console'] = pygame.font.Font(
                    font_found_path, 
                    DesignSystem.scale_int(DesignSystem.FONT_SIZES['console'])
                )
                DesignSystem.FONTS['label'] = pygame.font.Font(
                    font_found_path,
                    DesignSystem.scale_int(DesignSystem.FONT_SIZES['label'])
                )
                DesignSystem.FONTS['title'] = pygame.font.Font(
                    font_found_path,
                    DesignSystem.scale_int(DesignSystem.FONT_SIZES['title'])
                )
                DesignSystem.FONTS['small'] = pygame.font.Font(
                    font_found_path,
                    DesignSystem.scale_int(DesignSystem.FONT_SIZES['small'])
                )
            else:
                # Fallback to default monospace
                default_font = pygame.font.get_default_font()
                DesignSystem.FONTS['console'] = pygame.font.Font(
                    default_font, 
                    DesignSystem.scale_int(DesignSystem.FONT_SIZES['console'])
                )
                DesignSystem.FONTS['label'] = pygame.font.Font(
                    default_font,
                    DesignSystem.scale_int(DesignSystem.FONT_SIZES['label'])
                )
                DesignSystem.FONTS['title'] = pygame.font.Font(
                    default_font,
                    DesignSystem.scale_int(DesignSystem.FONT_SIZES['title'])
                )
                DesignSystem.FONTS['small'] = pygame.font.Font(
                    default_font,
                    DesignSystem.scale_int(DesignSystem.FONT_SIZES['small'])
                )
        except:
            # Ultimate fallback
            DesignSystem.FONTS['console'] = pygame.font.Font(
                None, 
                DesignSystem.scale_int(DesignSystem.FONT_SIZES['console'])
            )
            DesignSystem.FONTS['label'] = pygame.font.Font(
                None,
                DesignSystem.scale_int(DesignSystem.FONT_SIZES['label'])
            )
            DesignSystem.FONTS['title'] = pygame.font.Font(
                None,
                DesignSystem.scale_int(DesignSystem.FONT_SIZES['title'])
            )
            DesignSystem.FONTS['small'] = pygame.font.Font(
                None,
                DesignSystem.scale_int(DesignSystem.FONT_SIZES['small'])
            )
    
    @staticmethod
    def get_font(size='label'):
        """Get font by size name."""
        return DesignSystem.FONTS.get(size, DesignSystem.FONTS['label'])

