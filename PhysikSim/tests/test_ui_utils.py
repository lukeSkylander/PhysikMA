import tkinter as tk
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from ui_utils import set_state_recursive

class DummyWidget:
    def __init__(self, children=None):
        self._children = children or []
        self.state = None

    def configure(self, **kwargs):
        if "state" in kwargs:
            self.state = kwargs["state"]

    def winfo_children(self):
        return self._children

def test_set_state_recursive_nested_widgets():
    leaf = DummyWidget()
    impulse_frame = DummyWidget([leaf])
    slider_frame = DummyWidget([impulse_frame])
    set_state_recursive(slider_frame, tk.DISABLED)
    assert leaf.state == tk.DISABLED
    assert impulse_frame.state == tk.DISABLED
    set_state_recursive(slider_frame, tk.NORMAL)
    assert leaf.state == tk.NORMAL
    assert impulse_frame.state == tk.NORMAL
