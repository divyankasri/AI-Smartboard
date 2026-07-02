

import os
import sys
import time
import queue
import threading
import tkinter as tk
from tkinter import messagebox
import cv2
import numpy as np
import customtkinter as ctk
from PIL import Image, ImageTk

# ==========================================
# SERVICE INTEGRATION & FALLBACKS
# ==========================================
try:
    import mediapipe as mp
    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False

try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False

try:
    from gemini_service import ask_gemini
except ImportError:
    def ask_gemini(question):
        return f"Mock Gemini response for: {question}", 1.5

try:
    from history_service import log_history
except ImportError:
    def log_history(q, a, e):
        pass

try:
    from answer_board import AnswerBoardApp
except ImportError:
    AnswerBoardApp = None


# ==========================================
# THEME CONFIGURATION
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
WARN_COLOR = "#F59E0B"       # Amber-500


class HandTrackingApp(ctk.CTk):
    """
    Main CustomTkinter window wrapping the OpenCV thread loop and air writing canvas.
    """
    def __init__(self, controller=None):
        super().__init__()

        self.controller = controller
        
        # Camera configurations
        self.cap = None
        self.camera_idx = 0
        self.is_camera_running = False
        
        # Threading/Queues
        self.result_queue = queue.Queue()
        self.is_ocr_processing = False
        
        # MediaPipe initialization
        if HAS_MEDIAPIPE:
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.7
            )
            self.mp_draw = mp.solutions.drawing_utils

        # EasyOCR Reader loaded in background thread to avoid startup latency
        self.ocr_reader = None
        threading.Thread(target=self._initialize_ocr, daemon=True).start()

        # Canvas drawing parameters
        self.canvas_width = 640
        self.canvas_height = 480
        self.canvas = np.zeros((self.canvas_height, self.canvas_width, 3), dtype=np.uint8)
        
        # Stroke history for Undo/Redo
        self.strokes = []        # List of lists: each inner list contains points (x, y, color, thickness)
        self.redo_stack = []     # Backup for popped strokes
        self.current_stroke = [] # Temp points collector
        
        # Drawing tool parameters
        self.current_color = (0, 148, 13) # Default Green (BGR format: 13, 148, 0 -> #0D9488 in RGB style)
        self.current_thickness = 8
        self.eraser_radius = 40
        self.last_x, self.last_y = 0, 0
        
        # FPS counter states
        self.prev_frame_time = 0
        self.fps = 0

        # Configure window settings
        self.title("AI Smartboard Pro - Gesture Workspace")
        self.geometry("1100x720")
        self.minsize(980, 640)
        self.configure(fg_color=BG_COLOR)

        # Center window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 1100) // 2
        y = (self.winfo_screenheight() - 720) // 2
        self.geometry(f"1100x720+{x}+{y}")

        # Initialize Fonts
        self.font_title = ctk.CTkFont(family="Inter", size=22, weight="bold")
        self.font_header = ctk.CTkFont(family="Inter", size=15, weight="bold")
        self.font_body = ctk.CTkFont(family="Inter", size=13, weight="normal")
        self.font_status = ctk.CTkFont(family="Inter", size=12, weight="bold")
        self.font_small = ctk.CTkFont(family="Inter", size=11, weight="normal")

        # Build UI layout & shortcuts
        self._build_ui()
        self._setup_shortcuts()

        # Try to initialize Camera feed
        self.start_camera()

    def _initialize_ocr(self):
        """Initializes the EasyOCR reader in the background."""
        if HAS_EASYOCR:
            try:
                # Load English reader model
                self.ocr_reader = easyocr.Reader(['en'], gpu=False)
            except Exception as e:
                print(f"Error initializing EasyOCR Reader: {e}")

    def _build_ui(self):
        """Constructs application UI structure."""
        self.grid_columnconfigure(0, weight=1, minsize=260)  # Controls Sidebar
        self.grid_columnconfigure(1, weight=3, minsize=660)  # Camera Preview Panel
        self.grid_rowconfigure(0, weight=0)                  # Header
        self.grid_rowconfigure(1, weight=1)                  # Content Area
        self.grid_rowconfigure(2, weight=0)                  # Footer

        # ----------------- HEADER PANEL -----------------
        self.header = ctk.CTkFrame(self, fg_color=BG_COLOR, height=60, corner_radius=0)
        self.header.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)
        self.header.grid_columnconfigure(1, weight=1)

        # Back/Home Button
        self.home_btn = ctk.CTkButton(
            self.header, text="←  Home", width=90, height=34,
            fg_color="transparent", border_color=BORDER_COLOR, border_width=1,
            text_color=TEXT_PRIMARY, hover_color=CARD_BG, font=self.font_status,
            command=self.go_home
        )
        self.home_btn.grid(row=0, column=0, sticky="w")

        # Title Block
        title_container = ctk.CTkFrame(self.header, fg_color="transparent")
        title_container.grid(row=0, column=1, sticky="w", padx=20)
        ctk.CTkLabel(title_container, text="AI SMARTBOARD PRO", text_color=TEXT_PRIMARY, font=self.font_title).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(title_container, text="Air Writing & Hand Gesture Control Canvas", text_color=TEXT_MUTED, font=self.font_small).grid(row=1, column=0, sticky="w")

        # Live FPS & Connection badge
        badge_frame = ctk.CTkFrame(self.header, fg_color=CARD_BG, height=34, corner_radius=8, border_color=BORDER_COLOR, border_width=1)
        badge_frame.grid(row=0, column=2, sticky="e")
        
        self.fps_label = ctk.CTkLabel(badge_frame, text="FPS: --", font=self.font_status, text_color=SUCCESS_COLOR)
        self.fps_label.pack(side="left", padx=(12, 12))

        # Divider
        ctk.CTkFrame(self, height=1, fg_color=BORDER_COLOR).grid(row=0, column=0, columnspan=2, sticky="s")

        # ----------------- LEFT CONTROLS SIDEBAR -----------------
        self.sidebar = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12, border_color=BORDER_COLOR, border_width=1)
        self.sidebar.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)
        self.sidebar.grid_columnconfigure(0, weight=1)

        # Brush Color Section
        ctk.CTkLabel(self.sidebar, text="Pen Color", text_color=TEXT_PRIMARY, font=self.font_header, anchor="w").grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        
        color_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        color_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        
        # Color palettes definitions (RGB format for buttons, BGR converted for OpenCV)
        colors = [
            ("#0D9488", (0, 148, 13)),     # Teal Green
            ("#3B82F6", (246, 130, 59)),   # Indigo Blue
            ("#EF4444", (68, 68, 239)),    # Crimson Red
            ("#F59E0B", (11, 158, 245)),   # Amber Yellow
            ("#FFFFFF", (255, 255, 255))   # Plain White
        ]
        self.color_buttons = []
        for i, (hex_code, bgr_val) in enumerate(colors):
            btn = ctk.CTkButton(
                color_frame, text="", width=28, height=28, corner_radius=14,
                fg_color=hex_code, hover_color=hex_code, border_color=BORDER_COLOR,
                border_width=1, command=lambda c=bgr_val, h=hex_code: self.change_color(c, h)
            )
            btn.grid(row=0, column=i, padx=4)
            self.color_buttons.append((btn, hex_code))
            
        # Draw initial active color highlight
        self.change_color((0, 148, 13), "#0D9488")

        # Brush Thickness Section
        ctk.CTkLabel(self.sidebar, text="Pen Thickness", text_color=TEXT_PRIMARY, font=self.font_header, anchor="w").grid(row=2, column=0, sticky="ew", padx=15, pady=(15, 5))
        self.thickness_slider = ctk.CTkSlider(
            self.sidebar, from_=2, to=30, number_of_steps=14, height=16,
            button_color=ACCENT_COLOR, button_hover_color=ACCENT_HOVER,
            command=self.change_thickness
        )
        self.thickness_slider.set(self.current_thickness)
        self.thickness_slider.grid(row=3, column=0, sticky="ew", padx=15, pady=5)
        
        self.thickness_lbl = ctk.CTkLabel(self.sidebar, text=f"Thickness: {self.current_thickness}px", text_color=TEXT_MUTED, font=self.font_small, anchor="w")
        self.thickness_lbl.grid(row=4, column=0, sticky="ew", padx=15, pady=(0, 10))

        # Action Buttons Section
        ctk.CTkLabel(self.sidebar, text="Canvas Tools", text_color=TEXT_PRIMARY, font=self.font_header, anchor="w").grid(row=5, column=0, sticky="ew", padx=15, pady=(10, 5))
        
        btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        btn_frame.grid(row=6, column=0, sticky="ew", padx=15, pady=5)
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        self.undo_btn = ctk.CTkButton(
            btn_frame, text="↩  Undo", height=32, fg_color="transparent", border_color=BORDER_COLOR,
            border_width=1, text_color=TEXT_PRIMARY, hover_color=BG_COLOR, font=self.font_status, command=self.undo_stroke
        )
        self.undo_btn.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self.redo_btn = ctk.CTkButton(
            btn_frame, text="↪  Redo", height=32, fg_color="transparent", border_color=BORDER_COLOR,
            border_width=1, text_color=TEXT_PRIMARY, hover_color=BG_COLOR, font=self.font_status, command=self.redo_stroke
        )
        self.redo_btn.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        self.clear_btn = ctk.CTkButton(
            self.sidebar, text="🧹 Clear Whole Canvas", height=34, fg_color="transparent", border_color=BORDER_COLOR,
            border_width=1, text_color=TEXT_PRIMARY, hover_color="#3F1C1C", font=self.font_status, command=self.clear_canvas
        )
        self.clear_btn.grid(row=7, column=0, sticky="ew", padx=15, pady=6)

        # Divider
        ctk.CTkFrame(self.sidebar, height=1, fg_color=BORDER_COLOR).grid(row=8, column=0, sticky="ew", padx=15, pady=15)

        # AI OCR Processing Panel
        ctk.CTkLabel(self.sidebar, text="AI OCR Engine", text_color=TEXT_PRIMARY, font=self.font_header, anchor="w").grid(row=9, column=0, sticky="ew", padx=15, pady=(0, 5))

        self.ocr_btn = ctk.CTkButton(
            self.sidebar, text="Extract & Ask AI ✦", height=40, fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER,
            text_color=TEXT_PRIMARY, font=self.font_status, command=self.trigger_ocr_process
        )
        self.ocr_btn.grid(row=10, column=0, sticky="ew", padx=15, pady=8)

        # Status displays
        self.status_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.status_container.grid(row=11, column=0, sticky="nsew", padx=15, pady=(5, 15))
        self.status_container.grid_columnconfigure(0, weight=1)

        self.gesture_lbl = ctk.CTkLabel(self.status_container, text="Gesture: Hovering/Selecting", text_color=TEXT_MUTED, font=self.font_body, anchor="w")
        self.gesture_lbl.pack(fill="x", pady=2)

        self.ai_status_lbl = ctk.CTkLabel(self.status_container, text="AI Status: Ready", text_color=TEXT_MUTED, font=self.font_body, anchor="w")
        self.ai_status_lbl.pack(fill="x", pady=2)

        # ----------------- MAIN VIDEO PREVIEW PANEL -----------------
        self.preview_panel = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12, border_color=BORDER_COLOR, border_width=1)
        self.preview_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=10)
        self.preview_panel.grid_columnconfigure(0, weight=1)
        self.preview_panel.grid_rowconfigure(0, weight=1)

        # Embedded image label for Camera feed
        self.video_display = ctk.CTkLabel(self.preview_panel, text="Camera Stream loading...", text_color=TEXT_MUTED, font=self.font_body)
        self.video_display.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        # ----------------- FOOTER PANEL -----------------
        footer = ctk.CTkFrame(self, fg_color=BG_COLOR, height=25)
        footer.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=5)
        ctk.CTkLabel(footer, text="Gesture Map: ☝ Index Up: Draw  |  ✌ Index+Middle Up: Select/Hover  |  🖐 Open Palm: Eraser  |  ✊ Fist: Idle", text_color=TEXT_MUTED, font=self.font_small).pack(side="left")
        ctk.CTkLabel(footer, text="Ctrl+Z: Undo  |  Ctrl+Y: Redo  |  Ctrl+L: Clear", text_color=TEXT_MUTED, font=self.font_small).pack(side="right")

    # ==========================================
    # LOGIC, INTERACTION & UTILITIES
    # ==========================================

    def _setup_shortcuts(self):
        """Binds universal application shortcuts."""
        self.bind("<Control-z>", lambda e: self.undo_stroke())
        self.bind("<Control-Z>", lambda e: self.undo_stroke())
        self.bind("<Control-y>", lambda e: self.redo_stroke())
        self.bind("<Control-Y>", lambda e: self.redo_stroke())
        self.bind("<Control-l>", lambda e: self.clear_canvas())
        self.bind("<Control-L>", lambda e: self.clear_canvas())
        self.bind("<Control-h>", lambda e: self.go_home())
        self.bind("<Control-H>", lambda e: self.go_home())

    def change_color(self, bgr_val: tuple, hex_code: str):
        """Changes the pen color and applies highlight styling to color buttons."""
        self.current_color = bgr_val
        for btn, code in self.color_buttons:
            if code == hex_code:
                btn.configure(border_color=TEXT_PRIMARY, border_width=2)
            else:
                btn.configure(border_color=BORDER_COLOR, border_width=1)

    def change_thickness(self, val):
        """Changes the drawing brush thickness state."""
        self.current_thickness = int(val)
        self.thickness_lbl.configure(text=f"Thickness: {self.current_thickness}px")

    # ==========================================
    # GESTURE CANVAS GRAPHICS ENGINE
    # ==========================================

    def clear_canvas(self):
        """Wipes the drawing canvas array completely."""
        self.strokes.clear()
        self.redo_stack.clear()
        self.current_stroke.clear()
        self.canvas = np.zeros((self.canvas_height, self.canvas_width, 3), dtype=np.uint8)
        self.update_canvas_from_strokes()

    def undo_stroke(self):
        """Pops the last rendered line stroke into redo stack."""
        if self.strokes:
            self.redo_stack.append(self.strokes.pop())
            self.update_canvas_from_strokes()

    def redo_stroke(self):
        """Pops back line stroke from redo history."""
        if self.redo_stack:
            self.strokes.append(self.redo_stack.pop())
            self.update_canvas_from_strokes()

    def update_canvas_from_strokes(self):
        """Re-draws all recorded strokes back onto the base canvas clean slate."""
        self.canvas = np.zeros((self.canvas_height, self.canvas_width, 3), dtype=np.uint8)
        
        for stroke in self.strokes:
            for i in range(1, len(stroke)):
                pt1, pt2, color, thickness, is_eraser = stroke[i-1], stroke[i], stroke[i-1][2], stroke[i-1][3], stroke[i-1][4]
                if is_eraser:
                    # Render eraser as black line stroke to clear canvas content
                    cv2.line(self.canvas, (pt1[0], pt1[1]), (pt2[0], pt2[1]), (0, 0, 0), thickness)
                else:
                    cv2.line(self.canvas, (pt1[0], pt1[1]), (pt2[0], pt2[1]), color, thickness)

    # ==========================================
    # CAMERA STREAM LOOP (CV2 + MEDIAPIPE)
    # ==========================================

    def start_camera(self):
        """Attempts camera allocation and schedules loop updates."""
        try:
            self.cap = cv2.VideoCapture(self.camera_idx)
            if not self.cap.isOpened():
                raise ConnectionError("Camera could not be accessed.")
            
            self.is_camera_running = True
            self._camera_update_loop()
        except Exception as e:
            self.video_display.configure(text=f"Camera Error: {e}\n\nPlease check camera connections.")
            self.update_status_bar("Camera setup failed.", error=True)

    def _camera_update_loop(self):
        """Primary application execution loop executing 30 times a second."""
        if not self.is_camera_running or self.cap is None:
            return

        success, frame = self.cap.read()
        if not success:
            # Re-schedule loop check
            self.after(15, self._camera_update_loop)
            return

        # Resize and flip frame mirror-wise
        frame = cv2.resize(frame, (self.canvas_width, self.canvas_height))
        frame = cv2.flip(frame, 1)

        # Gesture and Tracking computations
        processed_frame = self._process_tracking_layers(frame)

        # Convert frame to RGB PIL Image format for ctk integration
        img_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        
        # Form ctk-compatible Image and assign
        img_ctk = ImageTk.PhotoImage(image=img_pil)
        self.video_display.configure(image=img_ctk, text="")
        self.video_display._image_cache = img_ctk  # Cache reference to prevent garbage collection

        # Calculate FPS
        curr_time = time.time()
        self.fps = int(1 / (curr_time - self.prev_frame_time)) if self.prev_frame_time > 0 else 0
        self.prev_frame_time = curr_time
        self.fps_label.configure(text=f"FPS: {self.fps}")

        # Continue update cycle
        self.after(15, self._camera_update_loop)

    def _process_tracking_layers(self, frame) -> np.ndarray:
        """Processes hand landmarks, interprets gestures, and draws lines."""
        if not HAS_MEDIAPIPE:
            # Draw canvas directly on camera frames if ML pipeline is missing
            return self._blend_canvas_preview(frame)

        # Convert to RGB for MediaPipe Hand Analysis
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)

        gesture = "Hovering/Selecting"
        x, y = 0, 0

        if results.multi_hand_landmarks:
            for hand_lms in results.multi_hand_landmarks:
                # Get Index finger Tip landmarks
                index_tip = hand_lms.landmark[8]
                middle_tip = hand_lms.landmark[12]
                ring_tip = hand_lms.landmark[16]
                pinky_tip = hand_lms.landmark[20]
                thumb_tip = hand_lms.landmark[4]

                # Convert normalized landmarks to pixel coordinates
                x = int(index_tip.x * self.canvas_width)
                y = int(index_tip.y * self.canvas_height)

                # Gesture Mapping logic (detecting finger extension stats)
                # True if finger tip y is above knuckle y (lower coordinate value means higher y coordinate visually)
                index_up = index_tip.y < hand_lms.landmark[6].y
                middle_up = middle_tip.y < hand_lms.landmark[10].y
                ring_up = ring_tip.y < hand_lms.landmark[14].y
                pinky_up = pinky_tip.y < hand_lms.landmark[18].y
                thumb_up = thumb_tip.y < hand_lms.landmark[2].y

                # Draw finger tip cursor location
                cv2.circle(frame, (x, y), 8, (0, 255, 255), -1)

                # A. Eraser Mode (All fingers extended / open palm)
                if index_up and middle_up and ring_up and pinky_up:
                    gesture = "Eraser Mode"
                    cv2.circle(frame, (x, y), self.eraser_radius, (200, 200, 200), 2)
                    
                    if self.last_x != 0 and self.last_y != 0:
                        # Append eraser stroke points
                        if not self.current_stroke:
                            self.redo_stack.clear()
                        self.current_stroke.append((x, y, (0, 0, 0), self.eraser_radius, True))
                        cv2.line(self.canvas, (self.last_x, self.last_y), (x, y), (0, 0, 0), self.eraser_radius)
                    
                    self.last_x, self.last_y = x, y

                # B. Writing Mode (Only Index finger extended up)
                elif index_up and not middle_up:
                    gesture = "Writing Mode"
                    cv2.circle(frame, (x, y), self.current_thickness, self.current_color, -1)
                    
                    if self.last_x != 0 and self.last_y != 0:
                        if not self.current_stroke:
                            self.redo_stack.clear()
                        self.current_stroke.append((x, y, self.current_color, self.current_thickness, False))
                        cv2.line(self.canvas, (self.last_x, self.last_y), (x, y), self.current_color, self.current_thickness)
                    
                    self.last_x, self.last_y = x, y

                # C. Idle Mode (Fist / All fingers folded)
                elif not index_up and not middle_up and not ring_up and not pinky_up:
                    gesture = "Idle (Fist)"
                    self._finalize_current_stroke()
                    self.last_x, self.last_y = 0, 0

                # D. Cursor / Hover Mode (Index and Middle extended)
                else:
                    gesture = "Hovering/Selecting"
                    self._finalize_current_stroke()
                    self.last_x, self.last_y = 0, 0
                    
                # Render MediaPipe joints on preview frame
                self.mp_draw.draw_landmarks(frame, hand_lms, self.mp_hands.HAND_CONNECTIONS)
        else:
            self._finalize_current_stroke()
            self.last_x, self.last_y = 0, 0

        # Update dynamic labels
        self.gesture_lbl.configure(text=f"Gesture: {gesture}")
        
        return self._blend_canvas_preview(frame)

    def _finalize_current_stroke(self):
        """Saves current temporary stroke list into strokes database history."""
        if self.current_stroke:
            self.strokes.append(self.current_stroke)
            self.current_stroke = []

    def _blend_canvas_preview(self, frame) -> np.ndarray:
        """Blends canvas lines onto camera frame using color channels thresholding."""
        # Convert canvas to grayscale and threshold it to isolate colored strokes
        img_gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        _, img_inv = cv2.threshold(img_gray, 5, 255, cv2.THRESH_BINARY_INV)
        
        # Bitwise actions to mask background and blend canvas lines onto webcam frame
        img_inv = cv2.cvtColor(img_inv, cv2.COLOR_GRAY2BGR)
        frame_bg = cv2.bitwise_and(frame, img_inv)
        frame_fg = cv2.bitwise_and(self.canvas, self.canvas)
        
        return cv2.add(frame_bg, frame_fg)

    # ==========================================
    # EASYOCR & GEMINI ENGINE ASYNC WORKERS
    # ==========================================

    def trigger_ocr_process(self):
        """Trigger point starting OCR extraction and AI query pipeline."""
        if self.is_ocr_processing:
            return

        # Check OCR engine status
        if HAS_EASYOCR and self.ocr_reader is None:
            messagebox.showinfo("Engine Loading", "EasyOCR models are still loading in the background. Please wait.")
            return

        self.is_ocr_processing = True
        self.ocr_btn.configure(state="disabled")
        self.home_btn.configure(state="disabled")
        self.clear_btn.configure(state="disabled")
        self.ocr_btn.configure(text="Processing AI...")
        self.ai_status_lbl.configure(text="AI Status: Analyzing handwriting...")

        # Start background OCR worker thread
        threading.Thread(target=self._async_ocr_ai_worker, daemon=True).start()
        
        # Start queue responses check polling loop
        self.after(100, self._poll_result_queue)

    def _async_ocr_ai_worker(self):
        """Asynchronous execution pipeline running OCR + Gemini requests."""
        start_time = time.time()
        try:
            # 1. OCR Extraction Phase
            extracted_text = ""
            
            if HAS_EASYOCR and self.ocr_reader:
                # Convert canvas drawing to grayscale for optimal text contrast recognition
                gray_canvas = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
                
                # Check if canvas is completely empty (all black pixels)
                if cv2.countNonZero(gray_canvas) == 0:
                    self.result_queue.put({"success": False, "error": "Canvas is empty. Draw a question first!"})
                    return
                
                # Run OCR text detection
                ocr_results = self.ocr_reader.readtext(gray_canvas)
                extracted_text = " ".join([result[1] for result in ocr_results]).strip()
            else:
                # Mock local simulation if EasyOCR package is missing
                time.sleep(1.0)
                extracted_text = "What is the capital of France?"

            if not extracted_text:
                self.result_queue.put({"success": False, "error": "Could not recognize handwriting. Make strokes clearer!"})
                return

            # 2. Gemini Query Phase
            self.result_queue.put({"update_status": f"AI Status: Querying Gemini for: '{extracted_text}'"})
            answer, elapsed = ask_gemini(extracted_text)
            
            # Save query log locally
            log_history(extracted_text, answer, elapsed)

            self.result_queue.put({
                "success": True,
                "question": extracted_text,
                "answer": answer,
                "elapsed": elapsed
            })
        except Exception as e:
            self.result_queue.put({"success": False, "error": str(e)})

    def _poll_result_queue(self):
        """Queries queue output and triggers interface updates."""
        try:
            while True:
                msg = self.result_queue.get_nowait()
                
                if "update_status" in msg:
                    self.ai_status_lbl.configure(text=msg["update_status"])
                    continue
                
                self._finalize_ai_pipeline(msg)
                return
        except queue.Empty:
            if self.is_ocr_processing:
                self.after(100, self._poll_result_queue)

    def _finalize_ai_pipeline(self, msg: dict):
        """Unlocks interface elements and routes success responses."""
        self.is_ocr_processing = False
        self.ocr_btn.configure(state="normal")
        self.home_btn.configure(state="normal")
        self.clear_btn.configure(state="normal")
        self.ocr_btn.configure(text="Extract & Ask AI ✦")
        self.ai_status_lbl.configure(text="AI Status: Ready")

        if msg["success"]:
            # Prompt user with extracted text verification before opening answer board
            confirm = messagebox.askyesno(
                "OCR Extracted Text",
                f"Recognized Question:\n\n\"{msg['question']}\"\n\nDo you want to see the AI Answer Board?"
            )
            if confirm and AnswerBoardApp:
                # Launch Answer Board with parameters
                board = AnswerBoardApp(answer_text=msg["answer"], elapsed_time=msg["elapsed"])
                board.protocol("WM_DELETE_WINDOW", lambda: self._on_board_close(board))
                self.withdraw() # Hide this tracking window
                board.mainloop()
        else:
            messagebox.showerror("AI Processing Error", msg["error"])

    def _on_board_close(self, board):
        """Restores tracking interface when Answer Board is closed."""
        board.destroy()
        self.deiconify()

    def update_status_bar(self, text: str, error: bool = False):
        """Helper to show status logs."""
        print(f"Status: {text} | Error: {error}")

    # ==========================================
    # NAVIGATION METHODS
    # ==========================================

    def go_home(self):
        """Handles dashboard launch transition back to home launcher."""
        self.release_camera()
        
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
                threading.Thread(target=home.main if hasattr(home, "main") else home.run, daemon=True).start()
            else:
                self.destroy()
        except ImportError:
            self.destroy()

    def release_camera(self):
        """Cleans and releases active camera devices."""
        self.is_camera_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def destroy(self):
        """Auto camera release hook on close/destroy event."""
        self.release_camera()
        super().destroy()


# ==========================================
# SYSTEM RUNNER ENTRY POINT
# ==========================================
if __name__ == "__main__":
    try:
        app = HandTrackingApp()
        app.protocol("WM_DELETE_WINDOW", app.destroy)
        app.mainloop()
    except Exception as e:
        print(f"Fatal Startup Error: {e}")
        sys.exit(1)