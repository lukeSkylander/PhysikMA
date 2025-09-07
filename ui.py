"""
PhysikSim - Physics Simulation Interface
=======================================

A comprehensive physics simulation application for visualizing pendulum dynamics
in both 2D and 3D environments with real-time parameter control and theming.

Author: Luca Ulrich
Repository: PhysikSim
License: MIT

This module provides the main user interface for the physics simulation,
including controls for pendulum parameters, visualization options, and
real-time plotting with matplotlib integration.
"""

# ============================================================================
# IMPORTS AND DEPENDENCIES
# ============================================================================

# Standard library imports for GUI and file operations
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
from tkinter import filedialog
import datetime
import time
import os

# Matplotlib for scientific plotting and visualization
import matplotlib
# Embed matplotlib using the TkAgg backend for tkinter integration
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import animation
import matplotlib.pyplot as plt
plt.style.use('dark_background')  # Default dark theme for plots

# Scientific computing
import numpy as np

# Local modules for specific functionality
from save_projection_svg import export_projections  # SVG export functionality
from ui_utils import set_state_recursive  # UI utility functions

# ============================================================================
# THEME CONFIGURATION AND GLOBAL VARIABLES
# ============================================================================

# Color scheme variables for theming support
DARK_BG = "#0d1117"  # GitHub dark background
DARKER_BG = "#010409"  # Even darker for contrast
AX_BG = "#000000"  # Matplotlib axes background color
FG_COLOR = "#ffffff"  # Foreground text color
ACCENT_BG = "#21262d"  # Subtle accent background
ACCENT_BLUE = "#58a6ff"  # Modern blue accent for primary elements
ACCENT_GREEN = "#56d364"  # Success green for positive feedback
ACCENT_ORANGE = "#f85149"  # Warning/error red for alerts
ACCENT_PURPLE = "#bc8cff"  # Purple accent for special elements
BORDER_COLOR = "#30363d"  # Subtle borders
TEXT_MUTED = "#7d8590"  # Muted text for secondary information

# Status colors for user feedback messages
STATUS_SUCCESS = "#2ecc71"  # Green for successful operations
STATUS_WARNING = "#ff8c00"  # Orange for warnings

# UI layout and animation parameters
PADDING = 8  # Standard padding for UI elements
BORDER_RADIUS = 6  # Corner radius for visual elements
TARGET_FPS = 30  # Target frame rate for animations
MAX_TRAIL_POINTS = 100000  # Maximum points to show in trajectory trails

# ============================================================================
# PRESET CONFIGURATIONS AND THEME DEFINITIONS
# ============================================================================

# Predefined pendulum configurations for different simulation scenarios
# Each preset includes physical parameters and recommended simulation duration
PRESET_CONFIGS = {
    "Simple Pendulum": {
        "L": 1.0, "phi": 15, "g": 9.81, "h": 0.01, "drag": 0.0, "t_end": 30.0
    },
    "Foucault Pendulum": {  # Earth's rotation effect simulation
        "L": 2.0, "phi": 10, "psi": 0, "g": 9.81, "h": 0.005, "t_end": 120.0
    },
    "Damped Pendulum": {  # Pendulum with air resistance
        "L": 1.0, "phi": 30, "g": 9.81, "h": 0.01, "drag": 0.1, "t_end": 60.0
    },
    "Chaotic Pendulum": {  # Near-inverted pendulum showing chaotic behavior
        "L": 1.0, "phi": 179, "g": 9.81, "h": 0.001, "drag": 0.01, "t_end": 20.0
    }
}

# UI animation and interaction settings
ANIMATION_DURATION = 150  # Milliseconds for UI transitions
HOVER_LIFT = 2  # Pixels to lift elements on hover

# Color theme definitions for different visual styles
# Each theme includes background, accent, and semantic colors
THEMES = {
    "Dark": {  # GitHub dark theme
        "bg": "#0d1117", "accent": "#58a6ff", "darker": "#010409",
        "success": "#56d364", "warning": "#f85149", "purple": "#bc8cff"
    },
    "Light": {  # Clean light theme
        "bg": "#ffffff", "accent": "#0969da", "darker": "#f6f8fa",
        "success": "#28a745", "warning": "#dc3545", "purple": "#6f42c1"
    },
    "Solarized": {  # Solarized dark color scheme
        "bg": "#002b36", "accent": "#268bd2", "darker": "#073642",
        "success": "#859900", "warning": "#cb4b16", "purple": "#d33682"
    },
    "Dracula": {  # Popular Dracula theme
        "bg": "#282a36", "accent": "#bd93f9", "darker": "#1e1f29",
        "success": "#50fa7b", "warning": "#ff5555", "purple": "#bd93f9"
    },
    "Nord": {
        "bg": "#2e3440", "accent": "#88c0d0", "darker": "#3b4252",
        "success": "#a3be8c", "warning": "#bf616a", "purple": "#b48ead"
    }
}

# Animation functions for smooth UI transitions
def ease_in_out_cubic(t):
    """Smooth cubic easing function."""
    return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2

def _lighten_color(color_hex, factor):
    """Lighten a hex color by a factor (0.0 to 1.0)."""
    try:
        color_hex = color_hex.lstrip('#')
        rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(min(255, int(c + (255 - c) * factor)) for c in rgb)
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    except:
        return color_hex

def _darken_color(color_hex, factor):
    """Darken a hex color by a factor (0.0 to 1.0)."""
    try:
        color_hex = color_hex.lstrip('#')
        rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(max(0, int(c * (1 - factor))) for c in rgb)
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    except:
        return color_hex

def create_hover_effect(widget, lift_distance=HOVER_LIFT):
    """Create smooth hover effect for widgets."""
    original_relief = widget.cget("relief") if hasattr(widget, 'cget') else "flat"
    
    def on_enter(event):
        try:
            if hasattr(widget, 'configure'):
                widget.configure(relief="raised")
        except Exception:
            pass
    
    def on_leave(event):
        try:
            if hasattr(widget, 'configure'):
                widget.configure(relief=original_relief)
        except Exception:
            pass
    
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)

def animate_widget_transition(widget, start_alpha=0.0, end_alpha=1.0, duration=ANIMATION_DURATION):
    """Smooth transition animation for widgets."""
    try:
        steps = max(int(duration * 30), 10)  # 30 FPS
        step_alpha = (end_alpha - start_alpha) / steps
        current_alpha = start_alpha
        
        def update_step():
            nonlocal current_alpha
            current_alpha += step_alpha
            
            # Apply alpha effect (simplified for tkinter)
            alpha_value = ease_in_out_cubic(current_alpha)
            
            if hasattr(widget, 'configure'):
                try:
                    # Simple state change to simulate animation
                    if alpha_value > 0.5:
                        widget.configure(state='normal')
                    widget.update_idletasks()
                except Exception:
                    pass
            
            if current_alpha < end_alpha:
                widget.after(int(1000/30), update_step)
                
        update_step()
    except Exception:
        pass

def create_fade_in_effect(widget, duration=ANIMATION_DURATION / 1000):
    """Create smooth fade-in effect for widgets."""
    try:
        # Simple implementation for tkinter
        if hasattr(widget, 'configure'):
            widget.configure(state='normal')
            widget.update_idletasks()
    except Exception:
        pass

def create_animated_button(parent, text, command, style="TButton", **kwargs):
    """Create a button with enhanced hover animations and modern styling."""
    button = ttk.Button(parent, text=text, command=command, style=style, **kwargs)
    
    # Store original style
    original_style = style
    
    def on_enter(event):
        try:
            # Enhanced hover effect with lift animation
            button.configure(style="Hover.TButton")
            # Simulate lift effect with border change
            create_fade_in_effect(button, duration=0.1)
        except Exception:
            pass
    
    def on_leave(event):
        try:
            # Return to original style with smooth transition
            button.configure(style=original_style)
        except Exception:
            pass
    
    def on_click(event):
        try:
            # Quick press animation
            button.configure(style="Pressed.TButton")
            button.after(100, lambda: button.configure(style=original_style))
        except Exception:
            pass
    
    # Bind events for hover effects
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)
    button.bind("<Button-1>", on_click)
    
    return button

def create_modern_frame(parent, **kwargs):
    """Create a frame with modern rounded corner appearance simulation."""
    frame = ttk.Frame(parent, style="Card.TFrame", **kwargs)
    
    # Add subtle shadow effect simulation with border styling
    frame.configure(relief="solid", borderwidth=1)
    
    return frame

def enhance_button_appearance(button):
    """Add modern styling to buttons with enhanced visual effects."""
    def on_enter(event):
        # Create lift effect with enhanced borders
        try:
            current_style = button.cget('style')
            if 'Modern' in current_style:
                button.configure(relief="raised", borderwidth=3)
            create_fade_in_effect(button, duration=0.1)
        except Exception:
            pass
        
    def on_leave(event):
        # Return to flat appearance
        try:
            button.configure(relief="flat", borderwidth=2)
        except Exception:
            pass
        
    def on_click(event):
        # Quick press animation with visual feedback
        try:
            button.configure(relief="sunken", borderwidth=1)
            button.after(100, lambda: button.configure(relief="flat", borderwidth=2))
        except Exception:
            pass
    
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)
    button.bind("<Button-1>", on_click)
    
    return button

def apply_modern_styling_to_all_widgets(root_widget):
    """Apply modern styling to all existing widgets in the application."""
    def style_widget_recursive(widget):
        # Apply modern styling to buttons
        if isinstance(widget, ttk.Button):
            enhance_button_appearance(widget)
        
        # Apply styling to frames
        elif isinstance(widget, ttk.LabelFrame):
            try:
                widget.configure(style="Card.TFrame")
            except:
                pass
        
        # Recursively apply to all children
        try:
            for child in widget.winfo_children():
                style_widget_recursive(child)
        except:
            pass
    
    # Apply to the entire root window
    style_widget_recursive(root_widget)

def create_hover_effect(widget):
    """Add smooth hover effects to widgets."""
    original_cursor = widget.cget('cursor') if hasattr(widget, 'cget') else ""
    
    def on_enter(event):
        try:
            widget.configure(cursor="hand2")
        except:
            pass
    
    def on_leave(event):
        try:
            widget.configure(cursor=original_cursor)
        except:
            pass
    
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)
    return widget

def create_animated_button(parent, text, command, style="Modern.TButton", **kwargs):
    """Create a button with smooth animations and hover effects."""
    btn = ttk.Button(parent, text=text, style=style, **kwargs)
    
    # Add hover effect
    create_hover_effect(btn)
    
    # Add click animation
    original_command = command
    def animated_command():
        # Quick visual feedback on click
        btn.state(['pressed'])
        btn.after(100, lambda: btn.state(['!pressed']))
        if original_command:
            btn.after(50, original_command)
    
    btn.configure(command=animated_command)
    return btn


def configure_fonts() -> None:
    """Load preferred fonts and apply them globally."""

    preferred = ("Inter", "Roboto")
    default_font = tkfont.nametofont("TkDefaultFont")
    for family in preferred:
        try:
            tkfont.Font(family=family)
            default_font.configure(family=family)
            break
        except tk.TclError:
            continue

    for name in ("TkTextFont", "TkMenuFont", "TkHeadingFont"):
        try:
            tkfont.nametofont(name).configure(
                family=default_font.cget("family")
            )
        except tk.TclError:
            pass


# ============================================================================
# THEME CONFIGURATION AND STYLING FUNCTIONS
# ============================================================================

def configure_theme(root: tk.Tk, theme_name="Dark") -> ttk.Style:
    """
    Configure the application's visual theme and TTK widget styles.
    
    This function sets up the complete visual appearance of the application,
    including colors, fonts, and widget styles based on the selected theme.
    It updates global color variables and applies consistent styling across
    all UI components.
    
    Args:
        root: The main Tkinter window
        theme_name: Name of the theme to apply ("Dark", "Light", "Solarized", etc.)
        
    Returns:
        Configured TTK Style object
    """
    global DARK_BG, ACCENT_BLUE, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_PURPLE, DARKER_BG, FG_COLOR, AX_BG
    
    # Initialize TTK style system with base theme
    style = ttk.Style(root)
    style.theme_use("clam")  # Use 'clam' as base for consistent cross-platform appearance
    
    # Update global color variables based on selected theme
    theme = THEMES.get(theme_name, THEMES["Dark"])
    DARK_BG = theme["bg"]  # Main background color
    ACCENT_BLUE = theme["accent"]  # Primary accent color
    DARKER_BG = theme["darker"]  # Darker background for contrast areas
    ACCENT_GREEN = theme["success"]  # Success/positive feedback color
    ACCENT_ORANGE = theme["warning"]  # Warning/error feedback color
    ACCENT_PURPLE = theme["purple"]  # Secondary accent color
    
    # Set foreground (text) and plot background colors based on theme
    if theme_name == "Light":
        FG_COLOR = "#000000"  # Black text for light theme
        AX_BG = "#f8f9fa"     # Light gray for plots
    else:
        FG_COLOR = "#ffffff"  # White text for dark themes
        AX_BG = "#000000"     # Black for plots

    # ========== TTK WIDGET STYLING ==========
    # Configure base frame appearance with modern padding and flat design
    style.configure("TFrame", background=DARK_BG, padding=PADDING, relief="flat")
    
    # Configure label styling with consistent typography and colors
    style.configure("TLabel", background=DARK_BG, foreground=FG_COLOR, padding=PADDING, font=("Inter", 10))
    
    # ========== LABELFRAME STYLING ==========
    # Ensure TLabelframe layout exists before styling
    try:
        style.layout("TLabelframe")
    except tk.TclError:
        # Create a basic layout if it doesn't exist to prevent errors
        style.layout("TLabelframe", [
            ('Labelframe.border', {'sticky': 'nswe', 'children': [
                ('Labelframe.padding', {'sticky': 'nswe', 'children': [
                    ('Labelframe.label', {'side': 'top', 'sticky': 'w'}),
                    ('Labelframe.focus', {'sticky': 'nswe'})
                ]})
            ]})
        ])
    
    # Configure the main LabelFrame style with enhanced typography and borders
    style.configure(
        "TLabelframe", 
        background=DARK_BG, 
        foreground=FG_COLOR,  # This affects the label text
        borderwidth=1,
        relief="solid",
        padding=PADDING,
        font=("Inter", 14, "bold")  # Large font for better visibility
    )
    
    # Configure the LabelFrame label element with enhanced styling
    style.configure(
        "TLabelframe.Label",
        background=DARK_BG, 
        foreground=FG_COLOR,
        font=("Inter", 14, "bold"),  # Large, bold font for section headers
        padding=(8, 4)  # Adequate spacing around label text
    )
    
    # ========== ENHANCED LABELFRAME STYLES ==========
    # Enhanced Black.TLabelframe styling for darker contrast frames
    style.configure(
        "Black.TLabelframe",
        background=DARKER_BG,
        foreground=FG_COLOR,
        borderwidth=1,
        relief="solid", 
        padding=PADDING,
        font=("Inter", 14, "bold")  # LARGER font for better visibility
    )
    
    # Configure the label element for Black style with consistent theming
    style.configure(
        "Black.TLabelframe.Label",
        background=DARKER_BG,
        foreground=FG_COLOR,
        font=("Inter", 14, "bold"),  # Large, bold font for readability
        padding=(8, 4)
    )
    
    # ========== STATE MAPPING FOR CONSISTENT COLORS ==========
    # Map widget states to ensure colors are applied consistently
    style.map("TLabelframe",
              background=[('active', DARK_BG), ('!active', DARK_BG), ('disabled', DARK_BG)],
              foreground=[('active', FG_COLOR), ('!active', FG_COLOR), ('disabled', FG_COLOR)])
    
    # Map label element states for consistent text appearance
    style.map("TLabelframe.Label",
              background=[('active', DARK_BG), ('!active', DARK_BG), ('disabled', DARK_BG)],
              foreground=[('active', FG_COLOR), ('!active', FG_COLOR), ('disabled', FG_COLOR)])
    
    style.map("Black.TLabelframe",
              background=[('active', DARKER_BG), ('!active', DARKER_BG), ('disabled', DARKER_BG)],
              foreground=[('active', FG_COLOR), ('!active', FG_COLOR), ('disabled', FG_COLOR)])
    
    # Map state styling for Black.TLabelframe elements
    style.map("Black.TLabelframe.Label",
              background=[('active', DARKER_BG), ('!active', DARKER_BG), ('disabled', DARKER_BG)],
              foreground=[('active', FG_COLOR), ('!active', FG_COLOR), ('disabled', FG_COLOR)])
    
    # ========== CHECKBOX STYLING ==========
    # Configure checkbox appearance with theme-consistent colors
    style.configure(
        "TCheckbutton", 
        background=DARK_BG, 
        foreground=FG_COLOR, 
        padding=PADDING,
        font=("Inter", 10)
    )
    
    # ========== BUTTON STYLING ==========
    # Enhanced button styles with modern flat design and hover effects
    style.configure(
        "TButton",
        background=ACCENT_BG,
        foreground=FG_COLOR,
        padding=PADDING,
        borderwidth=1,
        relief="flat"
    )
    
    style.configure(
        "Modern.TButton",
        background=ACCENT_BLUE,
        foreground="white",
        borderwidth=2,
        focuscolor="none",
        padding=(16, 10),
        font=("Inter", 10, "bold"),
        relief="flat"
    )
    
    # Hover and pressed button styles for modern appearance
    style.configure(
        "Hover.TButton",
        background=_lighten_color(ACCENT_BLUE, 0.2),
        foreground="white",
        borderwidth=3,
        relief="raised",
        padding=(16, 10),
        font=("Inter", 10, "bold")
    )
    
    style.configure(
        "Pressed.TButton",
        background=_darken_color(ACCENT_BLUE, 0.2),
        foreground="white",
        borderwidth=1,
        relief="sunken",
        padding=(16, 10),
        font=("Inter", 10, "bold")
    )
    
    # Create rounded corner effect with enhanced borders and hover states
    style.map("Modern.TButton",
              background=[('active', _lighten_color(ACCENT_BLUE, 0.3)),
                         ('pressed', _darken_color(ACCENT_BLUE, 0.2))],
              relief=[('pressed', 'sunken'),
                     ('active', 'raised')])
    
    # Enhanced colored button variants with modern styling
    style.configure("Success.TButton", 
                   background=ACCENT_GREEN, 
                   foreground="white", 
                   relief="flat",
                   padding=(16, 10),
                   borderwidth=2,
                   font=("Inter", 10, "bold"))
    style.map("Success.TButton",
              background=[('active', _lighten_color(ACCENT_GREEN, 0.3)),
                         ('pressed', _darken_color(ACCENT_GREEN, 0.2))],
              relief=[('pressed', 'sunken'), ('active', 'raised')])
    
    style.configure("Warning.TButton", 
                   background=ACCENT_ORANGE, 
                   foreground="white", 
                   relief="flat",
                   padding=(16, 10),
                   borderwidth=2,
                   font=("Inter", 10, "bold"))
    style.map("Warning.TButton",
              background=[('active', _lighten_color(ACCENT_ORANGE, 0.3)),
                         ('pressed', _darken_color(ACCENT_ORANGE, 0.2))],
              relief=[('pressed', 'sunken'), ('active', 'raised')])
    
    style.configure("Purple.TButton", 
                   background=ACCENT_PURPLE, 
                   foreground="white", 
                   relief="flat",
                   padding=(16, 10),
                   borderwidth=2,
                   font=("Inter", 10, "bold"))
    style.map("Purple.TButton",
              background=[('active', _lighten_color(ACCENT_PURPLE, 0.3)),
                         ('pressed', _darken_color(ACCENT_PURPLE, 0.2))],
              relief=[('pressed', 'sunken'), ('active', 'raised')])
    
    # Enhanced input styles with modern rounded appearance and proper theming
    style.configure(
        "TEntry",
        fieldbackground=DARKER_BG,
        foreground=FG_COLOR,
        insertcolor=FG_COLOR,
        padding=(12, 8),
        borderwidth=2,
        relief="flat",
        font=("Inter", 10)
    )
    
    style.configure(
        "TCombobox",
        fieldbackground=DARKER_BG,
        background=DARK_BG,
        foreground=FG_COLOR,
        padding=(12, 8),
        borderwidth=2,
        relief="flat",
        font=("Inter", 10),
        selectbackground=ACCENT_BLUE,
        selectforeground="white"
    )
    
    # Enhanced combobox styling for dropdown arrow and selection
    style.map("TCombobox",
              fieldbackground=[('readonly', DARKER_BG)],
              selectbackground=[('readonly', ACCENT_BLUE)],
              selectforeground=[('readonly', 'white')])
    
    # Modern card frames with enhanced styling
    style.configure(
        "Card.TFrame",
        background=DARKER_BG,
        relief="solid",
        borderwidth=1,
        padding=20
    )
    
    # Enhanced checkbutton styling
    style.configure("TCheckbutton", 
                   background=DARK_BG, 
                   foreground=FG_COLOR,
                   focuscolor="none",
                   borderwidth=0,
                   font=("Inter", 10))
    
    # Modern scale styling
    style.configure("TScale",
                   background=DARK_BG,
                   troughcolor=DARKER_BG,
                   borderwidth=0,
                   sliderlength=20)
    
    # Enhanced notebook (tabs) styling
    style.configure("TNotebook", background=DARK_BG, borderwidth=0)
    style.configure(
        "TNotebook.Tab",
        background=DARKER_BG,
        foreground=FG_COLOR,
        padding=(12, 8),
        borderwidth=1,
        font=("Inter", 10, "bold")
    )
    style.map("TNotebook.Tab",
              background=[('selected', ACCENT_BLUE), 
                         ('active', _lighten_color(DARKER_BG, 0.2))])

    # Update root background
    root.configure(bg=DARK_BG)
    
    return style


class Tooltip:
    """Enhanced tooltip with smooth animations and modern styling."""

    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self.tipwindow: tk.Toplevel | None = None
        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event: tk.Event | None = None) -> None:
        if self.tipwindow is not None:
            return
        
        # Calculate position
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.configure(bg=DARKER_BG)
        
        # Modern tooltip styling
        frame = tk.Frame(tw, bg=DARKER_BG, relief="solid", borderwidth=1)
        frame.pack()
        
        label = tk.Label(
            frame,
            text=self.text,
            justify="left",
            background=DARKER_BG,
            foreground=FG_COLOR,
            font=("Inter", 9),
            padx=12,
            pady=8
        )
        label.pack()

    def hide_tooltip(self, event: tk.Event | None = None) -> None:
        if self.tipwindow is not None:
            self.tipwindow.destroy()
            self.tipwindow = None


def create_parameter_card(parent: tk.Widget, title: str, parameters: list) -> ttk.Frame:
    """Create a modern card-style frame for parameter groupings."""
    card = ttk.Frame(parent, style="Card.TFrame")
    
    # Title label with enhanced styling
    title_label = ttk.Label(card, text=title, font=("Inter", 12, "bold"))
    title_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
    
    for i, (label_text, variable, tooltip_text, entry_width) in enumerate(parameters):
        # Parameter label
        label = ttk.Label(card, text=label_text)
        label.grid(row=i+1, column=0, sticky="w", padx=(0, 8), pady=2)
        
        # Parameter entry with enhanced styling
        entry = ttk.Entry(card, textvariable=variable, width=entry_width)
        entry.grid(row=i+1, column=1, sticky="ew", pady=2)
        
        # Add tooltip if provided
        if tooltip_text:
            Tooltip(entry, tooltip_text)
    
    card.columnconfigure(1, weight=1)
    return card


def create_preset_selector(parent: tk.Widget, apply_callback) -> ttk.Frame:
    """Create a preset configuration selector with modern styling."""
    preset_frame = ttk.Frame(parent, style="Card.TFrame")
    
    title_label = ttk.Label(preset_frame, text="Quick Presets", font=("Inter", 12, "bold"))
    title_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
    
    # Preset buttons with different colors
    presets = [
        ("Simple", "Simple Pendulum", "Modern.TButton"),
        ("Foucault", "Foucault Pendulum", "Purple.TButton"),
        ("Damped", "Damped Pendulum", "Warning.TButton"),
        ("Chaotic", "Chaotic Pendulum", "Warning.TButton")
    ]
    
    for i, (short_name, config_key, button_style) in enumerate(presets):
        btn = ttk.Button(
            preset_frame, 
            text=short_name, 
            style=button_style,
            command=lambda key=config_key: apply_callback(key)
        )
        btn.grid(row=1, column=i, padx=2, pady=4, sticky="ew")
        
        # Add tooltip with configuration details
        if config_key in PRESET_CONFIGS:
            config = PRESET_CONFIGS[config_key]
            tooltip_text = "\n".join([f"{k}: {v}" for k, v in config.items()])
            Tooltip(btn, tooltip_text)
    
    preset_frame.columnconfigure((0, 1, 2, 3), weight=1)
    return preset_frame


def create_enhanced_control_panel(parent: tk.Widget, control_callbacks: dict) -> ttk.Frame:
    """Create an enhanced control panel with modern styling and additional features."""
    control_frame = ttk.Frame(parent, style="Card.TFrame")
    
    # Main control buttons with enhanced styling
    controls = [
        ("▶ Start", "start", "Success.TButton"),
        ("⏸ Pause", "pause", "Warning.TButton"),
        ("⏹ Stop", "stop", "Modern.TButton"),
        ("↻ Reset", "reset", "Purple.TButton")
    ]
    
    for i, (text, action, style) in enumerate(controls):
        btn = ttk.Button(
            control_frame,
            text=text,
            style=style,
            command=control_callbacks.get(action, lambda: None)
        )
        btn.grid(row=0, column=i, padx=4, pady=8, sticky="ew")
    
    # Additional controls row
    export_btn = ttk.Button(control_frame, text="📊 Export Data", style="Modern.TButton")
    export_btn.grid(row=1, column=0, columnspan=2, padx=4, pady=4, sticky="ew")
    
    screenshot_btn = ttk.Button(control_frame, text="📸 Screenshot", style="Modern.TButton")
    screenshot_btn.grid(row=1, column=2, columnspan=2, padx=4, pady=4, sticky="ew")
    
    control_frame.columnconfigure((0, 1, 2, 3), weight=1)
    return control_frame


def create_visualization_enhancements(parent: tk.Widget) -> ttk.Frame:
    """Create enhanced visualization options with modern styling."""
    viz_frame = ttk.Frame(parent, style="Card.TFrame")
    
    # Title
    title_label = ttk.Label(viz_frame, text="Visualization Options", font=("Inter", 12, "bold"))
    title_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
    
    # Plot type selection
    plot_type_label = ttk.Label(viz_frame, text="Plot Type:")
    plot_type_label.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
    
    plot_type_var = tk.StringVar(value="Energy")
    plot_type_combo = ttk.Combobox(
        viz_frame, 
        textvariable=plot_type_var,
        values=["Energy", "Angles", "Phase Space", "Frequency Analysis"],
        state="readonly",
        width=15
    )
    plot_type_combo.grid(row=1, column=1, columnspan=2, sticky="ew", pady=4)
    
    # Trail options
    trail_label = ttk.Label(viz_frame, text="Trail Length:")
    trail_label.grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
    
    trail_var = tk.IntVar(value=500)
    trail_scale = ttk.Scale(viz_frame, variable=trail_var, from_=0, to=2000, orient="horizontal")
    trail_scale.grid(row=2, column=1, sticky="ew", padx=4, pady=4)
    
    trail_entry = ttk.Entry(viz_frame, textvariable=trail_var, width=8)
    trail_entry.grid(row=2, column=2, sticky="ew", pady=4)
    
    # Color scheme
    color_label = ttk.Label(viz_frame, text="Color Scheme:")
    color_label.grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
    
    color_var = tk.StringVar(value="Default")
    color_combo = ttk.Combobox(
        viz_frame,
        textvariable=color_var,
        values=["Default", "Rainbow", "Heat", "Cool", "Plasma"],
        state="readonly",
        width=15
    )
    color_combo.grid(row=3, column=1, columnspan=2, sticky="ew", pady=4)
    
    viz_frame.columnconfigure(1, weight=1)
    return viz_frame, plot_type_var, trail_var, color_var


def create_settings_tab(parent, settings_vars, update_status_func, configure_theme_func, root):
    """Create a comprehensive settings tab with dynamic controls."""
    settings_frame = ttk.Frame(parent)
    
    # Create scrollable settings area
    settings_canvas = tk.Canvas(settings_frame, background=DARK_BG, highlightthickness=0)
    settings_scrollbar = ttk.Scrollbar(settings_frame, orient="vertical", command=settings_canvas.yview)
    settings_canvas.configure(yscrollcommand=settings_scrollbar.set)
    
    settings_canvas.pack(side="left", fill="both", expand=True)
    settings_scrollbar.pack(side="right", fill="y")
    
    settings_content = ttk.Frame(settings_canvas)
    settings_window = settings_canvas.create_window((0, 0), window=settings_content, anchor="nw")
    
    def configure_settings_scroll(event):
        settings_canvas.configure(scrollregion=settings_canvas.bbox("all"))
        settings_canvas.itemconfig(settings_window, width=settings_canvas.winfo_width())
    
    settings_content.bind("<Configure>", configure_settings_scroll)
    settings_canvas.bind("<Configure>", lambda e: settings_canvas.itemconfig(settings_window, width=e.width))
    
    # Mouse wheel scrolling
    def on_mousewheel(event):
        settings_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    settings_canvas.bind("<MouseWheel>", on_mousewheel)
    
    # Simulation Settings Section
    # FIXED: Update settings frames
    sim_settings_frame = ttk.LabelFrame(settings_content, text="🚀 Simulation Settings")
    sim_settings_frame.configure(style="TLabelframe")  # Apply style after creation
    sim_settings_frame.pack(fill="x", padx=PADDING, pady=PADDING)
    sim_settings_frame.columnconfigure(1, weight=1)
    
    # Simulation duration
    ttk.Label(sim_settings_frame, text="Simulation Duration [s]:").grid(row=0, column=0, sticky="w", padx=8, pady=4)
    t_end_scale = ttk.Scale(sim_settings_frame, variable=settings_vars['t_end'], from_=5.0, to=120.0, orient="horizontal")
    t_end_scale.grid(row=0, column=1, sticky="ew", padx=8, pady=4)
    t_end_entry = ttk.Entry(sim_settings_frame, textvariable=settings_vars['t_end'], width=10)
    t_end_entry.grid(row=0, column=2, padx=8, pady=4)
    
    # Animation quality
    ttk.Label(sim_settings_frame, text="Animation Quality:").grid(row=1, column=0, sticky="w", padx=8, pady=4)
    quality_combo = ttk.Combobox(sim_settings_frame, textvariable=settings_vars['animation_quality'],
                                values=["Low", "Medium", "High", "Ultra"], state="readonly")
    quality_combo.grid(row=1, column=1, columnspan=2, sticky="ew", padx=8, pady=4)
    
    # Trail length with dynamic label
    trail_label = ttk.Label(sim_settings_frame, text="Trail Length:")
    trail_label.grid(row=2, column=0, sticky="w", padx=8, pady=4)
    trail_scale = ttk.Scale(sim_settings_frame, variable=settings_vars['trail_length'], from_=0, to=20000, orient="horizontal")
    trail_scale.grid(row=2, column=1, sticky="ew", padx=8, pady=4)
    trail_entry = ttk.Entry(sim_settings_frame, textvariable=settings_vars['trail_length'], width=10)
    trail_entry.grid(row=2, column=2, padx=8, pady=4)
    
    # Dynamic trail length description
    def update_trail_description(*args):
        trail_val = settings_vars['trail_length'].get()
        if trail_val == 0:
            description = "🚫 No trail - trajectory will not be visible"
        elif trail_val < 50:
            description = f"⚪ Very short trail - last {trail_val} points (quick fade) •"
        elif trail_val < 200:
            description = f"🔵 Short trail - last {trail_val} points (moderate fade) •••"
        elif trail_val < 500:
            description = f"🟢 Medium trail - last {trail_val} points (visible history) •••••"
        elif trail_val < 1000:
            description = f"🟡 Long trail - last {trail_val} points (extended history) •••••••"
        else:
            description = f"🔴 Very long trail - last {trail_val} points (full trajectory) •••••••••"
        trail_help_label.configure(text=description)
    
    trail_help_label = ttk.Label(sim_settings_frame, text="", font=("Inter", 8), foreground=TEXT_MUTED)
    trail_help_label.grid(row=3, column=0, columnspan=3, sticky="w", padx=20, pady=(0, 8))
    
    # Update description initially and when value changes
    settings_vars['trail_length'].trace_add("write", update_trail_description)
    update_trail_description()  # Set initial description
    
    # Development Settings Section
    dev_settings_frame = ttk.LabelFrame(settings_content, text="🔧 Development Settings")
    dev_settings_frame.configure(style="TLabelframe")
    dev_settings_frame.pack(fill="x", padx=PADDING, pady=PADDING)
    dev_settings_frame.columnconfigure(1, weight=1)
    
    # RK4 test simulations toggle
    ttk.Checkbutton(dev_settings_frame, text="Show RK4 Test Simulations", 
                   variable=settings_vars['show_rk4_tests']).grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=4)
    
    rk4_help_label = ttk.Label(dev_settings_frame, text="Enable RK4 numerical integration test cases for development", 
                              font=("Inter", 8), foreground=TEXT_MUTED)
    rk4_help_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 8))
    
    # Appearance Settings Section
    appearance_frame = ttk.LabelFrame(settings_content, text="🎨 Appearance Settings")
    appearance_frame.configure(style="TLabelframe")  # Apply style after creation
    appearance_frame.pack(fill="x", padx=PADDING, pady=PADDING)
    appearance_frame.columnconfigure(1, weight=1)
    
    # Theme selection
    ttk.Label(appearance_frame, text="Theme:").grid(row=0, column=0, sticky="w", padx=8, pady=4)
    theme_combo = ttk.Combobox(appearance_frame, textvariable=settings_vars['current_theme'],
                              values=list(THEMES.keys()), state="readonly")
    theme_combo.grid(row=0, column=1, sticky="ew", padx=8, pady=4)
    
    # Visual options checkboxes
    ttk.Checkbutton(appearance_frame, text="Show Grid", variable=settings_vars['grid_visible']).grid(row=1, column=0, sticky="w", padx=8, pady=4)
    ttk.Checkbutton(appearance_frame, text="Show FPS Counter", variable=settings_vars['show_fps']).grid(row=1, column=1, sticky="w", padx=8, pady=4)
    
    # Reset settings button
    def reset_settings_to_defaults():
        """Reset all settings to default values with animation."""
        update_status_func("🔄 Resetting settings to defaults...", 50, True)
        
        settings_vars['t_end'].set(30.0)
        settings_vars['current_theme'].set("Dark")
        settings_vars['trail_length'].set(500)
        settings_vars['animation_quality'].set("High")
        settings_vars['grid_visible'].set(True)
        settings_vars['show_fps'].set(True)
        settings_vars['show_rk4_tests'].set(False)
        
        # Apply theme change
        configure_theme_func(root, "Dark")
        
        update_status_func("✅ Settings reset successfully", 100, True)
        root.after(2000, lambda: update_status_func("🚀 Ready", 0))
    
    reset_settings_btn = create_animated_button(
        settings_content,
        text="🔄 Reset to Defaults",
        command=reset_settings_to_defaults,
        style="Warning.TButton"
    )
    reset_settings_btn.pack(pady=PADDING)
    
    return settings_frame

# ============================================================================
# MAIN APPLICATION ENTRY POINT
# ============================================================================

def main():
    """
    Main application entry point that initializes and runs the PhysikSim interface.
    
    This function sets up the complete user interface including theme configuration,
    widget creation, event handlers, and the main application loop. It serves as
    the central orchestrator for all simulation functionality.
    """
    # Initialize main window with title and basic configuration
    root = tk.Tk()
    root.title("PhysikSim - Dynamic Physics Simulator")

    # Configure fonts for consistent typography across the application
    configure_fonts()
    
    # ========== GLOBAL VARIABLE INITIALIZATION ==========
    # Settings variables - declare early for global access throughout the app
    t_end_var = tk.DoubleVar(value=30.0)  # Simulation end time in seconds
    current_theme_var = tk.StringVar(value="Dark")  # Current UI theme
    auto_screenshot_var = tk.BooleanVar(value=True)  # Auto-screenshot feature
    trail_length_var = tk.IntVar(value=500)  # Trail/trajectory length
    animation_quality_var = tk.StringVar(value="High")  # Animation quality setting
    grid_visible_var = tk.BooleanVar(value=True)  # Grid visibility toggle
    show_fps_var = tk.BooleanVar(value=True)  # FPS display toggle
    show_rk4_tests_var = tk.BooleanVar(value=False)  # Show RK4 test simulations
    
    # Apply initial theme configuration
    style = configure_theme(root, current_theme_var.get())
    root.configure(bg=DARK_BG)
    
    # ========== THEME CHANGE HANDLER ==========
    def on_theme_change(*args):
        """
        Enhanced theme change handler with immediate theme application.
        
        This function is called whenever the user changes the theme selection,
        ensuring all UI elements and plots are updated to match the new theme.
        """
        new_theme = current_theme_var.get()
        
        # Apply new theme with proper global variable updates
        configure_theme(root, new_theme)
        
        # Update matplotlib style based on theme preference
        if new_theme == "Light":
            plt.style.use('default')  # Use matplotlib's light theme
        else:
            plt.style.use('dark_background')
        
        # Update matplotlib plots immediately
        update_plot_theme(new_theme)
        
        # CRITICAL FIX: Force immediate canvas background updates
        try:
            # Update figure backgrounds
            if 'fig_anim' in globals() and fig_anim is not None:
                fig_anim.patch.set_facecolor(DARK_BG)
                fig_anim.set_facecolor(DARK_BG)
            if 'fig_plot' in globals() and fig_plot is not None:
                fig_plot.patch.set_facecolor(DARK_BG)
                fig_plot.set_facecolor(DARK_BG)
            
            # Update canvas widget backgrounds immediately
            if 'canvas_anim' in globals() and canvas_anim is not None:
                canvas_widget = canvas_anim.get_tk_widget()
                canvas_widget.configure(bg=DARK_BG, highlightbackground=DARK_BG, highlightcolor=DARK_BG)
                
                # Update all parent frames
                try:
                    parent = canvas_widget.master
                    while parent and parent != root:
                        try:
                            parent.configure(background=DARK_BG)
                        except:
                            pass
                        parent = getattr(parent, 'master', None)
                except:
                    pass
                
                # Force immediate redraw
                canvas_anim.draw_idle()
            
            if 'canvas_plot' in globals() and canvas_plot is not None:
                canvas_widget = canvas_plot.get_tk_widget()
                canvas_widget.configure(bg=DARK_BG, highlightbackground=DARK_BG, highlightcolor=DARK_BG)
                
                # Update all parent frames
                try:
                    parent = canvas_widget.master
                    while parent and parent != root:
                        try:
                            parent.configure(background=DARK_BG)
                        except:
                            pass
                        parent = getattr(parent, 'master', None)
                except:
                    pass
                
                # Force immediate redraw
                canvas_plot.draw_idle()
            
            # Update axis themes if they exist
            if 'ax_anim' in globals() and ax_anim is not None:
                ax_anim.set_facecolor(AX_BG)
                ax_anim.tick_params(colors=FG_COLOR)
                
                # Handle 3D specific theming
                if hasattr(ax_anim, 'zaxis'):
                    ax_anim.xaxis.label.set_color(FG_COLOR)
                    ax_anim.yaxis.label.set_color(FG_COLOR)
                    ax_anim.zaxis.label.set_color(FG_COLOR)
                    
                    # Update 3D panes
                    if hasattr(ax_anim, 'xaxis') and hasattr(ax_anim.xaxis, 'pane'):
                        ax_anim.xaxis.pane.fill = False
                        ax_anim.yaxis.pane.fill = False
                        ax_anim.zaxis.pane.fill = False
                        ax_anim.xaxis.pane.set_edgecolor(FG_COLOR)
                        ax_anim.yaxis.pane.set_edgecolor(FG_COLOR)
                        ax_anim.zaxis.pane.set_edgecolor(FG_COLOR)
                        ax_anim.xaxis.pane.set_alpha(0.1)
                        ax_anim.yaxis.pane.set_alpha(0.1)
                        ax_anim.zaxis.pane.set_alpha(0.1)
                    
                    # Force update all 3D tick label colors
                    for tick in ax_anim.xaxis.get_major_ticks():
                        tick.label1.set_color(FG_COLOR)
                    for tick in ax_anim.yaxis.get_major_ticks():
                        tick.label1.set_color(FG_COLOR)
                    for tick in ax_anim.zaxis.get_major_ticks():
                        tick.label1.set_color(FG_COLOR)
                else:
                    # 2D axis theming
                    if hasattr(ax_anim, 'spines'):
                        for spine in ax_anim.spines.values():
                            spine.set_edgecolor(FG_COLOR)
                    ax_anim.grid(True, alpha=0.3, color=FG_COLOR)
            
            if 'ax_plot' in globals() and ax_plot is not None:
                ax_plot.set_facecolor(AX_BG)
                ax_plot.tick_params(colors=FG_COLOR)
                for spine in ax_plot.spines.values():
                    spine.set_edgecolor(FG_COLOR)
                ax_plot.grid(True, alpha=0.3, color=FG_COLOR)
            
        except Exception as e:
            print(f"Error updating canvas backgrounds: {e}")
        
        # Force all LabelFrames to update their styles
        def force_labelframe_update(widget):
            if isinstance(widget, ttk.LabelFrame):
                try:
                    current_text = widget.cget('text')
                    if any(text in current_text for text in ["🎮 Simulation", "⚙️ Pendulum Parameters"]):
                        widget.configure(style="Black.TLabelframe")
                    else:
                        widget.configure(style="TLabelframe")
                    widget.update_idletasks()
                except Exception as e:
                    print(f"Error updating LabelFrame: {e}")
            
            try:
                for child in widget.winfo_children():
                    force_labelframe_update(child)
            except:
                pass
        
        force_labelframe_update(root)
        
        # Update ALL frame backgrounds
        def update_all_frames(widget):
            try:
                if hasattr(widget, 'configure'):
                    if isinstance(widget, (ttk.Frame, tk.Frame)):
                        widget.configure(background=DARK_BG)
                    elif isinstance(widget, tk.Canvas):
                        widget.configure(bg=DARK_BG, highlightbackground=DARK_BG)
                
                for child in widget.winfo_children():
                    update_all_frames(child)
            except:
                pass
        
        update_all_frames(root)
        
        # Force complete redraw
        root.update_idletasks()
        
        # Update status with feedback
        update_status(f"🎨 Applied {new_theme} theme", 100, True)
        root.after(2000, lambda: update_status("🚀 Ready", 0))
    # ============================================================================
    # MATPLOTLIB THEME INTEGRATION
    # ============================================================================
    
    def update_plot_theme(theme_name):
        """
        Update matplotlib plots to match the selected theme with comprehensive coverage.
        
        This function ensures that all matplotlib figures, axes, and plot elements
        are updated to match the current UI theme. It handles both 2D and 3D plots,
        updating backgrounds, text colors, and axis styling.
        
        Args:
            theme_name: The name of the theme to apply to matplotlib plots
        """
        try:
            global AX_BG, FG_COLOR, DARK_BG
            
            # Apply matplotlib base style based on theme preference
            if theme_name == "Light":
                plt.style.use('default')  # Use matplotlib's light theme
            else:
                plt.style.use('dark_background')  # Use matplotlib's dark theme
            
            # ========== FIGURE BACKGROUND UPDATES ==========
            # Update figure backgrounds to match current theme
            if 'fig_anim' in globals() and fig_anim:
                fig_anim.patch.set_facecolor(DARK_BG)  # Animation figure background
                fig_anim.set_facecolor(DARK_BG)  # Force background update
            if 'fig_plot' in globals() and fig_plot:
                fig_plot.patch.set_facecolor(DARK_BG)  # Data plot figure background
                fig_plot.set_facecolor(DARK_BG)  # Force background update
            
            # ========== AXIS STYLING UPDATES ==========
            # Update axis backgrounds and colors for animation plot
            if 'ax_anim' in globals() and ax_anim:
                ax_anim.set_facecolor(AX_BG)  # Set plot area background
                if hasattr(ax_anim, 'tick_params'):
                    ax_anim.tick_params(colors=FG_COLOR)  # Update tick colors
                    # For 3D plots, update individual axis colors separately
                    if hasattr(ax_anim, 'zaxis'):
                        ax_anim.tick_params(axis='x', colors=FG_COLOR)
                        ax_anim.tick_params(axis='y', colors=FG_COLOR)
                        ax_anim.tick_params(axis='z', colors=FG_COLOR)
                        
                        # CRITICAL FIX: Force update all 3D tick label colors
                        for tick in ax_anim.xaxis.get_major_ticks():
                            tick.label1.set_color(FG_COLOR)
                        for tick in ax_anim.yaxis.get_major_ticks():
                            tick.label1.set_color(FG_COLOR)
                        for tick in ax_anim.zaxis.get_major_ticks():
                            tick.label1.set_color(FG_COLOR)
                if hasattr(ax_anim, 'spines'):
                    for spine in ax_anim.spines.values():
                        spine.set_edgecolor(FG_COLOR)
                
                # For 3D plots, also update the pane colors and ALL text elements
                if hasattr(ax_anim, 'xaxis') and hasattr(ax_anim.xaxis, 'pane'):
                    ax_anim.xaxis.pane.fill = False
                    ax_anim.yaxis.pane.fill = False
                    ax_anim.zaxis.pane.fill = False
                    ax_anim.xaxis.pane.set_edgecolor(FG_COLOR)
                    ax_anim.yaxis.pane.set_edgecolor(FG_COLOR)  
                    ax_anim.zaxis.pane.set_edgecolor(FG_COLOR)
                    ax_anim.xaxis.pane.set_alpha(0.1)
                    ax_anim.yaxis.pane.set_alpha(0.1)
                    ax_anim.zaxis.pane.set_alpha(0.1)
                
                # Update 3D axis colors and labels
                if hasattr(ax_anim, 'zaxis'):
                    ax_anim.xaxis.label.set_color(FG_COLOR)
                    ax_anim.yaxis.label.set_color(FG_COLOR)
                    ax_anim.zaxis.label.set_color(FG_COLOR)
                    
                    # Update existing axis labels if they exist
                    if ax_anim.get_xlabel():
                        ax_anim.set_xlabel(ax_anim.get_xlabel(), color=FG_COLOR, fontweight='bold')
                    if ax_anim.get_ylabel():
                        ax_anim.set_ylabel(ax_anim.get_ylabel(), color=FG_COLOR, fontweight='bold')
                    if hasattr(ax_anim, 'get_zlabel') and ax_anim.get_zlabel():
                        ax_anim.set_zlabel(ax_anim.get_zlabel(), color=FG_COLOR, fontweight='bold')
                
                # Update grid
                if hasattr(ax_anim, 'grid'):
                    ax_anim.grid(True, alpha=0.3, color=FG_COLOR)
                
                # Update title if it exists
                if ax_anim.get_title():
                    ax_anim.set_title(ax_anim.get_title(), color=FG_COLOR, fontweight='bold')
            
            # Update axis backgrounds and colors for graph plot
            if 'ax_plot' in globals() and ax_plot:
                ax_plot.set_facecolor(AX_BG)
                ax_plot.tick_params(colors=FG_COLOR)
                for spine in ax_plot.spines.values():
                    spine.set_edgecolor(FG_COLOR)
                ax_plot.grid(True, alpha=0.3, color=FG_COLOR)
                
                # Update all text elements on the plot
                if ax_plot.get_xlabel():
                    ax_plot.set_xlabel(ax_plot.get_xlabel(), color=FG_COLOR, fontweight='bold')
                if ax_plot.get_ylabel():
                    ax_plot.set_ylabel(ax_plot.get_ylabel(), color=FG_COLOR, fontweight='bold')
                if ax_plot.get_title():
                    ax_plot.set_title(ax_plot.get_title(), color=FG_COLOR, fontweight='bold')
                
                # Update legend if it exists
                legend = ax_plot.get_legend()
                if legend:
                    legend.set_facecolor(DARKER_BG)
                    legend.set_edgecolor(FG_COLOR)
                    for text in legend.get_texts():
                        text.set_color(FG_COLOR)
                
                # Update all existing lines to use theme-appropriate colors
                lines = ax_plot.get_lines()
                for i, line in enumerate(lines):
                    if i == 0:
                        line.set_color(ACCENT_BLUE)
                    elif i == 1:
                        line.set_color(ACCENT_ORANGE)
                    elif i == 2:
                        line.set_color(ACCENT_GREEN)
                    else:
                        line.set_color(ACCENT_PURPLE)
                
                # CRITICAL FIX: Update theta_line and psi_line if they exist (for angle plots)
                try:
                    if theta_line is not None:
                        theta_line.set_color(ACCENT_BLUE)
                    if psi_line is not None:
                        psi_line.set_color(ACCENT_ORANGE)
                except NameError:
                    # theta_line and psi_line not defined in this scope
                    pass
            
            # CRITICAL: Force comprehensive canvas widget background updates
            root.update_idletasks()  # Process pending updates first
            
            if 'canvas_anim' in globals() and canvas_anim:
                # Update the tkinter canvas background to match theme
                canvas_widget = canvas_anim.get_tk_widget()
                canvas_widget.configure(bg=DARK_BG, highlightbackground=DARK_BG, highlightcolor=DARK_BG)
                # Also update ALL parent frames up the hierarchy
                try:
                    parent = canvas_widget.master
                    while parent and parent != root:
                        try:
                            parent.configure(background=DARK_BG)
                        except:
                            pass
                        parent = getattr(parent, 'master', None)
                except:
                    pass
                canvas_anim.draw_idle()
                
            if 'canvas_plot' in globals() and canvas_plot:
                # CRITICAL FIX: Update the angle graph canvas background to match theme
                canvas_widget = canvas_plot.get_tk_widget()
                canvas_widget.configure(bg=DARK_BG, highlightbackground=DARK_BG, highlightcolor=DARK_BG)
                # Also update ALL parent frames up the hierarchy
                try:
                    parent = canvas_widget.master
                    while parent and parent != root:
                        try:
                            parent.configure(background=DARK_BG)
                        except:
                            pass
                        parent = getattr(parent, 'master', None)
                except:
                    pass
                canvas_plot.draw_idle()
                
        except Exception as e:
            print(f"Theme update error: {e}")

    def refresh_all_labelframe_themes():
        """Force refresh all LabelFrame widgets to apply current theme."""
        try:
            def update_labelframes_recursive(widget):
                """Recursively update all LabelFrame widgets."""
                if isinstance(widget, ttk.LabelFrame):
                    try:
                        # Get current style and text
                        current_style = widget.cget('style') if hasattr(widget, 'cget') else ''
                        current_text = widget.cget('text') if hasattr(widget, 'cget') else ''
                        
                        # Determine appropriate style based on context and text content
                        # If it's in a darker container (like sidebar), use Black.TLabelFrame
                        # Settings frames should use regular TLabelFrame style
                        parent = widget.master
                        use_black_style = False
                        
                        # Check text content to determine style
                        if current_text:
                            # Settings frames should use regular style
                            if any(text in current_text for text in ["Simulation Settings", "Appearance Settings"]):
                                use_black_style = False
                            # Sidebar frames (Parameters, Simulation) should use black style
                            elif any(text in current_text for text in ["Pendulum Parameters", "🎮 Simulation"]):
                                use_black_style = True
                            # Visualization options in main area should use regular style
                            elif "Visualization Options" in current_text:
                                use_black_style = False
                            # Check if the current style suggests it should be black
                            elif 'Black' in current_style:
                                use_black_style = True
                        
                        # Also check parent background as fallback
                        if not current_text and hasattr(parent, 'cget'):
                            try:
                                parent_bg = parent.cget('background')
                                if parent_bg and (parent_bg == DARKER_BG or 'dark' in str(parent_bg).lower()):
                                    use_black_style = True
                            except:
                                pass
                        
                        # Apply appropriate style
                        try:
                            if use_black_style:
                                widget.configure(style="Black.TLabelframe")
                            else:
                                widget.configure(style="TLabelframe")
                        except tk.TclError:
                            # If style fails, just update colors directly
                            try:
                                widget.configure(foreground=FG_COLOR)
                            except:
                                pass
                        
                        # Ensure text is preserved and styled
                        if current_text:
                            widget.configure(text=current_text)
                        
                        # Force update
                        widget.update_idletasks()
                    except Exception as e:
                        print(f"Error updating LabelFrame: {e}")
                
                # Recursively process children
                try:
                    for child in widget.winfo_children():
                        update_labelframes_recursive(child)
                except Exception:
                    pass
            
            # Start from root and update all LabelFrames
            update_labelframes_recursive(root)
            
        except Exception as e:
            print(f"Error refreshing LabelFrame themes: {e}")
    
    current_theme_var.trace_add("write", on_theme_change)
    # Start with a window sized relative to the display and maximize when possible.
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    width = int(screen_width * 0.8)
    height = int(screen_height * 0.8)
    root.geometry(f"{width}x{height}")
    try:
        root.state("zoomed")
    except tk.TclError:
        pass
    # Ensure a sensible minimum size so controls and plots do not overlap on
    # common displays.
    root.minsize(1280, 800)

    # Enhanced keyboard shortcuts for better user experience
    def setup_keyboard_shortcuts():
        """Set up comprehensive keyboard shortcuts."""
        shortcuts = {
            '<space>': lambda e: run_or_play() if 'run_or_play' in locals() else None,
            '<Escape>': lambda e: pause_sim() if 'pause_sim' in locals() else None,
            '<Control-r>': lambda e: reset_sim() if 'reset_sim' in locals() else None,
            '<Control-s>': lambda e: step_sim() if 'step_sim' in locals() else None,
            '<Control-q>': lambda e: root.quit(),
            '<F11>': lambda e: toggle_fullscreen(),
            '<F2>': lambda e: show_help_dialog(),
            '<Control-t>': lambda e: cycle_theme()
        }
        
        for key, func in shortcuts.items():
            root.bind(key, func)
    
    def cycle_theme():
        """Cycle through available themes."""
        themes = list(THEMES.keys())
        current = current_theme_var.get()
        current_idx = themes.index(current) if current in themes else 0
        next_idx = (current_idx + 1) % len(themes)
        current_theme_var.set(themes[next_idx])
    
    def toggle_fullscreen():
        """Toggle fullscreen mode with smooth transition."""
        try:
            current_state = root.attributes('-fullscreen')
            root.attributes('-fullscreen', not current_state)
        except tk.TclError:
            try:
                if root.state() == 'zoomed':
                    root.state('normal')
                else:
                    root.state('zoomed')
            except tk.TclError:
                pass
    
    def toggle_fullscreen():
        """Toggle fullscreen mode."""
        try:
            current_state = root.attributes('-fullscreen')
            root.attributes('-fullscreen', not current_state)
        except tk.TclError:
            try:
                if root.state() == 'zoomed':
                    root.state('normal')
                else:
                    root.state('zoomed')
            except tk.TclError:
                pass
    
    def show_help_dialog():
        """Show enhanced help dialog with comprehensive controls and animations."""
        help_text = """🔥 PhysikSim - Interactive Physics Simulator

⌨️ KEYBOARD SHORTCUTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎮 Simulation Controls:
Space          ▶ Start/Resume simulation
Escape         ⏸ Pause simulation  
Ctrl+R         ↻ Reset simulation
Ctrl+S         ⏭ Step simulation (frame by frame)
Ctrl+Q         ❌ Quit application

🎨 Interface Controls:
F11            🖥️ Toggle fullscreen mode
F2             ❓ Show this help dialog
Ctrl+T         🎨 Cycle through themes

🖱️ MOUSE CONTROLS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📐 3D Visualization:
• Left Click + Drag     🔄 Rotate 3D view (built-in matplotlib)
• Mouse Wheel          🔍 Zoom in/out
• Right Click + Drag   📐 Pan view (built-in matplotlib)
• Middle Click         🎯 Reset camera position

📊 2D Plots:
• Mouse Wheel          🔍 Zoom plot area
• Left Click + Drag    📐 Pan plot view
• Double Click         🎯 Reset zoom level

🎛️ INTERFACE NAVIGATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧭 Top Navigation Bar:
🎮 Simulation    - Select simulation type and run controls
⚙️ Parameters    - Adjust pendulum physics parameters  
📤 Export        - Save animations and plots
🔧 Settings      - Configure appearance and simulation

💡 QUICK TIPS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 Getting Started:
• Use preset configurations for quick setup
• Adjust parameters with sliders or direct input
• Enable trajectory visualization for 3D pendulums
• Change animation speed with speed controls

⚡ Performance Tips:
• Lower trail length for smoother animations
• Use medium quality for better performance
• Disable force vectors if not needed
• Reset camera if 3D view becomes disoriented

🎨 Visualization Options:
• Toggle trajectory to see pendulum paths
• Enable force vectors to see physical forces
• Use different themes for better visibility
• Export high-quality SVG/PNG images

📊 Analysis Features:
• Switch between angle, velocity, energy plots
• Use angle view to compare θ and ψ motions
• Energy plots show conservation principles
• Step through simulations frame by frame

🔬 PHYSICS PARAMETERS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

L    📏 Pendulum length (affects period)
θ₀   📐 Initial polar angle (amplitude)
ψ₀   🧭 Initial azimuth angle (3D direction)  
g    🌍 Gravitational acceleration
h    ⏱️ Time step (smaller = more accurate)
b    💨 Air resistance coefficient
s    ⚡ Animation speed multiplier

Made with ❤️ for physics education and simulation"""
        
        # Create larger help window with better responsive sizing
        help_window = tk.Toplevel(root)
        help_window.title("PhysikSim - Help & Controls")
        
        # Make window larger and more responsive
        screen_width = help_window.winfo_screenwidth()
        screen_height = help_window.winfo_screenheight()
        window_width = min(900, int(screen_width * 0.6))  # Larger width
        window_height = min(700, int(screen_height * 0.7))  # Larger height
        
        help_window.geometry(f"{window_width}x{window_height}")
        help_window.configure(bg=DARK_BG)
        help_window.transient(root)
        help_window.grab_set()
        help_window.resizable(True, True)
        
        # Center the help window on screen
        help_window.update_idletasks()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        help_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Modern window icon (if available)
        try:
            help_window.iconbitmap("icon.ico")  # Add icon if you have one
        except:
            pass
        
        # Main container with padding
        main_frame = ttk.Frame(help_window, style="Card.TFrame")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title section with enhanced styling
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ttk.Label(
            title_frame,
            text="PhysikSim Help & Controls",
            font=("Inter", 18, "bold"),
            foreground=ACCENT_BLUE
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Complete guide to keyboard shortcuts, mouse controls, and features",
            font=("Inter", 11),
            foreground=TEXT_MUTED
        )
        subtitle_label.pack(pady=(6, 0))
        
        # Scrollable text area with modern styling
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Create scrollable text widget
        text_widget = tk.Text(
            text_frame,
            bg=ACCENT_BG,
            fg=FG_COLOR,
            font=("Consolas", 10),  # Slightly larger font
            wrap=tk.WORD,
            padx=25,
            pady=25,
            relief="flat",
            borderwidth=0,
            selectbackground=ACCENT_BLUE,
            selectforeground="white",
            insertbackground=FG_COLOR,
            state=tk.NORMAL
        )
        
        # Scrollbar for text widget
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Pack text widget and scrollbar
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Insert help text with color formatting
        text_widget.insert(tk.END, help_text)
        
        # Configure text tags for syntax highlighting
        text_widget.tag_configure("header", foreground=ACCENT_BLUE, font=("Inter", 12, "bold"))
        text_widget.tag_configure("shortcut", foreground=ACCENT_GREEN, font=("Consolas", 10, "bold"))
        text_widget.tag_configure("description", foreground=FG_COLOR)
        text_widget.tag_configure("separator", foreground=TEXT_MUTED)
        text_widget.tag_configure("emoji", font=("Segoe UI Emoji", 11))
        
        # Apply formatting to specific text patterns
        content = text_widget.get("1.0", tk.END)
        lines = content.split('\n')
        
        text_widget.delete("1.0", tk.END)
        
        for line in lines:
            start_pos = text_widget.index(tk.INSERT)
            
            if line.strip().startswith('━'):
                text_widget.insert(tk.END, line + '\n', "separator")
            elif any(x in line for x in ['KEYBOARD SHORTCUTS:', 'MOUSE CONTROLS:', 'INTERFACE NAVIGATION:', 'QUICK TIPS:', 'PHYSICS PARAMETERS:']):
                text_widget.insert(tk.END, line + '\n', "header")
            elif any(x in line for x in ['Space', 'Escape', 'Ctrl+', 'F11', 'F1', 'F2', 'Left Click', 'Mouse Wheel', 'Right Click', 'Middle Click', 'Double Click']):
                # Split line to highlight shortcuts
                parts = line.split('  ', 1)  # Split on double space
                if len(parts) == 2:
                    text_widget.insert(tk.END, parts[0], "shortcut")
                    text_widget.insert(tk.END, '  ' + parts[1] + '\n', "description")
                else:
                    text_widget.insert(tk.END, line + '\n', "description")
            else:
                text_widget.insert(tk.END, line + '\n', "description")
        
        # Make text read-only
        text_widget.config(state=tk.DISABLED)
        
        # Enhanced button frame with better wrapping
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Configure grid for better button wrapping
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        button_frame.columnconfigure(3, weight=1)
        
        # Modern buttons with different styles - better arranged
        def close_help():
            help_window.destroy()
        
        def open_settings():
            help_window.destroy()
            try:
                show_settings()  # Call your settings function if it exists
            except NameError:
                update_status("Settings not available", 1)
        
        def reset_to_defaults():
            help_window.destroy()
            try:
                reset_sim()  # Call your reset function if it exists
            except NameError:
                update_status("Reset function not available", 1)
        
        def test_mouse_controls():
            """Test function to demonstrate mouse controls."""
            help_window.destroy()
            update_status("🖱️ Mouse controls active - Try zooming and panning!", 0)
            root.after(4000, lambda: update_status("🚀 Ready", 0))
        
        # Row 1 - Action buttons
        settings_btn = create_animated_button(
            button_frame,
            text="🔧 Settings",
            command=open_settings,
            style="Modern.TButton"
        )
        settings_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        reset_btn = create_animated_button(
            button_frame,
            text="↻ Reset",
            command=reset_to_defaults,
            style="Warning.TButton"
        )
        reset_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        test_btn = create_animated_button(
            button_frame,
            text="🖱️ Test Controls",
            command=test_mouse_controls,
            style="Purple.TButton"
        )
        test_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        copy_btn = create_animated_button(
            button_frame,
            text="📋 Copy",
            command=lambda: help_window.clipboard_clear() or help_window.clipboard_append(
                "PhysikSim Shortcuts:\nSpace=Play/Pause, Escape=Stop, Ctrl+R=Reset, F11=Fullscreen, F1=Help\nMouse: Wheel=Zoom, Drag=Pan, Double-click=Reset"
            ),
            style="Purple.TButton"
        )
        copy_btn.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        
        # Row 2 - Close button spanning full width
        close_btn = create_animated_button(
            button_frame,
            text="✅ Got it! Close Help",
            command=close_help,
            style="Success.TButton"
        )
        close_btn.grid(row=1, column=0, columnspan=4, padx=5, pady=(10, 5), sticky="ew")
        
        # Keyboard shortcuts for the help dialog itself
        def handle_help_keypress(event):
            if event.keysym == 'Escape':
                close_help()
            elif event.state & 0x4 and event.keysym == 'w':  # Ctrl+W
                close_help()
            elif event.keysym == 'F1':
                close_help()
            elif event.keysym == 'Return':
                close_help()
        
        help_window.bind("<KeyPress>", handle_help_keypress)
        help_window.focus_set()
        
        # Add fade-in effect
        create_fade_in_effect(help_window)
        
        # Status update
        update_status("📖 Help dialog opened - Press Escape to close", 0)
        root.after(3000, lambda: update_status("🚀 Ready", 0))

    # Grid layout: row 0 holds the top bar, row 1 is split into
    # a sidebar (column 0) and the main display area (column 1), and row 2 holds the status bar.
    root.rowconfigure(0, weight=0)
    root.rowconfigure(1, weight=1)
    root.rowconfigure(2, weight=0)
    root.columnconfigure(0, weight=0)
    root.columnconfigure(1, weight=1)

    # Enhanced status bar with animations
    status_frame = ttk.Frame(root)
    status_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=2)
    
    status_label = ttk.Label(status_frame, text="🚀 Ready", font=("Inter", 9))
    status_label.pack(side=tk.LEFT, padx=8)
    
    # Animated progress bar
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(
        status_frame, 
        variable=progress_var, 
        mode='determinate',
        length=200
    )
    progress_bar.pack(side=tk.RIGHT, padx=8)
    
    def update_status(message: str, progress: float = 0, animate: bool = True):
        """Update status with optional animation."""
        status_label.config(text=message)
        if animate:
            animate_progress(progress)
        else:
            progress_var.set(progress)
        root.update_idletasks()
    
    def animate_progress(target_progress: float, duration: int = 500):
        """Smoothly animate progress bar."""
        start_progress = progress_var.get()
        start_time = time.time()
        
        def update():
            elapsed = (time.time() - start_time) * 1000
            progress = min(elapsed / duration, 1.0)
            
            eased_progress = ease_in_out_cubic(progress)
            current_value = start_progress + (target_progress - start_progress) * eased_progress
            progress_var.set(current_value)
            
            if progress < 1.0:
                root.after(16, update)
        
        update()

    # Automatically scale fonts with window size.
    default_fonts = [tkfont.nametofont(name)
                     for name in ("TkDefaultFont", "TkTextFont",
                                 "TkMenuFont", "TkHeadingFont")]
    slider_font = tkfont.Font(size=12)
    desc_font = tkfont.Font(size=10)
    inputs: list[ttk.Entry] = []
    desc_label: ttk.Label | None = None
    run_play_btn = None
    pendulum_export_button = None
    diagram_export_button = None
    MAX_BUTTON_WIDTH = 12
    # ========================================================================
    # GLOBAL SIMULATION STATE VARIABLES
    # ========================================================================
    
    # Font size tracking for responsive UI scaling
    last_font_size = None  # Tracks last applied general font size
    last_slider_font_size = None  # Tracks last applied slider/input font size
    last_desc_font_size = None  # Tracks last applied description font size
    
    # Simulation state management
    screenshot_taken = False  # Flag to prevent duplicate screenshots
    pendulum_data: dict[str, np.ndarray] | None = None  # Stores simulation results
    running = False  # Controls animation playback state
    has_run = False  # Tracks if simulation has been executed at least once
    
    # ========================================================================
    # RESPONSIVE UI FUNCTIONS
    # ========================================================================
    
    def resize_ui(event):
        """
        Dynamically adjust font sizes and layout based on window dimensions.
        
        This function ensures the UI remains readable and proportional
        when the user resizes the application window.
        
        Args:
            event: Tkinter event containing resize information
        """
        nonlocal last_font_size, last_slider_font_size, last_desc_font_size
        # Only handle resize events triggered by the root window itself
        if event.widget is not root:
            return
        
        # Calculate appropriate font size based on window dimensions
        size = max(8, int(min(event.width, event.height) / 50))

        # Update general fonts if size changed
        if size != last_font_size:
            for f in default_fonts:
                f.configure(size=size)
            last_font_size = size

        # Update description fonts (slightly smaller)
        desc_size = max(8, size - 2)
        if desc_size != last_desc_font_size:
            desc_font.configure(size=desc_size)
            last_desc_font_size = desc_size

        # Update input/slider fonts (larger for better readability)
        entry_size = min(int(size * 1.4), 32)
        if entry_size != last_slider_font_size:
            slider_font.configure(size=entry_size)
            for e in inputs:
                e.configure(font=slider_font)
            last_slider_font_size = entry_size

        # CRITICAL FIX: Update description wrapping based on current sidebar state
        if desc_label is not None:
            # Check if sidebar is currently open by checking its width
            current_sidebar_width = sidebar.winfo_width() if sidebar.winfo_exists() else 0
            if current_sidebar_width > 0:
                # Sidebar is open, use its width for wrapping calculation
                update_description_wrapping(current_sidebar_width)
            else:
                # Sidebar is closed, use a default reasonable width
                sidebar_width = int(root.winfo_width() * 0.3)
                desc_label.configure(wraplength=max(200, sidebar_width - 40))
        
        # Update button widths if they exist
        if run_play_btn is not None:
            btn_width = min(MAX_BUTTON_WIDTH, max(1, event.width // 30))
            if pendulum_export_button is not None:
                pendulum_export_button.configure(width=btn_width)
            if diagram_export_button is not None:
                diagram_export_button.configure(width=btn_width)


    root.bind("<Configure>", resize_ui)

    def auto_screenshot():
        """Only triggers SVG export for 3D pendulum, no Windows screenshots."""
        nonlocal screenshot_taken
        if not screenshot_taken and option_var.get() == "3D Pendulum":
            screenshot_taken = True
            # Only export SVG projections for 3D pendulum with actual trajectory data
            if pendulum_data is not None:
                trajectory_data = {
                    'x': pendulum_data['x'],
                    'y': pendulum_data['y'], 
                    'z': pendulum_data['z']
                }
                export_projections(trajectory_data=trajectory_data)
            else:
                # Fallback to parameters if no trajectory data available
                params = dict(
                    L=l_var.get(),
                    theta0=np.radians(phi_var.get()),
                    phi0=np.radians(psi_var.get()),
                    phi_dot0=np.radians(psi_dot_var.get()),
                    g=g_var.get(),
                    h=h_var.get(),
                    t_final=30.0,
                    air_resistance=drag_var.get(),
                    force_x=force_x_var.get(),
                    force_y=force_y_var.get(),
                    force_z=force_z_var.get(),
                )
                export_projections(**params)

    def export_pendulum():
        selection = option_var.get()
        if selection == "3D Pendulum":
            file_path = filedialog.asksaveasfilename(
                defaultextension=".svg",
                filetypes=[("SVG files", "*.svg")],
                title="Pendel exportieren",
            )
            if not file_path:
                return
            base, _ = os.path.splitext(file_path)
            
            # Use actual trajectory data if available (includes impulses)
            if pendulum_data is not None:
                trajectory_data = {
                    'x': pendulum_data['x'],
                    'y': pendulum_data['y'],
                    'z': pendulum_data['z']
                }
                export_projections(
                    out_floor=base + "_floor.svg",
                    out_wall_yz=base + "_wall_yz.svg",
                    out_wall_xz=base + "_wall_xz.svg",
                    trajectory_data=trajectory_data
                )
            else:
                # Fallback to fresh simulation if no trajectory data
                params = dict(
                    L=l_var.get(),
                    theta0=np.radians(phi_var.get()),
                    phi0=np.radians(psi_var.get()),
                    phi_dot0=np.radians(psi_dot_var.get()),
                    g=g_var.get(),
                    h=h_var.get(),
                    t_final=30.0,
                    air_resistance=drag_var.get(),
                    force_x=force_x_var.get(),
                    force_y=force_y_var.get(),
                    force_z=force_z_var.get(),
                )
                export_projections(
                    out_floor=base + "_floor.svg",
                    out_wall_yz=base + "_wall_yz.svg",
                    out_wall_xz=base + "_wall_xz.svg",
                    **params,
                )
        else:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("SVG files", "*.svg")],
                title="Pendel exportieren",
            )
            if not file_path:
                return
            fig_anim.savefig(file_path, facecolor=fig_anim.get_facecolor())

    def export_plot():
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("SVG files", "*.svg")],
            title="Diagramm exportieren",
        )
        if not file_path:
            return
        fig_plot.savefig(file_path, facecolor=fig_plot.get_facecolor())

    def apply_impulse():
        """Apply an impulse to the running 3D pendulum simulation with enhanced error handling."""
        try:
            # Enhanced validation checks
            if option_var.get() != "3D Pendulum":
                update_status("⚠️ Impulse only works during 3D pendulum simulation", 0)
                return
            
            if pendulum_data is None:
                update_status("⚠️ No simulation data available - run simulation first", 0)
                return
                
            if not running:
                update_status("⚠️ Simulation must be running to apply impulse", 0)
                return
            
            frame_key = pendulum_data.get("frame")
            if frame_key is None:
                update_status("⚠️ No active simulation frame to apply impulse", 0)
                return

            frame = int(frame_key)
            t = pendulum_data["t"]
            
            # Enhanced bounds checking
            if frame <= 0:
                update_status("⚠️ Cannot apply impulse at simulation start", 0)
                return
                
            if frame >= len(t) - 10:  # Leave buffer at end
                update_status("⚠️ Cannot apply impulse near end of simulation", 0)
                return

            # Validate impulse values
            fx = force_x_var.get()
            fy = force_y_var.get()
            fz = force_z_var.get()
            
            # Check for reasonable impulse magnitudes
            max_impulse = 50.0  # Reasonable upper limit
            if abs(fx) > max_impulse or abs(fy) > max_impulse or abs(fz) > max_impulse:
                update_status(f"⚠️ Impulse too large (max ±{max_impulse})", 0)
                return
            
            # Check if impulse is too small to matter
            min_impulse = 0.001
            if abs(fx) < min_impulse and abs(fy) < min_impulse and abs(fz) < min_impulse:
                update_status("⚠️ Impulse too small to have effect", 0)
                return

            # Get current simulation parameters with validation
            L_val = max(0.1, l_var.get())  # Ensure positive length
            g_val = max(0.1, g_var.get())  # Ensure positive gravity
            h = max(0.001, min(0.1, h_var.get()))  # Clamp time step
            drag_val = max(0.0, min(1.0, drag_var.get()))  # Clamp drag
            
            # Get current state at the frame where impulse is applied
            theta = pendulum_data["Angle"]
            psi = pendulum_data["Psi"]
            theta_dot = pendulum_data["Angular velocity"]
            phi_dot = pendulum_data["phi_dot"]
            
            # Validate state arrays
            required_keys = ["Angle", "Psi", "Angular velocity", "phi_dot"]
            for key in required_keys:
                if key not in pendulum_data:
                    update_status(f"⚠️ Missing simulation data: {key}", 0)
                    return
                if len(pendulum_data[key]) <= frame:
                    update_status(f"⚠️ Invalid frame index for {key}", 0)
                    return
            
            # Calculate remaining simulation time with safety margin
            remaining_frames = len(t) - frame - 5  # Leave 5 frame buffer
            if remaining_frames <= 0:
                update_status("⚠️ Not enough simulation time remaining", 0)
                return
                
            t_final = max(0.1, remaining_frames * h)  # Ensure minimum simulation time

            try:
                update_status(f"🚀 Applying impulse at frame {frame}...", 50, True)
                
                import pendulum3d as mod
                
                # Validate initial conditions
                theta_0 = theta[frame]
                psi_0 = psi[frame]
                theta_dot_0 = theta_dot[frame]
                phi_dot_0 = phi_dot[frame]
                
                # Check for NaN or infinite values
                initial_values = [theta_0, psi_0, theta_dot_0, phi_dot_0]
                if any(not np.isfinite(val) for val in initial_values):
                    update_status("⚠️ Invalid simulation state - cannot apply impulse", 0)
                    return
                
                # Check for extreme values that might cause instability
                if abs(theta_0) > np.pi or abs(psi_0) > 2*np.pi:
                    update_status("⚠️ Extreme angle values - impulse may cause instability", 0)
                    return
                
                if abs(theta_dot_0) > 100 or abs(phi_dot_0) > 100:
                    update_status("⚠️ Extreme velocity values - impulse may cause instability", 0)
                    return
                
                # Run simulation from current point with applied impulse
                (
                    t_new,
                    theta_new,
                    psi_new,
                    theta_dot_new,
                    phi_dot_new,
                    energy_new,
                ) = mod.run(
                    L=L_val,
                    theta0=theta_0,
                    phi0=psi_0,
                    theta_dot0=theta_dot_0,
                    phi_dot0=phi_dot_0,
                    g=g_val,
                    h=h,
                    air_resistance=drag_val,
                    force_x=fx,
                    force_y=fy,
                    force_z=fz,
                    t_final=t_final,
                    plot=False,
                )

                # Validate simulation results
                if len(t_new) == 0:
                    update_status("⚠️ Simulation failed - no data returned", 0)
                    return
                    
                # Check for NaN or infinite values in results
                arrays_to_check = [theta_new, psi_new, theta_dot_new, phi_dot_new, energy_new]
                for arr in arrays_to_check:
                    if np.any(~np.isfinite(arr)):
                        update_status("⚠️ Simulation produced invalid values", 0)
                        return

                # CRITICAL FIX: Robust array size handling
                expected_length = len(t) - frame
                actual_length = len(t_new)
                
                # Determine the safe update length
                safe_length = min(expected_length, actual_length, remaining_frames)
                
                if safe_length <= 0:
                    update_status("⚠️ No data to update after impulse", 0)
                    return
                
                # Truncate or pad arrays safely
                def safe_resize_array(arr, target_length):
                    """Safely resize array to target length."""
                    if len(arr) == target_length:
                        return arr
                    elif len(arr) > target_length:
                        return arr[:target_length]
                    else:
                        # Pad with last value
                        last_val = arr[-1] if len(arr) > 0 else 0
                        return np.pad(arr, (0, target_length - len(arr)), 'constant', constant_values=last_val)
                
                # Resize all arrays to safe length
                theta_new = safe_resize_array(theta_new, safe_length)
                psi_new = safe_resize_array(psi_new, safe_length)
                theta_dot_new = safe_resize_array(theta_dot_new, safe_length)
                phi_dot_new = safe_resize_array(phi_dot_new, safe_length)
                energy_new = safe_resize_array(energy_new, safe_length)

                # Apply azimuth wrapping to prevent discontinuities
                psi_new_wrapped = ((psi_new + np.pi) % (2 * np.pi)) - np.pi

                # Recalculate dependent variables with error checking
                try:
                    x_new = L_val * np.sin(theta_new) * np.cos(psi_new)
                    y_new = L_val * np.sin(theta_new) * np.sin(psi_new)
                    z_new = -L_val * np.cos(theta_new)
                    
                    vx_new = L_val * (
                        theta_dot_new * np.cos(theta_new) * np.cos(psi_new)
                        - phi_dot_new * np.sin(theta_new) * np.sin(psi_new)
                    )
                    vy_new = L_val * (
                        theta_dot_new * np.cos(theta_new) * np.sin(psi_new)
                        + phi_dot_new * np.sin(theta_new) * np.cos(psi_new)
                    )
                    vz_new = -L_val * theta_dot_new * np.sin(theta_new)

                    kinetic_new = 0.5 * (L_val ** 2) * (
                        theta_dot_new ** 2 + (np.sin(theta_new) ** 2) * phi_dot_new ** 2
                    )
                    potential_new = g_val * L_val * (1 - np.cos(theta_new))
                    acceleration_new = (
                        np.sin(theta_new) * np.cos(theta_new) * phi_dot_new ** 2
                        - (g_val / L_val) * np.sin(theta_new)
                        - drag_val * theta_dot_new * np.abs(theta_dot_new)
                    )
                except Exception as calc_error:
                    update_status(f"⚠️ Error calculating derived quantities: {str(calc_error)}", 0)
                    return

                # CRITICAL FIX: Safe array updates with bounds checking
                try:
                    # Define safe update slice
                    update_end = min(frame + safe_length, len(theta))
                    actual_update_length = update_end - frame
                    
                    if actual_update_length <= 0:
                        update_status("⚠️ No valid range to update", 0)
                        return
                    
                    # Update arrays with proper bounds
                    update_slice = slice(frame, update_end)
                    data_slice = slice(0, actual_update_length)
                    
                    # Safely update all arrays
                    theta[update_slice] = theta_new[data_slice]
                    psi[update_slice] = psi_new_wrapped[data_slice]
                    theta_dot[update_slice] = theta_dot_new[data_slice]
                    phi_dot[update_slice] = phi_dot_new[data_slice]
                    pendulum_data["Energy"][update_slice] = energy_new[data_slice]
                    pendulum_data["Kinetic"][update_slice] = kinetic_new[data_slice]
                    pendulum_data["Potential"][update_slice] = potential_new[data_slice]
                    pendulum_data["Angular acceleration"][update_slice] = acceleration_new[data_slice]
                    
                    # Update position and velocity arrays
                    pendulum_data["x"][update_slice] = x_new[data_slice]
                    pendulum_data["y"][update_slice] = y_new[data_slice]
                    pendulum_data["z"][update_slice] = z_new[data_slice]
                    pendulum_data["vx"][update_slice] = vx_new[data_slice]
                    pendulum_data["vy"][update_slice] = vy_new[data_slice]
                    pendulum_data["vz"][update_slice] = vz_new[data_slice]

                except Exception as update_error:
                    update_status(f"⚠️ Error updating simulation data: {str(update_error)}", 0)
                    return

                # Reset impulse forces to zero after successful application
                force_x_var.set(0.0)
                force_y_var.set(0.0)
                force_z_var.set(0.0)
                
                update_status(f"✅ Impulse applied successfully at frame {frame}", 100, True)
                root.after(2000, lambda: update_status("🚀 Ready", 0))
                
            except ImportError:
                update_status("❌ pendulum3d module not found", 0)
            except Exception as sim_error:
                update_status(f"❌ Simulation error: {str(sim_error)[:50]}...", 0)
                print(f"Detailed simulation error: {sim_error}")
                
        except Exception as e:
            update_status(f"❌ Impulse application failed: {str(e)[:50]}...", 0)
            print(f"Detailed impulse error: {e}")
            
            # Reset impulse forces on any error
            try:
                force_x_var.set(0.0)
                force_y_var.set(0.0)
                force_z_var.set(0.0)
            except:
                pass

    # Dynamic options list based on RK4 test setting
    def get_simulation_options():
        """Get simulation options based on current settings."""
        base_options = ["Pendulum", "3D Pendulum"]
        if show_rk4_tests_var.get():
            return ["RK4 Test 1", "RK4 Test 2", "RK4 Test 3"] + base_options
        return base_options

    # Initialize with base options
    option_var = tk.StringVar(value="Pendulum")

    # Top bar with main navigation buttons
    top_bar = ttk.Frame(root, padding=PADDING)
    top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
    top_bar.columnconfigure(0, weight=1)
    top_bar.columnconfigure(1, weight=1)
    top_bar.columnconfigure(2, weight=1)

    # Sidebar that slides in from the left
    sidebar = ttk.Frame(root, padding=PADDING)
    # Use a reasonable default height initially, will be updated when animating
    sidebar.place(x=0, y=60, width=0, height=root.winfo_screenheight() - 120)

    sidebar_container = ttk.Frame(sidebar)
    sidebar_container.pack(fill="both", expand=True)

    close_btn = ttk.Button(sidebar, text="✕ Close", command=lambda: hide_sidebar(), style="Warning.TButton")
    close_btn.pack(anchor="ne", padx=PADDING, pady=PADDING)

    desc_label = ttk.Label(sidebar, text="", justify="left", font=desc_font, wraplength=400)
    desc_label.pack(side="bottom", fill="x", padx=PADDING, pady=PADDING)

    sim_controls = ttk.Frame(sidebar_container)

    # Scrollable parameters area: remove extra padding so content sits flush at top
    params_viz_container = ttk.Frame(sidebar_container, padding=0)
    params_viz_container.columnconfigure(0, weight=1)
    params_viz_container.rowconfigure(0, weight=1)

    params_viz_frame = ttk.Frame(params_viz_container, padding=0)
    params_viz_frame.grid(row=0, column=0, sticky="nsew")
    params_viz_frame.columnconfigure(0, weight=1)
    params_viz_frame.rowconfigure(0, weight=1)

    params_viz_canvas = tk.Canvas(
        params_viz_frame, background=DARK_BG, highlightthickness=0
    )
    params_viz_scrollbar = ttk.Scrollbar(
        params_viz_frame, orient="vertical", command=params_viz_canvas.yview
    )
    params_viz_canvas.configure(yscrollcommand=params_viz_scrollbar.set)

    params_viz_canvas.grid(row=0, column=0, sticky="nsew")
    params_viz_scrollbar.grid(row=0, column=1, sticky="ns")

    params_viz = ttk.Frame(params_viz_canvas, padding=0)
    params_viz.columnconfigure(0, weight=1)
    _params_viz_window = params_viz_canvas.create_window(
        (0, 0), window=params_viz, anchor="nw"
    )
    # Ensure the scroll position starts at the very top
    root.after(0, lambda: params_viz_canvas.yview_moveto(0))

    def _configure_params_viz(event: tk.Event) -> None:
        params_viz_canvas.configure(scrollregion=params_viz_canvas.bbox("all"))

    params_viz.bind("<Configure>", _configure_params_viz)

    def _on_canvas_configure(event: tk.Event) -> None:
        params_viz_canvas.itemconfig(_params_viz_window, width=event.width)
        # Keep scrollregion in sync with current content size
        params_viz_canvas.configure(scrollregion=params_viz_canvas.bbox("all"))

    params_viz_canvas.bind("<Configure>", _on_canvas_configure)

    def _on_mousewheel(event: tk.Event) -> str | None:
        # Normalize scrolling across platforms and ensure direction is correct.
        # Windows/macOS provide event.delta; many Linux builds use Button-4/5.
        if hasattr(event, "delta") and event.delta != 0:
            direction = -1 if event.delta > 0 else 1  # up: negative scroll (towards 0)
            params_viz_canvas.yview_scroll(direction, "units")
        else:
            direction = -1 if getattr(event, "num", 0) == 4 else 1
            params_viz_canvas.yview_scroll(direction, "units")
        return "break"

    def _bind_mousewheel(event: tk.Event) -> None:
        # Bind only on the canvas and focus it to receive wheel events on Windows/macOS.
        params_viz_canvas.focus_set()
        params_viz_canvas.bind("<MouseWheel>", _on_mousewheel)
        params_viz_canvas.bind("<Button-4>", _on_mousewheel)
        params_viz_canvas.bind("<Button-5>", _on_mousewheel)

    def _unbind_mousewheel(event: tk.Event) -> None:
        params_viz_canvas.unbind("<MouseWheel>")
        params_viz_canvas.unbind("<Button-4>")
        params_viz_canvas.unbind("<Button-5>")

    params_viz_canvas.bind("<Enter>", _bind_mousewheel)
    params_viz_canvas.bind("<Leave>", _unbind_mousewheel)

    export_controls = ttk.Frame(sidebar_container)
    export_controls.columnconfigure(0, weight=1)

    # Create settings controls with variables passed
    settings_vars = {
        't_end': t_end_var,
        'current_theme': current_theme_var,
        'trail_length': trail_length_var,
        'animation_quality': animation_quality_var,
        'grid_visible': grid_visible_var,
        'show_fps': show_fps_var,
        'show_rk4_tests': show_rk4_tests_var
    }
    
    settings_controls = create_settings_tab(sidebar_container, settings_vars, update_status, configure_theme, root)

    def show_sim():
        show_sidebar(sim_controls)

    def show_params():
        show_sidebar(params_viz_container)
        # Reset scroll to top each time the Parameters panel is shown
        params_viz_canvas.update_idletasks()
        params_viz_canvas.yview_moveto(0)

    def show_export():
        show_sidebar(export_controls)
    
    def show_settings():
        show_sidebar(settings_controls)

    # Enhanced top bar buttons with modern styling
    sim_btn = create_animated_button(top_bar, text="🎮 Simulation", command=show_sim, style="Modern.TButton")
    sim_btn.grid(row=0, column=0, padx=PADDING, pady=PADDING, sticky="ew")
    
    params_btn = create_animated_button(top_bar, text="⚙️ Parameters", command=show_params, style="Modern.TButton")
    params_btn.grid(row=0, column=1, padx=PADDING, pady=PADDING, sticky="ew")
    
    export_btn = create_animated_button(top_bar, text="📤 Export", command=show_export, style="Modern.TButton")
    export_btn.grid(row=0, column=2, padx=PADDING, pady=PADDING, sticky="ew")
    
    settings_btn = create_animated_button(top_bar, text="🔧 Settings", command=show_settings, style="Modern.TButton")
    settings_btn.grid(row=0, column=3, padx=PADDING, pady=PADDING, sticky="ew")

    # Update top bar column configuration for 4 buttons
    top_bar.columnconfigure(3, weight=1)

    # Variables for pendulum parameters
    l_var = tk.DoubleVar(value=1.0)
    phi_var = tk.DoubleVar(value=np.degrees(0.1))  # polar angle
    psi_var = tk.DoubleVar(value=0.0)  # azimuth angle for 3D
    psi_dot_var = tk.DoubleVar(value=0.0)  # azimuth velocity for 3D
    g_var = tk.DoubleVar(value=9.81)
    h_var = tk.DoubleVar(value=0.01)
    drag_var = tk.DoubleVar(value=0.0)
    speed_var = tk.DoubleVar(value=1.0)
    show_vectors_var = tk.BooleanVar(value=False)

    force_x_var = tk.DoubleVar(value=0.0)
    force_y_var = tk.DoubleVar(value=0.0)
    force_z_var = tk.DoubleVar(value=0.0)
    show_trajectory_var = tk.BooleanVar(value=False)
    show_axes_var = tk.BooleanVar(value=True)
    show_true_path_var = tk.BooleanVar(value=False)
    fps_var = tk.StringVar(value="FPS: 0")


    graph_options = ["Angle", "Angular velocity", "Angular acceleration", "Energy"]
    graph_var = tk.StringVar(value=graph_options[0])

    # ============================================================================
    # VALIDATION AND SAFETY FUNCTIONS
    # ============================================================================

    def validate_simulation_state():
        """Validate that the simulation is in a good state for impulse application."""
        if pendulum_data is None:
            return False, "No simulation data"
        
        required_keys = ["t", "Angle", "Psi", "Angular velocity", "phi_dot", "x", "y", "z"]
        for key in required_keys:
            if key not in pendulum_data:
                return False, f"Missing {key}"
            if len(pendulum_data[key]) == 0:
                return False, f"Empty {key} array"
        
        return True, "OK"

    def safe_parameter_bounds():
        """Ensure all parameters are within safe bounds."""
        try:
            # Clamp length
            l_val = l_var.get()
            if l_val < 0.1 or l_val > 10.0:
                l_var.set(max(0.1, min(10.0, l_val)))
            
            # Clamp gravity
            g_val = g_var.get()
            if g_val < 0.1 or g_val > 20.0:
                g_var.set(max(0.1, min(20.0, g_val)))
            
            # Clamp time step
            h_val = h_var.get()
            if h_val < 0.001 or h_val > 1:
                h_var.set(max(0.001, min(1.0, h_val)))
            
            # Clamp drag
            drag_val = drag_var.get()
            if drag_val < 0.0 or drag_val > 1.0:
                drag_var.set(max(0.0, min(1.0, drag_val)))
            
            return True
        except:
            return False

    def validate_impulse_values():
        """Validate impulse values before application."""
        try:
            fx = force_x_var.get()
            fy = force_y_var.get()
            fz = force_z_var.get()
            
            # Check for reasonable bounds
            max_impulse = 20.0  # More conservative limit
            if any(abs(f) > max_impulse for f in [fx, fy, fz]):
                return False, f"Impulse too large (max ±{max_impulse})"
            
            # Check for minimum effect
            min_impulse = 0.01
            if all(abs(f) < min_impulse for f in [fx, fy, fz]):
                return False, "Impulse too small"
            
            # Check for NaN or infinite
            if any(not np.isfinite(f) for f in [fx, fy, fz]):
                return False, "Invalid impulse values"
            
            return True, "OK"
        except:
            return False, "Error reading impulse values"

    # Add automatic parameter validation
    def auto_validate_parameters(*args):
        """Automatically validate parameters when they change."""
        try:
            safe_parameter_bounds()
        except:
            pass

    # Enhanced parameter validation and smart suggestions
    def validate_parameter(var: tk.DoubleVar, min_val: float, max_val: float, name: str) -> bool:
        """Validate parameter ranges and provide smart suggestions."""
        try:
            value = var.get()
            if not (min_val <= value <= max_val):
                update_status(f"⚠ {name}: {value:.3f} outside range [{min_val}, {max_val}]", 0)
                return False
            return True
        except tk.TclError:
            update_status(f"⚠ {name}: Invalid value", 0)
            return False

    def apply_preset_config(preset_name: str):
        """Apply a preset configuration with validation."""
        if preset_name not in PRESET_CONFIGS:
            update_status(f"⚠ Unknown preset: {preset_name}", 0)
            return
        
        config = PRESET_CONFIGS[preset_name]
        update_status(f"📋 Applying preset: {preset_name}", 25)
        
        # Apply configuration with validation
        try:
            if "L" in config:
                l_var.set(config["L"])
            if "phi" in config:
                phi_var.set(config["phi"])
            if "psi" in config:
                psi_var.set(config["psi"])
            if "g" in config:
                g_var.set(config["g"])
            if "h" in config:
                h_var.set(config["h"])
            if "drag" in config:
                drag_var.set(config["drag"])
            
            update_status(f"✅ Preset '{preset_name}' applied successfully", 100)
            root.after(2000, lambda: update_status("Ready", 0))
            
        except Exception as e:
            update_status(f"❌ Error applying preset: {str(e)}", 0)

    def suggest_parameters():
        """Provide intelligent parameter suggestions based on current settings."""
        l_val = l_var.get()
        phi_val = phi_var.get()
        
        suggestions = []
        
        # Time step suggestions
        if l_val > 2.0 and h_var.get() > 0.005:
            suggestions.append("Consider smaller time step (h < 0.005) for longer pendulums")
        
        # Angle suggestions
        if phi_val > 150:
            suggestions.append("Large angles may show chaotic behavior")
        elif phi_val < 5:
            suggestions.append("Small angles approximate simple harmonic motion")
        
        # Damping suggestions
        if drag_var.get() == 0 and phi_val > 90:
            suggestions.append("Add damping (drag > 0) for realistic high-amplitude motion")
        
        if suggestions:
            suggestion_text = "💡 " + "; ".join(suggestions)
            update_status(suggestion_text, 0)
            root.after(5000, lambda: update_status("Ready", 0))

    def setup_parameter_validation():
        """Set up automatic parameter validation and suggestions."""
        # Add validation callbacks
        for var, (min_val, max_val, name) in [
            (l_var, (0.1, 10.0, "Length")),
            (phi_var, (0, 180, "Angle")),
            (g_var, (0.1, 20.0, "Gravity")),
            (h_var, (0.0001, 0.1, "Time step")),
            (drag_var, (0.0, 1.0, "Damping"))
        ]:
            var.trace_add("write", lambda *_, v=var, mn=min_val, mx=max_val, n=name: 
                         validate_parameter(v, mn, mx, n))
        
        # Add smart suggestions trigger
        phi_var.trace_add("write", lambda *_: root.after(500, suggest_parameters))
        l_var.trace_add("write", lambda *_: root.after(500, suggest_parameters))

    # Connect validation to parameter changes for safety
    l_var.trace_add("write", auto_validate_parameters)
    g_var.trace_add("write", auto_validate_parameters)
    h_var.trace_add("write", auto_validate_parameters)
    drag_var.trace_add("write", auto_validate_parameters)

    # ========== SIMULATION SELECTION UI ==========
    # Create simulation selection group inside the sidebar with proper theming
    sim_frame = ttk.LabelFrame(
        sim_controls, text="🎮 Simulation"
    )
    sim_frame.configure(style="Black.TLabelframe")  # Apply dark theme style
    sim_frame.grid(row=0, column=0, sticky="ew", padx=PADDING, pady=PADDING)
    sim_frame.columnconfigure(0, weight=1)
    
    # Create dropdown for simulation type selection with dynamic options
    def update_simulation_dropdown():
        """Update simulation dropdown options based on settings."""
        current_options = get_simulation_options()
        dropdown['values'] = current_options
        
        # If current selection is not in new options, reset to first option
        if option_var.get() not in current_options:
            option_var.set(current_options[0])
    
    dropdown = ttk.Combobox(sim_frame, textvariable=option_var, values=get_simulation_options(), state="readonly")
    dropdown.grid(row=0, column=0, padx=PADDING, pady=PADDING, sticky="ew")

    # Update dropdown when RK4 test setting changes
    def on_rk4_tests_change(*args):
        """Handle changes to RK4 tests visibility setting."""
        update_simulation_dropdown()
        update_status(f"RK4 tests {'enabled' if show_rk4_tests_var.get() else 'disabled'}")
        root.after(2000, lambda: update_status("Ready"))
    
    show_rk4_tests_var.trace_add("write", on_rk4_tests_change)

    # Note: 3D visualization controls have been moved to the visualization tab
    # for better organization and user experience
    
    # ========== SIDEBAR ANIMATION VARIABLES ==========
    # Variables for smooth sidebar width animation
    sidebar_target_width = 0
    sidebar_animation_start_time = 0
    sidebar_animation_start_width = 0

    def update_description_wrapping(sidebar_width: int) -> None:
        """Update description text wrapping based on sidebar width."""
        if desc_label is not None:
            # Calculate appropriate wrap length based on sidebar width
            # Leave margins for padding and scrollbar
            effective_width = max(200, sidebar_width - 60)  # 60px for padding and scrollbar
            desc_label.configure(wraplength=effective_width)
            desc_label.update_idletasks()

    def animate_sidebar(opening: bool) -> None:
        """Enhanced sidebar animation with smooth easing and proper layout updates."""
        nonlocal sidebar_target_width, sidebar_animation_start_time, sidebar_animation_start_width
        
        if opening and sidebar_target_width == 0:
            sidebar_target_width = int(root.winfo_width() * 0.3)
            sidebar_animation_start_time = root.tk.call('clock', 'milliseconds')
            sidebar_animation_start_width = sidebar.winfo_width()
        elif not opening and sidebar_target_width > 0:
            # Initialize closing animation
            if not hasattr(animate_sidebar, '_closing_start_time'):
                animate_sidebar._closing_start_time = root.tk.call('clock', 'milliseconds')
                animate_sidebar._closing_start_width = sidebar.winfo_width()
            
        current_time = root.tk.call('clock', 'milliseconds')
        
        if opening:
            elapsed = max(0, current_time - sidebar_animation_start_time)
            progress = min(1.0, elapsed / ANIMATION_DURATION)
            eased_progress = ease_in_out_cubic(progress)
            new_w = int(sidebar_animation_start_width + 
                       (sidebar_target_width - sidebar_animation_start_width) * eased_progress)
        else:
            close_elapsed = max(0, current_time - animate_sidebar._closing_start_time)
            close_progress = min(1.0, close_elapsed / ANIMATION_DURATION)
            close_eased = ease_in_out_cubic(close_progress)
            new_w = int(animate_sidebar._closing_start_width * (1.0 - close_eased))
        
        # Calculate position and size
        x_pos = -sidebar_target_width + new_w if opening else -new_w
        y_pos = top_bar.winfo_height()
        
        # Ensure sidebar doesn't exceed screen bounds
        screen_height = root.winfo_screenheight()
        window_height = root.winfo_height()
        max_height = min(screen_height - y_pos - 50, window_height - y_pos)
        sidebar_height = max(200, max_height)
        
        sidebar.place(x=x_pos, y=y_pos, width=new_w, height=sidebar_height)
        
        # CRITICAL FIX: Update the main grid column configuration
        # This ensures the display area resizes properly
        if opening:
            root.columnconfigure(0, minsize=new_w, weight=0)
            root.columnconfigure(1, weight=1)  # Ensure main area takes remaining space
        else:
            # When closing, gradually reduce the minimum width
            root.columnconfigure(0, minsize=new_w, weight=0)
            root.columnconfigure(1, weight=1)
        
        # CRITICAL FIX: Update description text wrapping based on current sidebar width
        update_description_wrapping(new_w)
        
        # Continue animation if not complete
        if opening and progress < 1.0:
            root.after(int(1000 / TARGET_FPS), lambda: animate_sidebar(True))
        elif not opening and close_progress < 1.0:
            root.after(int(1000 / TARGET_FPS), lambda: animate_sidebar(False))
        else:
            # Animation complete
            if not opening:
                sidebar_target_width = 0
                # Reset column configuration when fully closed
                root.columnconfigure(0, minsize=0, weight=0)
                root.columnconfigure(1, weight=1)
                # Clean up closing animation attributes
                if hasattr(animate_sidebar, '_closing_start_time'):
                    delattr(animate_sidebar, '_closing_start_time')
                    delattr(animate_sidebar, '_closing_start_width')

    def show_sidebar(frame: ttk.Frame) -> None:
        """Show sidebar with smooth transition animation and proper scaling."""
        # Hide all children with fade effect
        for child in sidebar_container.winfo_children():
            child.pack_forget()
        
        # Show new frame with fade-in effect
        frame.pack(fill="both", expand=True)
        create_fade_in_effect(frame)
        
        # Animate sidebar expansion
        animate_sidebar(True)
        
        # Update status
        frame_name = frame.winfo_name() or "panel"
        update_status(f"Switched to {frame_name}")
        
        # Only show description for parameters tab, hide for all others
        if frame == params_viz_container:
            desc_label.pack(side="bottom", fill="x", padx=PADDING, pady=PADDING)  # Show for parameters
        else:
            desc_label.pack_forget()  # Hide for simulation, export, and settings tabs
        
        # Auto-hide status after delay
        root.after(2000, lambda: update_status("Ready"))

    def hide_sidebar(event: tk.Event | None = None) -> None:
        """Hide sidebar with proper reverse animation."""
        animate_sidebar(False)
        
        # Update status
        update_status("Sidebar closed")
        root.after(1000, lambda: update_status("Ready"))

    root.bind("<Escape>", hide_sidebar)


    # Parameter controls grouped in a dedicated frame
    # FIXED: Update parameters frame creation
    params_frame = ttk.LabelFrame(
        params_viz, text="⚙️ Pendulum Parameters"
    )
    params_frame.configure(style="Black.TLabelframe")  # Apply style after creation
    # Make the parameters frame flush with the top of the scroll box
    params_frame.grid(
        row=0,
        column=0,
        columnspan=3,
        sticky="ew",
        padx=PADDING,
        pady=(0, PADDING),
    )
    params_frame.columnconfigure(1, weight=1)

    # Add preset selector at the top of parameters
    preset_frame = ttk.Frame(params_frame, style="Card.TFrame")
    preset_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=4, pady=(0, 8))
    
    preset_label = ttk.Label(preset_frame, text="Quick Presets:", font=("Inter", 10, "bold"))
    preset_label.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 4))
    
    # Preset buttons
    preset_buttons = [
        ("Simple", "Simple Pendulum", "Modern.TButton"),
        ("Foucault", "Foucault Pendulum", "Purple.TButton"),
        ("Damped", "Damped Pendulum", "Warning.TButton"),
        ("Chaotic", "Chaotic Pendulum", "Warning.TButton")
    ]
    
    for i, (short_name, config_key, button_style) in enumerate(preset_buttons):
        btn = ttk.Button(
            preset_frame,
            text=short_name,
            style=button_style,
            command=lambda key=config_key: apply_preset_config(key)
        )
        btn.grid(row=1, column=i, padx=2, pady=2, sticky="ew")
        
        # Add tooltip with configuration details
        if config_key in PRESET_CONFIGS:
            config = PRESET_CONFIGS[config_key]
            tooltip_text = "\n".join([f"{k}: {v}" for k, v in config.items()])
            Tooltip(btn, f"Apply {config_key} configuration:\n{tooltip_text}")
    
    preset_frame.columnconfigure((0, 1, 2, 3), weight=1)

    def create_scale_entry(parent, text, var, row, tip, frm, to):
        pady_val = (0, 8) if row == 0 else 8
        
        # Enhanced label with better typography
        label = ttk.Label(parent, text=text, font=("Inter", 10, "normal"))
        label.grid(row=row, column=0, sticky="w", padx=8, pady=pady_val)
        
        # Modern scale with enhanced styling
        scale = ttk.Scale(parent, variable=var, from_=frm, to=to, orient="horizontal")
        scale.grid(row=row, column=1, sticky="ew", padx=8, pady=pady_val)
        
        # Enhanced entry with better styling
        entry = ttk.Entry(parent, textvariable=var, font=("Inter", 10), width=10)
        entry.grid(row=row, column=2, sticky="ew", padx=8, pady=pady_val)
        
        inputs.append(entry)
        
        # Enhanced tooltips with better styling
        Tooltip(scale, f"{tip}\nRange: {frm} - {to}")
        Tooltip(entry, f"{tip}\nEnter value or use slider")

        def _update(*_args):
            try:
                val = float(var.get())
            except tk.TclError:
                return
            if scale.get() != val:
                scale.set(val)
            try:
                if float(entry.get()) != val:
                    entry.delete(0, tk.END)
                    entry.insert(0, f"{val:.3f}")
            except ValueError:
                entry.delete(0, tk.END)
                entry.insert(0, f"{val:.3f}")

        var.trace_add("write", _update)

        def _on_entry(event):
            try:
                var.set(float(entry.get()))
            except ValueError:
                pass

        entry.bind("<Return>", _on_entry)
        entry.bind("<FocusOut>", _on_entry)

        return label, scale, entry

    row = 2  # Start after preset frame (rows 0-1)
    l_widgets = create_scale_entry(
        params_frame, "Länge [m]", l_var, row, "Pendellänge in Metern", 0.1, 10.0
    )
    row += 1
    phi_widgets = create_scale_entry(
        params_frame,
        "θ₀ [°]",
        phi_var,
        row,
        "Anfangspolarwinkel in Grad",
        -180,
        180,
    )
    row += 1
    g_widgets = create_scale_entry(
        params_frame,
        "g [m/s²]",
        g_var,
        row,
        "Gravitationsbeschleunigung",
        0,
        20,
    )
    row += 1
    h_widgets = create_scale_entry(
        params_frame,
        "h [Δs]",
        h_var,
        row,
        "Integrationszeitintervall",
        0.001,
        1,
    )
    row += 1
    drag_widgets = create_scale_entry(
        params_frame,
        "b [-]",
        drag_var,
        row,
        "Luftwiderstandskoeffizient",
        0,
        1,
    )
    row += 1
    speed_widgets = create_scale_entry(
        params_frame,
        "s [-]",
        speed_var,
        row,
        "Simulationsgeschwindigkeit",
        0.1,
        5,
    )
    row += 1
    psi_widgets = create_scale_entry(
        params_frame,
        "ψ₀ [°]",
        psi_var,
        row,
        "Initialer Azimutwinkel",
        -180,
        180,
    )
    row += 1
    psi_dot_widgets = create_scale_entry(
        params_frame,
        "ψ̇₀ [°/s]",
        psi_dot_var,
        row,
        "Initiale Azimutwinkelgeschwindigkeit",
        -360,
        360,
    )
    row += 1

    fx_widgets = create_scale_entry(
        params_frame,
        "P_x [N·s]",
        force_x_var,
        row,
        "Impuls entlang der x-Achse",
        -10,
        10,
    )
    row += 1
    fy_widgets = create_scale_entry(
        params_frame,
        "P_y [N·s]",
        force_y_var,
        row,
        "Impuls entlang der y-Achse",
        -10,
        10,
    )
    row += 1
    fz_widgets = create_scale_entry(
        params_frame,
        "P_z [N·s]",
        force_z_var,
        row,
        "Impuls entlang der z-Achse",
        -10,
        10,
    )
    row += 1

    # Enhanced impulse button with validation
    def safe_apply_impulse():
        """Apply impulse with enhanced validation and feedback."""
        # Pre-validate before attempting impulse
        valid, message = validate_impulse_values()
        if not valid:
            update_status(f"⚠️ {message}", 0)
            return
        
        valid, message = validate_simulation_state()
        if not valid:
            update_status(f"⚠️ {message}", 0)
            return
        
        # All validations passed, apply impulse
        apply_impulse()

    apply_impulse_btn = ttk.Button(
        params_frame, text="⚡ Apply Impulse", command=safe_apply_impulse
    )
    apply_impulse_btn.grid(row=row, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
    row += 1

    # Add impulse status indicator
    impulse_status_label = ttk.Label(params_frame, text="", font=("Inter", 8))
    impulse_status_label.grid(row=row, column=0, columnspan=3, padx=5, pady=2)
    row += 1

    def update_impulse_status(*args):
        """Update impulse status based on current values."""
        try:
            fx = force_x_var.get()
            fy = force_y_var.get()
            fz = force_z_var.get()
            
            magnitude = np.sqrt(fx**2 + fy**2 + fz**2)
            
            if magnitude < 0.01:
                impulse_status_label.configure(text="", foreground=TEXT_MUTED)
            elif magnitude > 20.0:
                impulse_status_label.configure(text="⚠️ Too large", foreground=ACCENT_ORANGE)
            else:
                impulse_status_label.configure(text=f"Magnitude: {magnitude:.2f}", foreground=ACCENT_GREEN)
        except:
            impulse_status_label.configure(text="", foreground=TEXT_MUTED)

    # Connect status updates to force variables
    force_x_var.trace_add("write", update_impulse_status)
    force_y_var.trace_add("write", update_impulse_status)
    force_z_var.trace_add("write", update_impulse_status)

    # FIXED: Update visualization frame creation
    viz_frame = ttk.LabelFrame(params_viz, text="👁️ Visualization Options")
    viz_frame.configure(style="TLabelframe")  # Apply style after creation
    viz_frame.grid(row=1, column=0, columnspan=3, padx=PADDING, pady=PADDING, sticky="ew")
    viz_frame.columnconfigure(0, weight=1)

    graph_dropdown = ttk.Combobox(viz_frame, textvariable=graph_var,
                                  values=graph_options, state="readonly")
    graph_dropdown.grid(row=0, column=0, sticky="w", padx=5, pady=5)

    show_vectors_check = ttk.Checkbutton(
        viz_frame, text="Force vectors", variable=show_vectors_var
    )
    show_vectors_check.grid(row=1, column=0, sticky="w", padx=5, pady=5)

    # 3D visualization controls
    trajectory_check = ttk.Checkbutton(
        viz_frame,
        text="Draw trajectory",
        variable=show_trajectory_var,
    )
    trajectory_check.grid(row=2, column=0, sticky="w", padx=5, pady=5)

    axes_check = ttk.Checkbutton(
        viz_frame,
        text="Show axes",
        variable=show_axes_var,
    )
    axes_check.grid(row=3, column=0, sticky="w", padx=5, pady=5)

    true_path_check = ttk.Checkbutton(
        viz_frame,
        text="Show true 3D path",
        variable=show_true_path_var,
    )
    true_path_check.grid(row=4, column=0, sticky="w", padx=5, pady=5)

    # Define three_d_widgets list after all widgets are created
    three_d_widgets = [
        psi_widgets[0],
        psi_widgets[1],
        psi_widgets[2],
        psi_dot_widgets[0],
        psi_dot_widgets[1],
        psi_dot_widgets[2],
        fx_widgets[0],
        fx_widgets[1],
        fx_widgets[2],
        fy_widgets[0],
        fy_widgets[1],
        fy_widgets[2],
        fz_widgets[0],
        fz_widgets[1],
        fz_widgets[2],
        apply_impulse_btn,
        true_path_check,
    ]

    reset_cam_btn = ttk.Button(
        viz_frame, text="Reset camera", command=lambda: reset_camera()
    )
    reset_cam_btn.grid(row=5, column=0, sticky="w", padx=5, pady=5)

    # Action buttons
    action_frame = ttk.Frame(sim_controls)
    action_frame.grid(row=2, column=0, padx=PADDING, pady=PADDING, sticky="ew")
    action_frame.columnconfigure(0, weight=1)

    # Description placed at the bottom of the sidebar
    desc_text_default = (
        "Adjust parameters using the inputs above and press Run to start the "
        "simulation. The pendulum animation appears in the top-right quadrant "
        "while the chosen quantity is plotted below it."
    )
    desc_text_pend = (
        "L: pendulum length\n"
        "θ₀: initial polar angle (deg)\n"
        "g: gravitational acceleration\n"
        "h: time step\n"
        "b: air resistance coefficient\n"
        "s: animation speed"
    )
    desc_text_pend3d = (
        desc_text_pend + "\n"
        "ψ₀: initial azimuth angle (deg)\n"
        "ψ̇₀: initial azimuth angular velocity (deg/s)\n"
        "P_x: impulse along x\n"
        "P_y: impulse along y\n"
        "P_z: impulse along z"
    )

    desc_label.configure(text=desc_text_default)

    # Right column for 3D view and diagrams
    display_frame = ttk.Frame(root)
    display_frame.grid(row=1, column=1, sticky="nsew")
    display_frame.columnconfigure(0, weight=1)
    display_frame.rowconfigure(0, weight=3)
    display_frame.rowconfigure(1, weight=2)

    # Top: 3D canvas, Bottom: diagram area with theme-aware styling
    anim_frame = ttk.Frame(display_frame, style="Card.TFrame")
    anim_frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
    plot_frame = ttk.Frame(display_frame, style="Card.TFrame")
    plot_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

    # Use theme-appropriate figure backgrounds
    fig_anim = plt.figure(figsize=(10, 8))
    fig_anim.patch.set_facecolor(DARK_BG)
    ax_anim = fig_anim.add_subplot(111)
    ax_anim.set_facecolor(AX_BG)

    # Apply theme colors to initial axis
    ax_anim.tick_params(colors=FG_COLOR)
    for spine in ax_anim.spines.values():
        spine.set_edgecolor(FG_COLOR)
    ax_anim.grid(True, alpha=0.3, color=FG_COLOR)

    default_elev, default_azim = 30, -60
    canvas_anim = FigureCanvasTkAgg(fig_anim, master=anim_frame)
    canvas_anim.get_tk_widget().pack(expand=True, fill="both", padx=5, pady=5)

    # Add 3D mouse controls for zooming and camera reset
    def on_scroll_3d(event):
        """Handle mouse wheel scrolling for 3D zoom."""
        if ax_anim and hasattr(ax_anim, 'set_xlim'):
            # Get current limits
            xlim = ax_anim.get_xlim()
            ylim = ax_anim.get_ylim()
            zlim = ax_anim.get_zlim()
            
            # Calculate zoom factor
            zoom_factor = 0.9 if event.button == 'up' else 1.1
            
            # Calculate center points
            x_center = (xlim[0] + xlim[1]) / 2
            y_center = (ylim[0] + ylim[1]) / 2
            z_center = (zlim[0] + zlim[1]) / 2
            
            # Calculate new ranges
            x_range = (xlim[1] - xlim[0]) * zoom_factor / 2
            y_range = (ylim[1] - ylim[0]) * zoom_factor / 2
            z_range = (zlim[1] - zlim[0]) * zoom_factor / 2
            
            # Apply new limits
            ax_anim.set_xlim(x_center - x_range, x_center + x_range)
            ax_anim.set_ylim(y_center - y_range, y_center + y_range)
            ax_anim.set_zlim(z_center - z_range, z_center + z_range)
            
            canvas_anim.draw_idle()
    
    def on_click_3d(event):
        """Handle mouse clicks for 3D camera reset."""
        if event.button == 2 and ax_anim and hasattr(ax_anim, 'view_init'):  # Middle click
            # Reset view and zoom
            ax_anim.view_init(default_elev, default_azim)
            limit = l_var.get() * 1.2
            ax_anim.set_xlim(-limit, limit)
            ax_anim.set_ylim(-limit, limit)
            ax_anim.set_zlim(-limit, limit)
            canvas_anim.draw_idle()
            update_status("🎯 3D camera reset", 0)
    
    # Connect 3D mouse controls
    fig_anim.canvas.mpl_connect('scroll_event', on_scroll_3d)
    fig_anim.canvas.mpl_connect('button_press_event', on_click_3d)

    def reset_camera() -> None:
        """Reset 3D camera to default position and zoom level."""
        if ax_anim and hasattr(ax_anim, "view_init"):
            ax_anim.view_init(default_elev, default_azim)
            # Reset zoom to default
            limit = l_var.get() * 1.2
            ax_anim.set_xlim(-limit, limit)
            ax_anim.set_ylim(-limit, limit)
            ax_anim.set_zlim(-limit, limit)
            canvas_anim.draw_idle()
            update_status("🎯 3D camera reset to default position", 0)

    fig_plot, ax_plot = plt.subplots(figsize=(6, 5))
    fig_plot.patch.set_facecolor(DARK_BG)
    ax_plot.set_facecolor(AX_BG)

    # Apply theme colors to plot axis
    ax_plot.tick_params(colors=FG_COLOR)
    for spine in ax_plot.spines.values():
        spine.set_edgecolor(FG_COLOR)
    ax_plot.grid(True, alpha=0.3, color=FG_COLOR)
    canvas_plot = FigureCanvasTkAgg(fig_plot, master=plot_frame)
    canvas_plot.get_tk_widget().pack(expand=True, fill="both", padx=PADDING, pady=PADDING)

    # Add 2D plot mouse controls
    def on_scroll_2d(event):
        """Handle mouse wheel scrolling for 2D plot zoom."""
        if ax_plot and event.inaxes == ax_plot:
            # Get current limits
            xlim = ax_plot.get_xlim()
            ylim = ax_plot.get_ylim()
            
            # Calculate zoom factor
            zoom_factor = 0.9 if event.button == 'up' else 1.1
            
            # Get mouse position in data coordinates
            x_mouse = event.xdata if event.xdata else (xlim[0] + xlim[1]) / 2
            y_mouse = event.ydata if event.ydata else (ylim[0] + ylim[1]) / 2
            
            # Calculate new ranges centered on mouse position
            x_range = (xlim[1] - xlim[0]) * zoom_factor / 2
            y_range = (ylim[1] - ylim[0]) * zoom_factor / 2
            
            # Apply new limits
            ax_plot.set_xlim(x_mouse - x_range, x_mouse + x_range)
            ax_plot.set_ylim(y_mouse - y_range, y_mouse + y_range)
            
            canvas_plot.draw_idle()
    
    # Variables for 2D plot panning
    _pan_start = None
    
    def on_press_2d(event):
        """Handle mouse press for 2D plot panning."""
        nonlocal _pan_start
        if event.button == 1 and event.inaxes == ax_plot:  # Left click
            _pan_start = (event.xdata, event.ydata)
    
    def on_motion_2d(event):
        """Handle mouse motion for 2D plot panning."""
        nonlocal _pan_start
        if _pan_start and event.button == 1 and event.inaxes == ax_plot:
            if event.xdata and event.ydata:
                # Calculate movement
                dx = _pan_start[0] - event.xdata
                dy = _pan_start[1] - event.ydata
                
                # Get current limits
                xlim = ax_plot.get_xlim()
                ylim = ax_plot.get_ylim()
                
                # Apply panning
                ax_plot.set_xlim(xlim[0] + dx, xlim[1] + dx)
                ax_plot.set_ylim(ylim[0] + dy, ylim[1] + dy)
                
                canvas_plot.draw_idle()
    
    def on_release_2d(event):
        """Handle mouse release for 2D plot panning."""
        nonlocal _pan_start
        _pan_start = None
    
    def on_double_click_2d(event):
        """Handle double click for 2D plot zoom reset."""
        if event.button == 1 and event.inaxes == ax_plot and event.dblclick:
            # Reset to auto-scale
            ax_plot.relim()
            ax_plot.autoscale()
            canvas_plot.draw_idle()
            update_status("🎯 2D plot zoom reset", 0)
    
    # Connect 2D mouse controls
    fig_plot.canvas.mpl_connect('scroll_event', on_scroll_2d)
    fig_plot.canvas.mpl_connect('button_press_event', on_press_2d)
    fig_plot.canvas.mpl_connect('motion_notify_event', on_motion_2d)
    fig_plot.canvas.mpl_connect('button_release_event', on_release_2d)
    fig_plot.canvas.mpl_connect('button_press_event', on_double_click_2d)

    theta_line = psi_line = None

    def update_inputs(*args):
        """Enable or disable controls and apply proper theming based on the selected module."""
        nonlocal ax_anim, has_run
        selection = option_var.get()
        pendulum_selected = selection in ("Pendulum", "3D Pendulum")
        has_run = False
        if run_play_btn is not None:
            run_play_btn.configure(text="▶ Run")

        if pendulum_selected:
            anim_frame.grid()
            fig_anim.clf()
            fig_anim.patch.set_facecolor(DARK_BG)
            
            # CRITICAL FIX: Force immediate canvas background updates when switching modes
            if 'canvas_anim' in globals() and canvas_anim:
                canvas_widget = canvas_anim.get_tk_widget()
                canvas_widget.configure(bg=DARK_BG, highlightbackground=DARK_BG, highlightcolor=DARK_BG)
                
                # Update parent frame background hierarchy
                try:
                    parent = canvas_widget.master
                    while parent and parent != root:
                        try:
                            parent.configure(background=DARK_BG)
                        except:
                            pass
                        parent = getattr(parent, 'master', None)
                except:
                    pass
                
                # Force immediate canvas redraw
                canvas_anim.draw_idle()
            
            if selection == "3D Pendulum":
                ax_anim = fig_anim.add_subplot(111, projection="3d")
                ax_anim.view_init(default_elev, default_azim)
                limit = l_var.get() * 1.2
                ax_anim.set_xlim(-limit, limit)
                ax_anim.set_ylim(-limit, limit)
                ax_anim.set_zlim(-limit, limit)
                ax_anim.set_box_aspect([1, 1, 1])
                
                # Apply 3D theme colors
                ax_anim.tick_params(colors=FG_COLOR)
                ax_anim.xaxis.label.set_color(FG_COLOR)
                ax_anim.yaxis.label.set_color(FG_COLOR)
                ax_anim.zaxis.label.set_color(FG_COLOR)
                
                # Style 3D panes
                if hasattr(ax_anim, 'xaxis') and hasattr(ax_anim.xaxis, 'pane'):
                    ax_anim.xaxis.pane.fill = False
                    ax_anim.yaxis.pane.fill = False
                    ax_anim.zaxis.pane.fill = False
                    ax_anim.xaxis.pane.set_edgecolor(FG_COLOR)
                    ax_anim.yaxis.pane.set_edgecolor(FG_COLOR)
                    ax_anim.zaxis.pane.set_edgecolor(FG_COLOR)
                    ax_anim.xaxis.pane.set_alpha(0.1)
                    ax_anim.yaxis.pane.set_alpha(0.1)
                    ax_anim.zaxis.pane.set_alpha(0.1)
            else:
                ax_anim = fig_anim.add_subplot(111)
                # Apply 2D theme colors
                ax_anim.tick_params(colors=FG_COLOR)
                for spine in ax_anim.spines.values():
                    spine.set_edgecolor(FG_COLOR)
                ax_anim.grid(True, alpha=0.3, color=FG_COLOR)
                
            ax_anim.set_facecolor(AX_BG)
            state = tk.NORMAL
            if selection == "3D Pendulum":
                desc_label.configure(text=desc_text_pend3d)
            else:
                desc_label.configure(text=desc_text_pend)
        else:
            anim_frame.grid_remove()
            fig_anim.clf()
            fig_anim.patch.set_facecolor(DARK_BG)
            ax_anim = None
            state = tk.DISABLED
            desc_label.configure(text=desc_text_default)
            
        # Apply theming to plot area as well with canvas background updates
        ax_plot.set_facecolor(AX_BG)
        ax_plot.tick_params(colors=FG_COLOR)
        for spine in ax_plot.spines.values():
            spine.set_edgecolor(FG_COLOR)
        ax_plot.grid(True, alpha=0.3, color=FG_COLOR)
        
        # CRITICAL FIX: Force plot figure and canvas background updates
        fig_plot.patch.set_facecolor(DARK_BG)
        if 'canvas_plot' in globals() and canvas_plot:
            canvas_widget = canvas_plot.get_tk_widget()
            canvas_widget.configure(bg=DARK_BG, highlightbackground=DARK_BG, highlightcolor=DARK_BG)
            
            # Update parent frame background hierarchy
            try:
                parent = canvas_widget.master
                while parent and parent != root:
                    try:
                        parent.configure(background=DARK_BG)
                    except:
                        pass
                    parent = getattr(parent, 'master', None)
            except:
                pass
            
            # Force immediate canvas redraw
            canvas_plot.draw_idle()
            
        set_state_recursive(params_frame, state)
        set_state_recursive(viz_frame, state)

        if pendulum_selected:
            graph_dropdown.configure(state="readonly")
            show_vectors_check.configure(state=tk.NORMAL)
        else:
            graph_dropdown.configure(state=tk.DISABLED)
            show_vectors_check.configure(state=tk.DISABLED)
            show_vectors_var.set(False)

        if selection == "3D Pendulum":
            for w in three_d_widgets:
                w.grid()
            trajectory_check.configure(state=tk.NORMAL)
            axes_check.configure(state=tk.NORMAL)
            reset_cam_btn.configure(state=tk.NORMAL)
        else:
            for w in three_d_widgets:
                w.grid_remove()
            trajectory_check.configure(state=tk.DISABLED)
            axes_check.configure(state=tk.DISABLED)
            reset_cam_btn.configure(state=tk.DISABLED)
            
        params_viz_canvas.update_idletasks()
        params_viz_canvas.configure(scrollregion=params_viz_canvas.bbox("all"))
        params_viz_canvas.yview_moveto(0)
        
        # CRITICAL FIX: Force comprehensive theme update after mode switch
        root.after(100, lambda: update_plot_theme(current_theme_var.get()))

    option_var.trace_add("write", update_inputs)
    update_inputs()

    def update_graph(*args):
        nonlocal screenshot_taken
        if option_var.get() in ("Pendulum", "3D Pendulum") and pendulum_data is not None:
            ax_plot.clear()
            ax_plot.set_facecolor(AX_BG)
            
            # Apply theme colors to all graph types
            ax_plot.tick_params(colors=FG_COLOR)
            for spine in ax_plot.spines.values():
                spine.set_edgecolor(FG_COLOR)
            ax_plot.grid(True, alpha=0.3, color=FG_COLOR)
            
            if option_var.get() == "3D Pendulum" and graph_var.get() == "Angle":
                init_plot()

            # SIMPLIFIED: Remove complex synchronization that's causing issues
            # Keep pendulum animation in ani[0] if available
            pend_anim = ani[0] if ani else None
            
            # FIXED: Properly handle animation switching
            # Stop all existing graph animations (keep only the first one which is pendulum)
            if len(ani) > 1:
                for i in range(1, len(ani)):
                    try:
                        if hasattr(ani[i], 'event_source'):
                            ani[i].event_source.stop()
                    except:
                        pass
                # Remove all but the first animation
                ani[:] = ani[:1]

            screenshot_taken = False
            
            # Create new graph animation
            ani_line = None
            try:
                if graph_var.get() == "Energy":
                    t = pendulum_data["t"]
                    total = pendulum_data["Energy"]
                    kinetic = pendulum_data["Kinetic"]
                    potential = pendulum_data["Potential"]
                    min_val = min(np.min(total), np.min(kinetic), np.min(potential))
                    max_val = max(np.max(total), np.max(kinetic), np.max(potential))
                    ani_line = animate_energy(
                        fig_plot, ax_plot, t, kinetic,
                        potential, total, speed_var.get(), (min_val, max_val)
                    )
                elif option_var.get() == "3D Pendulum" and graph_var.get() == "Angle":
                    theta = pendulum_data["Angle"]
                    psi = pendulum_data["Psi"]
                    max_amp = max(np.max(np.abs(theta)), np.max(np.abs(psi)))
                    y_range = (-max_amp * 1.1, max_amp * 1.1)
                    ani_line = animate_angles(
                        pendulum_data["t"],
                        theta,
                        psi,
                        speed_var.get(),
                        y_range,
                    )
                elif option_var.get() == "Pendulum" and graph_var.get() == "Angle":
                    ani_line = animate_two_lines(
                        fig_plot,
                        ax_plot,
                        pendulum_data["t"],
                        pendulum_data["Angle"],
                        pendulum_data["Sine"],
                        speed_var.get(),
                        (-2.5, 2.5),
                        labels=("θ (actual)", "Sine"),
                    )
                else:
                    dataset = pendulum_data.get(graph_var.get(), pendulum_data["Angle"])
                    if graph_var.get() == "Angle":
                        max_val = np.max(np.abs(dataset))
                        y_range = (-max_val * 1.1, max_val * 1.1)
                    else:
                        y_range = None
                    ani_line = animate_line(
                        fig_plot, ax_plot, pendulum_data["t"],
                        dataset, speed_var.get(), y_range
                    )
            except Exception as e:
                print(f"Error creating graph animation: {e}")
                ani_line = None
            
            # FIXED: Properly add the new animation and manage its state
            if ani_line:
                # Start the new animation if the simulation is running
                if running:
                    try:
                        ani_line.event_source.start()
                    except:
                        pass
                else:
                    try:
                        ani_line.event_source.stop()
                    except:
                        pass
                ani.append(ani_line)
            # Apply theme colors to axis labels with bold font
            ax_plot.set_xlabel('t', color=FG_COLOR, fontweight='bold')
            ax_plot.set_ylabel('Angle' if graph_var.get() == "Angle" else graph_var.get(), color=FG_COLOR, fontweight='bold')
            
            # Apply theme to plot title
            title_text = 'Angle' if graph_var.get() == "Angle" else graph_var.get()
            ax_plot.set_title(title_text, color=FG_COLOR, fontweight='bold')
            
            canvas_plot.draw()

    graph_var.trace_add("write", update_graph)

    def init_plot():
        """Initialize plot with proper theme support."""
        nonlocal theta_line, psi_line
        ax_plot.clear()
        ax_plot.set_facecolor(AX_BG)
        
        # Apply theme colors
        ax_plot.tick_params(colors=FG_COLOR)
        for spine in ax_plot.spines.values():
            spine.set_edgecolor(FG_COLOR)
        ax_plot.grid(True, alpha=0.3, color=FG_COLOR)
        
        theta_line, = ax_plot.plot([], [], color=ACCENT_BLUE, label="θ(t)", lw=2)
        psi_line, = ax_plot.plot([], [], color=ACCENT_ORANGE, label="ψ(t)", lw=2)
        ax_plot.set_xlabel("Zeit [s]", color=FG_COLOR, fontweight='bold')
        ax_plot.set_ylabel("Winkel [rad]", color=FG_COLOR, fontweight='bold')
        
        # Theme-aware legend
        legend = ax_plot.legend(facecolor=DARKER_BG, edgecolor=FG_COLOR)
        legend.get_frame().set_alpha(0.8)
        for text in legend.get_texts():
            text.set_color(FG_COLOR)
        
        # CRITICAL FIX: Update the figure background to match theme
        fig_plot.patch.set_facecolor(DARK_BG)
        
        # CRITICAL FIX: Update canvas widget background
        if 'canvas_plot' in globals() and canvas_plot:
            canvas_widget = canvas_plot.get_tk_widget()
            canvas_widget.configure(bg=DARK_BG, highlightbackground=DARK_BG, highlightcolor=DARK_BG)
            
            # Update parent frame background
            try:
                parent = canvas_widget.master
                while parent and parent != root:
                    try:
                        parent.configure(background=DARK_BG)
                    except:
                        pass
                    parent = getattr(parent, 'master', None)
            except:
                pass

    init_plot()

    # Placeholder handlers for future zoom and tooltip features
    def _on_zoom(_event):
        """Zoom placeholder."""
        pass

    def _show_tooltip(_event):
        """Tooltip placeholder."""
        pass

    fig_plot.canvas.mpl_connect("scroll_event", _on_zoom)
    fig_plot.canvas.mpl_connect("motion_notify_event", _show_tooltip)

    ani = []

    # Determine whether the current Matplotlib backend supports blitting.
    # TkAgg does not support blitting, whereas other interactive backends
    # (e.g., QtAgg) do. Retrieve the backend once and reuse the result for
    # all animations defined below.
    blit = matplotlib.get_backend() != "TkAgg"

    def animate_line(fig, ax, t, y, speed, y_range=None):
        """Animate a line plot with proper theme support and optimized rendering."""
        ax.clear()
        ax.set_facecolor(AX_BG)  # Use theme-appropriate background
        
        # Apply theme colors to axes
        ax.tick_params(colors=FG_COLOR)
        for spine in ax.spines.values():
            spine.set_edgecolor(FG_COLOR)
        ax.grid(True, alpha=0.3, color=FG_COLOR)
        
        line, = ax.plot([], [], color=ACCENT_BLUE, lw=2)
        ax.set_xlim(t[0], t[-1])
        if y_range is None:
            ax.set_ylim(min(y), max(y))
        else:
            ax.set_ylim(*y_range)
        ax.set_xlabel('Time [s]', color=FG_COLOR, fontweight='bold')
        ax.set_ylabel('Value', color=FG_COLOR, fontweight='bold')
        ax.set_title('Animation', color=FG_COLOR, fontweight='bold')

        def init():
            line.set_data([], [])
            return line,

        last_time = time.time()
        last_draw_time = 0  # Track when we last drew to prevent excessive redraws

        def update(frame):
            nonlocal last_time, last_draw_time
            if not running:
                return line,
            
            current = time.time()
            
            # FIXED: Less aggressive frame rate limiting to prevent flickering
            # Only limit if we're going way too fast
            if current - last_draw_time < 1.0 / (TARGET_FPS * 2):
                return line,
            
            # Update FPS counter
            dt = current - last_time
            if dt > 0:
                fps = 1.0 / dt
                fps_var.set(f"FPS: {fps:.1f}")
            last_time = current
            
            # FIX: Ensure frame index is within bounds
            frame_idx = min(frame, len(t) - 1)
            
            # FIXED: Show complete path to prevent flickering
            # Only use trail limits for very long simulations
            start_idx = 0
            if frame_idx > 1000:  # Only start limiting after 1000 frames
                start_idx = max(0, frame_idx - 800)  # Keep last 800 points
            
            line.set_data(t[start_idx:frame_idx+1], y[start_idx:frame_idx+1])
            if frame == len(t) - 1:
                root.after(0, auto_screenshot)
            
            last_draw_time = current
            return line,

        # Use proper interval calculation for smooth animation
        total_time = t[-1] - t[0] if len(t) > 1 else 1.0
        target_duration = max(1.0, total_time / speed)
        interval = max(16, int(target_duration * 1000 / len(t)))
        
        return animation.FuncAnimation(
            fig,
            update,
            frames=len(t),
            init_func=init,
            blit=blit,
            interval=interval,
            repeat=False,
        )

    def animate_angles(t, theta, psi, speed, y_range=None):
        """Animate θ and ψ using the pre-created lines."""
        ax_plot.set_xlim(t[0], t[-1])
        if y_range is None:
            min_val = min(np.min(theta), np.min(psi))
            max_val = max(np.max(theta), np.max(psi))
            ax_plot.set_ylim(min_val, max_val)
        else:
            ax_plot.set_ylim(*y_range)

        def init():
            theta_line.set_data([], [])
            psi_line.set_data([], [])
            return theta_line, psi_line

        last_time = time.time()
        last_draw_time = 0  # Anti-flicker timing

        def update(frame):
            nonlocal last_time, last_draw_time
            if not running:
                return theta_line, psi_line
                
            current = time.time()
            
            # CRITICAL FIX: Remove the frame rate limiting that causes flickering
            # The original limiting was too aggressive for angle plots
            
            # Update FPS counter
            dt = current - last_time
            if dt > 0:
                fps = 1.0 / dt
                fps_var.set(f"FPS: {fps:.1f}")
            last_time = current
            
            # FIXED: Always show complete trajectory without trail limits
            # This prevents the flickering caused by changing start indices
            theta_line.set_data(t[0:frame+1], theta[0:frame+1])
            psi_line.set_data(t[0:frame+1], psi[0:frame+1])
            
            if frame == len(t) - 1:
                root.after(0, auto_screenshot)
            
            return theta_line, psi_line

        # Optimize interval calculation to prevent excessive updates
        total_time = t[-1] - t[0] if len(t) > 1 else 1.0
        target_duration = max(1.0, total_time / speed)  # Minimum 1 second duration
        interval = max(16, int(target_duration * 1000 / len(t)))  # Minimum 16ms (60fps)

        return animation.FuncAnimation(
            fig_plot,
            update,
            frames=len(t),
            init_func=init,
            blit=blit,
            interval=interval,
            repeat=False,
        )

    def animate_two_lines(
        fig, ax, t, y1, y2, speed, y_range=None, labels=("θ", "ψ")
    ):
        """Animate two line plots with proper theme support."""
        ax.clear()
        ax.set_facecolor(AX_BG)
        
        # Apply theme colors to axes
        ax.tick_params(colors=FG_COLOR)
        for spine in ax.spines.values():
            spine.set_edgecolor(FG_COLOR)
        ax.grid(True, alpha=0.3, color=FG_COLOR)
        
        line1, = ax.plot([], [], color=ACCENT_BLUE, label=labels[0], lw=2)
        line2, = ax.plot([], [], color=ACCENT_ORANGE, label=labels[1], lw=2)
        ax.set_xlim(t[0], t[-1])
        if y_range is None:
            min_val = min(np.min(y1), np.min(y2))
            max_val = max(np.max(y1), np.max(y2))
            ax.set_ylim(min_val, max_val)
        else:
            ax.set_ylim(*y_range)
        ax.set_xlabel('Time [s]', color=FG_COLOR, fontweight='bold')
        ax.set_ylabel('Angle [rad]', color=FG_COLOR, fontweight='bold')
        ax.set_title('Angle Comparison', color=FG_COLOR, fontweight='bold')
        
        # Theme-aware legend
        legend = ax.legend(facecolor=DARKER_BG, edgecolor=FG_COLOR)
        legend.get_frame().set_alpha(0.8)
        for text in legend.get_texts():
            text.set_color(FG_COLOR)

        def init():
            line1.set_data([], [])
            line2.set_data([], [])
            return line1, line2

    def animate_two_lines(
        fig, ax, t, y1, y2, speed, y_range=None, labels=("θ", "ψ")
    ):
        """Animate two line plots with proper theme support and continuous animation."""
        ax.clear()
        ax.set_facecolor(AX_BG)
        
        # Apply theme colors to axes
        ax.tick_params(colors=FG_COLOR)
        for spine in ax.spines.values():
            spine.set_edgecolor(FG_COLOR)
        ax.grid(True, alpha=0.3, color=FG_COLOR)
        
        line1, = ax.plot([], [], color=ACCENT_BLUE, label=labels[0], lw=2)
        line2, = ax.plot([], [], color=ACCENT_ORANGE, label=labels[1], lw=2)
        ax.set_xlim(t[0], t[-1])
        if y_range is None:
            min_val = min(np.min(y1), np.min(y2))
            max_val = max(np.max(y1), np.max(y2))
            ax.set_ylim(min_val, max_val)
        else:
            ax.set_ylim(*y_range)
        ax.set_xlabel('Time [s]', color=FG_COLOR, fontweight='bold')
        ax.set_ylabel('Angle [rad]', color=FG_COLOR, fontweight='bold')
        ax.set_title('Angle Comparison', color=FG_COLOR, fontweight='bold')
        
        # Theme-aware legend
        legend = ax.legend(facecolor=DARKER_BG, edgecolor=FG_COLOR)
        legend.get_frame().set_alpha(0.8)
        for text in legend.get_texts():
            text.set_color(FG_COLOR)

        def init():
            line1.set_data([], [])
            line2.set_data([], [])
            return line1, line2

        last_time = time.time()

        def update(frame):
            nonlocal last_time
            if not running:
                return line1, line2
                
            current = time.time()
            
            # Update FPS counter
            dt = current - last_time
            if dt > 0:
                fps = 1.0 / dt
                fps_var.set(f"FPS: {fps:.1f}")
            last_time = current
            
            # FIXED: Ensure continuous animation with proper bounds checking
            frame_idx = min(frame, len(t) - 1)
            line1.set_data(t[0:frame_idx+1], y1[0:frame_idx+1])
            line2.set_data(t[0:frame_idx+1], y2[0:frame_idx+1])
            
            if frame == len(t) - 1:
                root.after(0, auto_screenshot)
                
            return line1, line2

        # Use proper interval calculation for smooth animation
        total_time = t[-1] - t[0] if len(t) > 1 else 1.0
        target_duration = max(1.0, total_time / speed)
        interval = max(16, int(target_duration * 1000 / len(t)))
        
        return animation.FuncAnimation(
            fig,
            update,
            frames=len(t),
            init_func=init,
            blit=blit,
            interval=interval,
            repeat=False,
        )

    def animate_pendulum(fig, ax, t, phi, L, speed):
        """Animate 2D pendulum with proper theme support and synchronized timing."""
        ax.clear()
        ax.set_facecolor(AX_BG)  # Use theme-appropriate background
        
        # Apply theme colors to axes
        ax.tick_params(colors=FG_COLOR)
        for spine in ax.spines.values():
            spine.set_edgecolor(FG_COLOR)
        ax.grid(True, alpha=0.3, color=FG_COLOR)
        
        # CRITICAL FIX: Update the figure background to match theme
        fig.patch.set_facecolor(DARK_BG)
        
        x = L * np.sin(phi)
        y = -L * np.cos(phi)
        line, = ax.plot([], [], 'o-', lw=2, markersize=15, color=ACCENT_BLUE)
        ax.set_xlim(-L * 1.2, L * 1.2)
        ax.set_ylim(-L * 1.2, L * 0.2)
        ax.set_aspect('equal', adjustable='box')
        ax.set_title('2D Pendulum', color=FG_COLOR, fontsize=12, fontweight='bold')

        # CRITICAL FIX: Update canvas widget background for 2D pendulum
        if 'canvas_anim' in globals() and canvas_anim:
            canvas_widget = canvas_anim.get_tk_widget()
            canvas_widget.configure(bg=DARK_BG, highlightbackground=DARK_BG, highlightcolor=DARK_BG)
            
            # Update parent frame background
            try:
                parent = canvas_widget.master
                while parent and parent != root:
                    try:
                        parent.configure(background=DARK_BG)
                    except:
                        pass
                    parent = getattr(parent, 'master', None)
            except:
                pass

        def init():
            line.set_data([], [])
            return line,

        last_time = time.time()

        def update(frame):
            nonlocal last_time
            if not running:
                return line,
            
            # FIXED: Ensure frame index is within bounds and matches graph animation
            frame_idx = min(frame, len(t) - 1)
            line.set_data([0, x[frame_idx]], [0, y[frame_idx]])
            
            if frame == len(t) - 1:
                root.after(0, auto_screenshot)
            
            current = time.time()
            dt = current - last_time
            if dt > 0:
                fps_var.set(f"FPS: {1.0 / dt:.1f}")
            last_time = current
            return line,

        # FIXED: Use exactly the same interval calculation as graph animations
        total_time = t[-1] - t[0] if len(t) > 1 else 1.0
        target_duration = max(1.0, total_time / speed)
        interval = max(16, int(target_duration * 1000 / len(t)))
        
        return animation.FuncAnimation(
            fig,
            update,
            frames=len(t),
            init_func=init,
            blit=blit,
            interval=interval,
            repeat=False,
        )

    # ============================================================================
    # 3D ANIMATION SYSTEM
    # ============================================================================
    
    def animate_pendulum3d(
        fig,
        ax,
        t,
        x,
        y,
        z,
        vx,
        vy,
        vz,
        L,
        g,
        speed,
        show_trajectory=False,
        show_vectors=False,
        applied_force=None,
        show_axes=True,
        show_true_path=False,
    ):
        """
        Animate a 3D pendulum with proper theme support and optimized performance.

        This function creates a smooth 3D animation of a pendulum system, handling
        the visual representation of the mass, string, trajectory, force vectors,
        coordinate axes, and the true 3D path of the pendulum mass.

        Args:
            fig: Matplotlib figure object for the 3D plot
            ax: 3D axes object for rendering the pendulum
            t: Current time value
            x, y, z: Position coordinates of the pendulum mass
            vx, vy, vz: Velocity components of the pendulum mass
            L: Length of the pendulum string
            g: Gravitational acceleration constant
            speed: Animation speed multiplier
            show_trajectory: Boolean flag to display the pendulum's projected path
            show_vectors: Boolean flag to display force vectors
            applied_force: Optional external force vector to visualize
            show_axes: Boolean flag to display coordinate axes
            show_true_path: Boolean flag to display the true 3D path of the mass
        """

        # CRITICAL FIX: Ensure figure background is set at start of animation
        fig.patch.set_facecolor(DARK_BG)
        fig.set_facecolor(DARK_BG)
        
        # Clear previous frame and apply theme-appropriate background
        ax.clear()
        ax.set_facecolor(AX_BG)  # Use theme-appropriate background color
        
        if not show_axes:
            ax.set_axis_off()
        else:
            ax.set_axis_on()
            # Apply theme colors to 3D axes
            ax.tick_params(colors=FG_COLOR)
            ax.xaxis.label.set_color(FG_COLOR)
            ax.yaxis.label.set_color(FG_COLOR)
            ax.zaxis.label.set_color(FG_COLOR)
            
            # Set axis labels with theme colors
            ax.set_xlabel('X [m]', color=FG_COLOR, fontweight='bold')
            ax.set_ylabel('Y [m]', color=FG_COLOR, fontweight='bold')
            ax.set_zlabel('Z [m]', color=FG_COLOR, fontweight='bold')
            
            # Style 3D panes with theme colors
            ax.xaxis.pane.fill = False
            ax.yaxis.pane.fill = False
            ax.zaxis.pane.fill = False
            ax.xaxis.pane.set_edgecolor(FG_COLOR)
            ax.yaxis.pane.set_edgecolor(FG_COLOR)
            ax.zaxis.pane.set_edgecolor(FG_COLOR)
            ax.xaxis.pane.set_alpha(0.1)
            ax.yaxis.pane.set_alpha(0.1)
            ax.zaxis.pane.set_alpha(0.1)
            
            # Apply theme colors to tick labels
            ax.tick_params(axis='x', colors=FG_COLOR)
            ax.tick_params(axis='y', colors=FG_COLOR)
            ax.tick_params(axis='z', colors=FG_COLOR)
            
            # CRITICAL FIX: Force tick label colors in light mode
            for tick in ax.xaxis.get_major_ticks():
                tick.label1.set_color(FG_COLOR)
            for tick in ax.yaxis.get_major_ticks():
                tick.label1.set_color(FG_COLOR)
            for tick in ax.zaxis.get_major_ticks():
                tick.label1.set_color(FG_COLOR)
        
        line, = ax.plot([], [], [], "o-", lw=2, markersize=8, color=ACCENT_BLUE)
        arrows = []
        limit = L * 1.2
        ax.set_xlim(-limit, limit)
        ax.set_ylim(-limit, limit)
        ax.set_zlim(-limit, limit)
        ax.set_box_aspect([1, 1, 1])
        ax.set_title("3D Pendulum", color=FG_COLOR, fontsize=12, fontweight='bold')
        
        # FIXED: Projection lines with dynamic alpha for better trail visualization
        line_xy, = ax.plot([], [], [], color=ACCENT_GREEN, lw=2, alpha=0.9, label='XY Projection')
        line_yz, = ax.plot([], [], [], color=ACCENT_ORANGE, lw=2, alpha=0.9, label='YZ Projection')
        line_zx, = ax.plot([], [], [], color=ACCENT_PURPLE, lw=2, alpha=0.9, label='ZX Projection')
        
        # TRUE PATH visualization line
        true_path_line, = ax.plot([], [], [], color='#ffff00', lw=3, alpha=0.9, label='True 3D Path')
        
        # Additional trail lines for fade effect
        trail_lines_xy = []
        trail_lines_yz = []
        trail_lines_zx = []

        # Precompute accelerations from velocity arrays
        ax_vals = np.gradient(vx, t, edge_order=2)
        ay_vals = np.gradient(vy, t, edge_order=2)
        az_vals = np.gradient(vz, t, edge_order=2)

        def init():
            line.set_data([], [])
            line.set_3d_properties([])
            line_xy.set_data([], [])
            line_xy.set_3d_properties([])
            line_yz.set_data([], [])
            line_yz.set_3d_properties([])
            line_zx.set_data([], [])
            line_zx.set_3d_properties([])
            true_path_line.set_data([], [])
            true_path_line.set_3d_properties([])
            # Clear any existing trail lines
            for trail_line in trail_lines_xy + trail_lines_yz + trail_lines_zx:
                trail_line.remove()
            trail_lines_xy.clear()
            trail_lines_yz.clear()
            trail_lines_zx.clear()
            return line, line_xy, line_yz, line_zx, true_path_line

        last_time = time.time()
        last_draw_time = 0  # Prevent excessive redraws

        def update(frame):
            nonlocal last_time, last_draw_time
            if not running:
                return tuple()
            
            current = time.time()
            
            # Limit drawing frequency to prevent flickering
            if current - last_draw_time < 1.0 / TARGET_FPS:
                return tuple()
            
            # CRITICAL FIX: Ensure figure background is maintained during animation
            fig.patch.set_facecolor(DARK_BG)
            
            line.set_data([0, x[frame]], [0, y[frame]])
            line.set_3d_properties([0, z[frame]])

            for arr in arrows:
                arr.remove()
            arrows.clear()

            if show_vectors:
                r_vec = np.array([x[frame], y[frame], z[frame]])
                r_hat = r_vec / np.linalg.norm(r_vec)
                v_vec = np.array([vx[frame], vy[frame], vz[frame]])
                a_vec = np.array([ax_vals[frame], ay_vals[frame], az_vals[frame]])

                f_vec = (
                    applied_force[frame]
                    if applied_force is not None
                    else np.zeros(3)
                )

                g_vec = np.array([0.0, 0.0, -g])

                # tension (mass = 1); project forces onto radial direction
                T = g_vec.dot(r_hat) - a_vec.dot(r_hat) - f_vec.dot(r_hat)
                t_vec = -T * r_hat

                force_scale = 0.3 * L / g if g != 0 else 0.3 * L

                # Use theme colors for force vectors
                arrows.append(
                    ax.quiver(
                        x[frame],
                        y[frame],
                        z[frame],
                        g_vec[0],
                        g_vec[1],
                        g_vec[2],
                        length=force_scale,
                        normalize=False,
                        color=ACCENT_BLUE,
                        alpha=0.8
                    )
                )
                arrows.append(
                    ax.quiver(
                        x[frame],
                        y[frame],
                        z[frame],
                        t_vec[0],
                        t_vec[1],
                        t_vec[2],
                        length=force_scale,
                        normalize=False,
                        color=ACCENT_ORANGE,
                        alpha=0.8
                    )
                )
                if applied_force is not None:
                    arrows.append(
                        ax.quiver(
                            x[frame],
                            y[frame],
                            z[frame],
                            f_vec[0],
                            f_vec[1],
                            f_vec[2],
                            length=force_scale,
                            normalize=False,
                            color=ACCENT_GREEN,
                            alpha=0.8
                        )
                    )

            # Update FPS counter
            dt = current - last_time
            if dt > 0:
                fps = 1.0 / dt
                fps_var.set(f"FPS: {fps:.1f}")
            last_time = current

            # Handle trajectory projections and true path
            artists = [line, *arrows]

            if show_trajectory:
                # Use dynamic trail length from settings
                trail_length = trail_length_var.get()
                
                if trail_length == 0:
                    # No trail - hide projections
                    line_xy.set_data([], [])
                    line_xy.set_3d_properties([])
                    line_yz.set_data([], [])
                    line_yz.set_3d_properties([])
                    line_zx.set_data([], [])
                    line_zx.set_3d_properties([])
                else:
                    # Calculate trail slice - show last N points up to current frame
                    start_idx = max(0, frame + 1 - trail_length)
                    end_idx = frame + 1
                    trajectory_slice = slice(start_idx, end_idx)
                    trail_points = end_idx - start_idx
                    
                    # XY projection on floor (z = -limit) - DYNAMIC TRAIL
                    line_xy.set_data(x[trajectory_slice], y[trajectory_slice])
                    line_xy.set_3d_properties(np.full(trail_points, -limit))
                    
                    # YZ projection on side wall (x = limit) - DYNAMIC TRAIL
                    line_yz.set_data(np.full(trail_points, limit), y[trajectory_slice])
                    line_yz.set_3d_properties(z[trajectory_slice])
                    
                    # ZX projection on back wall (y = -limit) - DYNAMIC TRAIL
                    line_zx.set_data(x[trajectory_slice], np.full(trail_points, -limit))
                    line_zx.set_3d_properties(z[trajectory_slice])
                
                artists.extend([line_xy, line_yz, line_zx])
            else:
                # Hide projections when trajectory is not enabled
                line_xy.set_data([], [])
                line_xy.set_3d_properties([])
                line_yz.set_data([], [])
                line_yz.set_3d_properties([])
                line_zx.set_data([], [])
                line_zx.set_3d_properties([])

            # Handle TRUE 3D PATH visualization
            if show_true_path:
                # Use dynamic trail length for true path as well
                trail_length = trail_length_var.get()
                
                if trail_length == 0:
                    # Show complete path up to current frame
                    true_path_line.set_data(x[0:frame+1], y[0:frame+1])
                    true_path_line.set_3d_properties(z[0:frame+1])
                else:
                    # Show only the trail length
                    start_idx = max(0, frame + 1 - trail_length)
                    end_idx = frame + 1
                    path_slice = slice(start_idx, end_idx)
                    
                    true_path_line.set_data(x[path_slice], y[path_slice])
                    true_path_line.set_3d_properties(z[path_slice])
                
                artists.append(true_path_line)
            else:
                # Hide true path when not enabled
                true_path_line.set_data([], [])
                true_path_line.set_3d_properties([])

            if frame == len(t) - 1:
                root.after(0, auto_screenshot)

            if pendulum_data is not None:
                pendulum_data["frame"] = frame

            last_draw_time = current
            return tuple(artists)        # Optimize interval calculation for 3D rendering
        total_time = t[-1] - t[0] if len(t) > 1 else 1.0
        target_duration = max(2.0, total_time / speed)  # Minimum 2 seconds for 3D
        interval = max(33, int(target_duration * 1000 / len(t)))  # Minimum 33ms (30fps) for 3D
        
        return animation.FuncAnimation(
            fig,
            update,
            frames=len(t),
            init_func=init,
            blit=False,  # 3D animations don't support blitting
            interval=interval,
            repeat=False,
        )

    def animate_energy(fig, ax, t, kinetic, potential, total, speed,
                       y_range=None):
        """Animate energy plots with proper theme support."""
        ax.clear()
        ax.set_facecolor(AX_BG)
        
        # Apply theme colors to axes
        ax.tick_params(colors=FG_COLOR)
        for spine in ax.spines.values():
            spine.set_edgecolor(FG_COLOR)
        ax.grid(True, alpha=0.3, color=FG_COLOR)
        
        line_k, = ax.plot([], [], color=ACCENT_BLUE, label="Kinetic", lw=2)
        line_p, = ax.plot([], [], color=ACCENT_ORANGE, label="Potential", lw=2)
        line_t, = ax.plot([], [], color=ACCENT_GREEN, label="Total", lw=2)
        ax.set_xlim(t[0], t[-1])
        if y_range is None:
            y_min = min(np.min(kinetic), np.min(potential), np.min(total))
            y_max = max(np.max(kinetic), np.max(potential), np.max(total))
            ax.set_ylim(y_min, y_max)
        else:
            ax.set_ylim(*y_range)
        ax.set_xlabel('Time [s]', color=FG_COLOR, fontweight='bold')
        ax.set_ylabel('Energy [J]', color=FG_COLOR, fontweight='bold')
        ax.set_title('Energy Analysis', color=FG_COLOR, fontweight='bold')
        
        # Theme-aware legend
        legend = ax.legend(facecolor=DARKER_BG, edgecolor=FG_COLOR)
        legend.get_frame().set_alpha(0.8)
        for text in legend.get_texts():
            text.set_color(FG_COLOR)

        def init():
            line_k.set_data([], [])
            line_p.set_data([], [])
            line_t.set_data([], [])
            return line_k, line_p, line_t

        last_time = time.time()

        def update(frame):
            nonlocal last_time
            if not running:
                return line_k, line_p, line_t
            start_idx = 0
            current = time.time()
            
            dt = current - last_time
            if dt > 0:
                fps = 1.0 / dt
                fps_var.set(f"FPS: {fps:.1f}")
                if dt > 1.0 / TARGET_FPS:
                    start_idx = max(0, frame - MAX_TRAIL_POINTS)
            line_k.set_data(t[start_idx:frame], kinetic[start_idx:frame])
            line_p.set_data(t[start_idx:frame], potential[start_idx:frame])
            line_t.set_data(t[start_idx:frame], total[start_idx:frame])
            if frame == len(t) - 1:
                root.after(0, auto_screenshot)
            last_time = current
            return line_k, line_p, line_t

        interval = max(1, int(1000 / (TARGET_FPS * speed)))
        return animation.FuncAnimation(
            fig,
            update,
            frames=len(t),
            init_func=init,
            blit=blit,
            interval=interval,
            repeat=False,
        )

    pendulum_data = None

    def setup_rk4_test1():
        nonlocal ax_anim
        fig_anim.clf()
        fig_anim.patch.set_facecolor(DARK_BG)
        ax_anim = fig_anim.add_subplot(111)
        ax_anim.set_facecolor(AX_BG)
        
        # Apply theme colors to axes
        ax_anim.tick_params(colors=FG_COLOR)
        for spine in ax_anim.spines.values():
            spine.set_edgecolor(FG_COLOR)
        ax_anim.grid(True, alpha=0.3, color=FG_COLOR)
        
        import rk4_test1 as mod
        t, y = mod.run(ax=ax_plot)
        
        # Apply comprehensive theme to the plot created by the module
        ax_plot.set_facecolor(AX_BG)
        ax_plot.tick_params(colors=FG_COLOR)
        for spine in ax_plot.spines.values():
            spine.set_edgecolor(FG_COLOR)
        ax_plot.grid(True, alpha=0.3, color=FG_COLOR)
        
        # Update all text elements to use theme colors
        if ax_plot.get_title():
            ax_plot.set_title(ax_plot.get_title(), color=FG_COLOR, fontweight='bold')
        if ax_plot.get_xlabel():
            ax_plot.set_xlabel(ax_plot.get_xlabel(), color=FG_COLOR, fontweight='bold')
        if ax_plot.get_ylabel():
            ax_plot.set_ylabel(ax_plot.get_ylabel(), color=FG_COLOR, fontweight='bold')
        
        # Update legend if it exists
        legend = ax_plot.get_legend()
        if legend:
            legend.set_facecolor(DARKER_BG)
            legend.set_edgecolor(FG_COLOR)
            for text in legend.get_texts():
                text.set_color(FG_COLOR)
        
        # Update all line colors to use theme colors
        for line in ax_plot.get_lines():
            line.set_color(ACCENT_BLUE)
        
        # Force redraw to apply theme changes
        canvas_plot.draw_idle()
        
        anim = animate_line(fig_anim, ax_anim, t, y, speed_var.get())
        return [anim], None

    def setup_rk4_test2():
        nonlocal ax_anim
        fig_anim.clf()
        fig_anim.patch.set_facecolor(DARK_BG)
        ax_anim = fig_anim.add_subplot(111)
        ax_anim.set_facecolor(AX_BG)
        
        # Apply theme colors to axes
        ax_anim.tick_params(colors=FG_COLOR)
        for spine in ax_anim.spines.values():
            spine.set_edgecolor(FG_COLOR)
        ax_anim.grid(True, alpha=0.3, color=FG_COLOR)
        
        import rk4_test2 as mod
        t, y = mod.run(ax=ax_plot)
        
        # Apply comprehensive theme to the plot created by the module
        ax_plot.set_facecolor(AX_BG)
        ax_plot.tick_params(colors=FG_COLOR)
        for spine in ax_plot.spines.values():
            spine.set_edgecolor(FG_COLOR)
        ax_plot.grid(True, alpha=0.3, color=FG_COLOR)
        
        # Update all text elements to use theme colors
        if ax_plot.get_title():
            ax_plot.set_title(ax_plot.get_title(), color=FG_COLOR, fontweight='bold')
        if ax_plot.get_xlabel():
            ax_plot.set_xlabel(ax_plot.get_xlabel(), color=FG_COLOR, fontweight='bold')
        if ax_plot.get_ylabel():
            ax_plot.set_ylabel(ax_plot.get_ylabel(), color=FG_COLOR, fontweight='bold')
        
        # Update legend if it exists
        legend = ax_plot.get_legend()
        if legend:
            legend.set_facecolor(DARKER_BG)
            legend.set_edgecolor(FG_COLOR)
            for text in legend.get_texts():
                text.set_color(FG_COLOR)
        
        # Update all line colors to use theme colors
        for line in ax_plot.get_lines():
            line.set_color(ACCENT_ORANGE)
        
        # Force redraw to apply theme changes
        canvas_plot.draw_idle()
        
        anim = animate_line(fig_anim, ax_anim, t, y, speed_var.get())
        return [anim], None

    def setup_rk4_test3():
        nonlocal ax_anim
        fig_anim.clf()
        fig_anim.patch.set_facecolor(DARK_BG)
        ax_anim = fig_anim.add_subplot(111)
        ax_anim.set_facecolor(AX_BG)
        
        # Apply theme colors to axes
        ax_anim.tick_params(colors=FG_COLOR)
        for spine in ax_anim.spines.values():
            spine.set_edgecolor(FG_COLOR)
        ax_anim.grid(True, alpha=0.3, color=FG_COLOR)
        
        import rk4_test3 as mod
        t, x, _ = mod.run(ax=ax_plot)
        
        # Apply comprehensive theme to the plot created by the module
        ax_plot.set_facecolor(AX_BG)
        ax_plot.tick_params(colors=FG_COLOR)
        for spine in ax_plot.spines.values():
            spine.set_edgecolor(FG_COLOR)
        ax_plot.grid(True, alpha=0.3, color=FG_COLOR)
        
        # Update all text elements to use theme colors
        if ax_plot.get_title():
            ax_plot.set_title(ax_plot.get_title(), color=FG_COLOR, fontweight='bold')
        if ax_plot.get_xlabel():
            ax_plot.set_xlabel(ax_plot.get_xlabel(), color=FG_COLOR, fontweight='bold')
        if ax_plot.get_ylabel():
            ax_plot.set_ylabel(ax_plot.get_ylabel(), color=FG_COLOR, fontweight='bold')
        
        # Update legend if it exists
        legend = ax_plot.get_legend()
        if legend:
            legend.set_facecolor(DARKER_BG)
            legend.set_edgecolor(FG_COLOR)
            for text in legend.get_texts():
                text.set_color(FG_COLOR)
        
        # Update all line colors to use theme colors
        for line in ax_plot.get_lines():
            line.set_color(ACCENT_GREEN)
        
        # Force redraw to apply theme changes
        canvas_plot.draw_idle()
        
        anim = animate_line(fig_anim, ax_anim, t, x, speed_var.get())
        return [anim], None

    def create_synchronized_animations(t, speed):
        """Create animations with synchronized timing."""
        total_time = t[-1] - t[0] if len(t) > 1 else 1.0
        target_duration = max(1.0, total_time / speed)
        interval = max(16, int(target_duration * 1000 / len(t)))
        return interval

    def setup_pendulum():
        import pendulum as mod
        
        # Use the t_end setting from the settings tab
        simulation_time = t_end_var.get()
        
        t, phi, omega, energy = mod.run(
            L=l_var.get(),
            phi0=np.radians(phi_var.get()),  # Convert degrees to radians
            g=g_var.get(),
            h=h_var.get(),
            t_final=simulation_time,  # Use the settings value
            air_resistance=drag_var.get(),
            plot=False,
        )
        
        # CRITICAL FIX: Update figure and canvas backgrounds for 2D pendulum
        fig_anim.patch.set_facecolor(DARK_BG)
        fig_plot.patch.set_facecolor(DARK_BG)
        
        # CRITICAL FIX: Force canvas widget background updates for both windows
        if 'canvas_anim' in globals() and canvas_anim:
            canvas_widget = canvas_anim.get_tk_widget()
            canvas_widget.configure(bg=DARK_BG, highlightbackground=DARK_BG, highlightcolor=DARK_BG)
            
            # Update entire parent frame hierarchy
            try:
                parent = canvas_widget.master
                while parent and parent != root:
                    try:
                        parent.configure(background=DARK_BG)
                    except:
                        pass
                    parent = getattr(parent, 'master', None)
            except:
                pass
            
            # Force immediate redraw
            canvas_anim.draw_idle()
        
        if 'canvas_plot' in globals() and canvas_plot:
            canvas_widget = canvas_plot.get_tk_widget()
            canvas_widget.configure(bg=DARK_BG, highlightbackground=DARK_BG, highlightcolor=DARK_BG)
            
            # Update entire parent frame hierarchy
            try:
                parent = canvas_widget.master
                while parent and parent != root:
                    try:
                        parent.configure(background=DARK_BG)
                    except:
                        pass
                    parent = getattr(parent, 'master', None)
            except:
                pass
            
            # Force immediate redraw
            canvas_plot.draw_idle()
            try:
                parent = canvas_widget.master
                while parent and parent != root:
                    try:
                        parent.configure(background=DARK_BG)
                    except:
                        pass
                    parent = getattr(parent, 'master', None)
            except:
                pass
        
        L_val = l_var.get()
        g_val = g_var.get()
        drag_val = drag_var.get()
        kinetic = 0.5 * (L_val ** 2) * omega ** 2
        potential = g_val * L_val * (1 - np.cos(phi))
        acceleration = (
            -(g_val / L_val) * np.sin(phi) - drag_val * omega * np.abs(omega)
        )
        
        # FIXED: Create proper sine wave comparison
        initial_angle_deg = np.abs(phi_var.get())
        if initial_angle_deg < 30 and drag_val < 0.01:  # Small angle, low damping
            # Use proper analytical solution for small angles
            w0 = np.sqrt(g_val / L_val)
            sine = phi[0] * np.cos(w0 * t)  # Analytical small-angle solution
        else:
            # For large angles or damped motion, use a theoretical reference
            w0 = np.sqrt(g_val / L_val)  # Theoretical frequency
            sine = np.radians(phi_var.get()) * np.cos(w0 * t)  # Simple harmonic reference
        
        max_amp = max(np.max(np.abs(phi)), np.max(np.abs(sine)))
        
        pendulum = {
            "t": t,
            "Angle": phi,  # This is in radians
            "Sine": sine,
            "Angular velocity": omega,
            "Angular acceleration": acceleration,
            "Energy": energy,
            "Kinetic": kinetic,
            "Potential": potential,
        }
        animations = [
            animate_pendulum(fig_anim, ax_anim, t, phi, l_var.get(), speed_var.get())
        ]
        dataset = pendulum.get(graph_var.get(), pendulum["Angle"])
        if graph_var.get() == "Energy":
            min_val = min(np.min(dataset), np.min(kinetic), np.min(potential))
            max_val = max(np.max(dataset), np.max(kinetic), np.max(potential))
            animations.append(
                animate_energy(
                    fig_plot,
                    ax_plot,
                    t,
                    kinetic,
                    potential,
                    dataset,
                    speed_var.get(),
                    (min_val, max_val),
                )
            )
        elif graph_var.get() == "Angle":
            # FIXED: Always show comparison between actual and theoretical
            max_amp = max(np.max(np.abs(phi)), np.max(np.abs(sine)))
            animations.append(
                animate_two_lines(
                    fig_plot,
                    ax_plot,
                    t,
                    phi,
                    sine,
                    speed_var.get(),
                    (-max_amp * 1.1, max_amp * 1.1),  # Dynamic bounds
                    labels=("θ (actual)", "Sine"),  # Updated labels
                )
            )
        else:
            animations.append(
                animate_line(fig_plot, ax_plot, t, dataset, speed_var.get())
            )
        ax_plot.set_xlabel('t')
        ax_plot.set_ylabel(graph_var.get())
        return animations, pendulum

    def setup_pendulum3d():
        import pendulum3d as mod
        ax_anim.view_init(default_elev, default_azim)
        
        # Use the t_end setting from the settings tab
        simulation_time = t_end_var.get()
        
        (
            t,
            theta,
            psi,
            theta_dot,
            phi_dot,
            energy,
        ) = mod.run(
            L=l_var.get(),
            theta0=np.radians(phi_var.get()),
            phi0=np.radians(psi_var.get()),
            phi_dot0=np.radians(psi_dot_var.get()),
            g=g_var.get(),
            h=h_var.get(),
            t_final=simulation_time,  # Use the settings value
            air_resistance=drag_var.get(),
            force_x=force_x_var.get(),
            force_y=force_y_var.get(),
            force_z=force_z_var.get(),
            plot=False,
        )
        L_val = l_var.get()
        g_val = g_var.get()
        drag_val = drag_var.get()
        x = L_val * np.sin(theta) * np.cos(psi)
        y = L_val * np.sin(theta) * np.sin(psi)
        z = -L_val * np.cos(theta)
        vx = L_val * (
            theta_dot * np.cos(theta) * np.cos(psi)
            - phi_dot * np.sin(theta) * np.sin(psi)
        )
        vy = L_val * (
            theta_dot * np.cos(theta) * np.sin(psi)
            + phi_dot * np.sin(theta) * np.cos(psi)
        )
        vz = -L_val * theta_dot * np.sin(theta)
        max_amp = max(np.max(np.abs(theta)), np.max(np.abs(psi)))
        # Wrap azimuth angle to keep it in [-π, π] range for better visualization
        psi_wrapped = ((psi + np.pi) % (2 * np.pi)) - np.pi
        max_amp = max(np.max(np.abs(theta)), np.max(np.abs(psi_wrapped)))
        kinetic = 0.5 * (L_val ** 2) * (
            theta_dot ** 2 + (np.sin(theta) ** 2) * phi_dot ** 2
        )
        potential = g_val * L_val * (1 - np.cos(theta))
        acceleration = (
            np.sin(theta) * np.cos(theta) * phi_dot ** 2
            - (g_val / L_val) * np.sin(theta)
            - drag_val * theta_dot * np.abs(theta_dot)
        )
        pendulum = {
            "t": t,
            "Angle": theta,
            "Psi": psi_wrapped,  # Use wrapped version for plotting
            "Angular velocity": theta_dot,
            "phi_dot": phi_dot,
            "Angular acceleration": acceleration,
            "Energy": energy,
            "Kinetic": kinetic,
            "Potential": potential,
            "x": x,
            "y": y,
            "z": z,
            "vx": vx,
            "vy": vy,
            "vz": vz,
        }
        applied = None
        if show_vectors_var.get() and (
            force_x_var.get() or force_y_var.get() or force_z_var.get()
        ):
            applied = np.tile(
                [force_x_var.get(), force_y_var.get(), force_z_var.get()],
                (len(t), 1),
            )
        animations = [
            animate_pendulum3d(
                fig_anim,
                ax_anim,
                t,
                x,
                y,
                z,
                vx,
                vy,
                vz,
                l_var.get(),
                g_val,
                speed_var.get(),
                show_trajectory_var.get(),
                show_vectors_var.get(),
                applied,
                show_axes_var.get(),
                show_true_path_var.get(),
            )
        ]
        dataset = pendulum.get(graph_var.get(), pendulum["Angle"])
        if graph_var.get() == "Energy":
            min_val = min(np.min(dataset), np.min(kinetic), np.min(potential))
            max_val = max(np.max(dataset), np.max(kinetic), np.max(potential))
            animations.append(
                animate_energy(
                    fig_plot,
                    ax_plot,
                    t,
                    kinetic,
                    potential,
                    dataset,
                    speed_var.get(),
                    (min_val, max_val),
                )
            )
        elif graph_var.get() == "Angle":
            animations.append(
                animate_angles(
                    t,
                    theta,
                    psi_wrapped,  # Use wrapped psi
                    speed_var.get(),
                    (-max_amp * 1.1, max_amp * 1.1),  # Use dynamic bounds with margin
                )
            )
        else:
            animations.append(
                animate_line(fig_plot, ax_plot, t, dataset, speed_var.get())
            )
        ax_plot.set_xlabel('t')
        ax_plot.set_ylabel('Angle' if graph_var.get() == "Angle" else graph_var.get())
        return animations, pendulum

    simulation_setup = {
        "RK4 Test 1": setup_rk4_test1,
        "RK4 Test 2": setup_rk4_test2,
        "RK4 Test 3": setup_rk4_test3,
        "Pendulum": setup_pendulum,
        "3D Pendulum": setup_pendulum3d,
    }

    def run_selected():
        nonlocal ani, pendulum_data, screenshot_taken
        screenshot_taken = False
        selection = option_var.get()
        ax_plot.clear()
        ax_plot.set_facecolor(AX_BG)
        if selection == "3D Pendulum" and graph_var.get() == "Angle":
            init_plot()
        for a in ani:
            a.event_source.stop()
        ani.clear()
        pendulum_data = None
        fps_var.set("FPS: 0")
        setup_func = simulation_setup.get(selection)
        if setup_func is not None:
            new_ani, pendulum_data = setup_func()
            ani.extend(new_ani)
        canvas_anim.draw()
        canvas_plot.draw()
    def start_sim() -> None:
        nonlocal running
        running = True
        for a in ani:
            a.event_source.start()
        root.update_idletasks()

    def pause_sim() -> None:
        nonlocal running
        running = False
        for a in ani:
            a.event_source.stop()
        run_play_btn.configure(text="▶ Play")
        root.update_idletasks()

    def reset_sim() -> None:
        """Enhanced reset function with proper cleanup and smooth transitions."""
        nonlocal running, has_run
        
        try:
            # Show progress feedback with animation
            update_status("🔄 Resetting simulation...", 25, True)
            
            # Stop all animations properly
            running = False
            for animation in ani:
                try:
                    if hasattr(animation, 'event_source') and animation.event_source:
                        animation.event_source.stop()
                    if hasattr(animation, '_stop'):
                        animation._stop()
                except Exception:
                    pass
            
            # Clear animation list completely
            ani.clear()
            
            # Reset state variables
            has_run = False
            
            update_status("🧹 Clearing displays...", 50, True)
            
            # Clear and reset plots with proper theming
            try:
                if ax_plot:
                    ax_plot.clear()
                    ax_plot.set_facecolor(AX_BG)
                    ax_plot.grid(True, alpha=0.3, color=FG_COLOR)
                    ax_plot.tick_params(colors=FG_COLOR)
                    for spine in ax_plot.spines.values():
                        spine.set_edgecolor(FG_COLOR)
                
                if ax_anim:
                    ax_anim.clear()
                    ax_anim.set_facecolor(AX_BG)
                    # Reset 3D view if applicable
                    if hasattr(ax_anim, 'view_init'):
                        ax_anim.view_init(default_elev, default_azim)
                        # Reconfigure 3D plot limits
                        limit = l_var.get() * 1.2
                        ax_anim.set_xlim(-limit, limit)
                        ax_anim.set_ylim(-limit, limit)
                        ax_anim.set_zlim(-limit, limit)
                        ax_anim.set_box_aspect([1, 1, 1])
                
                # Reinitialize based on current selection
                selection = option_var.get()
                if selection == "3D Pendulum" and graph_var.get() == "Angle":
                    init_plot()
                
                update_status("🎨 Refreshing interface...", 75, True)
                
                # Reset UI elements with smooth transitions
                run_play_btn.configure(text="▶ Run")
                create_fade_in_effect(run_play_btn)
                
                # Force canvas redraw with proper themes
                canvas_anim.draw_idle()
                canvas_plot.draw_idle()
                
                update_status("✅ Reset complete!", 100, True)
                root.after(2000, lambda: update_status("🚀 Ready", 0))
                
            except Exception as e:
                update_status(f"❌ Reset failed: {str(e)}", 0)
                print(f"Reset error details: {e}")  # Debug output
                
            root.update_idletasks()
            
        except Exception as e:
            update_status(f"❌ Reset failed: {str(e)}", 0)
            print(f"Reset error details: {e}")  # Debug output

    def step_sim() -> None:
        for a in ani:
            a.event_source.stop()
            a._step()
        canvas_anim.draw()
        canvas_plot.draw()

    def set_speed(value: float) -> None:
        speed_var.set(value)

    def run_or_play() -> None:
        nonlocal has_run
        if not has_run:
            run_selected()
            start_sim()
            has_run = True
            run_play_btn.configure(text="▶ Play")
        else:
            start_sim()

    run_play_btn = ttk.Button(action_frame, text="▶ Run", command=run_or_play, style="Success.TButton")
    run_play_btn.grid(row=0, column=0, padx=PADDING, pady=PADDING, sticky="ew")
    
    pause_btn = ttk.Button(action_frame, text="⏸ Pause", command=pause_sim, style="Warning.TButton")
    pause_btn.grid(row=1, column=0, padx=PADDING, pady=PADDING, sticky="ew")
    
    reset_btn = ttk.Button(action_frame, text="↻ Reset", command=reset_sim, style="Purple.TButton")
    reset_btn.grid(row=2, column=0, padx=PADDING, pady=PADDING, sticky="ew")
    
    step_btn = ttk.Button(action_frame, text="⏭ Step", command=step_sim, style="Modern.TButton")
    step_btn.grid(row=3, column=0, padx=PADDING, pady=PADDING, sticky="ew")
    
    # Speed control with better alignment
    speed_frame = ttk.Frame(action_frame)
    speed_frame.grid(row=4, column=0, padx=PADDING, pady=PADDING, sticky="ew")
    speed_frame.columnconfigure(0, weight=1)

    speed_label = ttk.Label(speed_frame, text="Speed", font=("Inter", 10, "bold"))
    speed_label.grid(row=0, column=0, sticky="w", pady=(0, 4))

    speed_dropdown = ttk.Combobox(
        speed_frame,
        textvariable=speed_var,
        values=[0.5, 1.0, 2.0, 4.0],
        state="readonly",
        font=("Inter", 10),
        width=12
    )
    speed_dropdown.grid(row=1, column=0, sticky="ew", pady=(0, 8))
    speed_dropdown.bind(
        "<<ComboboxSelected>>", lambda e: set_speed(speed_var.get())
    )

    # FPS counter with proper alignment
    fps_label = ttk.Label(speed_frame, textvariable=fps_var, font=("Inter", 9))
    fps_label.grid(row=2, column=0, sticky="w")

    pendulum_export_button = ttk.Button(
        export_controls, text="Pendel exportieren", command=export_pendulum, style="Modern.TButton"
    )
    pendulum_export_button.grid(row=0, column=0, padx=PADDING, pady=PADDING, sticky="ew")

    diagram_export_button = ttk.Button(
        export_controls, text="Diagramm exportieren", command=export_plot, style="Modern.TButton"
    )
    diagram_export_button.grid(row=1, column=0, padx=PADDING, pady=PADDING, sticky="ew")

    btn_width = min(
        MAX_BUTTON_WIDTH,
        max(1, root.winfo_width() // 30)
    )
    pendulum_export_button.configure(width=btn_width)
    diagram_export_button.configure(width=btn_width)

    # Setup enhanced features
    setup_keyboard_shortcuts()
    setup_parameter_validation()
    update_status("✨ PhysikSim Ready - Press F2 for help", 0)
    
    # Apply comprehensive theming after all widgets are created
    def apply_comprehensive_theming():
        """Apply comprehensive theming to all elements including matplotlib."""
        try:
            # Update all matplotlib elements
            update_plot_theme(current_theme_var.get())
            
            # Apply modern styling to all widgets
            apply_modern_styling_to_all_widgets(root)
            
            # Update canvas backgrounds
            try:
                if 'params_viz_canvas' in locals():
                    params_viz_canvas.configure(bg=DARK_BG)
            except:
                pass
            
            root.update_idletasks()
            
        except Exception as e:
            print(f"Theming error: {e}")

    # Apply comprehensive theming after all widgets are created
    def apply_comprehensive_theming():
        """Apply comprehensive theming to all elements including matplotlib."""
        try:
            # Update all matplotlib elements
            update_plot_theme(current_theme_var.get())
            
            # Refresh all LabelFrame themes
            refresh_all_labelframe_themes()
            
            # Apply modern styling to all widgets
            apply_modern_styling_to_all_widgets(root)
            
            # Update canvas backgrounds
            try:
                if 'params_viz_canvas' in locals():
                    params_viz_canvas.configure(bg=DARK_BG)
            except:
                pass
            
            root.update_idletasks()
            
        except Exception as e:
            print(f"Theming error: {e}")

    # Apply theming with a small delay to ensure all widgets are created
    root.after(200, apply_comprehensive_theming)
    
    # Force an initial theme refresh
    # ========== DELAYED INITIALIZATION ==========
    # Schedule theme refresh after UI is fully loaded to ensure proper styling
    root.after(500, refresh_all_labelframe_themes)
    
    # Apply modern styling to all widgets across the entire application
    root.after(100, lambda: apply_modern_styling_to_all_widgets(root))

    # ========== START APPLICATION ==========
    # Start the main event loop to begin the interactive simulation
    root.mainloop()


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()

