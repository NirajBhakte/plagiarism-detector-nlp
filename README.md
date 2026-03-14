# plagiarism-detector-nlp

A semantic plagiarism detection tool built with transformer-based sentence embeddings to detect copied, paraphrased, and original academic content using cosine similarity and NLP preprocessing techniques.

## Features

- Detects **Copied**, **Paraphrased**, and **Original** sentences
- Uses **Sentence Transformers (`all-mpnet-base-v2`)** for semantic embeddings
- Cosine similarity based comparison
- Supports multiple reference documents
- Generates structured **CSV reports**
- Includes negation-aware logic to reduce false positives
- POST /api/detect-file : Upload PDF to run plagiarism detection

## Tech Stack

- Python
- Sentence Transformers
- PyTorch
- NLTK
- Scikit-learn
- NumPy
- Pandas

## Project Structure

```text
plagiarism-detector-nlp
│
├── src/
│   ├── detector.py
│   ├── embedder.py
│   ├── preprocess.py
│   └── similarity.py
│
├── data/
│   ├── reference_texts/
│   └── student_inputs/
│
├── frontend/
├── reports/
│   └── results.csv
│
├── requirements.txt
└── README.md