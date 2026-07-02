import json
import os
from datetime import datetime

HISTORY_FILE = "history/history.json"


def initialize_history():

    if not os.path.exists("history"):
        os.makedirs("history")

    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as file:
            json.dump([], file, indent=4)


def save_history(question, answer):

    initialize_history()

    with open(HISTORY_FILE, "r") as file:
        data = json.load(file)

    data.append(
        {
            "time": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "question": question,
            "answer": answer
        }
    )

    with open(HISTORY_FILE, "w") as file:
        json.dump(data, file, indent=4)


def load_history():

    initialize_history()

    with open(HISTORY_FILE, "r") as file:
        return json.load(file)
    