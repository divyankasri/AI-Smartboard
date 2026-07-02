import google.generativeai as genai
import time

from history_service import save_history

# ======================================
# GEMINI CONFIGURATION
# ======================================

API_KEY = "YOUR_API_KEY_HERE"

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

# ======================================
# ASK GEMINI
# ======================================

def ask_gemini(question):

    start_time = time.time()

    prompt = f"""
You are an educational AI assistant.

Rules:
- Explain in simple English.
- Give direct answers.
- Do not use markdown.
- Keep answers clear and concise.

Question:

{question}
"""

    try:

        response = model.generate_content(prompt)

        answer = response.text.strip()

        response_time = round(time.time() - start_time, 2)

        save_history(question, answer)

        return answer, response_time

    except Exception as e:

        return f"Error : {str(e)}", 0
    