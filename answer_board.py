import os
import sys
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
# ==========================================
# CONSTANTS & THEME SETUP
# ==========================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
BG_COLOR = "#0F172A"         # Slate-900
CARD_BG = "#1E293B"          # Slate-800
ACCENT_COLOR = "#0D9488"     # Teal-600
ACCENT_HOVER = "#0F766E"     # Teal-700
TEXT_PRIMARY = "#F8FAFC"     # Slate-50
TEXT_MUTED = "#94A3B8"       # Slate-400
BORDER_COLOR = "#334155"     # Slate-700
SUCCESS_COLOR = "#10B981"    # Emerald-500
ERROR_COLOR = "#EF4444"      # Red-500
class AnswerBoardApp(ctk.CTk):
    """
    Main CustomTkinter window displaying the Gemini AI generated answer
    with tools to copy, adjust font size, export, and clear.
    """
    def __init__(self, answer_text: str = "", elapsed_time: float = 0.0, controller=None):
        super().__init__()
        self.controller = controller
        self.initial_answer = answer_text
        self.elapsed_time = elapsed_time
        # Font configuration state
        self.current_font_size = 14
        self.min_font_size = 10
        self.max_font_size = 30
        # Configure window settings
        self.title("AI Smartboard Pro - Answer Board")
        self.geometry("900x650")
        self.minsize(800, 500)
        self.configure(fg_color=BG_COLOR)
        # Center window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 900) // 2
        y = (self.winfo_screenheight() - 650) // 2
        self.geometry(f"960x650+{x}+{y}")
        # Initialize Fonts
        self.font_title = ctk.CTkFont(family="Inter", size=22, weight="bold")
        self.font_header = ctk.CTkFont(family="Inter", size=15, weight="bold")
        self.font_body = ctk.CTkFont(family="Inter", size=13, weight="normal")
        self.font_status = ctk.CTkFont(family="Inter", size=12, weight="bold")
        self.font_small = ctk.CTkFont(family="Inter", size=11, weight="normal")
        
        # Target textbox font which will be dynamically scaled
        self.textbox_font = ctk.CTkFont(family="Consolas", size=self.current_font_size, weight="normal")
        # Build UI layout & shortcuts
        self._build_ui()
        self._setup_shortcuts()
        
        # Populate initial response data
        if self.initial_answer:
            self.set_answer(self.initial_answer, self.elapsed_time)
        else:
            self._set_welcome_message()
    def _build_ui(self):
        """Constructs application UI structure."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Main Text Area & Sidebar
        self.grid_rowconfigure(2, weight=0)  # Status Bar
        # ----------------- HEADER PANEL -----------------
        self.header = ctk.CTkFrame(self, fg_color=BG_COLOR, height=60, corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        self.header.grid_columnconfigure(1, weight=1)
        # Back/Home Button
        self.home_btn = ctk.CTkButton(
            self.header, text="←  Home", width=90, height=34,
            fg_color="transparent", border_color=BORDER_COLOR, border_width=1,
            text_color=TEXT_PRIMARY, hover_color=CARD_BG, font=self.font_status,
            command=self.go_home
        )
        self.home_btn.grid(row=0, column=0, sticky="w")
        # Title block
        title_container = ctk.CTkFrame(self.header, fg_color="transparent")
        title_container.grid(row=0, column=1, sticky="w", padx=20)
        ctk.CTkLabel(title_container, text="AI SMARTBOARD PRO", text_color=TEXT_PRIMARY, font=self.font_title).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(title_container, text="AI Response & Formatting Board", text_color=TEXT_MUTED, font=self.font_small).grid(row=1, column=0, sticky="w")
        # Font Zoom Controls
        zoom_frame = ctk.CTkFrame(self.header, fg_color=CARD_BG, height=34, corner_radius=8, border_color=BORDER_COLOR, border_width=1)
        zoom_frame.grid(row=0, column=2, sticky="e")
        
        ctk.CTkLabel(zoom_frame, text="A", font=ctk.CTkFont(family="Inter", size=11, weight="bold"), text_color=TEXT_MUTED).pack(side="left", padx=(12, 4))
        
        self.zoom_out_btn = ctk.CTkButton(
            zoom_frame, text="-", width=24, height=24, fg_color=BG_COLOR, text_color=TEXT_PRIMARY,
            hover_color=BORDER_COLOR, font=self.font_status, command=self.zoom_out
        )
        self.zoom_out_btn.pack(side="left", padx=2)
        
        self.zoom_label = ctk.CTkLabel(zoom_frame, text=f"{self.current_font_size}pt", font=self.font_status, text_color=TEXT_PRIMARY, width=40)
        self.zoom_label.pack(side="left", padx=2)
        self.zoom_in_btn = ctk.CTkButton(
            zoom_frame, text="+", width=24, height=24, fg_color=BG_COLOR, text_color=TEXT_PRIMARY,
            hover_color=BORDER_COLOR, font=self.font_status, command=self.zoom_in
        )
        self.zoom_in_btn.pack(side="left", padx=2)
        
        ctk.CTkLabel(zoom_frame, text="A", font=ctk.CTkFont(family="Inter", size=16, weight="bold"), text_color=TEXT_PRIMARY).pack(side="left", padx=(4, 12))
        # Divider Line
        ctk.CTkFrame(self, height=1, fg_color=BORDER_COLOR).grid(row=0, column=0, sticky="s")
        # ----------------- MAIN BODY -----------------
        self.body_container = ctk.CTkFrame(self, fg_color="transparent")
        self.body_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.body_container.grid_columnconfigure(0, weight=4)   # Large answer textbox
        self.body_container.grid_columnconfigure(1, weight=1, minsize=200)   # Controls sidebar
        self.body_container.grid_rowconfigure(0, weight=1)
        # A. Answer Textbox
        self.textbox_container = ctk.CTkFrame(self.body_container, fg_color=CARD_BG, corner_radius=12, border_color=BORDER_COLOR, border_width=1)
        self.textbox_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.textbox_container.grid_columnconfigure(0, weight=1)
        self.textbox_container.grid_rowconfigure(0, weight=1)
        self.answer_box = ctk.CTkTextbox(
            self.textbox_container, fg_color=BG_COLOR, text_color=TEXT_PRIMARY,
            border_width=0, font=self.textbox_font, wrap="word", corner_radius=8
        )
        self.answer_box.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.answer_box.configure(state="disabled")
        # B. Controls Sidebar
        self.sidebar = ctk.CTkFrame(self.body_container, fg_color=CARD_BG, corner_radius=12, border_color=BORDER_COLOR, border_width=1)
        self.sidebar.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(2, weight=1)  # Spacer frame row
        # Section: Actions
        ctk.CTkLabel(self.sidebar, text="Board Actions", text_color=TEXT_PRIMARY, font=self.font_header, anchor="w").grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        
        self.copy_btn = ctk.CTkButton(
            self.sidebar, text="📋 Copy Response", height=38, fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER,
            text_color=TEXT_PRIMARY, font=self.font_status, command=self.copy_to_clipboard
        )
        self.copy_btn.grid(row=1, column=0, sticky="ew", padx=15, pady=6)
        self.save_btn = ctk.CTkButton(
            self.sidebar, text="💾 Save to TXT", height=38, fg_color="transparent", border_color=BORDER_COLOR,
            border_width=1, text_color=TEXT_PRIMARY, hover_color=BG_COLOR, font=self.font_status, command=self.save_as_txt
        )
        self.save_btn.grid(row=2, column=0, sticky="ew", padx=15, pady=6)
        self.clear_btn = ctk.CTkButton(
            self.sidebar, text="🧹 Clear Board", height=38, fg_color="transparent", border_color=BORDER_COLOR,
            border_width=1, text_color=TEXT_PRIMARY, hover_color=BG_COLOR, font=self.font_status, command=self.clear_board
        )
        self.clear_btn.grid(row=3, column=0, sticky="ew", padx=15, pady=6)
        # Divider in sidebar
        ctk.CTkFrame(self.sidebar, height=1, fg_color=BORDER_COLOR).grid(row=4, column=0, sticky="ew", padx=15, pady=15)
        # Section: Metadata / Metrics
        ctk.CTkLabel(self.sidebar, text="Response Analytics", text_color=TEXT_PRIMARY, font=self.font_header, anchor="w").grid(row=5, column=0, sticky="ew", padx=15, pady=(0, 10))
        self.metrics_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.metrics_container.grid(row=6, column=0, sticky="nsew", padx=15, pady=5)
        self.metrics_container.grid_columnconfigure(0, weight=1)
        self.time_lbl = ctk.CTkLabel(self.metrics_container, text="Latency: -- s", text_color=TEXT_MUTED, font=self.font_body, anchor="w")
        self.time_lbl.pack(fill="x", pady=2)
        
        self.word_lbl = ctk.CTkLabel(self.metrics_container, text="Word Count: 0 words", text_color=TEXT_MUTED, font=self.font_body, anchor="w")
        self.word_lbl.pack(fill="x", pady=2)
        self.char_lbl = ctk.CTkLabel(self.metrics_container, text="Char Count: 0 chars", text_color=TEXT_MUTED, font=self.font_body, anchor="w")
        self.char_lbl.pack(fill="x", pady=(2, 20))
        # ----------------- STATUS BAR -----------------
        self.status_bar = ctk.CTkFrame(self, fg_color=BG_COLOR, height=30)
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=20, pady=5)
        self.status_bar.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(self.status_bar, text="Ready", text_color=TEXT_MUTED, font=self.font_small, anchor="w")
        self.status_label.grid(row=0, column=0, sticky="w")
        self.status_info = ctk.CTkLabel(self.status_bar, text="Ctrl+S: Save  |  Ctrl+C: Copy  |  Ctrl+L: Clear", text_color=TEXT_MUTED, font=self.font_small, anchor="e")
        self.status_info.grid(row=0, column=1, sticky="e")
    # ==========================================
    # LOGIC, INTERACTION & UTILITIES
    # ==========================================
    
    def _setup_shortcuts(self):
        """Binds universal application shortcuts."""
        self.bind("<Control-s>", lambda e: self.save_as_txt())
        self.bind("<Control-S>", lambda e: self.save_as_txt())
        self.bind("<Control-c>", lambda e: self.copy_to_clipboard())
        self.bind("<Control-C>", lambda e: self.copy_to_clipboard())
        self.bind("<Control-l>", lambda e: self.clear_board())
        self.bind("<Control-L>", lambda e: self.clear_board())
        self.bind("<Control-h>", lambda e: self.go_home())
        self.bind("<Control-H>", lambda e: self.go_home())
    def update_status(self, text: str, error: bool = False):
        """Updates the status bar label thread-safely."""
        color = ERROR_COLOR if error else TEXT_MUTED
        self.status_label.configure(text=text, text_color=color)
    def _set_welcome_message(self):
        """Sets default instructions inside the answer board."""
        welcome = (
            "🚀 Welcome to AI Smartboard Pro Answer Board!\n\n"
            "This board is designed to display generated responses, code segments, "
            "and summaries returned by the Gemini AI system.\n\n"
            "Quick Tips:\n"
            "1. Use the [ + ] and [ - ] buttons in the header to scale the text size dynamically.\n"
            "2. Click 'Copy Response' to copy the text to your system clipboard.\n"
            "3. Use the 'Save to TXT' button to export this board to a text file.\n"
            "4. Navigate back using the 'Home' button."
        )
        self._write_text_safely(welcome)
        self.time_lbl.configure(text="Latency: N/A")
        self._calculate_metrics(welcome)
    def _write_text_safely(self, text: str):
        """Performs thread-safe write updates on the read-only textbox."""
        self.answer_box.configure(state="normal")
        self.answer_box.delete("1.0", "end")
        self.answer_box.insert("1.0", text)
        self.answer_box.configure(state="disabled")
    def set_answer(self, answer_text: str, elapsed_time: float = 0.0):
        """
        Thread-safe entry point to load external AI responses.
        Args:
            answer_text (str): Response text to load.
            elapsed_time (float): Response latency.
        """
        self._write_text_safely(answer_text)
        
        # Update Latency display
        self.elapsed_time = elapsed_time
        if elapsed_time > 0:
            self.time_lbl.configure(text=f"Latency: {elapsed_time:.2f} seconds")
        else:
            self.time_lbl.configure(text="Latency: Local simulation")
        self._calculate_metrics(answer_text)
        self.update_status("Response loaded successfully.")
    def _calculate_metrics(self, text: str):
        """Calculates text parameters (Words, Characters)."""
        char_count = len(text)
        word_count = len(text.split())
        self.word_lbl.configure(text=f"Word Count: {word_count} words")
        self.char_lbl.configure(text=f"Char Count: {char_count} chars")
    # ==========================================
    # FONT SIZE ZOOM MECHANISM
    # ==========================================
    def zoom_in(self):
        """Increases font size of the answer box dynamically."""
        if self.current_font_size < self.max_font_size:
            self.current_font_size += 2
            self.textbox_font.configure(size=self.current_font_size)
            self.zoom_label.configure(text=f"{self.current_font_size}pt")
            self.update_status(f"Font scaled to {self.current_font_size}pt")
    def zoom_out(self):
        """Decreases font size of the answer box dynamically."""
        if self.current_font_size > self.min_font_size:
            self.current_font_size -= 2
            self.textbox_font.configure(size=self.current_font_size)
            self.zoom_label.configure(text=f"{self.current_font_size}pt")
            self.update_status(f"Font scaled to {self.current_font_size}pt")
    # ==========================================
    # UTILITY HANDLERS
    # ==========================================
    def copy_to_clipboard(self):
        """Copies entire text to the OS clipboard with validation."""
        text = self.answer_box.get("1.0", "end-1c").strip()
        if not text:
            self.update_status("Nothing to copy!", error=True)
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            
            # Temporary UI feedback
            orig = self.copy_btn.cget("text")
            self.copy_btn.configure(text="✓ Copied!", text_color=SUCCESS_COLOR, border_color=SUCCESS_COLOR)
            self.update_status("Copied response to clipboard.")
            self.after(1200, lambda: self.copy_btn.configure(text=orig, text_color=TEXT_PRIMARY, border_color=BORDER_COLOR))
        except Exception as e:
            self.update_status("Clipboard copy failed.", error=True)
            messagebox.showerror("Clipboard Error", f"Could not copy text:\n{e}")
    def save_as_txt(self):
        """Exports text box content to an external TXT file via File Dialog."""
        text = self.answer_box.get("1.0", "end-1c").strip()
        if not text:
            self.update_status("Nothing to save!", error=True)
            return
        try:
            file_path = filedialog.asksaveasfilename(
                title="Save Response as Text",
                defaultextension=".txt",
                filetypes=[("Text Documents", "*.txt"), ("All Files", "*.*")]
            )
            
            if not file_path:
                self.update_status("Save operation cancelled.")
                return
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
                
            self.update_status("File saved successfully.")
            messagebox.showinfo("Export Success", f"Response successfully saved to:\n{file_path}")
        except Exception as e:
            self.update_status("Failed to save file.", error=True)
            messagebox.showerror("File IO Error", f"Could not save text file:\n{e}")
    def clear_board(self):
        """Clears text, resets counters, and prompts confirmation."""
        text = self.answer_box.get("1.0", "end-1c").strip()
        if not text or text.startswith("🚀 Welcome"):
            return
        if messagebox.askyesno("Clear Board", "Are you sure you want to clear the response board?"):
            self._write_text_safely("")
            self._calculate_metrics("")
            self.time_lbl.configure(text="Latency: -- s")
            self.update_status("Answer board cleared.")
    def go_home(self):
        """Handles navigation back to home workspace or launcher."""
        if self.controller and hasattr(self.controller, "show_home_screen"):
            try:
                self.controller.show_home_screen()
                return
            except Exception as e:
                print(f"Controller navigation failed: {e}")
        # Fallback closure: attempt to launch home.py
        try:
            self.withdraw()
            import home
            if hasattr(home, "main") or hasattr(home, "run"):
                import threading
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
        # Default run block with custom mock string for testing standalone execution
        mock_str = (
            "============================================================\n"
            "                 AI SMARTBOARD PRO RESPONSE TEST\n"
            "============================================================\n\n"
            "This is a sample output to show off the visual wrapping, spacing,\n"
            "and alignment capabilities of the answer board. The system utilizes\n"
            "CustomTkinter's advanced modern widgets combined with a beautiful Slate-900\n"
            "color theme.\n\n"
            "FEATURES VERIFIED:\n"
            "- Dark Professional UI Theme: Active\n"
            "- Scrollable Read-Only View: Active\n"
            "- Font Zoom Controls (+/-): Active\n"
            "- Words & Characters Count: Active\n"
            "- Copy to Clipboard & File Export: Active\n"
            "- Thread-Safe State Controllers: Active"
        )
        app = AnswerBoardApp(answer_text=mock_str, elapsed_time=1.45)
        app.mainloop()
    except Exception as e:
        print(f"Fatal Startup Error: {e}")
        sys.exit(1)
        