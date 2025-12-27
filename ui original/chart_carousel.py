"""Enhanced Chart Carousel: PNG images + interactive HTML in Tk app with keyboard nav.

Loads PNG charts and corresponding HTML from `reports/charts/<PolicyName>/`.
- Display modes: PNG (static image) or HTML (interactive via embedded browser).
- Keyboard navigation: left/right arrow keys to cycle charts.
- "Switch to HTML" button toggles between PNG and interactive modes.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import webbrowser


class ChartCarousel(ttk.Frame):
    def __init__(self, master, charts_root=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.charts_root = charts_root or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports', 'charts')
        self.policy = None
        self.chart_files = []
        self.index = 0
        self.photo = None
        self.display_mode = 'png'  # 'png' or 'html'

        # UI: policy selector at top
        self.policy_var = tk.StringVar()
        self.policy_combo = ttk.Combobox(self, textvariable=self.policy_var, state='readonly')
        self.policy_combo.bind('<<ComboboxSelected>>', self.on_policy_selected)
        self.policy_combo.pack(fill='x', padx=4, pady=4)

        # Large canvas for chart display (expanded)
        self.canvas = tk.Canvas(self, bg='white', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True, padx=4, pady=4)

        # Control buttons at bottom
        controls = ttk.Frame(self)
        controls.pack(fill='x', padx=4, pady=4)
        
        self.prev_btn = ttk.Button(controls, text='◀ Prev', command=self.prev)
        self.prev_btn.pack(side='left', padx=2)
        
        self.next_btn = ttk.Button(controls, text='Next ▶', command=self.next)
        self.next_btn.pack(side='left', padx=2)
        
        self.info_label = ttk.Label(controls, text='')
        self.info_label.pack(side='left', padx=10)
        
        self.mode_btn = ttk.Button(controls, text='View Interactive HTML', command=self.toggle_mode)
        self.mode_btn.pack(side='right', padx=2)
        
        self.open_btn = ttk.Button(controls, text='Open in Browser', command=self.open_interactive)
        self.open_btn.pack(side='right', padx=2)

        # Enable keyboard navigation
        self.focus_set()
        self.bind('<Left>', lambda e: self.prev())
        self.bind('<Right>', lambda e: self.next())
        self.bind('<Tab>', lambda e: self.toggle_mode())
        
        self.reload_policies()
        self.bind('<Configure>', lambda e: self._redraw())

    def reload_policies(self):
        if not os.path.exists(self.charts_root):
            self.policy_combo['values'] = []
            return
        policies = [d for d in os.listdir(self.charts_root) if os.path.isdir(os.path.join(self.charts_root, d))]
        policies.sort()
        self.policy_combo['values'] = policies
        if policies:
            self.policy_combo.set(policies[0])
            self.load_policy(policies[0])

    def on_policy_selected(self, event=None):
        name = self.policy_var.get()
        self.load_policy(name)

    def load_policy(self, policy_name):
        self.policy = policy_name
        pdir = os.path.join(self.charts_root, policy_name)
        pngs = [f for f in os.listdir(pdir) if f.lower().endswith('.png')]
        pngs.sort()
        self.chart_files = [os.path.join(pdir, p) for p in pngs]
        self.index = 0
        self._redraw()

    def toggle_mode(self):
        """Switch between PNG and HTML display modes."""
        if not self.chart_files:
            messagebox.showinfo('No Charts', 'No charts available for selected policy.')
            return
        png = self.chart_files[self.index]
        html = os.path.splitext(png)[0] + '.html'
        if not os.path.exists(html):
            messagebox.showinfo('No HTML', f'HTML version not found for {os.path.basename(png)}.\nClick "Open in Browser" to view interactive chart.')
            return
        if self.display_mode == 'png':
            self.display_mode = 'html'
            self.mode_btn.config(text='View PNG Static')
        else:
            self.display_mode = 'png'
            self.mode_btn.config(text='View Interactive HTML')
        self._redraw()

    def _render_html(self):
        """Display HTML preview in canvas with hint to open in browser."""
        path = self.chart_files[self.index]
        html = os.path.splitext(path)[0] + '.html'
        title = os.path.basename(path).replace('_', ' ').replace('.png', '')
        
        # Draw preview info on canvas
        self.canvas.delete('all')
        self.canvas.create_text(10, 10, anchor='nw', text=title + ' (Interactive)', 
                                fill='black', font=('TkDefaultFont', 10, 'bold'))
        self.canvas.create_text(10, 40, anchor='nw', 
                                text='Interactive Plotly chart.\nClick "Open in Browser" for full interactivity:\n• Hover for values\n• Pan/zoom\n• Toggle series\n• Export to PNG',
                                fill='#333', font=('TkDefaultFont', 9))

    def _redraw(self):
        """Dispatch rendering based on display mode."""
        if not self.chart_files:
            self.canvas.delete('all')
            self.canvas.create_text(10, 10, anchor='nw', 
                                    text='No charts found. Run run_visualize.py or run_report.py to generate charts.',
                                    fill='gray', font=('TkDefaultFont', 9))
            self.info_label.config(text='')
            return
        
        # Update info label
        self.info_label.config(text=f'{self.index + 1} / {len(self.chart_files)}')
        
        if self.display_mode == 'html':
            self._render_html()
        else:
            self._render_png()

    def _render_png(self):
        """Render PNG image on canvas with title."""
        self.canvas.delete('all')
        path = self.chart_files[self.index]
        try:
            img = Image.open(path)
            # Resize to fit canvas while preserving aspect ratio
            cw = max(100, self.winfo_width() - 20)
            ch = max(100, self.winfo_height() - 80)
            img_ratio = img.width / img.height
            canvas_ratio = cw / ch
            if img_ratio > canvas_ratio:
                new_w = cw
                new_h = int(cw / img_ratio)
            else:
                new_h = ch
                new_w = int(ch * img_ratio)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(img)
            self.canvas.create_image(cw//2 + 10, ch//2 + 10, image=self.photo, anchor='center')
            # Title
            title = os.path.basename(path).replace('_', ' ').replace('.png', '')
            self.canvas.create_text(10, 10, anchor='nw', text=title, fill='black', font=('TkDefaultFont', 10, 'bold'))
        except Exception as e:
            self.canvas.create_text(10, 10, anchor='nw', text=f'Failed to load image: {e}', fill='red')

    def prev(self):
        if not self.chart_files:
            return
        self.index = (self.index - 1) % len(self.chart_files)
        self.display_mode = 'png'  # Reset to PNG when navigating
        self.mode_btn.config(text='View Interactive HTML')
        self._redraw()

    def next(self):
        if not self.chart_files:
            return
        self.index = (self.index + 1) % len(self.chart_files)
        self.display_mode = 'png'  # Reset to PNG when navigating
        self.mode_btn.config(text='View Interactive HTML')
        self._redraw()

    def open_interactive(self):
        # Open corresponding HTML if exists, else open PNG
        if not self.chart_files:
            return
        png = self.chart_files[self.index]
        html = os.path.splitext(png)[0] + '.html'
        if os.path.exists(html):
            webbrowser.open('file://' + os.path.abspath(html))
        else:
            webbrowser.open('file://' + os.path.abspath(png))
