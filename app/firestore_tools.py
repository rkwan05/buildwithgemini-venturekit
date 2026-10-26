"""Firestore integration tools for VentureKit.

Provides read and write access to the 'growth_plays' collection in Firestore.
"""
from typing import Any
from google.cloud import firestore

# IMPORTANT: Hardcoded GCP project ID string to ensure compatibility across
# local runs and deployed Agent Platform runtime (where google.auth.default()
# or GOOGLE_CLOUD_PROJECT can return project numbers).
PROJECT_ID = "qwiklabs-gcp-04-c8fa96deb89c"
COLLECTION_NAME = "growth_plays"

_db_client: firestore.Client | None = None


def get_db() -> firestore.Client:
    """Returns a singleton Firestore client with the hardcoded project ID."""
    global _db_client
    if _db_client is None:
        _db_client = firestore.Client(project=PROJECT_ID)
    return _db_client


def list_growth_plays(category: str = "") -> list[dict[str, Any]]:
    """Retrieves available growth plays from Firestore, optionally filtered by category.

    Args:
        category: Optional category filter (e.g. 'Pricing & Packaging', 'Revenue Expansion',
                  'Retention & Retention', 'Cost Optimization'). If empty, returns all plays.

    Returns:
        A list of growth play dictionaries containing details like id, title,
        typical_margin_lift_pct, implementation_days, difficulty, description, and kpi_impact.
    """
    db = get_db()
    col_ref = db.collection(COLLECTION_NAME)

    if category:
        docs = col_ref.where("category", "==", category).stream()
    else:
        docs = col_ref.stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        results.append(data)
    return results


def get_growth_play(play_id: str) -> dict[str, Any]:
    """Fetches full details of a specific growth play by its unique ID.

    Args:
        play_id: The document ID (e.g., 'retainer_conversion', 'vip_margin_bundle').

    Returns:
        The growth play details dictionary or an error message if not found.
    """
    db = get_db()
    doc_ref = db.collection(COLLECTION_NAME).document(play_id)
    snapshot = doc_ref.get()

    if not snapshot.exists:
        return {"error": f"Growth play with ID '{play_id}' not found."}

    data = snapshot.to_dict() or {}
    data["id"] = snapshot.id
    return data


def save_growth_play(
    play_id: str,
    title: str,
    category: str,
    typical_margin_lift_pct: float,
    implementation_days: int,
    difficulty: str,
    description: str,
    kpi_impact: str,
) -> dict[str, Any]:
    """Creates or updates a custom growth play in Firestore.

    Args:
        play_id: Unique slug identifier for the growth play (e.g., 'bogo_promo').
        title: Title of the growth play or strategy.
        category: Strategy category (e.g., 'Pricing & Packaging', 'Retention', 'Ops').
        typical_margin_lift_pct: Estimated profit margin lift percentage (e.g., 20.0).
        implementation_days: Estimated time to implement in days.
        difficulty: Complexity level ('Low', 'Medium', 'High').
        description: Summary of how to execute this growth play.
        kpi_impact: Key performance indicator target or outcome.

    Returns:
        A dictionary confirming the save status with the saved document data.
    """
    db = get_db()
    doc_ref = db.collection(COLLECTION_NAME).document(play_id)

    payload = {
        "id": play_id,
        "title": title,
        "category": category,
        "typical_margin_lift_pct": typical_margin_lift_pct,
        "implementation_days": implementation_days,
        "difficulty": difficulty,
        "description": description,
        "kpi_impact": kpi_impact,
    }

    doc_ref.set(payload, merge=True)
    return {"status": "success", "message": f"Saved growth play '{title}' ({play_id}).", "data": payload}
