console.log("app.js loaded");

let quizId = null;
let timers = {};

function renderQuestion(q) {
  const wrap = document.createElement("div");
  wrap.className = "row";
  wrap.dataset.qid = q.id;

  const title = document.createElement("p");
  title.textContent = q.prompt;
  wrap.appendChild(title);

  let inputArea;
  if (q.type === "tf") {
    inputArea = document.createElement("div");
    ["True", "False"].forEach(val => {
      const id = `${q.id}-${val}`;
      const lbl = document.createElement("label");
      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = q.id;
      // store strings to avoid edge cases when reading .value
      radio.value = val === "True" ? "true" : "false";
      radio.id = id;
      radio.onchange = () => { if (!timers[q.id]) timers[q.id] = performance.now(); };
      lbl.htmlFor = id;
      lbl.textContent = val;
      inputArea.appendChild(radio);
      inputArea.appendChild(lbl);
    });
  } else if (q.type === "mcq") {
    inputArea = document.createElement("div");
    q.options.forEach((opt, i) => {
      const id = `${q.id}-${i}`;
      const lbl = document.createElement("label");
      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = q.id;
      radio.value = opt;
      radio.id = id;
      radio.onchange = () => { if (!timers[q.id]) timers[q.id] = performance.now(); };
      lbl.htmlFor = id;
      lbl.textContent = opt;
      inputArea.appendChild(radio);
      inputArea.appendChild(lbl);
    });
  } else {
    const ta = document.createElement("textarea");
    ta.rows = 3;
    ta.oninput = () => { if (!timers[q.id]) timers[q.id] = performance.now(); };
    inputArea = ta;
  }

  wrap.appendChild(inputArea);
  return wrap;
}

function renderKeywordsBannerFromQuestions(questions) {
  // Gather unique keywords from FRQs
  const keywordSet = new Set();
  questions.forEach(q => {
    if (Array.isArray(q.keywords)) {
      q.keywords.forEach(k => keywordSet.add(String(k).toLowerCase()));
    }
  });

  // Remove any existing banner to avoid duplicates on restart
  document.getElementById("keywords")?.remove();

  const keywordsDiv = document.createElement("div");
  keywordsDiv.id = "keywords";
  keywordsDiv.style.background = "#eef6ff";
  keywordsDiv.style.border = "1px solid #c9e1ff";
  keywordsDiv.style.borderRadius = "8px";
  keywordsDiv.style.padding = "10px";
  keywordsDiv.style.marginBottom = "16px";
  keywordsDiv.style.fontSize = "15px";

  const list = [...keywordSet];
  const content = list.length
    ? `<b>All Keywords in this Quiz:</b><br>${list.join(", ")}`
    : `<b>All Keywords in this Quiz:</b><br><i>No FRQ keywords in this set.</i>`;

  keywordsDiv.innerHTML = content;

  const appDiv = document.getElementById("app");
  const quizDiv = document.getElementById("quiz");
  appDiv.insertBefore(keywordsDiv, quizDiv);
}

async function startQuiz() {
  console.log("Start clicked");
  const res = await fetch("/quiz");
  const data = await res.json();
  quizId = data.quiz_id;

  const quizDiv = document.getElementById("quiz");
  quizDiv.innerHTML = "";
  timers = {};

  // Render the keyword banner first
  // (works whether server sends .keywords or we derive from questions)
  if (Array.isArray(data.keywords)) {
    // If you added keywords on the server, prefer that list
    document.getElementById("keywords")?.remove();
    const keywordsDiv = document.createElement("div");
    keywordsDiv.id = "keywords";
    keywordsDiv.style.background = "#eef6ff";
    keywordsDiv.style.border = "1px solid #c9e1ff";
    keywordsDiv.style.borderRadius = "8px";
    keywordsDiv.style.padding = "10px";
    keywordsDiv.style.marginBottom = "16px";
    keywordsDiv.style.fontSize = "15px";
    const list = data.keywords;
    keywordsDiv.innerHTML = list.length
      ? `<b>All Keywords in this Quiz:</b><br>${list.join(", ")}`
      : `<b>All Keywords in this Quiz:</b><br><i>No FRQ keywords in this set.</i>`;
    document.getElementById("app").insertBefore(keywordsDiv, quizDiv);
  } else {
    // Otherwise derive from the questions we already have
    renderKeywordsBannerFromQuestions(data.questions);
  }

  // Render questions
  data.questions.forEach(q => quizDiv.appendChild(renderQuestion(q)));
  document.getElementById("submitBtn").disabled = false;
}

async function submitAnswers() {
  console.log("Submit clicked");

  if (!quizId) {
    alert("No quiz loaded. Click Start Quiz again.");
    return;
  }

  const rows = Array.from(document.querySelectorAll("#quiz [data-qid]"));
  if (!rows.length) {
    alert("No questions found. Click Start Quiz again.");
    return;
  }

  const now = performance.now();
  const answers = rows.map(row => {
    const qid = row.dataset.qid;
    const radios = row.querySelectorAll('input[type="radio"]');
    let response = null;

    if (radios.length) {
      const checked = Array.from(radios).find(r => r.checked);
      response = checked
        ? (checked.value === "true" ? true
           : checked.value === "false" ? false
           : checked.value)
        : null;
    } else {
      const ta = row.querySelector("textarea");
      response = ta ? ta.value : null;
    }

    const start = timers[qid] || now;
    const time_ms = Math.max(0, Math.round(now - start));
    return { id: qid, response, time_ms };
  });

  try {
    const res = await fetch("/grade", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ quiz_id: quizId, answers })
    });

    if (!res.ok) {
      const text = await res.text();
      document.getElementById("results").textContent =
        `Submit failed (${res.status}). If you edited Python files, click Start Quiz again.\n` + text;
      return;
    }

    const result = await res.json();
    // Show a quick score summary, then details
    const summary = `Score: ${result.score_total}/${result.score_max}\nTime: ${result.time_summary_ms} ms\n\n`;
    document.getElementById("results").textContent =
      summary + JSON.stringify(result.per_question, null, 2);
  } catch (err) {
    console.error(err);
    document.getElementById("results").textContent = "Submit errored: " + err;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  console.log("handlers attached");
  document.getElementById("startBtn")?.addEventListener("click", startQuiz);
  document.getElementById("submitBtn")?.addEventListener("click", submitAnswers);
});
