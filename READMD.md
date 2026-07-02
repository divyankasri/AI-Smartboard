# AI Smartboard

An AI-powered interactive smartboard that combines Computer Vision, Hand Gesture Recognition, OCR, and Generative AI to create a modern digital classroom experience.

## Overview

AI Smartboard transforms a webcam into an intelligent teaching and learning tool. Users can interact with the board using hand gestures, write and draw virtually, recognize text through OCR, and receive AI-generated answers to questions in real time.

## Features

* ✨ Hand Gesture Recognition
* 🖊️ Virtual Drawing and Writing
* 🤖 AI-Powered Question Answering
* 📄 Optical Character Recognition (OCR)
* 🎯 Interactive Digital Whiteboard
* 🖥️ User-Friendly Interface
* 📚 Educational and Classroom-Friendly Design

## Technologies Used

* Python
* OpenCV
* MediaPipe
* EasyOCR
* CustomTkinter
* Google Gemini API
* NumPy

## Project Structure

```text
AI-Smartboard/
│
├── home.py
├── answer_board.py
├── keyboard_mode.py
├── hand_tracking.py
├── gemini_service.py
├── history_service.py
├── ocr.py
├── config.py
├── utils.py
├── requirements.txt
├── settings.json
├── assets/
└── history/
```

## Installation

1. Clone the repository

```bash
git clone https://github.com/divyankasri/AI-Smartboard.git
cd AI-Smartboard
```

2. Create a virtual environment

```bash
python -m venv venv
```

3. Activate the virtual environment

Windows:

```bash
venv\Scripts\activate
```

4. Install dependencies

```bash
pip install -r requirements.txt
```

5. Configure your Gemini API key in the appropriate configuration file.

6. Run the application

```bash
python home.py
```

## Applications

* Smart Classrooms
* Digital Teaching
* Interactive Learning
* Educational Demonstrations
* AI-Assisted Learning Environments

## Future Improvements

* Voice Commands
* Multi-User Support
* Cloud-Based History Storage
* Advanced Gesture Controls
* AI-Powered Lesson Assistance

## Author

**Divyanka Srivastava**

B.Tech Computer Science Engineering
Jaipur National University

## License

This project is developed for educational and learning purposes.
