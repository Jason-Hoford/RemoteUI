"""Desktop viewer for RemoteCompose .rc files.

A tkinter-based GUI that wraps the existing rplayer rendering pipeline,
providing an interactive way to view, animate, and inspect .rc files
without memorizing CLI commands.

Architecture:
    .rc file  →  reader.py (parse)  →  RcDocument
                                          ↓
                          runtime.py (RuntimeState, expressions, animation)
                                          ↓
                          renderer.py (Skia offscreen render)  →  skia.Image
                                          ↓
                          encodeToData()  →  PNG bytes  →  tkinter PhotoImage
                                          ↓
                          tkinter Canvas (display)

Why tkinter:
    - Ships with Python — zero additional dependencies
    - All we need is: image display, sliders, buttons, file dialogs
    - Skia does the real rendering; tkinter is just the display shell
    - Practical testing tool, not a polished product

Limitations:
    - Frame rate limited by Skia render time + PNG encode + tkinter redraw
    - No GPU acceleration (offscreen CPU rendering only)
    - No touch/mouse interaction forwarded to .rc content
    - tkinter styling is basic/platform-native

Usage:
    python -m rplayer.viewer                  # open empty, use File > Open
    python -m rplayer.viewer demo.rc          # open a specific file
    python -m rplayer.viewer demos/output/    # open with a folder to browse
"""

import os
import sys
import io
import time
import math
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


def _import_skia():
    """Import skia, giving a clear error if missing."""
    try:
        import skia
        return skia
    except ImportError:
        messagebox.showerror(
            'Missing dependency',
            'skia-python is required.\n\nInstall with:\n  pip install skia-python')
        sys.exit(1)


class RcViewer:
    """Main viewer application window."""

    # Animation timing
    TARGET_FPS = 30
    FRAME_MS = 1000 // TARGET_FPS  # ~33ms per frame
    TIME_STEP = 1.0 / TARGET_FPS
    MAX_TIME = 300.0  # 5 minute max for slider

    def __init__(self, root: tk.Tk, initial_path: str = None):
        self.root = root
        self.root.title('rplayer Viewer')
        self.root.geometry('820x700')
        self.root.minsize(400, 350)

        # State
        self.rc_path = None
        self.doc = None
        self.runtime = None
        self.renderer = None
        self.current_time = 0.0
        self.playing = False
        self.last_frame_time = 0.0
        self._after_id = None
        self._photo = None  # prevent GC of PhotoImage
        self._folder_files = []  # .rc files in current folder
        self._folder_index = -1
        self._has_expressions = False

        self._build_ui()
        self._bind_keys()

        if initial_path:
            if os.path.isdir(initial_path):
                self._scan_folder(initial_path)
                if self._folder_files:
                    self._open_file(self._folder_files[0])
            elif os.path.isfile(initial_path):
                self._open_file(initial_path)

    # ── UI construction ──────────────────────────────────────────────

    def _build_ui(self):
        """Build the complete UI layout."""
        # Menu bar
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label='Open File...', command=self._cmd_open,
                              accelerator='Ctrl+O')
        file_menu.add_command(label='Open Folder...', command=self._cmd_open_folder)
        file_menu.add_separator()
        file_menu.add_command(label='Reload', command=self._cmd_reload,
                              accelerator='Ctrl+R')
        file_menu.add_separator()
        file_menu.add_command(label='Export Frame...', command=self._cmd_export_frame,
                              accelerator='Ctrl+S')
        file_menu.add_command(label='Export Sequence...', command=self._cmd_export_sequence)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.root.quit,
                              accelerator='Ctrl+Q')
        menubar.add_cascade(label='File', menu=file_menu)
        self.root.config(menu=menubar)

        # Main frame
        main = ttk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True)

        # ── Top info bar ──
        info_frame = ttk.Frame(main)
        info_frame.pack(fill=tk.X, padx=6, pady=(6, 2))

        self.lbl_file = ttk.Label(info_frame, text='No file loaded',
                                  font=('Segoe UI', 10))
        self.lbl_file.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.lbl_info = ttk.Label(info_frame, text='', font=('Segoe UI', 9))
        self.lbl_info.pack(side=tk.RIGHT)

        # ── Canvas area ──
        canvas_frame = ttk.Frame(main, relief='sunken', borderwidth=1)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        self.canvas = tk.Canvas(canvas_frame, bg='#404040',
                                highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # ── Time slider ──
        slider_frame = ttk.Frame(main)
        slider_frame.pack(fill=tk.X, padx=6, pady=2)

        self.lbl_time = ttk.Label(slider_frame, text='t=0.000s', width=12,
                                  font=('Consolas', 10))
        self.lbl_time.pack(side=tk.LEFT)

        self.time_var = tk.DoubleVar(value=0.0)
        self.slider = ttk.Scale(slider_frame, from_=0, to=self.MAX_TIME,
                                orient=tk.HORIZONTAL, variable=self.time_var,
                                command=self._on_slider_change)
        self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 4))

        self.lbl_max = ttk.Label(slider_frame, text='0.0s', width=8,
                                 font=('Consolas', 10))
        self.lbl_max.pack(side=tk.RIGHT)

        # ── Transport controls ──
        ctrl_frame = ttk.Frame(main)
        ctrl_frame.pack(fill=tk.X, padx=6, pady=(2, 6))

        self.btn_prev = ttk.Button(ctrl_frame, text='<< Prev',
                                   command=self._cmd_prev_file, width=8)
        self.btn_prev.pack(side=tk.LEFT, padx=(0, 2))

        self.btn_stop = ttk.Button(ctrl_frame, text='Stop',
                                   command=self._cmd_stop, width=6)
        self.btn_stop.pack(side=tk.LEFT, padx=2)

        self.btn_step_back = ttk.Button(ctrl_frame, text='< Step',
                                        command=self._cmd_step_back, width=6)
        self.btn_step_back.pack(side=tk.LEFT, padx=2)

        self.btn_play = ttk.Button(ctrl_frame, text='Play',
                                   command=self._cmd_play_pause, width=8)
        self.btn_play.pack(side=tk.LEFT, padx=2)

        self.btn_step_fwd = ttk.Button(ctrl_frame, text='Step >',
                                       command=self._cmd_step_forward, width=6)
        self.btn_step_fwd.pack(side=tk.LEFT, padx=2)

        self.btn_next = ttk.Button(ctrl_frame, text='Next >>',
                                   command=self._cmd_next_file, width=8)
        self.btn_next.pack(side=tk.LEFT, padx=2)

        # Right side: status
        self.lbl_status = ttk.Label(ctrl_frame, text='', font=('Segoe UI', 9),
                                    foreground='gray')
        self.lbl_status.pack(side=tk.RIGHT, padx=(8, 0))

        self.lbl_animated = ttk.Label(ctrl_frame, text='',
                                      font=('Segoe UI', 9, 'bold'))
        self.lbl_animated.pack(side=tk.RIGHT, padx=(8, 0))

    def _bind_keys(self):
        """Bind keyboard shortcuts."""
        self.root.bind('<Control-o>', lambda e: self._cmd_open())
        self.root.bind('<Control-r>', lambda e: self._cmd_reload())
        self.root.bind('<Control-s>', lambda e: self._cmd_export_frame())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<space>', lambda e: self._cmd_play_pause())
        self.root.bind('<Right>', lambda e: self._cmd_step_forward())
        self.root.bind('<Left>', lambda e: self._cmd_step_back())
        self.root.bind('<Home>', lambda e: self._cmd_stop())
        self.root.bind('<Escape>', lambda e: self._cmd_stop())
        self.root.bind('<Prior>', lambda e: self._cmd_prev_file())  # Page Up
        self.root.bind('<Next>', lambda e: self._cmd_next_file())   # Page Down

    # ── File loading ─────────────────────────────────────────────────

    def _open_file(self, path: str):
        """Load and display an .rc file."""
        from .player import load_rc
        from .renderer import RcRenderer

        path = os.path.abspath(path)
        self._stop_playback()

        try:
            self.doc, self.runtime = load_rc(path)
        except Exception as e:
            messagebox.showerror('Parse Error',
                                 f'Failed to parse:\n{path}\n\n{e}')
            return

        self.rc_path = path
        self.renderer = RcRenderer(self.doc, scale=1.0, runtime=self.runtime)
        self.current_time = 0.0
        self.time_var.set(0.0)

        # Detect if file has expressions (animated)
        self._has_expressions = bool(self.runtime._float_exprs)

        # Update UI
        basename = os.path.basename(path)
        self.root.title(f'rplayer Viewer — {basename}')
        self.lbl_file.config(text=basename)
        dims = f'{self.doc.width}x{self.doc.height}'
        ops = len(self.doc.operations)
        exprs = len(self.runtime._float_exprs)
        self.lbl_info.config(text=f'{dims}  |  {ops} ops  |  {exprs} exprs')

        if self._has_expressions:
            self.lbl_animated.config(text='ANIMATED', foreground='#0077cc')
        else:
            self.lbl_animated.config(text='STATIC', foreground='#666666')

        # Scan folder for prev/next
        folder = os.path.dirname(path)
        if not self._folder_files or os.path.dirname(
                self._folder_files[0] if self._folder_files else '') != folder:
            self._scan_folder(folder)
        if path in self._folder_files:
            self._folder_index = self._folder_files.index(path)
        self._update_nav_buttons()

        # Render first frame
        self._render_and_display(0.0)

    def _scan_folder(self, folder: str):
        """Scan a folder for .rc files and populate the navigation list."""
        try:
            files = sorted([
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.lower().endswith('.rc')
            ])
            self._folder_files = files
            self._folder_index = 0
        except OSError:
            self._folder_files = []
            self._folder_index = -1

    def _update_nav_buttons(self):
        """Enable/disable prev/next based on folder position."""
        has_files = len(self._folder_files) > 1
        self.btn_prev.config(state='normal' if has_files else 'disabled')
        self.btn_next.config(state='normal' if has_files else 'disabled')
        if has_files:
            pos = f'{self._folder_index + 1}/{len(self._folder_files)}'
            self.lbl_status.config(text=pos)
        else:
            self.lbl_status.config(text='')

    # ── Rendering ────────────────────────────────────────────────────

    def _render_and_display(self, t: float):
        """Render at time t and update the canvas display.

        Pipeline: runtime.step_to(t) → renderer.render() → PNG bytes → PhotoImage
        """
        if not self.renderer:
            return

        self.current_time = t

        # Step the runtime to the requested time
        # For t=0 or rewinding, reset and step forward
        if t <= 0:
            self.runtime.animation_time = 0.0
            self.runtime.frame_count = 0
            self.runtime.wall_time = 0.0
            self.runtime._reset_expressions()
            self.runtime.step(max(t, 0.0))
        else:
            self.runtime.step_to(t)

        # Render via Skia (reuses existing renderer pipeline)
        try:
            image = self.renderer.render()
        except Exception as e:
            self.lbl_status.config(text=f'Render error: {e}')
            return

        # Convert Skia Image → PNG bytes → tkinter PhotoImage
        png_data = image.encodeToData()
        self._photo = tk.PhotoImage(data=bytes(png_data))

        # Display centered on canvas
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        cx = max(0, (cw - self.doc.width) // 2)
        cy = max(0, (ch - self.doc.height) // 2)

        self.canvas.delete('all')
        self.canvas.create_image(cx, cy, anchor=tk.NW, image=self._photo)

        # Update time display
        self.lbl_time.config(text=f't={t:.3f}s')
        self.time_var.set(t)

    def _render_current(self):
        """Re-render at the current time (for reload, resize, etc.)."""
        self._render_and_display(self.current_time)

    # ── Animation playback ───────────────────────────────────────────

    def _start_playback(self):
        """Begin real-time animation playback."""
        if not self.renderer:
            return
        self.playing = True
        self.btn_play.config(text='Pause')
        self.last_frame_time = time.monotonic()
        self._animation_tick()

    def _stop_playback(self):
        """Stop animation playback."""
        self.playing = False
        self.btn_play.config(text='Play')
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None

    def _animation_tick(self):
        """Single animation frame — called repeatedly via root.after()."""
        if not self.playing:
            return

        now = time.monotonic()
        dt = now - self.last_frame_time
        self.last_frame_time = now

        new_time = self.current_time + dt
        if new_time > self.MAX_TIME:
            new_time = 0.0  # loop

        self._render_and_display(new_time)

        # Schedule next frame
        self._after_id = self.root.after(self.FRAME_MS, self._animation_tick)

    # ── Commands ─────────────────────────────────────────────────────

    def _cmd_open(self):
        """Open file dialog to select an .rc file."""
        initial = os.path.dirname(self.rc_path) if self.rc_path else ''
        path = filedialog.askopenfilename(
            title='Open .rc file',
            initialdir=initial or os.path.join(os.getcwd(), 'demos', 'output'),
            filetypes=[('RemoteCompose files', '*.rc'), ('All files', '*.*')])
        if path:
            self._open_file(path)

    def _cmd_open_folder(self):
        """Open a folder and browse .rc files within it."""
        initial = os.path.dirname(self.rc_path) if self.rc_path else ''
        folder = filedialog.askdirectory(
            title='Open folder with .rc files',
            initialdir=initial or os.path.join(os.getcwd(), 'demos', 'output'))
        if folder:
            self._scan_folder(folder)
            if self._folder_files:
                self._open_file(self._folder_files[0])
            else:
                messagebox.showinfo('No files', f'No .rc files found in:\n{folder}')

    def _cmd_reload(self):
        """Reload the current file from disk."""
        if self.rc_path:
            saved_time = self.current_time
            self._open_file(self.rc_path)
            if self._has_expressions and saved_time > 0:
                self._render_and_display(saved_time)

    def _cmd_play_pause(self):
        """Toggle play/pause."""
        if self.playing:
            self._stop_playback()
        else:
            self._start_playback()

    def _cmd_stop(self):
        """Stop playback and reset to t=0."""
        self._stop_playback()
        if self.renderer:
            self._render_and_display(0.0)

    def _cmd_step_forward(self):
        """Step forward one frame (~33ms)."""
        self._stop_playback()
        if self.renderer:
            self._render_and_display(self.current_time + self.TIME_STEP)

    def _cmd_step_back(self):
        """Step backward one frame (~33ms)."""
        self._stop_playback()
        if self.renderer:
            new_t = max(0.0, self.current_time - self.TIME_STEP)
            self._render_and_display(new_t)

    def _cmd_prev_file(self):
        """Navigate to previous .rc file in folder."""
        if not self._folder_files:
            return
        self._folder_index = (self._folder_index - 1) % len(self._folder_files)
        self._open_file(self._folder_files[self._folder_index])

    def _cmd_next_file(self):
        """Navigate to next .rc file in folder."""
        if not self._folder_files:
            return
        self._folder_index = (self._folder_index + 1) % len(self._folder_files)
        self._open_file(self._folder_files[self._folder_index])

    def _cmd_export_frame(self):
        """Export the current frame as PNG."""
        if not self.renderer:
            return
        default_name = os.path.splitext(os.path.basename(
            self.rc_path or 'frame'))[0]
        default_name += f'_t{self.current_time:.3f}s.png'
        path = filedialog.asksaveasfilename(
            title='Export frame as PNG',
            initialfile=default_name,
            defaultextension='.png',
            filetypes=[('PNG image', '*.png')])
        if path:
            try:
                image = self.renderer.render()
                image.save(path)
                self.lbl_status.config(text=f'Exported: {os.path.basename(path)}')
            except Exception as e:
                messagebox.showerror('Export Error', str(e))

    def _cmd_export_sequence(self):
        """Export a short frame sequence to a folder."""
        if not self.renderer:
            return
        folder = filedialog.askdirectory(title='Export frame sequence to folder')
        if not folder:
            return

        # Export 3 seconds at 10fps
        fps = 10
        duration = 3.0
        basename = os.path.splitext(os.path.basename(self.rc_path or 'seq'))[0]

        from .player import load_rc
        from .renderer import RcRenderer

        doc, runtime = load_rc(self.rc_path)
        renderer = RcRenderer(doc, runtime=runtime)

        count = int(duration * fps) + 1
        for i in range(count):
            t = i / fps
            runtime.step_to(t)
            image = renderer.render()
            fname = f'{basename}_f{i:04d}_t{t:.3f}s.png'
            image.save(os.path.join(folder, fname))

        self.lbl_status.config(text=f'Exported {count} frames to {folder}')

    def _on_slider_change(self, value):
        """Handle time slider drag."""
        if self.playing:
            return  # don't interfere with playback
        if self.renderer:
            t = float(value)
            self._render_and_display(t)


def main():
    """Entry point for the viewer application."""
    root = tk.Tk()

    # High-DPI awareness on Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    # Determine initial path from command line
    initial_path = None
    if len(sys.argv) > 1:
        initial_path = sys.argv[1]

    _import_skia()  # check dependency early

    app = RcViewer(root, initial_path=initial_path)
    root.mainloop()


if __name__ == '__main__':
    main()
