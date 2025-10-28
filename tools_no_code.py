from typing import List, Dict, Any
from datetime import datetime, timedelta
import json
import importlib

# Safe fallback for optional LangChain tool decorator

def tool(func=None, **kwargs):  # no-op decorator if LangChain not installed
    if func is None:
        def _wrap(f):
            return f
        return _wrap
    return func

# Try langchain_core.tools first, then langchain.tools
try:
    _tools_mod = importlib.import_module("langchain_core.tools")
    tool = getattr(_tools_mod, "tool", tool)  # type: ignore
except Exception:
    try:
        _tools_mod = importlib.import_module("langchain.tools")
        tool = getattr(_tools_mod, "tool", tool)  # type: ignore
    except Exception:
        pass


@tool
def grant_search(
    mission_keywords: List[str],
    region: str,
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    Discover grant/funding opportunities aligned with mission keywords and region, returning a list of opportunities.

    Inputs:
      - mission_keywords: e.g. ["women leadership scholarships", "undergraduate education"]
      - region: e.g. "NY, USA"
      - max_results: maximum number of results to return
    Output: List of dicts. Each dict contains keys:
      funder_name, mission_focus, award_size_min, award_size_max,
      deadline (ISO string), geographic_restriction, eligibility, url
    """
    # Mock data synthesized from inputs (replace with real API/DB later)
    keywords_str = ", ".join(mission_keywords) if mission_keywords else "general mission alignment"
    results: List[Dict[str, Any]] = []
    num = max(1, int(max_results))
    for i in range(num):
        results.append({
            "funder_name": f"Example Foundation {i+1}",
            "mission_focus": f"Focus on: {keywords_str}",
            "award_size_min": 5000 + i * 1000,
            "award_size_max": 25000 + i * 2000,
            "deadline": (datetime.now() + timedelta(days=90 + i * 15)).date().isoformat(),
            "geographic_restriction": region,
            "eligibility": "501(c)(3) non-profit organisation supporting women scholars",
            "url": f"https://examplefoundation.org/apply/{i+1}"
        })
    return results


@tool
def donor_prospect(
    past_donors: List[Dict[str, Any]],
    industry_filter: List[str] = None,
    region: str = None,
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Analyse past donors list, filter by criteria, and produce a sorted list of high-potential sponsors/donors.

    Inputs:
      - past_donors: list of donor records with keys:
          name, type (individual/org), industry, last_gift_amount,
          last_gift_date (string), region
      - industry_filter: optional list of industries, e.g. ["Finance","Technology"]
      - region: optional region filter
      - top_n: number of top prospects to return
    Output:
      - sorted list of dictionaries, each with donor info + potential_score
    """
    filtered = past_donors
    if industry_filter:
        inds = set(s.lower() for s in industry_filter)
        filtered = [d for d in filtered if str(d.get("industry", "")).lower() in inds]
    if region:
        r = region.lower()
        filtered = [d for d in filtered if r in str(d.get("region", "")).lower()]

    # Basic scoring: last gift amount * 0.5, with small recency bonus
    scored: List[Dict[str, Any]] = []
    for d in filtered:
        base = float(d.get("last_gift_amount", 0) or 0)
        recency_bonus = 0.0
        try:
            date_str = d.get("last_gift_date")
            if date_str:
                from datetime import datetime as _dt
                days_ago = max(1, (_dt.now() - _dt.fromisoformat(str(date_str))).days)
                recency_bonus = 1000 / days_ago
        except Exception:
            recency_bonus = 0.0
        score = base * 0.5 + recency_bonus
        item = dict(d)
        item["potential_score"] = round(score, 2)
        scored.append(item)

    scored_sorted = sorted(scored, key=lambda x: x["potential_score"], reverse=True)
    return scored_sorted[: max(0, int(top_n))]


@tool
def deposit_tracker(
    award_id: str,
    action: str,
    details: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Track awarded funds, record deposit receipt, allocate to scholarships or event costs, and update status.

    Inputs:
      - award_id: unique identifier for the award
      - action: one of ["register_award","record_deposit","allocate_funds","report_outcome"]
      - details: dictionary with relevant fields depending on action
    Output:
      - status dict showing updated record: award_id, status, and any relevant amounts/allocations
    """
    if action == "register_award":
        return {
            "award_id": award_id,
            "status": "Registered",
            "amount_awarded": (details or {}).get("amount_awarded")
        }
    elif action == "record_deposit":
        return {
            "award_id": award_id,
            "status": "Deposit Recorded",
            "deposit_amount": (details or {}).get("deposit_amount")
        }
    elif action == "allocate_funds":
        return {
            "award_id": award_id,
            "status": "Funds Allocated",
            "allocation_details": (details or {}).get("allocation_details")
        }
    elif action == "report_outcome":
        return {
            "award_id": award_id,
            "status": "Report Submitted",
            "outcome_details": (details or {}).get("outcome_details")
        }
    else:
        return {
            "award_id": award_id,
            "status": "Unknown action",
            "details": details
        }


__all__ = [
    "grant_search",
    "donor_prospect",
    "deposit_tracker",
]