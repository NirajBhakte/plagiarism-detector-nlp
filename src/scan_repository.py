# src/scan_repository.py

from typing import Any, Optional

from .supabase_client import get_supabase, is_supabase_configured

TABLE = "scans"


def _summary_to_row(summary: dict, input_type: str, label: Optional[str] = None) -> dict:
    results = summary.get("results", [])
    serialized_results = []
    for item in results:
        if isinstance(item, dict):
            serialized_results.append(
                {
                    "student_sentence": item.get("Student Sentence")
                    or item.get("student_sentence", ""),
                    "matched_source": item.get("Matched Source")
                    or item.get("matched_source", ""),
                    "source_file": item.get("Source File")
                    or item.get("source_file", "Unknown"),
                    "similarity_score": float(
                        item.get("Similarity Score")
                        or item.get("similarity_score", 0)
                    ),
                    "category": item.get("Category") or item.get("category", ""),
                }
            )
        else:
            serialized_results.append(item)

    row: dict[str, Any] = {
        "total_sentences": summary["total_sentences"],
        "plagiarized_sentences": summary["plagiarized_sentences"],
        "plagiarism_percent": float(summary["plagiarism_percent"]),
        "source_breakdown": summary.get("source_breakdown") or {},
        "results": serialized_results,
        "input_type": input_type,
    }
    if label:
        row["label"] = label
    return row


def save_scan(
    summary: dict,
    input_type: str,
    label: Optional[str] = None,
) -> dict:
    client = get_supabase()
    if client is None:
        raise RuntimeError(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
        )

    row = _summary_to_row(summary, input_type, label)
    response = client.table(TABLE).insert(row).execute()
    if not response.data:
        raise RuntimeError("Supabase insert returned no data.")
    return response.data[0]


def list_scans(limit: int = 50) -> list[dict]:
    client = get_supabase()
    if client is None:
        raise RuntimeError("Supabase is not configured.")

    limit = max(1, min(limit, 100))
    response = (
        client.table(TABLE)
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []


def get_scan(scan_id: str) -> Optional[dict]:
    client = get_supabase()
    if client is None:
        raise RuntimeError("Supabase is not configured.")

    response = (
        client.table(TABLE).select("*").eq("id", scan_id).limit(1).execute()
    )
    rows = response.data or []
    return rows[0] if rows else None
