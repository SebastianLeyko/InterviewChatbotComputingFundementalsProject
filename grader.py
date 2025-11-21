# Will hold: load_questions, load_rubric, sanitize_questions, grade_submission
# Leaving empty in Phase 1.
# grader.py
# grader.py
import json, random, re
from pathlib import Path

DATA_DIR = Path(__file__).parent
QUESTION_BANK_PATH = DATA_DIR / "question_bank.json"
RUBRIC_PATH = DATA_DIR / "rubric.json"

# ---------- loaders ----------
def _normalize_option(opt: str) -> str:
    # strips leading "A) " etc.
    return re.sub(r"^[A-Da-d]\)\s*", "", opt).strip()

def load_questions():
    with open(QUESTION_BANK_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    norm = []
    for q in raw:
        qq = dict(q)
        # ids as strings
        qq["id"] = str(qq["id"])
        # question -> prompt
        if "prompt" not in qq and "question" in qq:
            qq["prompt"] = qq["question"]
        # mcq cleanup
        if qq.get("type") == "mcq":
            if "options" in qq:
                qq["options"] = [_normalize_option(o) for o in qq["options"]]
            ans = qq.get("answer")
            # If answer is a letter like "B", convert to the option text
            if isinstance(ans, str) and len(ans) == 1 and ans.upper() in "ABCD":
                idx = "ABCD".index(ans.upper())
                qq["answer"] = qq["options"][idx]
        # frq: convert a lone answer into keywords list
        if qq.get("type") == "frq" and "keywords" not in qq and "answer" in qq:
            qq["keywords"] = [str(qq["answer"]).strip()]
        norm.append(qq)
    return norm

def load_rubric():
    with open(RUBRIC_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def pick_questions(all_qs, n):
    return random.sample(all_qs, min(n, len(all_qs)))

def sanitize_for_client(qs):
    out = []
    for q in qs:
        filtered = {k: v for k, v in q.items() if k not in ("answer",)}
        out.append(filtered)
    return out

# ---------- grading ----------
def _grade_tf(q, resp, rubric):
    correct = str(resp).lower() in ("true", "t", "1") if not isinstance(resp, bool) else resp
    is_right = (correct == q["answer"])
    score = 1 if is_right else 0
    fb = rubric["tf"]["feedback"]["1" if is_right else "0"]
    return score, 1, {"correct": is_right, "feedback": fb}

def _grade_mcq(q, resp, rubric):
    resp_norm = str(resp).strip()
    # Allow "A/B/C/D" too
    if len(resp_norm) == 1 and resp_norm.upper() in "ABCD":
        idx = "ABCD".index(resp_norm.upper())
        resp_norm = q["options"][idx]
    is_right = (resp_norm == q["answer"])
    score = 1 if is_right else 0
    fb = rubric["mcq"]["feedback"]["1" if is_right else "0"]
    return score, 1, {"correct": is_right, "feedback": fb}

def _grade_frq(q, resp, rubric):
    text = str(resp).lower()
    keys = [k.lower() for k in q.get("keywords", [])]
    hits = sum(1 for k in keys if k in text)
    total = max(1, len(keys))
    ratio = hits / total
    if ratio >= 0.75:
        score, level = 1.0, "high"
    elif ratio >= 0.5:
        score, level = 0.5, "medium"
    else:
        score, level = 0.0, "low"
    fb = rubric["frq"]["feedback"][level]
    return score, 1, {"keywords_hit": hits, "keywords_total": total, "feedback": fb}

def grade_submission(all_qs, rubric, answers):
    # Map id -> question
    qmap = {q["id"]: q for q in all_qs}
    per = []
    total = 0.0
    max_total = 0.0
    time_sum = 0

    for item in answers:
        qid = str(item.get("id"))
        resp = item.get("response")
        t_ms = int(item.get("time_ms", 0)) if str(item.get("time_ms", "0")).isdigit() else 0

        q = qmap.get(qid)
        if not q:
            continue

        if q["type"] == "tf":
            s, m, extra = _grade_tf(q, resp, rubric)
        elif q["type"] == "mcq":
            s, m, extra = _grade_mcq(q, resp, rubric)
        else:
            s, m, extra = _grade_frq(q, resp, rubric)

        per.append({"id": qid, "type": q["type"], "earned": s, "max": m, "time_ms": t_ms, **extra})
        total += s
        max_total += m
        time_sum += t_ms

    return {"score_total": total, "score_max": max_total, "per_question": per, "time_summary_ms": time_sum}
