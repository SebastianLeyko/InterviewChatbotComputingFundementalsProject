from flask import Flask, render_template, jsonify, request
import uuid
from grader import (
    load_questions,
    load_rubric,
    pick_questions,
    sanitize_for_client,
    grade_submission,
)

app = Flask(__name__)

# In-memory quiz store for this session
ACTIVE_QUIZZES = {}

@app.route("/")
def home():
    # for quick test, you can temporarily return plain text:
    # return "Hello from Flask"
    return render_template("index.html")

@app.route("/quiz")
def get_quiz():
    all_qs = load_questions()
    quiz_qs = pick_questions(all_qs, 10)
    quiz_id = str(uuid.uuid4())
    ACTIVE_QUIZZES[quiz_id] = [q["id"] for q in quiz_qs]
    return jsonify({"quiz_id": quiz_id, "questions": sanitize_for_client(quiz_qs)})

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
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
