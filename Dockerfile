# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Builder — install deps & pre-download ML models
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

# System deps needed to compile/install some Python packages (e.g. cffi, pypdfium2)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libssl-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only the requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install all Python dependencies into a prefix so they can be copied to final stage
RUN pip install --upgrade pip && \
    pip install --prefix=/install -r requirements.txt

# Pre-download NLTK data into a location accessible at runtime
ENV NLTK_DATA=/nltk_data
RUN python -c "import sys; sys.path.insert(0, '/install/lib/python3.11/site-packages'); \
    import nltk; \
    nltk.download('punkt',     download_dir='/nltk_data'); \
    nltk.download('punkt_tab', download_dir='/nltk_data')"

# Pre-download the SBERT model (all-mpnet-base-v2) so the container starts instantly
ENV SENTENCE_TRANSFORMERS_HOME=/sbert_cache
RUN python -c "import sys; sys.path.insert(0, '/install/lib/python3.11/site-packages'); \
    from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('all-mpnet-base-v2')"


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Runtime — lean final image
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Minimal runtime system libraries (pypdfium2 needs libgomp at runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy pre-downloaded NLTK data and SBERT model cache
COPY --from=builder /nltk_data /nltk_data
COPY --from=builder /sbert_cache /sbert_cache

# Copy application source code
COPY src/       ./src/
COPY frontend/  ./frontend/
COPY data/      ./data/

# Optional: copy database / embeddings directories if they exist and are needed
# (comment out if you generate these at runtime instead)
COPY database/   ./database/
COPY embeddings/ ./embeddings/

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NLTK_DATA=/nltk_data \
    SENTENCE_TRANSFORMERS_HOME=/sbert_cache \
    PORT=8000

# Supabase / app config — override these at `docker run` time via --env or --env-file
# ENV SUPABASE_URL=
# ENV SUPABASE_SERVICE_ROLE_KEY=
# ENV SAVE_SCANS_TO_SUPABASE=true

EXPOSE 8000

# Health-check: poll the /health endpoint every 60 s (model may take a few minutes to load)
HEALTHCHECK --interval=60s --timeout=10s --start-period=120s --retries=5 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start the FastAPI app via uvicorn
CMD ["sh", "-c", "python -m uvicorn src.api:app --host 0.0.0.0 --port ${PORT}"]
