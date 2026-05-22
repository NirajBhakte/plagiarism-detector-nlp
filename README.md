---
title: Plagiarism Detector API
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# 🛡️ AI-Powered Plagiarism Detector

A semantic plagiarism detection system that identifies **Copied**, **Paraphrased**, and **Original** content using **Sentence-BERT embeddings** and **cosine similarity**.

Unlike traditional plagiarism tools that rely only on keyword matching, this system analyzes **semantic meaning** of sentences to detect rewritten or paraphrased content.

---

## 🌐 Live Demo

| Layer | URL |
|-------|-----|
| 🖥️ Frontend (Vercel) | https://plagiarism-detector-nlp.vercel.app/ |
| ⚙️ Backend API (HuggingFace) | https://nayan2305-plagiarism-detector.hf.space |
| 📋 API Health Check | https://nayan2305-plagiarism-detector.hf.space/health |

---

## 🚀 Features

- Detects **Copied, Paraphrased, and Original** sentences
- Supports **PDF and TXT file uploads**
- **Compare against uploaded reference files** (dynamic mode)
- **Semantic similarity detection** using Sentence Transformers
- Sentence-level plagiarism analysis with **cosine similarity scoring**
- **PDF report generation** with full breakdown
- **Scan history** stored in Supabase
- Interactive **modern web interface**
- Dockerized for easy deployment

---

## 🧠 How It Works

1. Student text or document is uploaded.
2. Text is extracted and preprocessed.
3. Sentences are converted into **semantic embeddings** using **Sentence-BERT**.
4. Each sentence is compared with reference documents using **cosine similarity**.
5. Sentences are classified as:

| Category | Meaning |
|--------|--------|
| **Copied** | Nearly identical to source text |
| **Paraphrased** | Same meaning but different wording |
| **Original** | No significant similarity |

---

## 🛠️ Tech Stack

### Backend
- Python 3.11
- FastAPI
- Uvicorn
- Sentence Transformers (`all-mpnet-base-v2`)
- PyTorch
- Scikit-Learn
- NLTK
- pdfplumber (PDF parsing)
- ReportLab (PDF report generation)
- Pandas / NumPy

### Frontend
- HTML
- CSS
- JavaScript (deployed on Vercel)

### Storage & Database
- Supabase (scan history)

### DevOps
- Docker
- HuggingFace Spaces (backend)
- Vercel (frontend)

---

## 📂 Project Structure

```
plagiarism-detector-nlp
│
├── src/
│   ├── api.py                 # FastAPI app & all endpoints
│   ├── detector.py            # Core plagiarism detection logic
│   ├── embedder.py            # Sentence embedding wrapper
│   ├── preprocess.py          # Text cleaning & tokenization
│   ├── similarity.py          # Cosine similarity helpers
│   ├── report_generator.py    # PDF report generation
│   ├── scan_repository.py     # Supabase scan history CRUD
│   └── supabase_client.py     # Supabase client setup
│
├── frontend/
│   ├── index.html
│   ├── main.js
│   └── styles.css
│
├── data/
│   └── reference_texts/       # Pre-loaded reference documents
│
├── database/
│   └── migrations/
│
├── embeddings/
│   └── db_embeddings.pkl      # Pre-computed reference embeddings
│
├── Dockerfile                 # Docker image definition
├── build.sh                   # Pre-downloads model & NLTK data
├── start.sh                   # Starts uvicorn server
├── runtime.txt                # Python version (3.11)
├── requirements.txt
├── .env.example               # Environment variable template
└── README.md
```

---

## 🔑 Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Your Supabase project URL | Optional |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | Optional |
| `SAVE_SCANS_TO_SUPABASE` | Auto-save scans (`true`/`false`) | Optional |
| `PORT` | Server port (default: `8000`) | Optional |

> Supabase is optional — the detector works without it. Scan history features require it.

---

## ⚙️ Local Installation

Clone the repository:

```bash
git clone https://github.com/NirajBhakte/plagiarism-detector-nlp.git
cd plagiarism-detector-nlp
```

Create and activate virtual environment:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / Mac
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Download NLTK data:

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```

---

## ▶️ Running Locally

```bash
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

Open in browser:

```
http://127.0.0.1:8000
```

---

## 🐳 Running with Docker

Build the image:

```bash
docker build -t plagiarism-detector .
```

Run the container:

```bash
docker run -p 8000:8000 --env-file .env plagiarism-detector
```

Open in browser:

```
http://localhost:8000
```

---

## 📄 API Endpoints

### Health Check
```
GET /health
```
Returns model load status.

---

### Detect Plagiarism from Text
```
POST /api/detect
Content-Type: application/json

{ "text": "Your student text here..." }
```

---

### Detect Plagiarism from File
```
POST /api/detect-file
Content-Type: multipart/form-data

file: <.pdf or .txt file>
```

---

### Detect with Uploaded Reference Files
```
POST /api/detect-with-reference
Content-Type: multipart/form-data

student_file:    <.pdf or .txt>
reference_files: <one or more .pdf or .txt files>
```

---

### Generate PDF Report
```
POST /api/report-from-result
Content-Type: application/json

{ ...detection result JSON... }
```
Returns a downloadable PDF report.

---

### Scan History (requires Supabase)
```
GET  /api/scans          # List recent scans
GET  /api/scans/{id}     # Get a specific scan
POST /api/scans          # Save a scan manually
```

---

## 📊 Example Output

| Sentence | Score | Category |
|--------|--------|--------|
| Artificial intelligence is transforming industries. | 0.99 | Copied |
| Many organizations are adopting AI technology. | 0.82 | Paraphrased |
| Reading books improves creativity. | 0.12 | Original |

---

## 🚢 Deployment

### Backend → HuggingFace Spaces (Docker)
- SDK: Docker
- Port: `7860`
- Set secrets in HF Space Settings: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`

### Frontend → Vercel
- Deploy the `frontend/` folder
- Update `API_BASE` in `main.js` to point to your HF Space URL

---

## 👨‍💻 Contributors

- **Niraj Bhakte**
- **Nayan Dhanorkar**
- **Mitesh Wani**
- **Maithily Patle**

---

## 📌 Future Improvements

- OCR support for scanned PDFs
- Large-scale vector database integration
- Real-time plagiarism highlighting
- Multi-document batch comparison

---

## 📜 License

This project is developed for **academic and educational purposes**.
