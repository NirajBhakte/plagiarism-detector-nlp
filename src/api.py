# src/api.py

import os
import io
import threading
from typing import Any, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Query

load_dotenv()
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from . import scan_repository
from .supabase_client import is_supabase_configured


# ─────────────────────── Schemas ─────────────────────────── #

class DetectRequest(BaseModel):
    text: str


class DetectResultItem(BaseModel):
    student_sentence : str
    matched_source   : str
    source_file      : str
    similarity_score : float
    category         : str


class DetectResponse(BaseModel):
    total_sentences       : int
    plagiarized_sentences : int
    plagiarism_percent    : float
    source_breakdown      : dict[str, float]
    results               : list[DetectResultItem]


class ReportRequest(BaseModel):
    total_sentences       : int
    plagiarized_sentences : int
    plagiarism_percent    : float
    source_breakdown      : dict[str, float] = {}
    results               : list[DetectResultItem]


class SaveScanRequest(BaseModel):
    total_sentences       : int
    plagiarized_sentences : int
    plagiarism_percent    : float
    source_breakdown      : dict[str, float] = {}
    results               : list[DetectResultItem]
    input_type            : str = "text"
    label                 : Optional[str] = None


class ScanSummaryResponse(BaseModel):
    id                    : str
    label                 : Optional[str] = None
    input_type            : str
    total_sentences       : int
    plagiarized_sentences : int
    plagiarism_percent    : float
    source_breakdown      : dict
    created_at            : str


# ─────────────────────── Detector (background load) ──────── #
# Render scans $PORT before heavy imports finish. Do NOT import torch/detector
# at module level — only inside the background worker after uvicorn has bound.

_detector: Any = None
_detector_lock = threading.Lock()
_loading = False
_load_error: Optional[str] = None
_loader_started = False


def get_detector() -> Any:
    if _load_error:
        raise HTTPException(
            status_code=503,
            detail=f"Model failed to load: {_load_error}",
        )
    if _detector is None:
        raise HTTPException(
            status_code=503,
            detail="Server is still loading the model. Wait 3–5 minutes after deploy, then try again.",
        )
    return _detector


def _load_detector_worker() -> None:
    global _detector, _load_error, _loading
    try:
        from .detector import PlagiarismDetector

        print("Loading SBERT model and reference database...")
        detector = PlagiarismDetector()
        detector.load_database()
        with _detector_lock:
            _detector = detector
        print("Detector ready.")
    except Exception as exc:
        _load_error = str(exc)
        print(f"Detector load failed: {exc}")
    finally:
        _loading = False


def _start_model_loader() -> None:
    global _loader_started, _loading
    if _loader_started:
        return
    _loader_started = True
    _loading = True
    threading.Thread(target=_load_detector_worker, daemon=True).start()


# ─────────────────────── App ─────────────────────────────── #

app = FastAPI(
    title   = "Plagiarism Detector API",
    version = "1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ─────────────────────── Helper ──────────────────────────── #

def _build_response(summary: dict) -> DetectResponse:
    results = [
        DetectResultItem(
            student_sentence = item["Student Sentence"],
            matched_source   = item["Matched Source"],
            source_file      = item.get("Source File", "Unknown"),
            similarity_score = item["Similarity Score"],
            category         = item["Category"],
        )
        for item in summary["results"]
    ]
    return DetectResponse(
        total_sentences       = summary["total_sentences"],
        plagiarized_sentences = summary["plagiarized_sentences"],
        plagiarism_percent    = summary["plagiarism_percent"],
        source_breakdown      = summary.get("source_breakdown", {}),
        results               = results,
    )


def _should_auto_save_scans() -> bool:
    if not is_supabase_configured():
        return False
    return os.getenv("SAVE_SCANS_TO_SUPABASE", "true").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def _maybe_persist_scan(summary: dict, input_type: str) -> Optional[str]:
    if not _should_auto_save_scans():
        return None
    try:
        row = scan_repository.save_scan(summary, input_type)
        return row.get("id")
    except Exception as exc:
        print(f"Warning: could not save scan to Supabase: {exc}")
        return None


def _summary_dict_from_response(response: DetectResponse) -> dict:
    return {
        "total_sentences": response.total_sentences,
        "plagiarized_sentences": response.plagiarized_sentences,
        "plagiarism_percent": response.plagiarism_percent,
        "source_breakdown": response.source_breakdown,
        "results": [
            {
                "Student Sentence": r.student_sentence,
                "Matched Source": r.matched_source,
                "Source File": r.source_file,
                "Similarity Score": r.similarity_score,
                "Category": r.category,
            }
            for r in response.results
        ],
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_ready": _detector is not None,
        "loading": _loading,
        "error": _load_error,
    }


# ─────────────────────── Detection Endpoints ─────────────── #

@app.post("/api/detect", response_model=DetectResponse)
def detect_text(request: DetectRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    summary = get_detector().detect_from_text(request.text)
    _maybe_persist_scan(summary, "text")
    return _build_response(summary)


@app.post("/api/detect-file", response_model=DetectResponse)
async def detect_file(file: UploadFile = File(...)):
    filename = file.filename or ""
    if os.path.splitext(filename)[1].lower() not in {".pdf", ".txt"}:
        raise HTTPException(status_code=422, detail="Only .pdf or .txt files are supported.")
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    try:
        summary = get_detector().detect_from_bytes(file_bytes, filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {e}")
    _maybe_persist_scan(summary, "file")
    return _build_response(summary)


@app.post("/api/detect-with-reference", response_model=DetectResponse)
async def detect_with_reference(
    student_file    : UploadFile       = File(...),
    reference_files : List[UploadFile] = File(...),
):
    ALLOWED = {".pdf", ".txt"}
    s_ext = os.path.splitext(student_file.filename or "")[1].lower()
    if s_ext not in ALLOWED:
        raise HTTPException(status_code=422, detail=f"Unsupported student file type '{s_ext}'.")
    s_bytes = await student_file.read()
    if not s_bytes:
        raise HTTPException(status_code=400, detail="Student file is empty.")

    ref_data_list = []
    for r in reference_files:
        r_ext = os.path.splitext(r.filename or "")[1].lower()
        if r_ext not in ALLOWED:
            raise HTTPException(status_code=422, detail=f"Unsupported reference file type '{r_ext}'.")
        r_bytes = await r.read()
        if not r_bytes:
            raise HTTPException(status_code=400, detail=f"Reference file '{r.filename}' is empty.")
        ref_data_list.append((r_bytes, r.filename or "reference.txt"))

    if not ref_data_list:
        raise HTTPException(status_code=400, detail="No valid reference files provided.")

    try:
        summary = get_detector().detect_with_dynamic_references(
            student_bytes    = s_bytes,
            student_filename = student_file.filename or "student.txt",
            reference_files  = ref_data_list,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {e}")
    _maybe_persist_scan(summary, "with_reference")
    return _build_response(summary)


# ─────────────────────── Supabase scan history ─────────────── #

@app.get("/api/supabase/status")
def supabase_status():
    return {
        "configured": is_supabase_configured(),
        "auto_save": _should_auto_save_scans(),
    }


@app.post("/api/scans")
def create_scan(request: SaveScanRequest):
    if not is_supabase_configured():
        raise HTTPException(
            status_code=503,
            detail="Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.",
        )
    summary = _summary_dict_from_response(
        DetectResponse(
            total_sentences=request.total_sentences,
            plagiarized_sentences=request.plagiarized_sentences,
            plagiarism_percent=request.plagiarism_percent,
            source_breakdown=request.source_breakdown,
            results=request.results,
        )
    )
    try:
        row = scan_repository.save_scan(
            summary,
            request.input_type,
            request.label,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return row


@app.get("/api/scans", response_model=list[ScanSummaryResponse])
def list_scans(limit: int = Query(50, ge=1, le=100)):
    if not is_supabase_configured():
        raise HTTPException(status_code=503, detail="Supabase is not configured.")
    try:
        rows = scan_repository.list_scans(limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return [
        ScanSummaryResponse(
            id=row["id"],
            label=row.get("label"),
            input_type=row["input_type"],
            total_sentences=row["total_sentences"],
            plagiarized_sentences=row["plagiarized_sentences"],
            plagiarism_percent=row["plagiarism_percent"],
            source_breakdown=row.get("source_breakdown") or {},
            created_at=row["created_at"],
        )
        for row in rows
    ]


@app.get("/api/scans/{scan_id}")
def get_scan(scan_id: str):
    if not is_supabase_configured():
        raise HTTPException(status_code=503, detail="Supabase is not configured.")
    try:
        row = scan_repository.get_scan(scan_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if not row:
        raise HTTPException(status_code=404, detail="Scan not found.")
    return row


# ─────────────────────── Report Endpoint ─────────────────── #

@app.post("/api/report-from-result")
def report_from_result(request: ReportRequest):
    results_dicts = [
        {
            "Student Sentence" : r.student_sentence,
            "Matched Source"   : r.matched_source,
            "Source File"      : r.source_file,
            "Similarity Score" : r.similarity_score,
            "Category"         : r.category,
        }
        for r in request.results
    ]

    summary = {
        "total_sentences"      : request.total_sentences,
        "plagiarized_sentences": request.plagiarized_sentences,
        "plagiarism_percent"   : request.plagiarism_percent,
        "source_breakdown"     : request.source_breakdown,
        "results"              : results_dicts,
    }

    from .report_generator import generate_pdf_report_bytes

    pdf_bytes = generate_pdf_report_bytes(results_dicts, summary)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type = "application/pdf",
        headers    = {"Content-Disposition": 'attachment; filename="plagiarism_report.pdf"'},
    )


# ─────────────────────── Static Frontend ─────────────────── #

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

# Start ML load only after the app object exists (uvicorn binds port on import exit).
_start_model_loader()