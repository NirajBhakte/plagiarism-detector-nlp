const form = document.getElementById("detect-form");
const textArea = document.getElementById("text");
const runButton = document.getElementById("run-button");
const statusText = document.getElementById("status-text");
const scannerBar = document.getElementById("scanner-bar");
const wordCountEl = document.getElementById("word-count");

const dropZone = document.getElementById("file-drop-zone");
const fileInput = document.getElementById("file-upload");
const fileInfo = document.getElementById("file-info");
const fileNameSpan = document.getElementById("file-name");
const fileSizeSpan = document.getElementById("file-size");
const removeFileBtn = document.getElementById("remove-file");
const dropText = document.getElementById("drop-text");

const noResultsEl = document.getElementById("no-results");
const resultsContent = document.getElementById("results-content");
const summaryTotalEl = document.getElementById("summary-total");
const summaryPlagEl = document.getElementById("summary-plag");
const scoreRing = document.getElementById("score-ring");
const scoreText = document.getElementById("score-text");
const resultsList = document.getElementById("results-list");

let selectedFile = null;

// --- Textarea Word Count ---
textArea.addEventListener('input', () => {
    const text = textArea.value;
    const chars = text.length;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    wordCountEl.textContent = `${words} words | ${chars} chars`;
});

// --- File Upload Logic ---
dropZone.addEventListener('click', (e) => {
    if (e.target !== removeFileBtn) {
        fileInput.click();
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) handleFile(e.target.files[0]);
});

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
        handleFile(e.dataTransfer.files[0]);
    }
});

function handleFile(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    if (ext !== 'txt' && ext !== 'pdf') {
        setStatus("Only .txt and .pdf files are supported.", true);
        return;
    }
    selectedFile = file;
    fileNameSpan.textContent = file.name;
    fileSizeSpan.textContent = `(${(file.size / 1024 / 1024).toFixed(2)} MB)`;
    fileInfo.style.display = "flex";
    dropText.style.display = "none";
    // Clear textarea when file is selected
    textArea.value = "";
    textArea.dispatchEvent(new Event('input'));
    setStatus("");
}

removeFileBtn.addEventListener('click', () => {
    selectedFile = null;
    fileInput.value = "";
    fileInfo.style.display = "none";
    dropText.style.display = "block";
});

// --- UI Helpers ---
function setLoading(isLoading) {
  if (isLoading) {
    runButton.disabled = true;
    runButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="animation: spin 1s linear infinite;"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg> Analyzing...`;
    statusText.textContent = "Analyzing against reference database...";
    scannerBar.hidden = false;
  } else {
    runButton.disabled = false;
    runButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg> Check Plagiarism`;
    scannerBar.hidden = true;
  }
}

function setStatus(message, isError = false) {
  statusText.textContent = message || "";
  statusText.style.color = isError ? "var(--color-danger)" : "var(--text-muted)";
}

function getScoreColor(percent) {
    if (percent <= 20) return 'var(--color-safe)';
    if (percent <= 50) return 'var(--color-warn)';
    return 'var(--color-danger)';
}

function getScoreClass(percent) {
    if (percent <= 20) return 'safe';
    if (percent <= 50) return 'warn';
    return 'danger';
}

function updateSummary(data) {
  if (!data || data.total_sentences === 0) {
    resultsContent.hidden = true;
    noResultsEl.hidden = false;
    return;
  }

  resultsContent.hidden = false;
  noResultsEl.hidden = true;
  
  summaryTotalEl.textContent = data.total_sentences;
  summaryPlagEl.textContent = data.plagiarized_sentences;
  
  const percent = data.plagiarism_percent ?? 0;
  
  summaryPlagEl.className = `stat-value score-${getScoreClass(percent)}`;

  // Update Progress Ring
  const radius = scoreRing.r.baseVal.value;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percent / 100) * circumference;
  
  scoreRing.style.strokeDasharray = `${circumference} ${circumference}`;
  
  setTimeout(() => {
    scoreRing.style.strokeDashoffset = offset;
    scoreRing.style.stroke = getScoreColor(percent);
  }, 50);

  let start = 0;
  const duration = 1000;
  const increment = percent / (duration / 16); 
  
  if (percent === 0) {
      scoreText.textContent = `0%`;
      scoreText.style.color = getScoreColor(percent);
  } else {
      const timer = setInterval(() => {
          start += increment;
          if (start >= percent) {
              start = percent;
              clearInterval(timer);
          }
          scoreText.textContent = `${Math.round(start)}%`;
          scoreText.style.color = getScoreColor(percent);
      }, 16);
  }
}

function renderResults(results) {
  resultsList.innerHTML = "";

  if (!results || results.length === 0) return;

  results.forEach((item, index) => {
    // API previously returned fraction like 0.85, so * 100
    const score = item.similarity_score * 100;
    const scoreState = getScoreClass(score);
    const scoreColor = getScoreColor(score);
    
    const card = document.createElement("div");
    card.className = "result-card";
    card.style.borderLeftColor = scoreColor;
    card.style.animationDelay = `${index * 0.05}s`;

    card.innerHTML = `
        <div class="result-header">
            <p class="result-sentence">"${item.student_sentence}"</p>
            <span class="match-badge bg-${scoreState}">${score.toFixed(1)}%</span>
        </div>
        <div class="result-details">
            <strong>Category:</strong> ${item.category}<br>
            <strong>Matched Source:</strong> <a class="source-link" href="${item.matched_source}" target="_blank">${item.matched_source}</a>
        </div>
    `;

    card.addEventListener('click', () => {
        card.classList.toggle('expanded');
    });

    resultsList.appendChild(card);
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  
  const text = textArea.value.trim();

  if (!text && !selectedFile) {
    setStatus("Please paste text or upload a document.", true);
    return;
  }

  setLoading(true);
  setStatus("");
  
  // reset ring visual
  const radius = scoreRing.r.baseVal.value;
  scoreRing.style.strokeDashoffset = radius * 2 * Math.PI; 

  try {
    let response;

    if (selectedFile) {
        const formData = new FormData();
        formData.append("file", selectedFile);
        
        response = await fetch("/api/detect-file", {
            method: "POST",
            body: formData,
        });
    } else {
        response = await fetch("/api/detect", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ text }),
        });
    }

    if (!response.ok) {
        let errorData = await response.text();
        try {
            const json = JSON.parse(errorData);
            if (json.detail) errorData = json.detail;
        } catch(e){}
        throw new Error(errorData || `Request failed with ${response.status}`);
    }

    const data = await response.json();

    updateSummary(data);
    renderResults(data.results);
    setStatus("Detection completed successfully.");
    
    if (window.innerWidth <= 900) {
        document.getElementById("results-card").scrollIntoView({ behavior: 'smooth' });
    }

  } catch (error) {
    console.error(error);
    setStatus(`Error: ${error.message}`, true);
    updateSummary(null);
    renderResults([]);
  } finally {
    setLoading(false);
  }
});

const style = document.createElement('style');
style.innerHTML = `
@keyframes spin { 100% { transform: rotate(360deg); } }
`;
document.head.appendChild(style);
