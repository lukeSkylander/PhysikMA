import tkinter as tk

def set_state_recursive(widget, state):
    """Recursively set the state for a widget and all its descendants."""
    try:
        widget.configure(state=state)
    except tk.TclError:
        pass
    for child in widget.winfo_children():
        set_state_recursive(child, state)
