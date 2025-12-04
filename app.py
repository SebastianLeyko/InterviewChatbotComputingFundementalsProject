from flask import Flask, render_template, jsonify, request
import uuid
import csv
import json
from datetime import datetime
from pathlib import Path
import pdfplumber

from grader import (
    load_questions,
    load_rubric,
    pick_questions,
    sanitize_for_client,
    grade_submission,
    parse_questions_from_text,
    overwrite_question_bank,
    parse_rubric_from_text,
    overwrite_rubric,
)

app = Flask(__name__)

# In-memory quiz store for this session
ACTIVE_QUIZZES = {}

# -------------------------------
# LOGGING (overall attempts)
# -------------------------------
LOG_PATH = Path(__file__).parent / "results_log.csv"

def log_result(quiz_id, result):
    exists = LOG_PATH.exists()
    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["timestamp", "quiz_id", "score_total", "score_max",
                        "time_ms", "time_seconds"])
        w.writerow([
            datetime.now().isoformat(timespec="seconds"),
            quiz_id,
            result.get("score_total"),
            result.get("score_max"),
            result.get("time_summary_ms"),
            result.get("time_summary_seconds"),
        ])

# -------------------------------
# PER-QUESTION STATS LOGGING
# -------------------------------
STATS_PATH = Path(__file__).parent / "question_stats.json"

def load_question_stats():
    if STATS_PATH.exists():
        with open(STATS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_question_stats(stats):
    with open(STATS_PATH, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

def update_question_stats(per_question_list):
    """
    per_question_list is result["per_question"] from grade_submission.
    We define 'correct' as earned == max (full credit).
    """
    stats = load_question_stats()

    for item in per_question_list:
        qid = str(item.get("id"))
        earned = float(item.get("earned", 0))
        max_score = float(item.get("max", 1))

        is_correct = (max_score > 0 and abs(earned - max_score) < 1e-6)

        qstat = stats.get(qid, {"seen": 0, "correct": 0, "incorrect": 0})
        qstat["seen"] += 1
        if is_correct:
            qstat["correct"] += 1
        else:
            qstat["incorrect"] += 1

        stats[qid] = qstat

    save_question_stats(stats)

# optional endpoint to inspect stats
@app.route("/stats")
def stats():
    return jsonify(load_question_stats())

# -------------------------------
# PDF TEXT EXTRACTION & UPLOAD
# -------------------------------
def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text

@app.route("/upload", methods=["POST"])
def upload_pdf():
    uploaded_file = request.files.get("file")
    kind = request.form.get("kind", "questions")

    if not uploaded_file:
        return jsonify({"error": "No file uploaded"}), 400

    text = extract_text_from_pdf(uploaded_file)

    try:
        if kind == "questions":
            new_questions = parse_questions_from_text(text)
            if not new_questions:
                return jsonify({"error": "No questions parsed. Check format."}), 400
            overwrite_question_bank(new_questions)
            return jsonify({
                "status": "ok",
                "type": "questions",
                "count": len(new_questions),
            })

        elif kind == "rubric":
            new_rubric = parse_rubric_from_text(text)
            overwrite_rubric(new_rubric)
            return jsonify({
                "status": "ok",
                "type": "rubric",
            })

        else:
            return jsonify({"error": f"Unknown kind: {kind}"}), 400

    except Exception as e:
        return jsonify({"error": str(e), "debug_text_snippet": text[:400]}), 500

# -------------------------------
# QUIZ ENDPOINTS
# -------------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/quiz")
def get_quiz():
    all_qs = load_questions()
    stats = load_question_stats()

    # attach stats to each question so frontend can display them
    for q in all_qs:
        qid = str(q["id"])
        s = stats.get(qid, {"seen": 0, "correct": 0, "incorrect": 0})
        seen = s.get("seen", 0)
        correct = s.get("correct", 0)
        incorrect = s.get("incorrect", 0)
        rate = (correct / seen) if seen else None
        q["stats"] = {
            "seen": seen,
            "correct": correct,
            "incorrect": incorrect,
            "correct_rate": rate,
        }

    quiz_qs = pick_questions(all_qs, 10)  # always 10 random Qs
    quiz_id = str(uuid.uuid4())

    ACTIVE_QUIZZES[quiz_id] = [q["id"] for q in quiz_qs]

    return jsonify({
        "quiz_id": quiz_id,
        "questions": sanitize_for_client(quiz_qs),
    })

@app.route("/grade", methods=["POST"])
def grade():
    payload = request.get_json(force=True)
    quiz_id = payload.get("quiz_id")
    answers = payload.get("answers", [])

    if not quiz_id or quiz_id not in ACTIVE_QUIZZES:
        return jsonify({"error": "Invalid or expired quiz_id"}), 400

    allowed_ids = set(ACTIVE_QUIZZES[quiz_id])
    all_qs = [q for q in load_questions() if q["id"] in allowed_ids]

    result = grade_submission(all_qs, load_rubric(), answers)

    # update per-question stats + overall log
    update_question_stats(result["per_question"])
    log_result(quiz_id, result)

    return jsonify(result)

# -------------------------------
# RUN APP
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)
    # for ngrok: app.run(host="0.0.0.0", port=5000, debug=True)
