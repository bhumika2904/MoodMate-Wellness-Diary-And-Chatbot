from flask import Flask, render_template, request, jsonify
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer
import logging
import os
import sqlite3
from datetime import datetime

# --- Flask App Setup ---
app = Flask(__name__)

# --- Logging ---
logging.basicConfig(level=logging.CRITICAL)  # hide ChatterBot logs

# --- Ensure spaCy model is downloaded ---
try:
    import spacy
    spacy.load("en_core_web_sm")
except:
    os.system("python -m spacy download en_core_web_sm")

# --- ChatterBot Setup ---
chatbot = ChatBot("MentalHealthBot", read_only=True)

# Train with general English
corpus_trainer = ChatterBotCorpusTrainer(chatbot)
corpus_trainer.train("chatterbot.corpus.english")

# Train with mental health replies
custom_trainer = ListTrainer(chatbot)
custom_trainer.train([
    "I feel anxious",
    "It's okay to feel anxious sometimes. Try taking deep breaths. I'm here for you.",

    "I'm feeling sad",
    "I'm really sorry you're feeling this way. Do you want to talk about what's bothering you?",

    "I'm stressed about studies",
    "That’s completely understandable. Break your work into smaller tasks and don’t forget to take breaks.",

    "I feel alone",
    "You are not alone. I’m here for you anytime you want to talk.",

    "What should I do when I feel overwhelmed?",
    "Try grounding techniques like 5-4-3-2-1 or talking to someone you trust. You’re doing your best.",

    "How are you?",
    "I'm just a bot, but I'm here to support you!",

    "Thank you",
    "You're welcome. I'm always here to listen.",
])

# --- Database Setup ---
DB_PATH = "journal.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )''')
        conn.commit()

init_db()

# --- Routes ---

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/chatbot")
def chatbot_page():
    return render_template("chatbot.html")

@app.route("/journal")
def journal_page():
    return render_template("journal.html")

@app.route("/get_response", methods=["POST"])
def get_response():
    try:
        user_input = request.form.get("message", "").strip()
        if not user_input:
            return jsonify({"reply": "Please say something so I can respond."})
        response = chatbot.get_response(user_input)
        return jsonify({"reply": str(response)})
    except Exception as e:
        print("🔥 Chatbot error:", e)
        return jsonify({"reply": "Oops! Something went wrong. Try again later."})

@app.route("/save_journal", methods=["POST"])
def save_journal():
    try:
        entry = request.form.get("entry", "").strip()
        mood = request.form.get("mood", "🙂")
        if not entry:
            return jsonify({"message": "Journal entry is empty."})
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO journal (entry, mood, timestamp) VALUES (?, ?, ?)",
                      (entry, mood, datetime.now().isoformat()))
            conn.commit()
        return jsonify({"message": "Journal saved successfully!"})
    except Exception as e:
        print("🔥 Journal error:", e)
        return jsonify({"message": "Failed to save journal."})



@app.route("/journal/entries")
def view_entries():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT entry, mood, timestamp FROM journal ORDER BY timestamp DESC")
        entries = c.fetchall()
    return render_template("view_entries.html", entries=entries)


@app.route("/mood-stats")
def mood_stats():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Pie chart: count of each mood
        c.execute("SELECT mood, COUNT(*) FROM journal GROUP BY mood")
        mood_counts = c.fetchall()

        # Line chart: mood count by date
        c.execute("SELECT DATE(timestamp), mood, COUNT(*) FROM journal GROUP BY DATE(timestamp), mood")
        mood_by_day = c.fetchall()

    return render_template("mood_stats.html", mood_counts=mood_counts, mood_by_day=mood_by_day)


@app.route("/breathe")
def breathe():
    return render_template("breathe.html")




# --- Run ---
if __name__ == "__main__":
    app.run(debug=True)
