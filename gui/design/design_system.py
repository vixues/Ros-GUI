"""Industrial fighter cockpit design system with console typography."""
import pygame


class DesignSystem:
    """Industrial fighter cockpit design system with console typography."""
    
    # Black Color Palette - Industrial black theme
    COLORS = {
        # Background layers - Pure black tones
        'bg': (5, 5, 5),              # Pure black
        'bg_secondary': (10, 10, 10),  # Slightly lighter black
        'bg_panel': (15, 15, 15),      # Panel background
        
        # Surface layers - Dark grays
        'surface': (20, 20, 20),       # Main surface
        'surface_light': (30, 30, 30), # Light surface
        'surface_hover': (40, 40, 40),  # Hover state
        'surface_active': (50, 50, 50), # Active state
        
        # Primary colors - White/Gray (minimal, industrial)
        'primary': (255, 255, 255),     # Pure white
        'primary_dark': (200, 200, 200), # Dark gray
        'primary_light': (255, 255, 255), # White
        'primary_glow': (255, 255, 255, 60), # Glow effect
        
        # Status colors - Subtle, high contrast
        'success': (0, 255, 0),         # Green (operational)
        'success_glow': (0, 255, 0, 40),
        'warning': (255, 200, 0),       # Amber (caution)
        'warning_glow': (255, 200, 0, 40),
        'error': (255, 0, 0),            # Red (critical)
        'error_glow': (255, 0, 0, 40),
        
        # Text colors - White/Gray scale
        'text': (255, 255, 255),        # Pure white
        'text_secondary': (180, 180, 180), # Light gray
        'text_tertiary': (120, 120, 120),   # Medium gray
        'text_console': (0, 255, 0),        # Green console
        'text_label': (200, 200, 200),      # Light gray label
        
        # Border and accent - Gray scale
        'border': (60, 60, 60),         # Medium gray border
        'border_light': (100, 100, 100), # Light gray border
        'border_glow': (255, 255, 255, 80), # White glowing border
        'accent': (150, 150, 150),       # Gray accent
        'accent_glow': (150, 150, 150, 40),
        
        # Shadow and overlay
        'shadow': (0, 0, 0, 200),       # Strong black shadow
        'shadow_light': (0, 0, 0, 120),  # Light black shadow
        'overlay': (0, 0, 0, 150),      # Black overlay
    }
    
    # Typography - Console monospace style
    FONTS = {
        'console': None,  # Will be initialized with monospace
        'label': None,     # Medium size
        'title': None,     # Large size
        'small': None,     # Small size
    }
    
    # Spacing system
    SPACING = {
        'xs': 4,
        'sm': 8,
        'md': 12,
        'lg': 16,
        'xl': 24,
        'xxl': 32,
    }
    
    # Border radius
    RADIUS = {
        'none': 0,
        'sm': 4,
        'md': 6,
        'lg': 8,
        'xl': 12,
    }
    
    # Shadow offsets
    SHADOW_OFFSET = 3
    
    @staticmethod
    def init_fonts():
        """Initialize fonts with console monospace style."""
        # Try to load monospace font, fallback to default
        try:
            # Try common monospace fonts
            font_paths = [
                'consola.ttf', 'consolas.ttf', 'Courier New.ttf',
                'DejaVuSansMono.ttf', 'LiberationMono-Regular.ttf'
            ]
            font_found = None
            for path in font_paths:
                try:
                    font_found = pygame.font.Font(path, 14)
                    break
                except:
                    continue
            
            if font_found:
                DesignSystem.FONTS['console'] = font_found
                DesignSystem.FONTS['label'] = pygame.font.Font(font_paths[0] if font_found else None, 16)
                DesignSystem.FONTS['title'] = pygame.font.Font(font_paths[0] if font_found else None, 24)
                DesignSystem.FONTS['small'] = pygame.font.Font(font_paths[0] if font_found else None, 12)
            else:
                # Fallback to default monospace
                DesignSystem.FONTS['console'] = pygame.font.Font(pygame.font.get_default_font(), 14)
                DesignSystem.FONTS['label'] = pygame.font.Font(pygame.font.get_default_font(), 16)
                DesignSystem.FONTS['title'] = pygame.font.Font(pygame.font.get_default_font(), 24)
                DesignSystem.FONTS['small'] = pygame.font.Font(pygame.font.get_default_font(), 12)
        except:
            # Ultimate fallback
            DesignSystem.FONTS['console'] = pygame.font.Font(None, 14)
            DesignSystem.FONTS['label'] = pygame.font.Font(None, 16)
            DesignSystem.FONTS['title'] = pygame.font.Font(None, 24)
            DesignSystem.FONTS['small'] = pygame.font.Font(None, 12)
    
    @staticmethod
    def get_font(size='label'):
        """Get font by size name."""
        return DesignSystem.FONTS.get(size, DesignSystem.FONTS['label'])

