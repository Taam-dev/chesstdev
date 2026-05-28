"""
GUI overlay displaying Stockfish suggestions.
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

import chess

from config import Config
from engine_manager import EngineManager, AnalysisResult
from fen_parser import FENProvider


class ChessOverlay:
    """Always-on-top GUI showing Stockfish analysis with full custom background support."""

    def __init__(self):
        # --- Taskbar Icon Grouping on Windows ---
        import sys
        if sys.platform == "win32":
            try:
                import ctypes
                myappid = 'chessassistant.overlay.v1'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception:
                pass

        self.engine = EngineManager()
        self.fen_provider = FENProvider()
        self.auto_refresh = False
        self._running = True
        self._last_analyzed_fen = None
        self.current_bg = "#1a1a2e"
        self.bg_image_path = None
        self._last_width = 0
        self._last_height = 0

        self._build_gui()
        self.root.bind("<Configure>", self._on_resize)

    def _build_gui(self):
        self.root = tk.Tk()
        self.root.title("♟ Chess Assistant")
        self.root.geometry(f"{Config.OVERLAY_WIDTH}x{Config.OVERLAY_HEIGHT}")
        self.root.attributes("-topmost", True)
        self.root.resizable(True, True)
        self.root.configure(bg="#1a1a2e")

        # --- Icon ---
        import os
        import sys
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        icon_ico = os.path.join(base_dir, "icon.ico")
        icon_png = os.path.join(base_dir, "icon.png")
        icon_loaded = False
        
        if os.path.exists(icon_ico):
            try:
                self.root.iconbitmap(icon_ico)
                icon_loaded = True
            except Exception:
                pass
                
        if not icon_loaded and os.path.exists(icon_png):
            try:
                from PIL import Image, ImageTk
                self.icon_photo = ImageTk.PhotoImage(Image.open(icon_png))
                self.root.iconphoto(True, self.icon_photo)
            except Exception:
                pass

        try:
            self.root.attributes("-alpha", Config.OVERLAY_ALPHA)
        except tk.TclError:
            pass

        # --- Styles ---
        style = ttk.Style()
        style.theme_use("clam")

        bg = "#1a1a2e"
        fg = "#e0e0e0"

        style.configure("Dark.TFrame", background=bg)
        style.configure(
            "Dark.TLabel", background=bg, foreground=fg, font=("Consolas", 10)
        )
        style.configure(
            "Title.TLabel",
            background=bg,
            foreground="#f5c2e7",
            font=("Consolas", 16, "bold"),
        )
        style.configure(
            "Move.TLabel",
            background=bg,
            foreground="#a6e3a1",
            font=("Consolas", 28, "bold"),
        )
        style.configure(
            "Score.TLabel",
            background=bg,
            foreground="#fab387",
            font=("Consolas", 18, "bold"),
        )
        style.configure(
            "Eval.TLabel", background=bg, foreground="#cba6f7", font=("Consolas", 11)
        )
        style.configure(
            "PV.TLabel", background=bg, foreground="#89b4fa", font=("Consolas", 9)
        )
        style.configure(
            "Status.TLabel",
            background="#16213e",
            foreground="#7f8c8d",
            font=("Consolas", 9),
        )
        style.configure("Dark.TButton", font=("Consolas", 10, "bold"))
        style.configure(
            "Dark.TCheckbutton", background=bg, foreground=fg, font=("Consolas", 9)
        )

        # --- Canvas Background ---
        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg="#1a1a2e")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.bg_photo = None
        self.bg_image_id = self.canvas.create_image(0, 0, anchor=tk.NW)

        # --- Variables ---
        self.fen_var = tk.StringVar(value="")
        self.auto_var = tk.BooleanVar(value=False)
        self.depth_var = tk.IntVar(value=Config.ENGINE_DEPTH)
        self.theme_var = tk.StringVar(value="Default")
        self.play_as_var = tk.StringVar(value="Both")
        self.turn_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Ready — Enter FEN or click 🔄 Fetch FEN")
        self.opacity_var = tk.DoubleVar(value=95.0)

        # --- Widgets (placed via Canvas create_window) ---
        
        # FEN Entry
        self.fen_entry = ttk.Entry(self.root, textvariable=self.fen_var, font=("Consolas", 9))
        self.fen_entry_id = self.canvas.create_window(0, 0, window=self.fen_entry, anchor=tk.NW)

        # Buttons
        self.analyze_btn = ttk.Button(self.root, text="▶ Analyze", command=self._on_analyze, style="Dark.TButton")
        self.analyze_btn_id = self.canvas.create_window(0, 0, window=self.analyze_btn, anchor=tk.NW)

        self.top3_btn = ttk.Button(self.root, text="📊 Top 3", command=self._on_top3, style="Dark.TButton")
        self.top3_btn_id = self.canvas.create_window(0, 0, window=self.top3_btn, anchor=tk.NW)

        self.fetch_btn = ttk.Button(self.root, text="🔄 Fetch FEN", command=self._on_fetch_fen, style="Dark.TButton")
        self.fetch_btn_id = self.canvas.create_window(0, 0, window=self.fetch_btn, anchor=tk.NW)

        # Options
        self.auto_cb = ttk.Checkbutton(self.root, text="🔁 Auto", variable=self.auto_var, command=self._toggle_auto, style="Dark.TCheckbutton")
        self.auto_cb_id = self.canvas.create_window(0, 0, window=self.auto_cb, anchor=tk.NW)

        self.play_as_menu = ttk.Combobox(self.root, textvariable=self.play_as_var, values=["Both", "White", "Black"], width=6, state="readonly", font=("Consolas", 9))
        self.play_as_menu_id = self.canvas.create_window(0, 0, window=self.play_as_menu, anchor=tk.NW)

        self.depth_spin = ttk.Spinbox(self.root, from_=1, to=30, width=4, textvariable=self.depth_var, font=("Consolas", 10))
        self.depth_spin_id = self.canvas.create_window(0, 0, window=self.depth_spin, anchor=tk.NW)

        # Bg Config
        self.theme_menu = ttk.Combobox(self.root, textvariable=self.theme_var, values=["Default", "Choose Image..."], width=15, state="readonly", font=("Consolas", 9))
        self.theme_menu.bind("<<ComboboxSelected>>", self._on_theme_change)
        self.theme_menu_id = self.canvas.create_window(0, 0, window=self.theme_menu, anchor=tk.NW)

        self.opacity_slider = ttk.Scale(self.root, from_=0.0, to=100.0, variable=self.opacity_var, command=lambda e: self._update_background(), orient=tk.HORIZONTAL)
        self.opacity_slider_id = self.canvas.create_window(0, 0, window=self.opacity_slider, anchor=tk.NW)

        # --- Canvas Text Elements (Transparent Background) ---
        self.title_text_id = self.canvas.create_text(0, 0, text="♟ Chess Assistant", fill="#f5c2e7", font=("Consolas", 16, "bold"), anchor=tk.CENTER)
        self.fen_label_id = self.canvas.create_text(0, 0, text="FEN:", fill="#e0e0e0", font=("Consolas", 10), anchor=tk.W)
        
        self.play_as_label_id = self.canvas.create_text(0, 0, text="Play As:", fill="#e0e0e0", font=("Consolas", 10), anchor=tk.W)
        self.depth_label_id = self.canvas.create_text(0, 0, text="Depth:", fill="#e0e0e0", font=("Consolas", 10), anchor=tk.W)
        
        self.bg_label_id = self.canvas.create_text(0, 0, text="Bg:", fill="#e0e0e0", font=("Consolas", 10), anchor=tk.W)
        self.opacity_label_id = self.canvas.create_text(0, 0, text="Opacity:", fill="#e0e0e0", font=("Consolas", 10), anchor=tk.W)
        
        self.turn_text_id = self.canvas.create_text(0, 0, text="", fill="#e0e0e0", font=("Consolas", 10), anchor=tk.E)
        
        self.separator_line_id = self.canvas.create_line(0, 0, 0, 0, fill="#3f3f5f", width=1)

        # Results
        self.best_move_title_id = self.canvas.create_text(0, 0, text="Best Move:", fill="#e0e0e0", font=("Consolas", 10), anchor=tk.W)
        self.move_text_id = self.canvas.create_text(0, 0, text="—", fill="#a6e3a1", font=("Consolas", 28, "bold"), anchor=tk.W)
        self.move_desc_text_id = self.canvas.create_text(0, 0, text="", fill="#94e2d5", font=("Consolas", 11, "italic"), anchor=tk.W)

        self.eval_title_id = self.canvas.create_text(0, 0, text="Eval:", fill="#e0e0e0", font=("Consolas", 10), anchor=tk.W)
        self.score_text_id = self.canvas.create_text(0, 0, text="—", fill="#fab387", font=("Consolas", 18, "bold"), anchor=tk.W)
        self.eval_text_id = self.canvas.create_text(0, 0, text="", fill="#cba6f7", font=("Consolas", 11), anchor=tk.W)

        self.pv_text_id = self.canvas.create_text(0, 0, text="", fill="#89b4fa", font=("Consolas", 9), anchor=tk.NW, justify=tk.LEFT)

        # Status Bar
        self.status_rect_id = self.canvas.create_rectangle(0, 0, 0, 0, fill="#16213e", outline="")
        self.status_text_id = self.canvas.create_text(0, 0, text="Ready — Enter FEN or click 🔄 Fetch FEN", fill="#7f8c8d", font=("Consolas", 9), anchor=tk.W)

        # Setup initial layout positioning
        self._update_layout(Config.OVERLAY_WIDTH, Config.OVERLAY_HEIGHT)

        # --- Bindings ---
        self.root.bind("<Return>", lambda e: self._on_analyze())
        self.root.bind("<F5>", lambda e: self._on_fetch_fen())
        self.root.bind("<Escape>", lambda e: self._quit())
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

    def _update_layout(self, w: int, h: int):
        """Update positions of all elements on the canvas when the window is resized."""
        # 1. Update background image / solid bg
        self._update_background()

        # 2. Title (Centered)
        self.canvas.coords(self.title_text_id, w // 2, 25)

        # 3. FEN Row (y = 55)
        self.canvas.coords(self.fen_label_id, 15, 55 + 11)
        entry_width = max(100, w - 55 - 15)
        self.canvas.coords(self.fen_entry_id, 55, 55)
        self.canvas.itemconfigure(self.fen_entry_id, width=entry_width, height=22)

        # 4. Buttons Row (y = 90)
        self.canvas.coords(self.analyze_btn_id, 15, 90)
        self.canvas.itemconfigure(self.analyze_btn_id, width=85, height=26)

        self.canvas.coords(self.top3_btn_id, 105, 90)
        self.canvas.itemconfigure(self.top3_btn_id, width=75, height=26)

        self.canvas.coords(self.fetch_btn_id, 185, 90)
        self.canvas.itemconfigure(self.fetch_btn_id, width=105, height=26)

        # 5. Options Row (y = 125)
        self.canvas.coords(self.auto_cb_id, 15, 125)
        self.canvas.itemconfigure(self.auto_cb_id, width=70, height=22)

        self.canvas.coords(self.play_as_label_id, 95, 125 + 11)
        self.canvas.coords(self.play_as_menu_id, 155, 125)
        self.canvas.itemconfigure(self.play_as_menu_id, width=60, height=22)

        self.canvas.coords(self.depth_label_id, 225, 125 + 11)
        self.canvas.coords(self.depth_spin_id, 270, 125)
        self.canvas.itemconfigure(self.depth_spin_id, width=45, height=22)

        # 6. Bg Config Row (y = 160)
        self.canvas.coords(self.bg_label_id, 15, 160 + 11)
        self.canvas.coords(self.theme_menu_id, 45, 160)
        self.canvas.itemconfigure(self.theme_menu_id, width=120, height=22)

        self.canvas.coords(self.opacity_label_id, 180, 160 + 11)
        slider_width = max(50, w - 245 - 15)
        self.canvas.coords(self.opacity_slider_id, 245, 160)
        self.canvas.itemconfigure(self.opacity_slider_id, width=slider_width, height=22)

        # 7. Turn indicator (y = 195)
        self.canvas.coords(self.turn_text_id, w - 15, 195)

        # 8. Separator Line (y = 210)
        self.canvas.coords(self.separator_line_id, 15, 210, w - 15, 210)

        # 9. Results Area
        self.canvas.coords(self.best_move_title_id, 15, 235 + 18)
        self.canvas.coords(self.move_text_id, 105, 235 + 18)

        # Move description (y = 275)
        self.canvas.coords(self.move_desc_text_id, 20, 275)

        # Eval (y = 300)
        self.canvas.coords(self.eval_title_id, 15, 300 + 11)
        self.canvas.coords(self.score_text_id, 70, 300 + 11)

        # Eval description (y = 325)
        self.canvas.coords(self.eval_text_id, 15, 325)

        # PV / Top moves (y = 350)
        self.canvas.coords(self.pv_text_id, 15, 350)
        pv_width = max(100, w - 30)
        self.canvas.itemconfigure(self.pv_text_id, width=pv_width)

        # 10. Status Bar at the bottom
        self.canvas.coords(self.status_rect_id, 0, h - 25, w, h)
        self.canvas.coords(self.status_text_id, 10, h - 13)

    def _update_background(self):
        """Load, resize, and display background image blended with theme background color based on opacity."""
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        if w < 10 or h < 10:
            w, h = Config.OVERLAY_WIDTH, Config.OVERLAY_HEIGHT

        opacity = self.opacity_var.get() / 100.0  # opacity is 0.0 to 1.0

        if self.bg_image_path:
            try:
                from PIL import Image, ImageTk
                img = Image.open(self.bg_image_path)
                img = img.resize((w, h), Image.Resampling.LANCZOS).convert("RGBA")

                # Solid dark theme color #1a1a2e as base
                solid = Image.new("RGBA", (w, h), (26, 26, 46, 255))

                # Blend image and solid color
                blended = Image.blend(solid, img, opacity)
                self.bg_photo = ImageTk.PhotoImage(blended)
                self.canvas.itemconfig(self.bg_image_id, image=self.bg_photo)
                self.canvas.tag_lower(self.bg_image_id)
            except Exception as e:
                self._set_status(f"✗ Image error: {e}")
        else:
            # Default theme (solid color, brightness adjusted via opacity slider)
            self.canvas.itemconfig(self.bg_image_id, image="")
            self.bg_photo = None
            
            # Base color is #1a1a2e -> RGB(26, 26, 46). Adjust brightness based on opacity.
            r = int(26 * opacity)
            g = int(26 * opacity)
            b = int(46 * opacity)
            bg_hex = f"#{r:02x}{g:02x}{b:02x}"
            
            self.canvas.configure(bg=bg_hex)
            status_bg = self._get_darker_color(bg_hex, 0.8)
            self.canvas.itemconfig(self.status_rect_id, fill=status_bg)

    def _on_fetch_fen(self):
        """Fetch FEN from relay server."""
        self._set_status("Fetching FEN from relay server...")

        fen = self.fen_provider.get_fen()
        if fen:
            self.fen_var.set(fen)
            self._update_turn_indicator(fen)
            self._set_status(f"✓ FEN fetched from relay server")
        else:
            self._set_status(
                "✗ Failed to fetch FEN — Check relay server and userscript"
            )

    def _on_analyze(self):
        """Analyze current position."""
        # Try fetching new FEN from server first
        live_fen = self.fen_provider.get_fen()
        if live_fen:
            self.fen_var.set(live_fen)

        fen = self.fen_var.get().strip()
        if not fen:
            self._set_status("⚠ No FEN — Enter FEN or click 🔄 Fetch FEN")
            return

        try:
            chess.Board(fen)
        except ValueError as e:
            self._set_status(f"✗ Invalid FEN: {e}")
            return

        self._update_turn_indicator(fen)
        self._set_status("⏳ Analyzing...")
        self.analyze_btn.configure(state=tk.DISABLED)

        def worker():
            try:
                result = self.engine.analyze(fen, depth=self.depth_var.get())
                self.root.after(0, self._display_result, result)
                self._last_analyzed_fen = fen
            except Exception as ex:
                self.root.after(0, self._set_status, f"✗ Error: {ex}")
            finally:
                self.root.after(0, lambda: self.analyze_btn.configure(state=tk.NORMAL))

        threading.Thread(target=worker, daemon=True).start()

    def _on_top3(self):
        """Show top 3 moves."""
        live_fen = self.fen_provider.get_fen()
        if live_fen:
            self.fen_var.set(live_fen)

        fen = self.fen_var.get().strip()
        if not fen:
            self._set_status("⚠ No FEN")
            return

        try:
            chess.Board(fen)
        except ValueError:
            self._set_status("✗ Invalid FEN")
            return

        self._update_turn_indicator(fen)
        self._set_status("⏳ Analyzing top 3 moves...")
        self.top3_btn.configure(state=tk.DISABLED)

        def worker():
            try:
                results = self.engine.get_top_moves(
                    fen, count=3, depth=self.depth_var.get()
                )
                self.root.after(0, self._display_top_moves, results)
            except Exception as ex:
                self.root.after(0, self._set_status, f"✗ Error: {ex}")
            finally:
                self.root.after(0, lambda: self.top3_btn.configure(state=tk.NORMAL))

        threading.Thread(target=worker, daemon=True).start()

    def _toggle_auto(self):
        """Toggle auto-refresh."""
        self.auto_refresh = self.auto_var.get()
        if self.auto_refresh:
            self._set_status("🔁 Auto-refresh ON")
            self._auto_loop()
        else:
            self._set_status("Auto-refresh OFF")

    def _should_analyze(self, fen: str) -> bool:
        """Check if we should analyze based on 'Play As' setting and FEN turn."""
        try:
            board = chess.Board(fen)
            play_as = self.play_as_var.get()
            if play_as == "Both":
                return True
            elif play_as == "White" and board.turn == chess.WHITE:
                return True
            elif play_as == "Black" and board.turn == chess.BLACK:
                return True
            return False
        except Exception:
            return True

    def _auto_loop(self):
        """Automatically fetch FEN + analyze."""
        if not self.auto_refresh or not self._running:
            return

        fen = self.fen_provider.get_fen()
        if fen:
            if fen != self._last_analyzed_fen:
                self.fen_var.set(fen)
                self._update_turn_indicator(fen)
                if self._should_analyze(fen):
                    self._on_analyze()
                else:
                    opponent = "Black" if self.play_as_var.get() == "White" else "White"
                    self._set_status(f"⏳ Waiting for {opponent}'s move...")
                    self._last_analyzed_fen = fen
        else:
            self._set_status("🔁 Auto — No FEN received from server...")

        self.root.after(Config.REFRESH_INTERVAL_MS, self._auto_loop)

    def _display_result(self, result: AnalysisResult):
        self.canvas.itemconfig(self.move_text_id, text=result.best_move_san)
        self.canvas.itemconfig(self.move_desc_text_id, text=result.best_move_desc)
        self.canvas.itemconfig(self.score_text_id, text=result.score_display)
        self.canvas.itemconfig(self.eval_text_id, text=result.evaluation_text)

        # Eval color based on score
        score_color = "#fab387" # default orange
        if result.score_cp is not None:
            if result.score_cp > 50:
                score_color = "#a6e3a1"  # green
            elif result.score_cp < -50:
                score_color = "#f38ba8"  # red
        elif result.score_mate is not None:
            if result.score_mate > 0:
                score_color = "#a6e3a1"
            else:
                score_color = "#f38ba8"
        self.canvas.itemconfig(self.score_text_id, fill=score_color)

        pv_text = ""
        if result.pv:
            pv_text = "PV: " + " → ".join(result.pv)
        self.canvas.itemconfig(self.pv_text_id, text=pv_text)

        self._set_status(
            f"✓ Depth {result.depth} | {result.thinking_time}s | "
            f"UCI: {result.best_move_uci}"
        )

        # Transmit best move to FEN relay server
        if result.best_move_uci and result.best_move_uci != "—":
            def send_best():
                try:
                    import urllib.request
                    import urllib.parse
                    url = f"http://{Config.RELAY_HOST}:{Config.RELAY_PORT}/set_bestmove?move={urllib.parse.quote(result.best_move_uci)}"
                    urllib.request.urlopen(url, timeout=0.5)
                except Exception:
                    pass
            threading.Thread(target=send_best, daemon=True).start()

    def _display_top_moves(self, results: list[AnalysisResult]):
        if not results:
            self._set_status("No moves found")
            return

        best = results[0]
        self.canvas.itemconfig(self.move_text_id, text=best.best_move_san)
        self.canvas.itemconfig(self.move_desc_text_id, text=best.best_move_desc)
        self.canvas.itemconfig(self.score_text_id, text=best.score_display)
        self.canvas.itemconfig(self.eval_text_id, text=best.evaluation_text)

        lines = []
        medals = ["🥇", "🥈", "🥉"]
        for i, r in enumerate(results):
            medal = medals[i] if i < len(medals) else f"{i + 1}."
            pv = " → ".join(r.pv[:4])
            desc_part = f" ({r.best_move_desc})" if r.best_move_desc else ""
            lines.append(f"{medal} {r.best_move_san:6s}{desc_part} ({r.score_display})\n   PV: {pv}")

        self.canvas.itemconfig(self.pv_text_id, text="\n".join(lines))
        self._set_status(f"✓ Top {len(results)} moves — Depth {best.depth}")

        # Transmit best move to FEN relay server
        if best.best_move_uci and best.best_move_uci != "—":
            def send_best():
                try:
                    import urllib.request
                    import urllib.parse
                    url = f"http://{Config.RELAY_HOST}:{Config.RELAY_PORT}/set_bestmove?move={urllib.parse.quote(best.best_move_uci)}"
                    urllib.request.urlopen(url, timeout=0.5)
                except Exception:
                    pass
            threading.Thread(target=send_best, daemon=True).start()

    def _update_turn_indicator(self, fen: str):
        """Update turn label."""
        try:
            board = chess.Board(fen)
            turn = "⬜ White to move" if board.turn else "⬛ Black to move"
            move_num = board.fullmove_number
            text = f"{turn} (move {move_num})"
        except Exception:
            text = ""
        self.turn_var.set(text)
        if hasattr(self, "canvas") and hasattr(self, "turn_text_id"):
            self.canvas.itemconfig(self.turn_text_id, text=text)

    def _set_status(self, msg: str):
        self.status_var.set(msg)
        if hasattr(self, "canvas") and hasattr(self, "status_text_id"):
            self.canvas.itemconfig(self.status_text_id, text=msg)

    def _on_theme_change(self, event=None):
        theme = self.theme_var.get()
        if theme == "Choose Image...":
            from tkinter import filedialog
            file_path = filedialog.askopenfilename(
                title="Select Background Image",
                filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
            )
            if file_path:
                self.bg_image_path = file_path
                self._update_background()
            else:
                self._restore_previous_theme()
        else:
            self.bg_image_path = None
            self._update_background()

    def _restore_previous_theme(self):
        """Restore the combobox selection to match the active background."""
        if self.bg_image_path:
            self.theme_var.set("Choose Image...")
        else:
            self.theme_var.set("Default")

    def _get_darker_color(self, hex_color: str, factor: float = 0.8) -> str:
        """Calculate a darker version of a hex color for the status bar."""
        try:
            hex_color = hex_color.lstrip("#")
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            r = max(0, int(r * factor))
            g = max(0, int(g * factor))
            b = max(0, int(b * factor))
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return "#121212"

    def _on_resize(self, event=None):
        """Handle window resize to upscale/downscale background image."""
        if event and event.widget == self.root:
            w, h = event.width, event.height
            if w != self._last_width or h != self._last_height:
                self._last_width = w
                self._last_height = h
                self._update_layout(w, h)

    def _quit(self):
        self._running = False
        self.auto_refresh = False
        self.engine.stop()
        self.root.destroy()

    def run(self):
        """Start overlay GUI."""
        problems = Config.validate()
        if problems:
            for p in problems:
                print(f"⚠ {p}")

        try:
            self.engine.start()
            self._set_status("✓ Engine ready — Enter FEN or click 🔄 Fetch FEN")
        except FileNotFoundError as e:
            self._set_status(f"✗ {e}")

        self.root.mainloop()
