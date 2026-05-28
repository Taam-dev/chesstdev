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
    """Always-on-top GUI showing Stockfish analysis."""

    def __init__(self):
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
        icon_ico = "icon.ico"
        icon_png = "icon.png"
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

        self.main_frame = ttk.Frame(self.root, style="Dark.TFrame", padding=12)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Title ---
        ttk.Label(self.main_frame, text="♟ Chess Assistant", style="Title.TLabel").pack(
            pady=(0, 8)
        )

        # --- FEN Input ---
        fen_frame = ttk.Frame(self.main_frame, style="Dark.TFrame")
        fen_frame.pack(fill=tk.X, pady=4)

        ttk.Label(fen_frame, text="FEN:", style="Dark.TLabel").pack(side=tk.LEFT)

        self.fen_var = tk.StringVar(value="")
        self.fen_entry = ttk.Entry(
            fen_frame, textvariable=self.fen_var, width=50, font=("Consolas", 9)
        )
        self.fen_entry.pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)

        # --- Buttons ---
        btn_frame = ttk.Frame(self.main_frame, style="Dark.TFrame")
        btn_frame.pack(fill=tk.X, pady=6)

        self.analyze_btn = ttk.Button(
            btn_frame, text="▶ Analyze", command=self._on_analyze, style="Dark.TButton"
        )
        self.analyze_btn.pack(side=tk.LEFT, padx=3)

        self.top3_btn = ttk.Button(
            btn_frame, text="📊 Top 3", command=self._on_top3, style="Dark.TButton"
        )
        self.top3_btn.pack(side=tk.LEFT, padx=3)

        self.fetch_btn = ttk.Button(
            btn_frame,
            text="🔄 Fetch FEN",
            command=self._on_fetch_fen,
            style="Dark.TButton",
        )
        self.fetch_btn.pack(side=tk.LEFT, padx=3)

        # --- Options ---
        opt_frame = ttk.Frame(self.main_frame, style="Dark.TFrame")
        opt_frame.pack(fill=tk.X, pady=4)

        self.auto_var = tk.BooleanVar(value=False)
        auto_cb = ttk.Checkbutton(
            opt_frame,
            text="🔁 Auto",
            variable=self.auto_var,
            command=self._toggle_auto,
            style="Dark.TCheckbutton",
        )
        auto_cb.pack(side=tk.LEFT, padx=4)

        ttk.Label(opt_frame, text="Depth:", style="Dark.TLabel").pack(
            side=tk.LEFT, padx=(12, 2)
        )
        self.depth_var = tk.IntVar(value=Config.ENGINE_DEPTH)
        depth_spin = ttk.Spinbox(
            opt_frame,
            from_=1,
            to=30,
            width=4,
            textvariable=self.depth_var,
            font=("Consolas", 10),
        )
        depth_spin.pack(side=tk.LEFT, padx=2)

        ttk.Label(opt_frame, text="Bg:", style="Dark.TLabel").pack(
            side=tk.LEFT, padx=(12, 2)
        )
        self.theme_var = tk.StringVar(value="Default")
        self.theme_menu = ttk.Combobox(
            opt_frame,
            textvariable=self.theme_var,
            values=["Default", "Choose Image..."],
            width=15,
            state="readonly",
            font=("Consolas", 9),
        )
        self.theme_menu.pack(side=tk.LEFT, padx=2)
        self.theme_menu.bind("<<ComboboxSelected>>", self._on_theme_change)

        ttk.Label(opt_frame, text="Play As:", style="Dark.TLabel").pack(
            side=tk.LEFT, padx=(12, 2)
        )
        self.play_as_var = tk.StringVar(value="Both")
        self.play_as_menu = ttk.Combobox(
            opt_frame,
            textvariable=self.play_as_var,
            values=["Both", "White", "Black"],
            width=6,
            state="readonly",
            font=("Consolas", 9),
        )
        self.play_as_menu.pack(side=tk.LEFT, padx=2)

        # --- Turn indicator ---
        self.turn_var = tk.StringVar(value="")
        ttk.Label(opt_frame, textvariable=self.turn_var, style="Dark.TLabel").pack(
            side=tk.RIGHT, padx=4
        )

        # --- Separator ---
        ttk.Separator(self.main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        # --- Results ---
        result_frame = ttk.Frame(self.main_frame, style="Dark.TFrame")
        result_frame.pack(fill=tk.BOTH, expand=True)

        # Best Move
        move_row = ttk.Frame(result_frame, style="Dark.TFrame")
        move_row.pack(fill=tk.X, pady=4)
        ttk.Label(move_row, text="Best Move:", style="Dark.TLabel").pack(side=tk.LEFT)
        self.move_label = ttk.Label(move_row, text="—", style="Move.TLabel")
        self.move_label.pack(side=tk.LEFT, padx=12)

        # Move Description
        self.move_desc_label = ttk.Label(
            result_frame,
            text="",
            style="Dark.TLabel",
            foreground="#94e2d5",
            font=("Consolas", 11, "italic"),
        )
        self.move_desc_label.pack(fill=tk.X, padx=12, pady=(0, 6))

        # Eval score
        eval_row = ttk.Frame(result_frame, style="Dark.TFrame")
        eval_row.pack(fill=tk.X, pady=2)
        ttk.Label(eval_row, text="Eval:", style="Dark.TLabel").pack(side=tk.LEFT)
        self.score_label = ttk.Label(eval_row, text="—", style="Score.TLabel")
        self.score_label.pack(side=tk.LEFT, padx=12)

        # Eval text
        self.eval_text_label = ttk.Label(result_frame, text="", style="Eval.TLabel")
        self.eval_text_label.pack(fill=tk.X, pady=2)

        # PV / Top moves
        self.pv_label = ttk.Label(
            result_frame,
            text="",
            style="PV.TLabel",
            wraplength=Config.OVERLAY_WIDTH - 40,
            justify=tk.LEFT,
        )
        self.pv_label.pack(fill=tk.X, pady=6)

        # --- Status bar ---
        status_frame = ttk.Frame(self.main_frame, style="Dark.TFrame")
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_var = tk.StringVar(value="Ready — Enter FEN or click 🔄 Fetch FEN")
        
        # We need self.status_label to be accessible for color updating
        self.status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            style="Status.TLabel",
            anchor=tk.W,
        )
        self.status_label.pack(fill=tk.X)

        # --- Bindings ---
        self.root.bind("<Return>", lambda e: self._on_analyze())
        self.root.bind("<F5>", lambda e: self._on_fetch_fen())
        self.root.bind("<Escape>", lambda e: self._quit())
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def _display_result(self, result: AnalysisResult):
        self.move_label.configure(text=result.best_move_san)
        self.move_desc_label.configure(text=result.best_move_desc)
        self.score_label.configure(text=result.score_display)
        self.eval_text_label.configure(text=result.evaluation_text)

        # Eval color based on score
        if result.score_cp is not None:
            if result.score_cp > 50:
                self.score_label.configure(foreground="#a6e3a1")  # green
            elif result.score_cp < -50:
                self.score_label.configure(foreground="#f38ba8")  # red
            else:
                self.score_label.configure(foreground="#fab387")  # orange
        elif result.score_mate is not None:
            if result.score_mate > 0:
                self.score_label.configure(foreground="#a6e3a1")
            else:
                self.score_label.configure(foreground="#f38ba8")

        pv_text = ""
        if result.pv:
            pv_text = "PV: " + " → ".join(result.pv)
        self.pv_label.configure(text=pv_text)

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
        self.move_label.configure(text=best.best_move_san)
        self.move_desc_label.configure(text=best.best_move_desc)
        self.score_label.configure(text=best.score_display)
        self.eval_text_label.configure(text=best.evaluation_text)

        lines = []
        medals = ["🥇", "🥈", "🥉"]
        for i, r in enumerate(results):
            medal = medals[i] if i < len(medals) else f"{i + 1}."
            pv = " → ".join(r.pv[:4])
            desc_part = f" ({r.best_move_desc})" if r.best_move_desc else ""
            lines.append(f"{medal} {r.best_move_san:6s}{desc_part} ({r.score_display})\n   PV: {pv}")

        self.pv_label.configure(text="\n".join(lines))
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
            self.turn_var.set(f"{turn} (move {move_num})")
        except Exception:
            self.turn_var.set("")

    def _set_status(self, msg: str):
        self.status_var.set(msg)

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
                w = self.root.winfo_width()
                h = self.root.winfo_height()
                if w < 10 or h < 10:
                    w, h = Config.OVERLAY_WIDTH, Config.OVERLAY_HEIGHT
                self._update_bg_image(w, h)
            else:
                self._restore_previous_theme()
        else:
            self._remove_bg_image()
            self._update_bg_color("#1a1a2e")

    def _remove_bg_image(self):
        """Destroy or hide the background image label."""
        self.bg_image_path = None
        if hasattr(self, "bg_label"):
            self.bg_label.place_forget()

    def _restore_previous_theme(self):
        """Restore the combobox selection to match the active background."""
        if self.bg_image_path:
            self.theme_var.set("Choose Image...")
        else:
            self.theme_var.set("Default")

    def _update_bg_color(self, new_bg: str):
        self.current_bg = new_bg
        status_bg = self._get_darker_color(new_bg, 0.8)
        
        style = ttk.Style()
        style.configure("Dark.TFrame", background=new_bg)
        style.configure("Dark.TLabel", background=new_bg)
        style.configure("Title.TLabel", background=new_bg)
        style.configure("Move.TLabel", background=new_bg)
        style.configure("Score.TLabel", background=new_bg)
        style.configure("Eval.TLabel", background=new_bg)
        style.configure("PV.TLabel", background=new_bg)
        style.configure("Dark.TCheckbutton", background=new_bg)
        style.configure("Status.TLabel", background=status_bg)
        
        self.root.configure(bg=new_bg)

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
                if self.bg_image_path:
                    self._update_bg_image(w, h)

    def _update_bg_image(self, w: int, h: int):
        """Load, resize, and display background image."""
        if not self.bg_image_path:
            return
        try:
            from PIL import Image, ImageTk
            img = Image.open(self.bg_image_path)
            img = img.resize((w, h), Image.Resampling.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(img)
            
            if not hasattr(self, "bg_label"):
                self.bg_label = tk.Label(self.main_frame, image=self.bg_photo)
            else:
                self.bg_label.configure(image=self.bg_photo)
                
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            self.bg_label.lower()
        except Exception as e:
            self._set_status(f"✗ Image error: {e}")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

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
