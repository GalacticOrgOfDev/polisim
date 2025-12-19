"""Custom UI widgets for the economic projector application."""

import tkinter as tk
from tkinter import ttk


class ScrollableFrame(ttk.Frame):
    """A scrollable frame widget that can contain many child widgets."""
    
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Create main container frame
        self.canvas = tk.Canvas(self, highlightthickness=0)

        # Create scrollbars
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.hsb = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)

        # Create the scrollable frame inside the canvas
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)

        # Set up the scrolling window
        self._window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Configure canvas scrolling
        self.canvas.configure(
            yscrollcommand=self.vsb.set,
            xscrollcommand=self.hsb.set
        )

        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.hsb.grid(row=1, column=0, sticky="ew")

        # Configure grid weights
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Set minimum canvas size
        self.canvas.config(width=200, height=200)

        # Bind mouse wheel
        self.bind_mouse_scroll()

    def bind_mouse_scroll(self):
        """Enable mouse wheel scrolling in both directions."""
        def _on_mousewheel(event):
            shift_pressed = event.state & 0x1  # Check if Shift is pressed

            if shift_pressed:
                # Horizontal scroll
                self.canvas.xview_scroll(int(-1 * (event.delta/120)), "units")
            else:
                # Vertical scroll
                self.canvas.yview_scroll(int(-1 * (event.delta/120)), "units")

        # Bind mouse wheel events
        self.canvas.bind("<MouseWheel>", _on_mousewheel)

    def _on_frame_configure(self, event=None):
        """Update scroll region when frame size changes."""
        # Reset the scroll region to encompass the inner frame
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        # Get the requested width of the frame
        frame_width = self.scrollable_frame.winfo_reqwidth()
        frame_height = self.scrollable_frame.winfo_reqheight()

        # Get the width of the canvas's parent (the main window)
        parent_width = self.winfo_width() - self.vsb.winfo_reqwidth()
        parent_height = self.winfo_height() - self.hsb.winfo_reqheight()

        # Set canvas dimensions
        canvas_width = max(frame_width, parent_width)
        canvas_height = min(frame_height, parent_height)

        # Update canvas size
        self.canvas.config(width=canvas_width, height=canvas_height)
