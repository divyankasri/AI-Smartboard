"""
AI Smartboard Pro - Main Dashboard Hub
=====================================

This module implements the central dashboard window for the AI Smartboard Pro suite.
It displays branding, provides navigation cards, manages settings configuration via
JSON files, displays session history via history_service integration, and spawns
workspace modes (keyboard mode and air writing mode) as independent subprocesses.

Developer: Divyanka Srivastava
"""

import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

# Try importing history service
try:
    import history_service
except ImportError:
    history_service = None

# ==========================================
# CONFIGURATION & SETTINGS FILE
# ==========================================
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

DEFAULT_SETTINGS = {
    "appearance_mode": "Dark",
    "accent_color": "teal",
    "camera_id": 0,
    "ocr_lang": "English",
    "font_size": 14
}

def load_settings() -> dict:
    """Loads application settings from local JSON file."""
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure all default keys exist
            for k, v in DEFAULT_SETTINGS.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception:
        return DEFAULT_SETTINGS.copy()

def save_settings(settings: dict) -> bool:
    """Saves settings configuration to local JSON file."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
            return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False


# ==========================================
# CENTRAL APPLICATION DASHBOARD
# ==========================================
class HomeDashboard(ctk.CTk):
    """
    Main controller dashboard of the AI Smartboard Pro software.
    """
    def __init__(self):
        super().__init__()

        # Load and configure user settings
        self.app_settings = load_settings()
        self._apply_theme_settings()

        # Window settings
        self.title("AI Smartboard Pro - Hub")
        self.geometry("960x650")
        self.minsize(920, 580)

        # Center window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 960) // 2
        y = (self.winfo_screenheight() - 650) // 2
        self.geometry(f"960x650+{x}+{y}")

        # Config colors (mapped dynamically based on settings)
        self._setup_dynamic_colors()

        # Initialize Fonts
        self.font_title = ctk.CTkFont(family="Inter", size=24, weight="bold")
        self.font_header = ctk.CTkFont(family="Inter", size=16, weight="bold")
        self.font_body = ctk.CTkFont(family="Inter", size=13, weight="normal")
        self.font_status = ctk.CTkFont(family="Inter", size=12, weight="bold")
        self.font_small = ctk.CTkFont(family="Inter", size=11, weight="normal")

        # UI structures
        self._build_ui()
        self._setup_shortcuts()

    def _apply_theme_settings(self):
        """Applies configured settings themes."""
        ctk.set_appearance_mode(self.app_settings.get("appearance_mode", "Dark"))
        
        # Set theme colors
        accent = self.app_settings.get("accent_color", "teal").lower()
        if accent == "teal":
            ctk.set_default_color_theme("blue") # fallback blue template
        elif accent == "blue":
            ctk.set_default_color_theme("blue")
        else:
            ctk.set_default_color_theme("green")

    def _setup_dynamic_colors(self):
        """Sets custom slate theme colors based on loaded settings."""
        self.bg_color = "#0F172A"       # Slate-900
        self.card_bg = "#1E293B"        # Slate-800
        self.border_color = "#334155"   # Slate-700
        self.text_primary = "#F8FAFC"   # Slate-50
        self.text_muted = "#94A3B8"     # Slate-400
        
        accent = self.app_settings.get("accent_color", "teal").lower()
        if accent == "teal":
            self.accent_color = "#0D9488"
            self.accent_hover = "#0F766E"
        elif accent == "blue":
            self.accent_color = "#2563EB"
            self.accent_hover = "#1D4ED8"
        else:
            self.accent_color = "#16A34A"
            self.accent_hover = "#15803D"

        self.configure(fg_color=self.bg_color)

    def _build_ui(self):
        """Assembles dashboard grid layout."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Central workspace grid card selector
        self.grid_rowconfigure(2, weight=0)  # Footer Status bar

        # ----------------- HEADER PANEL -----------------
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", padx=35, pady=(30, 15))
        self.header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.header, text="AI SMARTBOARD PRO", text_color=self.text_primary, font=self.font_title, anchor="w"
        ).grid(row=0, column=0, sticky="w")
        
        ctk.CTkLabel(
            self.header, text="Central Navigation Hub & Air Gesture Suite", text_color=self.text_muted, font=self.font_body, anchor="w"
        ).grid(row=1, column=0, sticky="w")

        # Dynamic connection status badge
        badge = ctk.CTkFrame(self.header, fg_color=self.card_bg, height=36, corner_radius=18, border_color=self.border_color, border_width=1)
        badge.grid(row=0, column=1, rowspan=2, sticky="e")
        ctk.CTkLabel(badge, text="●", text_color="#10B981", font=self.font_status).pack(side="left", padx=(12, 6))
        ctk.CTkLabel(badge, text="Dashboard Online", text_color=self.text_primary, font=self.font_small).pack(side="left", padx=(0, 12))

        # ----------------- MAIN DESKTOP NAVIGATION GRID -----------------
        self.grid_container = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_container.grid(row=1, column=0, sticky="nsew", padx=25, pady=10)
        
        self.grid_container.grid_columnconfigure((0, 1), weight=1, uniform="nav_cols")
        self.grid_container.grid_rowconfigure((0, 1, 2), weight=1, uniform="nav_rows")

        # Navigation 1: Air Writing Mode Card
        self.card_air = ctk.CTkFrame(self.grid_container, fg_color=self.card_bg, corner_radius=12, border_color=self.border_color, border_width=1)
        self.card_air.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)
        self._build_nav_card(
            self.card_air, "✋  Air Writing Mode",
            "Write in air using hand gestures. The system captures handwriting, runs OCR, asks Gemini AI, and pops up answers.",
            "Start Camera", self.launch_air_writing
        )

        # Navigation 2: Keyboard Workspace Mode Card
        self.card_keyboard = ctk.CTkFrame(self.grid_container, fg_color=self.card_bg, corner_radius=12, border_color=self.border_color, border_width=1)
        self.card_keyboard.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=10, pady=10)
        self._build_nav_card(
            self.card_keyboard, "⌨  Keyboard Mode",
            "Distraction-free workspace. Type questions directly, view code snippets cleanly, and track session log queries.",
            "Launch Workspace", self.launch_keyboard_mode
        )

        # Bottom Utilities row
        utils_frame = ctk.CTkFrame(self.grid_container, fg_color="transparent")
        utils_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 15))
        utils_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="utils_cols")

        self.btn_history = ctk.CTkButton(
            utils_frame, text="📋 Session History", height=42, fg_color=self.card_bg, border_color=self.border_color,
            border_width=1, text_color=self.text_primary, hover_color=self.accent_color, font=self.font_status,
            command=self.open_history_window
        )
        self.btn_history.grid(row=0, column=0, padx=6, sticky="ew")

        self.btn_settings = ctk.CTkButton(
            utils_frame, text="⚙  Settings", height=42, fg_color=self.card_bg, border_color=self.border_color,
            border_width=1, text_color=self.text_primary, hover_color=self.accent_color, font=self.font_status,
            command=self.open_settings_window
        )
        self.btn_settings.grid(row=0, column=1, padx=6, sticky="ew")

        self.btn_about = ctk.CTkButton(
            utils_frame, text="ℹ  About Project", height=42, fg_color=self.card_bg, border_color=self.border_color,
            border_width=1, text_color=self.text_primary, hover_color=self.accent_color, font=self.font_status,
            command=self.open_about_dialog
        )
        self.btn_about.grid(row=0, column=2, padx=6, sticky="ew")

        self.btn_exit = ctk.CTkButton(
            utils_frame, text="❌ Exit Suite", height=42, fg_color=self.card_bg, border_color=self.border_color,
            border_width=1, text_color="#EF4444", hover_color="#3F1C1C", font=self.font_status,
            command=self.quit_suite
        )
        self.btn_exit.grid(row=0, column=3, padx=6, sticky="ew")

        # ----------------- FOOTER PANEL -----------------
        self.footer = ctk.CTkFrame(self, fg_color=self.bg_color, height=35)
        self.footer.grid(row=2, column=0, sticky="ew", padx=35, pady=(5, 15))
        
        ctk.CTkLabel(
            self.footer, text="Developer: Divyanka Srivastava • Final Year Project", text_color=self.text_muted, font=self.font_small
        ).pack(side="left")
        
        ctk.CTkLabel(
            self.footer, text="AI Smartboard SDK v1.2.0 (Stable)", text_color=self.text_muted, font=self.font_small
        ).pack(side="right")

    def _build_nav_card(self, parent, title, desc, btn_text, command):
        """Constructs layout inside primary mode selection cards."""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            parent, text=title, text_color=self.text_primary, font=self.font_header, anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 5))

        # Underline divider inside card
        ctk.CTkFrame(parent, height=1, fg_color=self.border_color).grid(row=1, column=0, sticky="ew", padx=20, pady=5)

        ctk.CTkLabel(
            parent, text=desc, text_color=self.text_muted, font=self.font_body, justify="left", wraplength=300
        ).grid(row=2, column=0, sticky="nw", padx=20, pady=15)

        # Primary Launch Button
        btn = ctk.CTkButton(
            parent, text=btn_text, height=40, fg_color=self.accent_color, hover_color=self.accent_hover,
            text_color=self.text_primary, font=self.font_status, command=command
        )
        btn.grid(row=3, column=0, sticky="ew", padx=20, pady=(10, 20))

    def _setup_shortcuts(self):
        """Registers dashboard shortcuts."""
        self.bind("<Control-s>", lambda e: self.open_settings_window())
        self.bind("<Control-S>", lambda e: self.open_settings_window())
        self.bind("<Control-h>", lambda e: self.open_history_window())
        self.bind("<Control-H>", lambda e: self.open_history_window())
        self.bind("<Escape>", lambda e: self.quit_suite())

    # ==========================================
    # SUBPROCESS SPAWN NAVIGATION SYSTEM
    # ==========================================
    def launch_air_writing(self):
        """Spawns hand_tracking.py as an isolated background subprocess."""
        self._spawn_subprocess("hand_tracking.py")

    def launch_keyboard_mode(self):
        """Spawns keyboard_mode.py as an isolated background subprocess."""
        self._spawn_subprocess("keyboard_mode.py")

    def _spawn_subprocess(self, script_name: str):
        """Safely invokes a script via the current python process environment."""
        try:
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"File '{script_name}' not found in directory.")
            
            # Non-blocking async launch
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            messagebox.showerror("Process Launch Error", f"Could not launch module '{script_name}':\n{e}")

    # ==========================================
    # DIALOG WINDOW SYSTEMS (History, Settings, About)
    # ==========================================

    def open_history_window(self):
        """Displays modern top-level list showing persistent queries history."""
        hist_win = ctk.CTkToplevel(self)
        hist_win.title("AI Smartboard Pro - Session History")
        hist_win.geometry("600x500")
        hist_win.configure(fg_color=self.bg_color)
        hist_win.transient(self)
        hist_win.grab_set()

        hist_win.grid_columnconfigure(0, weight=1)
        hist_win.grid_rowconfigure(1, weight=1)

        # Header Title
        ctk.CTkLabel(
            hist_win, text="Session Query History Logs", text_color=self.text_primary, font=self.font_header
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # Main Scrollable list frame
        scroll_frame = ctk.CTkScrollableFrame(hist_win, fg_color=self.card_bg, border_color=self.border_color, border_width=1)
        scroll_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        # Actions Row
        actions_frame = ctk.CTkFrame(hist_win, fg_color="transparent")
        actions_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=15)
        
        def refresh_history_view():
            # Clear previous items
            for widget in scroll_frame.winfo_children():
                widget.destroy()

            if not history_service:
                ctk.CTkLabel(scroll_frame, text="History service could not be loaded.", text_color=self.text_muted).pack(pady=20)
                return

            items = history_service.get_history()
            if not items:
                ctk.CTkLabel(scroll_frame, text="No query records logged yet.", text_color=self.text_muted).pack(pady=20)
                return

            # Render history rows
            for record in items:
                row = ctk.CTkFrame(scroll_frame, fg_color="transparent")
                row.pack(fill="x", pady=4, padx=4)
                
                # Truncate text preview
                q_text = record["question"].replace("\n", " ")
                if len(q_text) > 45:
                    q_text = q_text[:42] + "..."
                    
                lbl = ctk.CTkButton(
                    row, text=f"{record.get('timestamp', '--:--')} | {q_text}", anchor="w",
                    fg_color="transparent", text_color=self.text_primary, hover_color=self.border_color,
                    font=self.font_body, height=32,
                    command=lambda r=record: show_detail(r)
                )
                lbl.pack(fill="x")
                ctk.CTkFrame(scroll_frame, height=1, fg_color=self.border_color).pack(fill="x", padx=10)

        def show_detail(record: dict):
            # Popup displaying query details
            detail_win = ctk.CTkToplevel(hist_win)
            detail_win.title("Query Log Details")
            detail_win.geometry("500x400")
            detail_win.configure(fg_color=self.bg_color)
            detail_win.transient(hist_win)
            detail_win.grab_set()

            detail_win.grid_columnconfigure(0, weight=1)
            detail_win.grid_rowconfigure(1, weight=1)

            # Metadata header
            lbl_meta = ctk.CTkLabel(
                detail_win, text=f"Date: {record.get('date', 'N/A')}  |  Time: {record.get('timestamp', 'N/A')}  |  Latency: {record.get('elapsed', 0.0):.2f}s",
                text_color=self.text_muted, font=self.font_small
            )
            lbl_meta.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 5))

            # Scrollable details viewer
            txt_box = ctk.CTkTextbox(detail_win, fg_color=self.card_bg, border_color=self.border_color, border_width=1, font=self.font_body)
            txt_box.configure(wrap="word")
            txt_box.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
            
            content = f"QUESTION:\n{record['question']}\n\n" + "="*40 + f"\n\nANSWER:\n{record['answer']}"
            txt_box.insert("1.0", content)
            txt_box.configure(state="disabled")

            ctk.CTkButton(detail_win, text="Close Details", fg_color=self.accent_color, hover_color=self.accent_hover, text_color=self.text_primary, command=detail_win.destroy).grid(row=2, column=0, pady=15)

        def clear_all_history():
            if not messagebox.askyesno("Confirm Clear", "Clear all saved queries history permanently?"):
                return
            if history_service:
                history_service.clear_history()
            refresh_history_view()

        ctk.CTkButton(
            actions_frame, text="🧹 Clear All Logs", fg_color="transparent", border_color=self.border_color,
            border_width=1, text_color="#EF4444", hover_color="#3F1C1C", command=clear_all_history
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            actions_frame, text="Close Window", fg_color=self.accent_color, hover_color=self.accent_hover,
            text_color=self.text_primary, command=hist_win.destroy
        ).pack(side="right", padx=5)

        # Load initial values
        refresh_history_view()

    def open_settings_window(self):
        """Displays application config options interface."""
        set_win = ctk.CTkToplevel(self)
        set_win.title("AI Smartboard Pro - Settings")
        set_win.geometry("500x480")
        set_win.configure(fg_color=self.bg_color)
        set_win.transient(self)
        set_win.grab_set()

        set_win.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(set_win, text="System Configurations", text_color=self.text_primary, font=self.font_header).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(20, 15))

        # 1. Appearance Mode
        ctk.CTkLabel(set_win, text="Appearance Theme:", text_color=self.text_primary, font=self.font_body).grid(row=1, column=0, sticky="w", padx=20, pady=12)
        opt_appearance = ctk.CTkOptionMenu(set_win, values=["Dark", "Light", "System"], button_color=self.accent_color, button_hover_color=self.accent_hover, dropdown_fg_color=self.card_bg)
        opt_appearance.set(self.app_settings.get("appearance_mode", "Dark"))
        opt_appearance.grid(row=1, column=1, sticky="ew", padx=20, pady=12)

        # 2. Accent Color
        ctk.CTkLabel(set_win, text="Accent Hue Color:", text_color=self.text_primary, font=self.font_body).grid(row=2, column=0, sticky="w", padx=20, pady=12)
        opt_accent = ctk.CTkOptionMenu(set_win, values=["Teal", "Blue", "Green"], button_color=self.accent_color, button_hover_color=self.accent_hover, dropdown_fg_color=self.card_bg)
        opt_accent.set(self.app_settings.get("accent_color", "Teal").capitalize())
        opt_accent.grid(row=2, column=1, sticky="ew", padx=20, pady=12)

        # 3. Camera Selection
        ctk.CTkLabel(set_win, text="Default Camera ID:", text_color=self.text_primary, font=self.font_body).grid(row=3, column=0, sticky="w", padx=20, pady=12)
        opt_camera = ctk.CTkOptionMenu(set_win, values=["Camera 0", "Camera 1", "Camera 2"], button_color=self.accent_color, button_hover_color=self.accent_hover, dropdown_fg_color=self.card_bg)
        opt_camera.set(f"Camera {self.app_settings.get('camera_id', 0)}")
        opt_camera.grid(row=3, column=1, sticky="ew", padx=20, pady=12)

        # 4. OCR Language Selector
        ctk.CTkLabel(set_win, text="OCR Language Code:", text_color=self.text_primary, font=self.font_body).grid(row=4, column=0, sticky="w", padx=20, pady=12)
        opt_ocr = ctk.CTkOptionMenu(set_win, values=["English", "French", "Spanish"], button_color=self.accent_color, button_hover_color=self.accent_hover, dropdown_fg_color=self.card_bg)
        opt_ocr.set(self.app_settings.get("ocr_lang", "English"))
        opt_ocr.grid(row=4, column=1, sticky="ew", padx=20, pady=12)

        # 5. Font Size Slider
        ctk.CTkLabel(set_win, text="Workspace Font Size:", text_color=self.text_primary, font=self.font_body).grid(row=5, column=0, sticky="w", padx=20, pady=12)
        
        font_slider_frame = ctk.CTkFrame(set_win, fg_color="transparent")
        font_slider_frame.grid(row=5, column=1, sticky="ew", padx=20, pady=12)
        font_slider_frame.grid_columnconfigure(0, weight=1)
        
        lbl_font_sz = ctk.CTkLabel(font_slider_frame, text=f"{self.app_settings.get('font_size', 14)}px", text_color=self.text_muted, font=self.font_small, width=35)
        lbl_font_sz.pack(side="right")
        
        def update_font_lbl(val):
            lbl_font_sz.configure(text=f"{int(val)}px")

        font_slider = ctk.CTkSlider(font_slider_frame, from_=10, to=24, number_of_steps=7, button_color=self.accent_color, button_hover_color=self.accent_hover, command=update_font_lbl)
        font_slider.set(self.app_settings.get("font_size", 14))
        font_slider.pack(side="left", fill="x", expand=True)

        # Save Logic
        def save_and_close():
            new_settings = {
                "appearance_mode": opt_appearance.get(),
                "accent_color": opt_accent.get().lower(),
                "camera_id": int(opt_camera.get().split()[-1]),
                "ocr_lang": opt_ocr.get(),
                "font_size": int(font_slider.get())
            }
            if save_settings(new_settings):
                self.app_settings = new_settings
                self._apply_theme_settings()
                self._setup_dynamic_colors()
                messagebox.showinfo("Success", "Settings configuration applied successfully!")
                set_win.destroy()
            else:
                messagebox.showerror("Save Error", "Settings configuration save failed.")

        # Bottom buttons row
        btn_frame = ctk.CTkFrame(set_win, fg_color="transparent")
        btn_frame.grid(row=6, column=0, columnspan=2, pady=30, padx=20, sticky="ew")
        
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="transparent", border_color=self.border_color, border_width=1, text_color=self.text_primary, hover_color=self.card_bg, command=set_win.destroy).pack(side="left", padx=10, expand=True, fill="x")
        ctk.CTkButton(btn_frame, text="Save Settings", fg_color=self.accent_color, hover_color=self.accent_hover, text_color=self.text_primary, command=save_and_close).pack(side="right", padx=10, expand=True, fill="x")

    def open_about_dialog(self):
        """Displays top-level about window showing project metadata details."""
        about_win = ctk.CTkToplevel(self)
        about_win.title("About AI Smartboard Pro")
        about_win.geometry("520x420")
        about_win.configure(fg_color=self.bg_color)
        about_win.transient(self)
        about_win.grab_set()

        about_win.grid_columnconfigure(0, weight=1)
        about_win.grid_rowconfigure(1, weight=1)

        # Card container
        container = ctk.CTkFrame(about_win, fg_color=self.card_bg, border_color=self.border_color, border_width=1, corner_radius=12)
        container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        container.grid_columnconfigure(0, weight=1)

        # Title labels
        ctk.CTkLabel(container, text="AI SMARTBOARD PRO", text_color=self.text_primary, font=self.font_title).pack(pady=(20, 2))
        ctk.CTkLabel(container, text="Final Year Engineering Project", text_color=self.accent_color, font=self.font_status).pack()

        # Divider
        ctk.CTkFrame(container, height=1, fg_color=self.border_color).pack(fill="x", padx=30, pady=15)

        # Info body text box
        desc_box = ctk.CTkTextbox(container, fg_color="transparent", text_color=self.text_primary, font=self.font_body, height=150)
        desc_box.configure(wrap="word")
        desc_box.pack(fill="both", expand=True, padx=30)
        
        info_content = (
            "A modern smartboard workspace application allowing users to write in the air using "
            "web-camera finger tracking. The software tracks landmarks, recognizes handwriting with OCR, "
            "queries Gemini AI for answers, and formats results. \n\n"
            "Core Technologies:\n"
            "  • Python & CustomTkinter UI\n"
            "  • OpenCV (Camera capture & processing)\n"
            "  • MediaPipe Hands (Hand tracking and gesture controls)\n"
            "  • EasyOCR (Handwriting image extraction)\n"
            "  • Google Gemini Generative AI\n\n"
            "Developer: Divyanka Srivastava"
        )
        desc_box.insert("1.0", info_content)
        desc_box.configure(state="disabled")

        # Bottom Close Button
        ctk.CTkButton(
            about_win, text="Close Information", fg_color=self.accent_color, hover_color=self.accent_hover,
            text_color=self.text_primary, command=about_win.destroy
        ).grid(row=1, column=0, pady=(0, 20))

    def quit_suite(self):
        """Terminates the central dashboard window cleanly."""
        if messagebox.askyesno("Exit Smartboard Pro", "Confirm closing the application suite?"):
            self.destroy()


# ==========================================
# CENTRAL ENTRY RUNNER
# ==========================================
def main():
    try:
        app = HomeDashboard()
        app.mainloop()
    except Exception as e:
        print(f"Fatal dashboard startup error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
