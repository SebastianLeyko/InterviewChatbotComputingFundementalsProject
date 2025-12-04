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

# ---------- parse from text (PDF) ----------
def parse_questions_from_text(text: str):
    """
    Parse text in the 'QID / TYPE / QUESTION / OPTIONS / ANSWER / KEYWORDS' format
    into a list of question dicts our quiz can use directly.

    Every line starting with 'QID:' begins a new question block.
    '---' lines are ignored.
    """
    def process_block(lines):
        if not lines:
            return None

        qid = None
        qtype = None
        prompt = None
        options = []
        answer = None
        keywords = []

        for line in lines:
            up = line.upper()
            if up.startswith("QID:"):
                qid = line.split(":", 1)[1].strip()
            elif up.startswith("TYPE:"):
                qtype = line.split(":", 1)[1].strip().lower()
            elif up.startswith("QUESTION:"):
                prompt = line.split(":", 1)[1].strip()
            elif up.startswith("OPTIONS:"):
                raw = line.split(":", 1)[1]
                options = [o.strip() for o in raw.split(";") if o.strip()]
            elif up.startswith("ANSWER:"):
                answer = line.split(":", 1)[1].strip()
            elif up.startswith("KEYWORDS:"):
                raw = line.split(":", 1)[1]
                keywords = [k.strip() for k in raw.split(";") if k.strip()]

        if not (qid and qtype and prompt):
            return None  # malformed, skip

        q = {
            "id": qid,
            "type": qtype,
            "prompt": prompt,
        }

        if qtype == "tf":
            q["answer"] = (answer or "").lower().startswith("t")
        elif qtype == "mcq":
            q["options"] = options
            if answer:
                # if answer is a letter, convert to option text
                if len(answer) == 1 and answer.upper() in "ABCD":
                    idx = "ABCD".index(answer.upper())
                    if 0 <= idx < len(options):
                        q["answer"] = options[idx]
                    else:
                        q["answer"] = answer
                else:
                    q["answer"] = answer
        elif qtype == "frq":
            if keywords:
                q["keywords"] = keywords
            elif answer:
                q["keywords"] = [answer]

        return q

    questions = []
    current_lines = []

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line == "---":
            continue  # ignore blanks / separators

        if line.upper().startswith("QID:"):
            # new question starts; process previous one
            q = process_block(current_lines)
            if q:
                questions.append(q)
            current_lines = [line]
        else:
            current_lines.append(line)

    # last block
    q = process_block(current_lines)
    if q:
        questions.append(q)

    return questions

def overwrite_question_bank(new_questions):
    """
    Save parsed questions into question_bank.json (replacing existing).
    """
    with open(QUESTION_BANK_PATH, "w", encoding="utf-8") as f:
        json.dump(new_questions, f, indent=2)

def parse_rubric_from_text(text: str):
    """
    Parse the rubric text with [TF] / [MCQ] / [FRQ] sections.
    """
    current_section = None
    rubric = {
        "tf": {"criteria": {}, "feedback": {}},
        "mcq": {"criteria": {}, "feedback": {}},
        "frq": {"criteria": {}, "feedback": {}},
    }

    def map_section(name):
        name = name.lower()
        if "tf" in name:
            return "tf"
        if "mcq" in name:
            return "mcq"
        if "frq" in name:
            return "frq"
        return None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith("[") and line.endswith("]"):
            sec = map_section(line[1:-1])
            current_section = sec
            continue

        if not current_section:
            continue

        upper = line.upper()
        if upper.startswith("CRITERIA:"):
            _, rest = line.split(":", 1)
            parts = [p.strip() for p in rest.split("|")]
            if len(parts) >= 3:
                name, max_score, desc = parts[0], parts[1], " | ".join(parts[2:])
                try:
                    max_score = float(max_score)
                except ValueError:
                    max_score = 1.0
                rubric[current_section]["criteria"][name] = {
                    "description": desc,
                    "max_score": max_score,
                }
        elif upper.startswith("FEEDBACK:"):
            _, rest = line.split(":", 1)
            parts = [p.strip() for p in rest.split("|")]
            if len(parts) >= 2:
                key, text_fb = parts[0], " | ".join(parts[1:])
                rubric[current_section]["feedback"][key] = text_fb

    return rubric

def overwrite_rubric(new_rubric):
    with open(RUBRIC_PATH, "w", encoding="utf-8") as f:
        json.dump(new_rubric, f, indent=2)

def sanitize_for_client(qs):
    out = []
    for q in qs:
        filtered = {k: v for k, v in q.items() if k not in ("answer",)}
        out.append(filtered)
    return out

# ---------- grading ----------
def _grade_tf(q, resp, rubric):
    correct_val = resp
    if not isinstance(resp, bool):
        correct_val = str(resp).lower() in ("true", "t", "1")
    is_right = (correct_val == q["answer"])
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
        t_val = item.get("time_ms", 0)
        try:
            t_ms = int(t_val)
        except (TypeError, ValueError):
            t_ms = 0

        q = qmap.get(qid)
        if not q:
            continue

        if q["type"] == "tf":
            s, m, extra = _grade_tf(q, resp, rubric)
        elif q["type"] == "mcq":
            s, m, extra = _grade_mcq(q, resp, rubric)
        else:
            s, m, extra = _grade_frq(q, resp, rubric)

        per.append({
            "id": qid,
            "type": q["type"],
            "earned": s,
            "max": m,
            "time_ms": t_ms,
            "time_seconds": round(t_ms / 1000.0, 2),
            **extra,
        })
        total += s
        max_total += m
        time_sum += t_ms

    return {
        "score_total": total,
        "score_max": max_total,
        "per_question": per,
        "time_summary_ms": time_sum,
        "time_summary_seconds": round(time_sum / 1000.0, 2),
    }

