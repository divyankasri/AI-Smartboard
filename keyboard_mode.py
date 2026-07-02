"""
AI Smartboard Pro - Keyboard Mode
================================

This module provides a dark professional CustomTkinter user interface for interacting
with Gemini AI via keyboard input. It runs as a standalone executable and is compatible
with home.py, gemini_service.py, and history_service.py.

Designed with premium dark aesthetics, smooth micro-animations, keyboard shortcuts,
and robust multithreading.
"""

import os
import sys
import queue
import threading
import time
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

# ==========================================
# SERVICE INTEGRATION & FALLBACKS
# ==========================================
try:
    from gemini_service import ask_gemini
except ImportError:
    # Standalone mock implementation if gemini_service.py is not present
    def ask_gemini(question: str) -> tuple[str, float]:
        time.sleep(1.5)  # Simulate API latency
        mock_answers = {
            "hello": "Hello! How can I assist you with your Smartboard Pro session today?",
            "help": "Type a question in the input box, click 'Ask AI' or press Ctrl+Enter to get a response.",
            "features": "AI Smartboard Pro features Keyboard Mode, History Tracking, and Gesture/Voice controls.",
        }
        cleaned = question.strip().lower()
        if cleaned in mock_answers:
            return mock_answers[cleaned], 1.5
        return (
            f"Thank you for your question: '{question}'\n\n"
            f"This is a simulated response from the fallback Gemini Service.\n"
            f"To connect to your live Gemini API, place 'gemini_service.py' in the same folder."
        ), 1.5

try:
    from history_service import log_history, get_history
except ImportError:
    # Standalone memory-based history storage if history_service.py is not present
    _LOCAL_HISTORY = []

    def log_history(question: str, answer: str, elapsed: float) -> None:
        _LOCAL_HISTORY.insert(0, {
            "question": question,
            "answer": answer,
            "elapsed": elapsed,
            "timestamp": time.strftime("%H:%M:%S")
        })

    def get_history() -> list[dict]:
        return _LOCAL_HISTORY


# ==========================================
# CONSTANTS & CUSTOM THEME COLORS
# ==========================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG_COLOR = "#0F172A"         # Sleek Slate-900 background
CARD_BG = "#1E293B"          # Lighter Slate-800 for cards
ACCENT_COLOR = "#0D9488"     # Teal-600 primary button/indicator
ACCENT_HOVER = "#0F766E"     # Darker Teal-700 for hover state
TEXT_PRIMARY = "#F8FAFC"     # Slate-50 for high contrast text
TEXT_MUTED = "#94A3B8"       # Slate-400 for secondary details
BORDER_COLOR = "#334155"     # Slate-700 for subtle borders
SUCCESS_COLOR = "#10B981"    # Emerald-500
ERROR_COLOR = "#EF4444"      # Red-500
WARN_COLOR = "#F59E0B"       # Amber-500


class KeyboardModeApp(ctk.CTk):
    """
    Main application class for the Keyboard Mode UI of AI Smartboard Pro.
    """
    def __init__(self, controller=None):
        super().__init__()

        self.controller = controller
        self.is_processing = False
        self.result_queue = queue.Queue()
        self.loading_animation_id = None
        self.loading_dots = 0

        # Configure Window settings
        self.title("AI Smartboard Pro - Keyboard Mode")
        self.geometry("1100x700")
        self.minsize(950, 600)
        self.configure(fg_color=BG_COLOR)

        # Center window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 1100) // 2
        y = (self.winfo_screenheight() - 700) // 2
        self.geometry(f"1100x700+{x}+{y}")

        # Initialize UI Font Styles
        self.font_title = ctk.CTkFont(family="Inter", size=22, weight="bold")
        self.font_header = ctk.CTkFont(family="Inter", size=15, weight="bold")
        self.font_body = ctk.CTkFont(family="Inter", size=14, weight="normal")
        self.font_code = ctk.CTkFont(family="Consolas", size=13, weight="normal")
        self.font_status = ctk.CTkFont(family="Inter", size=12, weight="bold")
        self.font_small = ctk.CTkFont(family="Inter", size=11, weight="normal")

        # Build UI layout & shortcuts
        self._build_ui()
        self._setup_shortcuts()
        self.refresh_history_list()

    def _build_ui(self):
        """Constructs the application layout."""
        self.grid_columnconfigure(0, weight=1, minsize=250)  # Left Sidebar
        self.grid_columnconfigure(1, weight=3, minsize=650)  # Main Content
        self.grid_rowconfigure(0, weight=0)                  # Header
        self.grid_rowconfigure(1, weight=1)                  # Main Body Workspace
        self.grid_rowconfigure(2, weight=0)                  # Footer

        # ----------------- HEADER AREA -----------------
        self.header = ctk.CTkFrame(self, fg_color=BG_COLOR, height=60, corner_radius=0)
        self.header.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)
        self.header.grid_columnconfigure(1, weight=1)

        self.home_btn = ctk.CTkButton(
            self.header, text="←  Home", width=90, height=34,
            fg_color="transparent", border_color=BORDER_COLOR, border_width=1,
            text_color=TEXT_PRIMARY, hover_color=CARD_BG, font=self.font_status,
            command=self.go_home
        )
        self.home_btn.grid(row=0, column=0, sticky="w")

        title_container = ctk.CTkFrame(self.header, fg_color="transparent")
        title_container.grid(row=0, column=1, sticky="w", padx=20)
        
        ctk.CTkLabel(title_container, text="AI SMARTBOARD PRO", text_color=TEXT_PRIMARY, font=self.font_title).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(title_container, text="Keyboard Workspace Mode", text_color=TEXT_MUTED, font=self.font_small).grid(row=1, column=0, sticky="w")

        badge = ctk.CTkFrame(self.header, fg_color=CARD_BG, height=34, corner_radius=17)
        badge.grid(row=0, column=2, sticky="e")
        ctk.CTkLabel(badge, text="●", text_color=SUCCESS_COLOR, font=self.font_status).pack(side="left", padx=(12, 6))
        ctk.CTkLabel(badge, text="Gemini Online", text_color=TEXT_PRIMARY, font=self.font_small).pack(side="left", padx=(0, 12))

        # Divider
        ctk.CTkFrame(self, height=1, fg_color=BORDER_COLOR).grid(row=0, column=0, columnspan=2, sticky="s")

        # ----------------- LEFT SIDEBAR (History Log) -----------------
        self.sidebar = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12, border_color=BORDER_COLOR, border_width=1)
        self.sidebar.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)
        self.sidebar.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.sidebar, text="Recent Queries", text_color=TEXT_PRIMARY, font=self.font_header, anchor="w").grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))

        self.history_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.history_scroll.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.clear_hist_btn = ctk.CTkButton(
            self.sidebar, text="Clear Log History", height=30,
            fg_color="transparent", border_color=BORDER_COLOR, border_width=1,
            text_color=TEXT_MUTED, hover_color="#3F1C1C", font=self.font_small,
            command=self.clear_history
        )
        self.clear_hist_btn.grid(row=2, column=0, sticky="ew", padx=15, pady=15)

        # ----------------- MAIN WORKSPACE -----------------
        self.workspace = ctk.CTkFrame(self, fg_color="transparent")
        self.workspace.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=10)
        self.workspace.grid_columnconfigure(0, weight=1)
        self.workspace.grid_rowconfigure(0, weight=2)
        self.workspace.grid_rowconfigure(1, weight=3)

        # A. Input Section
        self.input_frame = ctk.CTkFrame(self.workspace, fg_color=CARD_BG, corner_radius=12, border_color=BORDER_COLOR, border_width=1)
        self.input_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.input_frame.grid_columnconfigure(0, weight=1)
        self.input_frame.grid_rowconfigure(1, weight=1)

        lbl_container = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        lbl_container.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 5))
        ctk.CTkLabel(lbl_container, text="Question Input", text_color=TEXT_PRIMARY, font=self.font_header).pack(side="left")
        ctk.CTkLabel(lbl_container, text="(Ctrl+Enter to submit)", text_color=TEXT_MUTED, font=self.font_small).pack(side="left", padx=10)

        self.question_box = ctk.CTkTextbox(self.input_frame, fg_color=BG_COLOR, text_color=TEXT_PRIMARY, border_color=BORDER_COLOR, border_width=1, font=self.font_body, wrap="word", corner_radius=8)
        self.question_box.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)
        self.question_box.bind("<KeyRelease>", self.update_char_count)

        control_bar = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        control_bar.grid(row=2, column=0, sticky="ew", padx=15, pady=(5, 10))
        self.char_count_label = ctk.CTkLabel(control_bar, text="0 / 1000 characters", text_color=TEXT_MUTED, font=self.font_small)
        self.char_count_label.pack(side="left")

        self.ask_btn = ctk.CTkButton(control_bar, text="Ask AI  ✦", width=120, height=34, fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER, text_color=TEXT_PRIMARY, font=self.font_status, command=self.submit_question)
        self.ask_btn.pack(side="right", padx=(10, 0))
        self.clear_btn = ctk.CTkButton(control_bar, text="Clear", width=70, height=34, fg_color="transparent", border_color=BORDER_COLOR, border_width=1, text_color=TEXT_PRIMARY, hover_color=CARD_BG, font=self.font_status, command=self.clear_fields)
        self.clear_btn.pack(side="right")

        # B. Output Section
        self.output_frame = ctk.CTkFrame(self.workspace, fg_color=CARD_BG, corner_radius=12, border_color=BORDER_COLOR, border_width=1)
        self.output_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self.output_frame.grid_columnconfigure(0, weight=1)
        self.output_frame.grid_rowconfigure(1, weight=1)

        a_header = ctk.CTkFrame(self.output_frame, fg_color="transparent")
        a_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 5))
        ctk.CTkLabel(a_header, text="AI Response Panel", text_color=TEXT_PRIMARY, font=self.font_header).pack(side="left")

        self.status_badge = ctk.CTkLabel(a_header, text="READY", font=self.font_status, text_color=BG_COLOR, fg_color=ACCENT_COLOR, corner_radius=6, height=20, width=70)
        self.status_badge.pack(side="left", padx=12)
        
        self.elapsed_label = ctk.CTkLabel(a_header, text="Time: -- s", text_color=TEXT_MUTED, font=self.font_small)
        self.elapsed_label.pack(side="left")

        self.copy_btn = ctk.CTkButton(a_header, text="📋 Copy Response", width=110, height=24, fg_color="transparent", border_color=BORDER_COLOR, border_width=1, text_color=TEXT_PRIMARY, hover_color=CARD_BG, font=self.font_small, command=self.copy_to_clipboard)
        self.copy_btn.pack(side="right")

        self.answer_box = ctk.CTkTextbox(self.output_frame, fg_color=BG_COLOR, text_color=TEXT_PRIMARY, border_color=BORDER_COLOR, border_width=1, font=self.font_code, wrap="word", corner_radius=8)
        self.answer_box.grid(row=1, column=0, sticky="nsew", padx=15, pady=(5, 15))
        self.answer_box.configure(state="disabled")

        # ----------------- FOOTER AREA -----------------
        footer = ctk.CTkFrame(self, fg_color=BG_COLOR, height=25)
        footer.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=5)
        ctk.CTkLabel(footer, text="Ctrl+Enter: Ask AI  |  Ctrl+L: Clear  |  Ctrl+H: Home", text_color=TEXT_MUTED, font=self.font_small).pack(side="left")
        ctk.CTkLabel(footer, text="Smartboard Pro SDK v1.2", text_color=TEXT_MUTED, font=self.font_small).pack(side="right")

    # ==========================================
    # INTERACTIONS & SHORTCUTS
    # ==========================================
    def _setup_shortcuts(self):
        self.bind("<Control-Return>", lambda e: self.submit_question())
        self.bind("<Control-l>", lambda e: self.clear_fields())
        self.bind("<Control-L>", lambda e: self.clear_fields())
        self.bind("<Control-h>", lambda e: self.go_home())
        self.bind("<Control-H>", lambda e: self.go_home())

    def update_char_count(self, event=None):
        count = len(self.question_box.get("1.0", "end-1c"))
        self.char_count_label.configure(text=f"{count} / 1000 characters")
        self.char_count_label.configure(text_color=ERROR_COLOR if count > 1000 else TEXT_MUTED)

    def update_status(self, text: str, color: str):
        self.status_badge.configure(text=text, fg_color=color)

    def _set_answer_text(self, text: str):
        self.answer_box.configure(state="normal")
        self.answer_box.delete("1.0", "end")
        self.answer_box.insert("1.0", text)
        self.answer_box.configure(state="disabled")

    def clear_fields(self):
        if self.is_processing:
            return
        self.question_box.delete("1.0", "end")
        self._set_answer_text("")
        self.update_status("READY", ACCENT_COLOR)
        self.elapsed_label.configure(text="Time: -- s")
        self.update_char_count()

    def copy_to_clipboard(self):
        txt = self.answer_box.get("1.0", "end-1c").strip()
        if not txt or txt.startswith("Retrieving"):
            return
        self.clipboard_clear()
        self.clipboard_append(txt)
        orig = self.copy_btn.cget("text")
        self.copy_btn.configure(text="✓ Copied!", text_color=SUCCESS_COLOR, border_color=SUCCESS_COLOR)
        self.after(1200, lambda: self.copy_btn.configure(text=orig, text_color=TEXT_PRIMARY, border_color=BORDER_COLOR))

    # ==========================================
    # WORKER THREADING & API INTEGRATION
    # ==========================================
    def submit_question(self):
        if self.is_processing:
            return

        question = self.question_box.get("1.0", "end-1c").strip()
        if not question:
            self.update_status("EMPTY QUERY", ERROR_COLOR)
            messagebox.showwarning("Empty Query", "Please enter a question first.")
            return
        if len(question) > 1000:
            self.update_status("OVER LIMIT", ERROR_COLOR)
            messagebox.showwarning("Limit Exceeded", "Keep questions under 1000 characters.")
            return

        # Lock UI
        self.is_processing = True
        self.ask_btn.configure(state="disabled")
        self.clear_btn.configure(state="disabled")
        self.question_box.configure(state="disabled")
        self.home_btn.configure(state="disabled")
        self.clear_hist_btn.configure(state="disabled")

        self.update_status("THINKING", WARN_COLOR)
        self.elapsed_label.configure(text="Processing...")
        self._set_answer_text("Retrieving Gemini response, please wait...")

        self.loading_dots = 0
        self._animate_loading()

        # Thread Dispatch
        threading.Thread(target=self._async_worker, args=(question,), daemon=True).start()
        self.after(100, self._poll_queue)

    def _animate_loading(self):
        if not self.is_processing:
            return
        self.loading_dots = (self.loading_dots + 1) % 4
        self.status_badge.configure(text=f"THINKING{'.' * self.loading_dots}")
        self.loading_animation_id = self.after(400, self._animate_loading)

    def _async_worker(self, question: str):
        start = time.time()
        try:
            ans, elapsed = ask_gemini(question)
            log_history(question, ans, elapsed)
            self.result_queue.put({"success": True, "answer": ans, "elapsed": elapsed})
        except Exception as e:
            self.result_queue.put({"success": False, "error": str(e), "elapsed": time.time() - start})

    def _poll_queue(self):
        try:
            res = self.result_queue.get_nowait()
            self._handle_result(res)
        except queue.Empty:
            if self.is_processing:
                self.after(100, self._poll_queue)

    def _handle_result(self, res: dict):
        self.is_processing = False
        if self.loading_animation_id:
            self.after_cancel(self.loading_animation_id)

        # Unlock UI
        self.ask_btn.configure(state="normal")
        self.clear_btn.configure(state="normal")
        self.question_box.configure(state="normal")
        self.home_btn.configure(state="normal")
        self.clear_hist_btn.configure(state="normal")

        if res["success"]:
            self.update_status("SUCCESS", SUCCESS_COLOR)
            self.elapsed_label.configure(text=f"Time: {res['elapsed']:.2f}s")
            self._set_answer_text(res["answer"])
            self.refresh_history_list()
        else:
            self.update_status("ERROR", ERROR_COLOR)
            self.elapsed_label.configure(text=f"Failed ({res['elapsed']:.2f}s)")
            err_msg = (
                f"An error occurred while calling the Gemini API:\n\n"
                f"{res['error']}\n\n"
                f"Checks:\n"
                f"- Network connection status\n"
                f"- API key/credentials in 'gemini_service.py'"
            )
            self._set_answer_text(err_msg)

    # ==========================================
    # HISTORY LOG & NAVIGATION
    # ==========================================
    def refresh_history_list(self):
        for widget in self.history_scroll.winfo_children():
            widget.destroy()

        items = get_history()
        if not items:
            ctk.CTkLabel(self.history_scroll, text="No queries logged in\nthis session.", text_color=TEXT_MUTED, font=self.font_small, pady=20).pack(fill="x")
            return

        for item in items:
            q_text = item["question"].replace("\n", " ")
            if len(q_text) > 26:
                q_text = q_text[:23] + "..."

            frame = ctk.CTkFrame(self.history_scroll, fg_color="transparent")
            frame.pack(fill="x", pady=2, padx=2)

            btn = ctk.CTkButton(
                frame, text=f"{item.get('timestamp', '--:--')} | {q_text}",
                anchor="w", fg_color="transparent", text_color=TEXT_PRIMARY,
                hover_color=BORDER_COLOR, height=28, font=self.font_small,
                command=lambda q=item["question"], a=item["answer"], t=item["elapsed"]: self.load_history_item(q, a, t)
            )
            btn.pack(fill="x")

    def load_history_item(self, question: str, answer: str, elapsed: float):
        if self.is_processing:
            return
        self.clear_fields()
        self.question_box.insert("1.0", question)
        self.update_char_count()
        self._set_answer_text(answer)
        self.update_status("LOG LOADED", SUCCESS_COLOR)
        self.elapsed_label.configure(text=f"Time: {elapsed:.2f}s")

    def clear_history(self):
        if self.is_processing:
            return
        if not messagebox.askyesno("Clear History", "Clear all logged query items?"):
            return
        try:
            import history_service
            if hasattr(history_service, "clear_history"):
                history_service.clear_history()
            elif hasattr(history_service, "_LOCAL_HISTORY"):
                history_service._LOCAL_HISTORY.clear()
            else:
                _LOCAL_HISTORY.clear()
        except Exception:
            _LOCAL_HISTORY.clear()

        self.refresh_history_list()
        self.update_status("LOG CLEARED", ACCENT_COLOR)

    def go_home(self):
        if self.is_processing:
            return
        if self.controller and hasattr(self.controller, "show_home_screen"):
            try:
                self.controller.show_home_screen()
                return
            except Exception as e:
                print(f"Navigation error: {e}")

        # Standalone Navigation Fallback
        try:
            self.withdraw()
            import home
            if hasattr(home, "main") or hasattr(home, "run"):
                threading.Thread(target=home.main if hasattr(home, "main") else home.run, daemon=True).start()
            else:
                self.destroy()
        except ImportError:
            self.destroy()


# ==========================================
# SYSTEM RUNNER ENTRY POINT
# ==========================================
if __name__ == "__main__":
    try:
        app = KeyboardModeApp()
        app.mainloop()
    except Exception as e:
        print(f"Fatal Startup Error: {e}")
        sys.exit(1)
        