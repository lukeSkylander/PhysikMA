import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
from tkinter import filedialog
import matplotlib
# Embed matplotlib using the TkAgg backend
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import animation
import matplotlib.pyplot as plt
plt.style.use('dark_background')
import numpy as np
import datetime
import time
import os
from save_projection_svg import export_projections
try:
    from PIL import ImageGrab  # type: ignore
except Exception:  # Pillow is optional; screenshot feature will fail gracefully
    ImageGrab = None
from ui_utils import set_state_recursive

# ---------------------------------------------------------------------------
# Theme configuration
# ---------------------------------------------------------------------------
DARK_BG = "#0d1117"  # GitHub dark background
DARKER_BG = "#010409"  # Even darker for contrast
AX_BG = "#000000"
FG_COLOR = "#ffffff"
ACCENT_BG = "#21262d"  # Subtle accent
ACCENT_BLUE = "#58a6ff"  # Modern blue accent
ACCENT_GREEN = "#56d364"  # Success green
ACCENT_ORANGE = "#f85149"  # Warning/error red
ACCENT_PURPLE = "#bc8cff"  # Purple accent
BORDER_COLOR = "#30363d"  # Subtle borders
TEXT_MUTED = "#7d8590"  # Muted text

# Status colours for future messages
STATUS_SUCCESS = "#2ecc71"  # green
STATUS_WARNING = "#ff8c00"  # orange

# Spacing and rounding parameters
PADDING = 8
BORDER_RADIUS = 6
TARGET_FPS = 30
MAX_TRAIL_POINTS = 1000

# Enhanced preset configurations with simulation end time
PRESET_CONFIGS = {
    "Simple Pendulum": {
        "L": 1.0, "phi": 15, "g": 9.81, "h": 0.01, "drag": 0.0, "t_end": 30.0
    },
    "Foucault Pendulum": {
        "L": 2.0, "phi": 10, "psi": 0, "g": 9.81, "h": 0.005, "t_end": 120.0
    },
    "Damped Pendulum": {
        "L": 1.0, "phi": 30, "g": 9.81, "h": 0.01, "drag": 0.1, "t_end": 60.0
    },
    "Chaotic Pendulum": {
        "L": 1.0, "phi": 179, "g": 9.81, "h": 0.001, "drag": 0.01, "t_end": 20.0
    }
}

# Animation and transition settings
ANIMATION_DURATION = 150  # milliseconds
HOVER_LIFT = 2  # pixels to lift on hover

# Enhanced Color themes with smooth transitions
THEMES = {
    "Dark": {
        "bg": "#0d1117", "accent": "#58a6ff", "darker": "#010409",
        "success": "#56d364", "warning": "#f85149", "purple": "#bc8cff"
    },
    "Light": {
        "bg": "#ffffff", "accent": "#0969da", "darker": "#f6f8fa",
        "success": "#28a745", "warning": "#dc3545", "purple": "#6f42c1"
    },
    "Solarized": {
        "bg": "#002b36", "accent": "#268bd2", "darker": "#073642",
        "success": "#859900", "warning": "#cb4b16", "purple": "#d33682"
    },
    "Dracula": {
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


def configure_theme(root: tk.Tk, theme_name="Dark") -> ttk.Style:
    """Configure ttk styles with enhanced modern theming and smooth transitions."""
    global DARK_BG, ACCENT_BLUE, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_PURPLE, DARKER_BG, FG_COLOR, AX_BG
    
    style = ttk.Style(root)
    style.theme_use("clam")
    
    # Get theme colors and update globals FIRST
    theme = THEMES.get(theme_name, THEMES["Dark"])
    DARK_BG = theme["bg"]
    ACCENT_BLUE = theme["accent"]
    DARKER_BG = theme["darker"]
    ACCENT_GREEN = theme["success"]
    ACCENT_ORANGE = theme["warning"]
    ACCENT_PURPLE = theme["purple"]
    
    # Update text and plot colors based on theme
    if theme_name == "Light":
        FG_COLOR = "#000000"  # Black text for light theme
        AX_BG = "#f8f9fa"     # Light gray for plots
    else:
        FG_COLOR = "#ffffff"  # White text for dark themes
        AX_BG = "#000000"     # Black for plots

    # Configure base styles with proper color inheritance and enhanced fonts
    style.configure("TFrame", background=DARK_BG, padding=PADDING, relief="flat")
    style.configure("TLabel", background=DARK_BG, foreground=FG_COLOR, padding=PADDING, font=("Inter", 10))
    # CRITICAL FIX: Configure TLabelframe with proper styling
    # First ensure the layout exists
    try:
        style.layout("TLabelframe")
    except tk.TclError:
        # Create a basic layout if it doesn't exist
        style.layout("TLabelframe", [
            ('Labelframe.border', {'sticky': 'nswe', 'children': [
                ('Labelframe.padding', {'sticky': 'nswe', 'children': [
                    ('Labelframe.label', {'side': 'top', 'sticky': 'w'}),
                    ('Labelframe.focus', {'sticky': 'nswe'})
                ]})
            ]})
        ])
    
    # Configure the main LabelFrame style with LARGE, VISIBLE text
    style.configure(
        "TLabelframe", 
        background=DARK_BG, 
        foreground=FG_COLOR,  # This affects the label text
        borderwidth=1,
        relief="solid",
        padding=PADDING,
        font=("Inter", 14, "bold")  # LARGER font for better visibility
    )
    
    # CRITICAL: Configure the label element specifically
    style.configure(
        "TLabelframe.Label",
        background=DARK_BG, 
        foreground=FG_COLOR,
        font=("Inter", 14, "bold"),  # Large, bold font
        padding=(8, 4)
    )
    
    # Enhanced Black.TLabelframe styling for darker frames
    style.configure(
        "Black.TLabelframe",
        background=DARKER_BG,
        foreground=FG_COLOR,
        borderwidth=1,
        relief="solid", 
        padding=PADDING,
        font=("Inter", 14, "bold")  # LARGER font for better visibility
    )
    
    # Configure the label element for Black style
    style.configure(
        "Black.TLabelframe.Label",
        background=DARKER_BG,
        foreground=FG_COLOR,
        font=("Inter", 14, "bold"),  # Large, bold font
        padding=(8, 4)
    )
    
    # CRITICAL: Map states to ensure colors are applied in all states
    style.map("TLabelframe",
              background=[('active', DARK_BG), ('!active', DARK_BG), ('disabled', DARK_BG)],
              foreground=[('active', FG_COLOR), ('!active', FG_COLOR), ('disabled', FG_COLOR)])
    
    style.map("TLabelframe.Label",
              background=[('active', DARK_BG), ('!active', DARK_BG), ('disabled', DARK_BG)],
              foreground=[('active', FG_COLOR), ('!active', FG_COLOR), ('disabled', FG_COLOR)])
    
    style.map("Black.TLabelframe",
              background=[('active', DARKER_BG), ('!active', DARKER_BG), ('disabled', DARKER_BG)],
              foreground=[('active', FG_COLOR), ('!active', FG_COLOR), ('disabled', FG_COLOR)])
    
    style.map("Black.TLabelframe.Label",
              background=[('active', DARKER_BG), ('!active', DARKER_BG), ('disabled', DARKER_BG)],
              foreground=[('active', FG_COLOR), ('!active', FG_COLOR), ('disabled', FG_COLOR)])
    style.configure(
        "TCheckbutton", 
        background=DARK_BG, 
        foreground=FG_COLOR, 
        padding=PADDING,
        font=("Inter", 10)
    )
    
    # Enhanced button styles with rounded appearance simulation
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
    
    # Trail length
    ttk.Label(sim_settings_frame, text="Trail Length:").grid(row=2, column=0, sticky="w", padx=8, pady=4)
    trail_scale = ttk.Scale(sim_settings_frame, variable=settings_vars['trail_length'], from_=0, to=2000, orient="horizontal")
    trail_scale.grid(row=2, column=1, sticky="ew", padx=8, pady=4)
    trail_entry = ttk.Entry(sim_settings_frame, textvariable=settings_vars['trail_length'], width=10)
    trail_entry.grid(row=2, column=2, padx=8, pady=4)
    
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
    ttk.Checkbutton(appearance_frame, text="Auto Screenshot", variable=settings_vars['auto_screenshot']).grid(row=2, column=0, sticky="w", padx=8, pady=4)
    
    # Reset settings button
    def reset_settings_to_defaults():
        """Reset all settings to default values with animation."""
        update_status_func("🔄 Resetting settings to defaults...", 50, True)
        
        settings_vars['t_end'].set(30.0)
        settings_vars['current_theme'].set("Dark")
        settings_vars['auto_screenshot'].set(True)
        settings_vars['trail_length'].set(500)
        settings_vars['animation_quality'].set("High")
        settings_vars['grid_visible'].set(True)
        settings_vars['show_fps'].set(True)
        
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


def main():
    root = tk.Tk()
    root.title("PhysikSim - Dynamic Physics Simulator")

    configure_fonts()
    
    # Settings variables - declare early for global access
    t_end_var = tk.DoubleVar(value=30.0)  # Simulation end time
    current_theme_var = tk.StringVar(value="Dark")
    auto_screenshot_var = tk.BooleanVar(value=True)
    trail_length_var = tk.IntVar(value=500)
    animation_quality_var = tk.StringVar(value="High")
    grid_visible_var = tk.BooleanVar(value=True)
    show_fps_var = tk.BooleanVar(value=True)
    
    style = configure_theme(root, current_theme_var.get())
    root.configure(bg=DARK_BG)
    
    # Theme change handler with smooth transition
    def on_theme_change(*args):
        """Enhanced theme change handler with comprehensive UI updates."""
        new_theme = current_theme_var.get()
        
        # Apply new theme with proper global variable updates
        configure_theme(root, new_theme)
        
        # Update matplotlib style based on theme
        if new_theme == "Light":
            plt.style.use('default')
        else:
            plt.style.use('dark_background')
        
        # Update matplotlib plots immediately
        update_plot_theme(new_theme)
        
        # CRITICAL: Force all LabelFrames to update their styles immediately
        def force_labelframe_update(widget):
            """Recursively force update all LabelFrame widgets with proper styling."""
            if isinstance(widget, ttk.LabelFrame):
                try:
                    current_text = widget.cget('text')
                    # Determine which style to use based on content
                    if any(text in current_text for text in ["🎮 Simulation", "⚙️ Pendulum Parameters"]):
                        widget.configure(style="Black.TLabelframe")
                    else:
                        widget.configure(style="TLabelframe")
                    
                    # Force immediate update
                    widget.update_idletasks()
                except Exception as e:
                    print(f"Error updating LabelFrame: {e}")
            
            # Process children
            try:
                for child in widget.winfo_children():
                    force_labelframe_update(child)
            except:
                pass
        
        # Apply to entire root
        force_labelframe_update(root)
        
        # CRITICAL: Update ALL frame backgrounds
        def update_all_frames(widget):
            """Update all frame backgrounds recursively."""
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
        
        # CRITICAL: Force canvas widget background updates with comprehensive approach
        try:
            if 'canvas_anim' in globals() and canvas_anim:
                canvas_widget = canvas_anim.get_tk_widget()
                canvas_widget.configure(bg=DARK_BG, highlightbackground=DARK_BG, highlightcolor=DARK_BG)
                # Update parent frame too
                try:
                    parent = canvas_widget.master
                    parent.configure(background=DARK_BG)
                    # Also update grandparent if it exists
                    if hasattr(parent, 'master') and parent.master:
                        try:
                            parent.master.configure(background=DARK_BG)
                        except:
                            pass
                except:
                    pass
                canvas_anim.draw_idle()
                
            if 'canvas_plot' in globals() and canvas_plot:
                canvas_widget = canvas_plot.get_tk_widget()
                canvas_widget.configure(bg=DARK_BG, highlightbackground=DARK_BG, highlightcolor=DARK_BG)
                # Update parent frame too
                try:
                    parent = canvas_widget.master
                    parent.configure(background=DARK_BG)
                    # Also update grandparent if it exists
                    if hasattr(parent, 'master') and parent.master:
                        try:
                            parent.master.configure(background=DARK_BG)
                        except:
                            pass
                except:
                    pass
                canvas_plot.draw_idle()
        except Exception as e:
            print(f"Canvas background update error: {e}")
        
        # Update other canvas backgrounds
        try:
            if 'params_viz_canvas' in locals():
                params_viz_canvas.configure(bg=DARK_BG, highlightbackground=DARK_BG)
        except:
            pass
        
        # Force complete redraw
        root.update_idletasks()
        
        # Update status with visual feedback
        if 'update_status' in locals():
            update_status(f"🎨 Applied {new_theme} theme", 100, True)
            root.after(2000, lambda: update_status("🚀 Ready", 0))
        
        # Update status with visual feedback
        if 'update_status' in locals():
            update_status(f"🎨 Applied {new_theme} theme", 100, True)
            root.after(2000, lambda: update_status("🚀 Ready", 0))

    def update_plot_theme(theme_name):
        """Update matplotlib plots to match the selected theme with comprehensive coverage."""
        try:
            global AX_BG, FG_COLOR, DARK_BG
            
            # Update matplotlib style first based on theme
            if theme_name == "Light":
                plt.style.use('default')
            else:
                plt.style.use('dark_background')
            
            # Update figure backgrounds to match current theme
            if 'fig_anim' in globals() and fig_anim:
                fig_anim.patch.set_facecolor(DARK_BG)
                # Force figure background update
                fig_anim.set_facecolor(DARK_BG)
            if 'fig_plot' in globals() and fig_plot:
                fig_plot.patch.set_facecolor(DARK_BG)
                # Force figure background update  
                fig_plot.set_facecolor(DARK_BG)
            
            # Update axis backgrounds and colors for animation plot
            if 'ax_anim' in globals() and ax_anim:
                ax_anim.set_facecolor(AX_BG)
                if hasattr(ax_anim, 'tick_params'):
                    ax_anim.tick_params(colors=FG_COLOR)
                    # For 3D plots, also update individual axis colors
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
                # Update the tkinter canvas background to match theme
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
            '<F1>': lambda e: show_help_dialog(),
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
    
    def show_help_dialog():
        """Show enhanced help dialog with animations."""
        help_text = """🔥 PhysikSim - Keyboard Shortcuts

⌨️ Simulation Controls:
Space          - Start/Resume simulation
Escape         - Pause simulation  
Ctrl+R         - Reset simulation
Ctrl+S         - Step simulation
Ctrl+Q         - Quit application

🎨 Interface:
F11            - Toggle fullscreen
F1             - Show this help
Ctrl+T         - Cycle themes

🖱️ Mouse Controls (3D View):
• Click and drag to rotate
• Scroll to zoom
• Right-click drag to pan

💡 Tips:
• Use presets for quick setup
• Adjust settings in Settings tab
• Export animations from Export tab
        """
        
        help_window = tk.Toplevel(root)
        help_window.title("PhysikSim Help & Shortcuts")
        help_window.geometry("500x400")
        help_window.configure(bg=DARK_BG)
        help_window.transient(root)
        help_window.grab_set()
        
        # Center the help window
        help_window.update_idletasks()
        x = (help_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (help_window.winfo_screenheight() // 2) - (400 // 2)
        help_window.geometry(f"500x400+{x}+{y}")
        
        # Modern help content
        text_widget = tk.Text(
            help_window, 
            bg=ACCENT_BG, 
            fg=FG_COLOR, 
            font=("Inter", 10),
            wrap=tk.WORD,
            padx=16,
            pady=16,
            relief="flat",
            borderwidth=0
        )
        text_widget.pack(expand=True, fill="both", padx=16, pady=16)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
        
        # Close button
        close_btn = create_animated_button(
            help_window,
            text="Got it! 👍",
            command=help_window.destroy,
            style="Success.TButton"
        )
        close_btn.pack(pady=16)
        root.bind('<F11>', lambda e: toggle_fullscreen())
        root.bind('<F2>', lambda e: show_help_dialog())
    
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
        """Show keyboard shortcuts help dialog."""
        help_text = """Keyboard Shortcuts:
        
Space          - Start/Resume simulation
Escape         - Pause simulation  
Ctrl+R         - Reset simulation
Ctrl+S         - Step simulation
Ctrl+Q         - Quit application
F11            - Toggle fullscreen
F2             - Show this help

Mouse Controls (3D View):
- Click and drag to rotate
- Scroll to zoom
- Right-click drag to pan
        """
        
        help_window = tk.Toplevel(root)
        help_window.title("Keyboard Shortcuts")
        help_window.geometry("400x300")
        help_window.configure(bg=DARK_BG)
        help_window.transient(root)
        help_window.grab_set()
        
        text_widget = tk.Text(
            help_window, 
            bg=ACCENT_BG, 
            fg=FG_COLOR, 
            font=("Inter", 10),
            wrap=tk.WORD,
            padx=16,
            pady=16
        )
        text_widget.pack(expand=True, fill="both", padx=16, pady=16)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)

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
    last_font_size = None
    last_slider_font_size = None
    last_desc_font_size = None
    screenshot_taken = False
    pendulum_data: dict[str, np.ndarray] | None = None
    running = False
    has_run = False
    def resize_ui(event):
        """Adjust fonts when the window size changes."""
        nonlocal last_font_size, last_slider_font_size, last_desc_font_size
        # Only handle resize events triggered by the root window itself
        if event.widget is not root:
            return
        size = max(8, int(min(event.width, event.height) / 50))

        if size != last_font_size:
            for f in default_fonts:
                f.configure(size=size)
            last_font_size = size

        desc_size = max(8, size - 2)
        if desc_size != last_desc_font_size:
            desc_font.configure(size=desc_size)
            last_desc_font_size = desc_size

        entry_size = min(int(size * 1.4), 32)
        if entry_size != last_slider_font_size:
            slider_font.configure(size=entry_size)
            for e in inputs:
                e.configure(font=slider_font)
            last_slider_font_size = entry_size

        if desc_label is not None:
            # Ensure description text fits within sidebar bounds with proper margins
            sidebar_width = int(root.winfo_width() * 0.3)
            desc_label.configure(wraplength=max(200, sidebar_width - 40))
        if run_play_btn is not None:
            btn_width = min(MAX_BUTTON_WIDTH, max(1, event.width // 30))
            if pendulum_export_button is not None:
                pendulum_export_button.configure(width=btn_width)
            if diagram_export_button is not None:
                diagram_export_button.configure(width=btn_width)


    root.bind("<Configure>", resize_ui)

    def take_screenshot():
        selection = option_var.get()
        if selection == "3D Pendulum":
            params = dict(
                L=l_var.get(),
                theta0=np.radians(phi_var.get()),
                phi0=np.radians(psi_var.get()),
                phi_dot0=np.radians(psi_dot_var.get()),
                g=g_var.get(),
                h=h_var.get(),
                t_final=pendulum_data["t"][-1] if pendulum_data is not None else 30.0,
                air_resistance=drag_var.get(),
                force_x=force_x_var.get(),
                force_y=force_y_var.get(),
                force_z=force_z_var.get(),
            )
            export_projections(**params)
        else:
            if ImageGrab is None:
                print("Pillow not available, cannot take screenshot.")
                return
            x = root.winfo_rootx()
            y = root.winfo_rooty()
            w = root.winfo_width()
            h = root.winfo_height()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(
                f"screenshot_{timestamp}.png"
            )

    def auto_screenshot():
        nonlocal screenshot_taken
        if not screenshot_taken:
            screenshot_taken = True
            take_screenshot()

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
            params = dict(
                L=l_var.get(),
                theta0=np.radians(phi_var.get()),
                phi0=np.radians(psi_var.get()),
                phi_dot0=np.radians(psi_dot_var.get()),
                g=g_var.get(),
                h=h_var.get(),
                t_final=pendulum_data["t"][-1] if pendulum_data is not None else 30.0,
                air_resistance=drag_var.get(),
                force_x=force_x_var.get(),
                force_y=force_y_var.get(),
                force_z=force_z_var.get(),
            )
            export_projections(
                out_floor=base + "_floor.svg",
                out_wall=base + "_wall.svg",
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
        """Apply an impulse to the running 3D pendulum simulation."""
        if option_var.get() != "3D Pendulum" or pendulum_data is None:
            return
        if pendulum_data.get("frame") is None:
            return

        import pendulum3d as mod

        frame = int(pendulum_data["frame"])
        t = pendulum_data["t"]
        if frame >= len(t) - 1:
            return

        L_val = l_var.get()
        g_val = g_var.get()
        h = h_var.get()
        drag_val = drag_var.get()
        fx = force_x_var.get()
        fy = force_y_var.get()
        fz = force_z_var.get()
        theta = pendulum_data["Angle"]
        psi = pendulum_data["Psi"]
        theta_dot = pendulum_data["Angular velocity"]
        phi_dot = pendulum_data["phi_dot"]
        remaining = len(t) - frame
        t_final = (remaining - 1) * h

        (
            _t_new,
            theta_new,
            psi_new,
            theta_dot_new,
            phi_dot_new,
            energy_new,
        ) = mod.run(
            L=L_val,
            theta0=theta[frame],
            phi0=psi[frame],
            theta_dot0=theta_dot[frame],
            phi_dot0=phi_dot[frame],
            g=g_val,
            h=h,
            air_resistance=drag_val,
            force_x=fx,
            force_y=fy,
            force_z=fz,
            t_final=t_final,
            plot=False,
        )

        x = pendulum_data["x"]
        y = pendulum_data["y"]
        z = pendulum_data["z"]
        vx = pendulum_data["vx"]
        vy = pendulum_data["vy"]
        vz = pendulum_data["vz"]

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

        slice_from = slice(frame, None)
        theta[slice_from] = theta_new
        psi[slice_from] = psi_new
        theta_dot[slice_from] = theta_dot_new
        phi_dot[slice_from] = phi_dot_new
        pendulum_data["Energy"][slice_from] = energy_new
        pendulum_data["Kinetic"][slice_from] = kinetic_new
        pendulum_data["Potential"][slice_from] = potential_new
        pendulum_data["Angular acceleration"][slice_from] = acceleration_new
        x[slice_from] = x_new
        y[slice_from] = y_new
        z[slice_from] = z_new
        vx[slice_from] = vx_new
        vy[slice_from] = vy_new
        vz[slice_from] = vz_new

        force_x_var.set(0.0)
        force_y_var.set(0.0)
        force_z_var.set(0.0)

    options = ["RK4 Test 1", "RK4 Test 2", "RK4 Test 3", "Pendulum", "3D Pendulum"]
    option_var = tk.StringVar(value=options[0])

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

    close_btn = ttk.Button(sidebar, text="Close", command=lambda: hide_sidebar())
    close_btn.pack(anchor="ne")

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
        'auto_screenshot': auto_screenshot_var,
        'trail_length': trail_length_var,
        'animation_quality': animation_quality_var,
        'grid_visible': grid_visible_var,
        'show_fps': show_fps_var
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
    fps_var = tk.StringVar(value="FPS: 0")


    graph_options = ["Angle", "Angular velocity", "Angular acceleration", "Energy"]
    graph_var = tk.StringVar(value=graph_options[0])

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

    # Simulation selection group inside the sidebar
    # FIXED: Update widget creations to explicitly set styles
    sim_frame = ttk.LabelFrame(
        sim_controls, text="🎮 Simulation"
    )
    sim_frame.configure(style="Black.TLabelframe")  # Apply style after creation
    sim_frame.grid(row=0, column=0, sticky="ew", padx=PADDING, pady=PADDING)
    sim_frame.columnconfigure(0, weight=1)
    dropdown = ttk.Combobox(sim_frame, textvariable=option_var, values=options, state="readonly")
    dropdown.grid(row=0, column=0, padx=PADDING, pady=PADDING, sticky="ew")

    # 3D options will be moved to visualization tab
    # viz_3d_frame = ttk.LabelFrame(sim_controls, text="3D Options")
    # viz_3d_frame.grid(row=1, column=0, sticky="ew", padx=PADDING, pady=PADDING)
    # viz_3d_frame.columnconfigure(0, weight=1)

    # 3D visualization controls will be added to viz_frame after it's created

    sidebar_target_width = 0
    sidebar_animation_start_time = 0
    sidebar_animation_start_width = 0

    def animate_sidebar(opening: bool) -> None:
        """Enhanced sidebar animation with smooth easing."""
        nonlocal sidebar_target_width, sidebar_animation_start_time, sidebar_animation_start_width
        
        if opening and sidebar_target_width == 0:
            sidebar_target_width = int(root.winfo_width() * 0.3)
            sidebar_animation_start_time = root.tk.call('clock', 'milliseconds')
            sidebar_animation_start_width = sidebar.winfo_width()
            
        current_time = root.tk.call('clock', 'milliseconds')
        elapsed = max(0, current_time - sidebar_animation_start_time)
        progress = min(1.0, elapsed / ANIMATION_DURATION)
        
        # Apply smooth easing
        eased_progress = ease_in_out_cubic(progress)
        
        if opening:
            new_w = int(sidebar_animation_start_width + 
                       (sidebar_target_width - sidebar_animation_start_width) * eased_progress)
        else:
            if not hasattr(animate_sidebar, '_closing_start_time'):
                animate_sidebar._closing_start_time = current_time
                animate_sidebar._closing_start_width = sidebar.winfo_width()
            
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
        root.columnconfigure(0, minsize=new_w)
        
        # Continue animation if not complete
        if progress < 1.0:
            root.after(int(1000 / TARGET_FPS), animate_sidebar, opening)
        elif not opening:
            sidebar_target_width = 0
            if hasattr(animate_sidebar, '_closing_start_time'):
                delattr(animate_sidebar, '_closing_start_time')
                delattr(animate_sidebar, '_closing_start_width')

    def show_sidebar(frame: ttk.Frame) -> None:
        """Show sidebar with smooth transition animation."""
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
        
        # Auto-hide status after delay
        root.after(2000, lambda: update_status("Ready"))

    def hide_sidebar(event: tk.Event | None = None) -> None:
        animate_sidebar(False)

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
        "Δt [s]",
        h_var,
        row,
        "Integrationszeitintervall",
        0.001,
        0.1,
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

    apply_impulse_btn = ttk.Button(
        params_frame, text="Impuls anwenden", command=apply_impulse
    )
    apply_impulse_btn.grid(row=row, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
    row += 1

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
    ]
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

    reset_cam_btn = ttk.Button(
        viz_frame, text="Reset camera", command=lambda: reset_camera()
    )
    reset_cam_btn.grid(row=4, column=0, sticky="w", padx=5, pady=5)

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

    def reset_camera() -> None:
        if ax_anim and hasattr(ax_anim, "view_init"):
            ax_anim.view_init(default_elev, default_azim)
        canvas_anim.draw_idle()

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
            
        # Apply theming to plot area as well
        ax_plot.set_facecolor(AX_BG)
        ax_plot.tick_params(colors=FG_COLOR)
        for spine in ax_plot.spines.values():
            spine.set_edgecolor(FG_COLOR)
        ax_plot.grid(True, alpha=0.3, color=FG_COLOR)
            
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

            # Keep pendulum animation in ani[0] if available
            pend_anim = ani[0] if ani else None
            ani.clear()
            if pend_anim:
                ani.append(pend_anim)

            screenshot_taken = False
            if graph_var.get() == "Energy":
                # Animate total, kinetic and potential energy together
                t = pendulum_data["t"]
                total = pendulum_data["Energy"]
                kinetic = pendulum_data["Kinetic"]
                potential = pendulum_data["Potential"]
                min_val = min(np.min(total), np.min(kinetic), np.min(potential))
                max_val = max(np.max(total), np.max(kinetic), np.max(potential))
                ani_line = animate_energy(fig_plot, ax_plot, t, kinetic,
                                          potential, total, speed_var.get(),
                                          (min_val, max_val))
            elif option_var.get() == "3D Pendulum" and graph_var.get() == "Angle":
                # Use dynamic amplitude bounds based on actual data
                theta = pendulum_data["Angle"]
                psi = pendulum_data["Psi"]
                max_amp = max(np.max(np.abs(theta)), np.max(np.abs(psi)))
                y_range = (-max_amp * 1.1, max_amp * 1.1)  # Add 10% margin
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
                    labels=("φ", "Sin(t)"),
                )
            else:
                dataset = pendulum_data.get(graph_var.get(), pendulum_data["Angle"])
                # Use dynamic bounds for angle data
                if graph_var.get() == "Angle":
                    max_val = np.max(np.abs(dataset))
                    y_range = (-max_val * 1.1, max_val * 1.1)  # Add 10% margin
                else:
                    y_range = None
                ani_line = animate_line(
                    fig_plot,
                    ax_plot,
                    pendulum_data["t"],
                    dataset,
                    speed_var.get(),
                    y_range,
                )
            
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
        ax_plot.set_xlabel("Zeit [s]", color=FG_COLOR)
        ax_plot.set_ylabel("Winkel [rad]", color=FG_COLOR)
        
        # Theme-aware legend
        legend = ax_plot.legend(facecolor=DARKER_BG, edgecolor=FG_COLOR)
        legend.get_frame().set_alpha(0.8)
        for text in legend.get_texts():
            text.set_color(FG_COLOR)

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
            
            # FIXED: Show complete path to prevent flickering
            # Only use trail limits for very long simulations
            start_idx = 0
            if frame > 1000:  # Only start limiting after 1000 frames
                start_idx = max(0, frame - 800)  # Keep last 800 points
            
            line.set_data(t[start_idx:frame+1], y[start_idx:frame+1])
            if frame == len(t) - 1:
                root.after(0, auto_screenshot)
            
            last_draw_time = current
            return line,

        # Optimize interval calculation to prevent excessive updates
        total_time = t[-1] - t[0] if len(t) > 1 else 1.0
        target_duration = max(1.0, total_time / speed)  # Minimum 1 second duration
        interval = max(16, int(target_duration * 1000 / len(t)))  # Minimum 16ms (60fps)
        
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

        last_time = time.time()
        last_draw_time = 0  # Anti-flicker timing

        def update(frame):
            nonlocal last_time, last_draw_time
            if not running:
                return line1, line2
                
            current = time.time()
            
            # FIXED: Less aggressive frame rate limiting to prevent flickering
            if current - last_draw_time < 1.0 / (TARGET_FPS * 2):
                return line1, line2
            
            # Update FPS counter
            dt = current - last_time
            if dt > 0:
                fps = 1.0 / dt
                fps_var.set(f"FPS: {fps:.1f}")
            last_time = current
            
            # FIXED: Show complete trajectory without trail limits
            line1.set_data(t[0:frame+1], y1[0:frame+1])
            line2.set_data(t[0:frame+1], y2[0:frame+1])
            
            if frame == len(t) - 1:
                root.after(0, auto_screenshot)
                
            last_draw_time = current
            return line1, line2

        # Optimize interval calculation to prevent excessive updates
        total_time = t[-1] - t[0] if len(t) > 1 else 1.0
        target_duration = max(1.0, total_time / speed)  # Minimum 1 second duration
        interval = max(16, int(target_duration * 1000 / len(t)))  # Minimum 16ms (60fps)
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
        """Animate 2D pendulum with proper theme support."""
        ax.clear()
        ax.set_facecolor(AX_BG)  # Use theme-appropriate background
        
        # Apply theme colors to axes
        ax.tick_params(colors=FG_COLOR)
        for spine in ax.spines.values():
            spine.set_edgecolor(FG_COLOR)
        ax.grid(True, alpha=0.3, color=FG_COLOR)
        
        x = L * np.sin(phi)
        y = -L * np.cos(phi)
        line, = ax.plot([], [], 'o-', lw=2, markersize=15, color=ACCENT_BLUE)
        ax.set_xlim(-L * 1.2, L * 1.2)
        ax.set_ylim(-L * 1.2, L * 0.2)
        ax.set_aspect('equal', adjustable='box')
        ax.set_title('2D Pendulum', color=FG_COLOR, fontsize=12, fontweight='bold')

        def init():
            line.set_data([], [])
            return line,

        last_time = time.time()

        def update(frame):
            nonlocal last_time
            if not running:
                return line,
            line.set_data([0, x[frame]], [0, y[frame]])
            if frame == len(t) - 1:
                root.after(0, auto_screenshot)
            current = time.time()
            dt = current - last_time
            if dt > 0:
                fps_var.set(f"FPS: {1.0 / dt:.1f}")
            last_time = current
            return line,

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
    ):
        """Animate a 3D pendulum with proper theme support and timing.

        The function now works directly with ``x, y, z`` coordinates and their
        corresponding velocities ``vx, vy, vz``. Force vectors (gravity, tension
        and an optional applied force) are computed using vector operations
        instead of angular quantities.
        """

        ax.clear()
        ax.set_facecolor(AX_BG)  # Use theme-appropriate background
        
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
        
        # FIXED: Projection lines that are always visible when trajectory is enabled
        line_xy, = ax.plot([], [], [], color=ACCENT_GREEN, lw=2, alpha=0.9, label='XY Projection')
        line_yz, = ax.plot([], [], [], color=ACCENT_ORANGE, lw=2, alpha=0.9, label='YZ Projection')
        line_zx, = ax.plot([], [], [], color=ACCENT_PURPLE, lw=2, alpha=0.9, label='ZX Projection')

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
            return line, line_xy, line_yz, line_zx

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

            # CRITICAL FIX: Always show full trajectory when enabled - NO TRAIL LIMITS
            if show_trajectory:
                # Show the COMPLETE trajectory from start to current frame
                # This ensures projections never disappear regardless of time
                trajectory_slice = slice(0, frame + 1)
                
                # XY projection on floor (z = -limit) - FULL PATH
                line_xy.set_data(x[trajectory_slice], y[trajectory_slice])
                line_xy.set_3d_properties(np.full(frame + 1, -limit))
                
                # YZ projection on side wall (x = limit) - FULL PATH
                line_yz.set_data(np.full(frame + 1, limit), y[trajectory_slice])
                line_yz.set_3d_properties(z[trajectory_slice])
                
                # ZX projection on back wall (y = -limit) - FULL PATH
                line_zx.set_data(x[trajectory_slice], np.full(frame + 1, -limit))
                line_zx.set_3d_properties(z[trajectory_slice])
                
                artists = [line, line_xy, line_yz, line_zx, *arrows]
            else:
                # Hide projections when trajectory is not enabled
                line_xy.set_data([], [])
                line_xy.set_3d_properties([])
                line_yz.set_data([], [])
                line_yz.set_3d_properties([])
                line_zx.set_data([], [])
                line_zx.set_3d_properties([])
                
                artists = [line, *arrows]

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

    def setup_pendulum():
        import pendulum as mod
        
        # Use the t_end setting from the settings tab
        simulation_time = t_end_var.get()
        
        t, phi, omega, energy = mod.run(
            L=l_var.get(),
            phi0=np.radians(phi_var.get()),
            g=g_var.get(),
            h=h_var.get(),
            t_final=simulation_time,  # Use the settings value
            air_resistance=drag_var.get(),
            plot=False,
        )
        L_val = l_var.get()
        g_val = g_var.get()
        drag_val = drag_var.get()
        kinetic = 0.5 * (L_val ** 2) * omega ** 2
        potential = g_val * L_val * (1 - np.cos(phi))
        acceleration = (
            -(g_val / L_val) * np.sin(phi) - drag_val * omega * np.abs(omega)
        )
        sine = np.sin(L_val * t)
        max_amp = max(np.max(np.abs(phi)), np.max(np.abs(sine)))
        pendulum = {
            "t": t,
            "Angle": phi,
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
            animations.append(
                animate_two_lines(
                    fig_plot,
                    ax_plot,
                    t,
                    phi,
                    sine,
                    speed_var.get(),
                    (-max_amp, max_amp),
                    labels=("θ", "Sine"),
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
        export_controls, text="Pendel exportieren", command=export_pendulum
    )
    pendulum_export_button.grid(row=0, column=0, padx=PADDING, pady=PADDING, sticky="ew")

    diagram_export_button = ttk.Button(
        export_controls, text="Diagramm exportieren", command=export_plot
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
    root.after(500, refresh_all_labelframe_themes)
    
    # Apply modern styling to all widgets in the application
    root.after(100, lambda: apply_modern_styling_to_all_widgets(root))

    root.mainloop()


if __name__ == "__main__":
    main()
