#!/usr/bin/env bash
# build.sh — runs during Render build phase, NOT at runtime.
# Pre-downloads the SBERT model and NLTK punkt data so the server
# starts instantly without any network calls at runtime.

set -e  # exit immediately if any command fails

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Downloading NLTK punkt tokenizer..."
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

echo "==> Pre-downloading SBERT model (all-mpnet-base-v2)..."
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-mpnet-base-v2')"

echo "==> Build complete. Model cached."