import cv2
import easyocr
from textblob import TextBlob
import numpy as np

print("Loading image...")

# Load image
img = cv2.imread("board.png")

if img is None:
    print("Error: board.png not found!")
    exit()

# Convert to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Reduce noise
gray = cv2.GaussianBlur(gray, (5, 5), 0)

# Better thresholding
thresh = cv2.threshold(
    gray,
    0,
    255,
    cv2.THRESH_BINARY + cv2.THRESH_OTSU
)[1]

# Save processed image
cv2.imwrite("processed.png", thresh)

# -------------------------
# Crop only written region
# -------------------------
coords = cv2.findNonZero(255 - thresh)

if coords is not None:

    x, y, w, h = cv2.boundingRect(coords)

    padding = 20

    x = max(0, x - padding)
    y = max(0, y - padding)

    w = min(thresh.shape[1] - x, w + padding * 2)
    h = min(thresh.shape[0] - y, h + padding * 2)

    cropped = thresh[y:y+h, x:x+w]

else:
    cropped = thresh

cv2.imwrite("cropped.png", cropped)

print("Running OCR...")

# OCR
reader = easyocr.Reader(['en'])

results = reader.readtext(
    cropped,
    detail=0,
    paragraph=True
)

# Combine all text
detected_text = " ".join(results)

print("\nDetected Text:")
print(detected_text)

# -------------------------
# Spell Correction
# -------------------------
corrected_text = str(TextBlob(detected_text).correct())

print("\nCorrected Text:")
print(corrected_text)

# -------------------------
# Final Question
# -------------------------
final_question = corrected_text.strip()

print("\nFinal Question:")
print(final_question)
