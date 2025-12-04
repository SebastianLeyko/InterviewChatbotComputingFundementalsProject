console.log("app.js loaded");

let quizId = null;
let timers = {}; // start times per question

function renderQuestion(q) {
  const wrap = document.createElement("div");
  wrap.className = "row";
  wrap.dataset.qid = q.id;

  const title = document.createElement("p");
  title.textContent = q.prompt;
  wrap.appendChild(title);

  // ----- show stats under the question -----
  if (q.stats) {
    const statsP = document.createElement("p");
    statsP.className = "stats";

    const seen = q.stats.seen || 0;
    const correct = q.stats.correct || 0;

    if (!seen) {
      statsP.textContent = "This is a new question (no history yet).";
    } else {
      let rate = q.stats.correct_rate;
      if (rate == null && seen > 0) {
        rate = correct / seen;
      }
      const pct = Math.round(rate * 100);
      statsP.textContent =
        `Class performance: ${correct}/${seen} correct (${pct}%).`;
    }

    wrap.appendChild(statsP);
  }

  // ----- input controls -----
  let inputArea;

  if (q.type === "tf") {
    inputArea = document.createElement("div");
    ["True", "False"].forEach(val => {
      const id = `${q.id}-${val}`;
      const lbl = document.createElement("label");
      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = q.id;
      radio.value = (val === "True");
      radio.id = id;
      radio.onchange = () => {
        if (!timers[q.id]) timers[q.id] = performance.now();
      };
      lbl.htmlFor = id;
      lbl.textContent = " " + val + " ";
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
      radio.onchange = () => {
        if (!timers[q.id]) timers[q.id] = performance.now();
      };
      lbl.htmlFor = id;
      lbl.textContent = " " + opt + " ";
      inputArea.appendChild(radio);
      inputArea.appendChild(lbl);
    });
  } else {
    // FRQ: textarea only, no per-question keywords shown
    const ta = document.createElement("textarea");
    ta.rows = 3;
    ta.oninput = () => {
      if (!timers[q.id]) timers[q.id] = performance.now();
    };
    inputArea = ta;
  }

  wrap.appendChild(inputArea);
  return wrap;
}

// ----- helper: update keyword bank at top -----
// Show a single bank of all FRQ keywords, NOT tied to specific questions
function updateKeywordBank(questions) {
  const box = document.getElementById("keywordsContent");
  if (!box) return;

  // collect keywords from all FRQs in this quiz
  const allKeywords = [];
  questions.forEach(q => {
    if (q.type === "frq" && Array.isArray(q.keywords)) {
      q.keywords.forEach(k => {
        if (k && typeof k === "string") {
          allKeywords.push(k.trim());
        }
      });
    }
  });

  if (allKeywords.length === 0) {
    box.textContent = "No free-response questions in this quiz.";
    return;
  }

  // deduplicate and sort
  const unique = Array.from(new Set(allKeywords)).sort((a, b) =>
    a.toLowerCase().localeCompare(b.toLowerCase())
  );

  // display as a single bank, no question IDs
  box.innerHTML = `<p>${unique.join(", ")}</p>`;
}

// ----- helper: nice results rendering -----
function renderResults(result) {
  const container = document.getElementById("results");
  if (!container) return;

  if (result.error) {
    container.textContent = "Error: " + result.error;
    return;
  }

  const total = result.score_total ?? 0;
  const max = result.score_max ?? 0;
  const timeSec = result.time_summary_seconds ?? 0;
  const per = Array.isArray(result.per_question) ? result.per_question : [];

  let html = "";

  html += `<strong>Score:</strong> ${total} / ${max}<br>`;
  html += `<strong>Total time:</strong> ${timeSec} seconds<br>`;

  if (per.length > 0) {
    html += `
      <table class="results-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Q ID</th>
            <th>Type</th>
            <th>Score</th>
            <th>Time (s)</th>
            <th>Feedback</th>
          </tr>
        </thead>
        <tbody>
    `;

    per.forEach((pq, idx) => {
      const fullCredit = pq.max > 0 && Math.abs(pq.earned - pq.max) < 1e-6;
      const rowClass = fullCredit
        ? "results-row-correct"
        : "results-row-incorrect";

      const timeSeconds = pq.time_seconds ?? Math.round((pq.time_ms || 0) / 100) / 10;
      const feedback = pq.feedback ?? "";

      html += `
        <tr class="${rowClass}">
          <td>${idx + 1}</td>
          <td>${pq.id}</td>
          <td>${pq.type}</td>
          <td>${pq.earned} / ${pq.max}</td>
          <td>${timeSeconds}</td>
          <td>${feedback}</td>
        </tr>
      `;
    });

    html += `</tbody></table>`;
  }

  // Optional: raw JSON in a collapsible section
  html += `
    <details>
      <summary>Raw JSON result</summary>
      <pre>${JSON.stringify(result, null, 2)}</pre>
    </details>
  `;

  container.innerHTML = html;
}

// ----- start quiz -----
document.getElementById("startBtn").onclick = async () => {
  const res = await fetch("/quiz");
  const data = await res.json();
  quizId = data.quiz_id;

  const quizDiv = document.getElementById("quiz");
  quizDiv.innerHTML = "";
  timers = {};

  // render questions
  data.questions.forEach(q => quizDiv.appendChild(renderQuestion(q)));

  // update keyword bank at top (global, anonymous keywords)
  updateKeywordBank(data.questions);

  document.getElementById("submitBtn").disabled = false;
  document.getElementById("results").textContent = "";
};

// ----- submit answers -----
document.getElementById("submitBtn").onclick = async () => {
  const quizDiv = document.getElementById("quiz");
  const blocks = Array.from(quizDiv.children);
  const now = performance.now();

  const answers = blocks.map(block => {
    const qid = block.dataset.qid;
    const radios = block.querySelectorAll('input[type="radio"]');
    let response = null;

    if (radios.length) {
      const checked = Array.from(radios).find(r => r.checked);
      if (checked) {
        if (checked.value === "true") response = true;
        else if (checked.value === "false") response = false;
        else response = checked.value;
      }
    } else {
      const ta = block.querySelector("textarea");
      response = ta ? ta.value : null;
    }

    const start = timers[qid] || now;
    const time_ms = Math.max(0, Math.round(now - start));

    return { id: qid, response, time_ms };
  });

  const res = await fetch("/grade", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ quiz_id: quizId, answers })
  });

  const result = await res.json();
  renderResults(result);
};

