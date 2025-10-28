from typing import List, Dict, Any, Optional
import importlib
from datetime import datetime, timedelta
import csv
import json

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


@tool("generate_outreach_letter",
      description="Generate a personalised outreach letter/email template for a given donor/sponsor based on their profile and our mission.")
def generate_outreach_letter(
    prospect: Dict[str, Any],
    mission_statement: str,
    event_name: str,
    sponsorship_tier: str
) -> str:
    """
    Inputs:
      - prospect: dict containing keys such as name, type (org/individual), industry, last_gift_amount, region
      - mission_statement: string, e.g. "Empowering undergraduate women through leadership scholarships in NY"
      - event_name: string, e.g. "Annual Scholarship Ball 2026"
      - sponsorship_tier: string, e.g. "Platinum Sponsor"
    Output:
      - A full outreach letter or email text (string)
    """
    name = prospect.get("name", "Valued Supporter")
    industry = prospect.get("industry", "")
    last_gift = prospect.get("last_gift_amount", 0)
    region = prospect.get("region", "")
    # This is a stub; you may refine tone, placeholders, etc.
    letter = (
        f"Dear {name},\n\n"
        f"As part of our mission {mission_statement}, we are pleased to invite you to join us as a {sponsorship_tier} "
        f"for the {event_name}. Your leadership in the {industry} sector, and generous past support of ${last_gift:,} in {region}, "
        "make you an ideal partner in helping us empower undergraduate women in our community.\n\n"
        "By sponsoring this event, you’ll be recognised as a leader committed to education and women's leadership, "
        "receive event benefits (table for 10, logo placement, special acknowledgement), and most importantly — help us award scholarships that transform lives.\n\n"
        "We hope you will join us and look forward to discussing this opportunity with you. Please let us know how you’d like to proceed.\n\n"
        "Warm regards,\n"
        "[Your Sorority Name]\n"
        "[Contact details]"
    )
    return letter


@tool("dashboard_summary",
      description="Generate a summary dashboard view text for the funding pipeline: opportunities count, upcoming deadlines, donor prospects, event projection.")
def dashboard_summary(
    opportunities: List[Dict[str, Any]],
    donor_prospects: List[Dict[str, Any]],
    event_projection: Dict[str, Any]
) -> str:
    """
    Inputs:
      - opportunities: list of opportunity dicts (with keys like funder_name, deadline, fit_score)
      - donor_prospects: list of prospect dicts (with keys like name, potential_score, last_gift_amount)
      - event_projection: dict with keys like target_revenue, projected_revenue, tickets_sold, sponsorships_sold
    Output:
      - A human-readable summary text of the dashboard
    """
    opp_count = len(opportunities)
    next_deadlines = sorted(opportunities, key=lambda x: x.get("deadline", ""))[:3]
    top_prospects = donor_prospects[:3]
    target = event_projection.get("target_revenue", 0)
    projected = event_projection.get("projected_revenue", 0)
    summary = (
        f"🔍 Funding Pipeline Summary:\n\n"
        f"• Opportunities in pipeline: {opp_count}\n"
    )
    if next_deadlines:
        summary += "• Next upcoming deadlines:\n"
        for opp in next_deadlines:
            summary += f"   - {opp.get('funder_name')} (Deadline: {opp.get('deadline')}, Fit Score: {opp.get('fit_score')})\n"
    summary += "\n• Top donor/sponsor prospects:\n"
    for p in top_prospects:
        summary += f"   - {p.get('name')} (Industry: {p.get('industry')}, Last Gift: ${p.get('last_gift_amount')}, Score: {p.get('potential_score')})\n"
    summary += (
        f"\n• Event Revenue Projection:\n"
        f"   Target: ${target:,}\n"
        f"   Projected: ${projected:,}\n"
        f"   Gap: ${target - projected:,}\n"
        "\nNext immediate steps: Check the top-3 escrow opportunities and reach out to the top pen-prospect donor this week."
    )
    return summary


# -------- Additional production-ready stubs --------

@tool("generate_grant_application_outline",
      description="Produce an outline draft of a grant application given an opportunity and org profile.")
def generate_grant_application_outline(
    opportunity: Dict[str, Any],
    org_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """Return a structured outline with common sections for a grant application."""
    return {
        "opportunity": opportunity.get("funder_name"),
        "outline": {
            "Executive Summary": f"Brief overview of program aligning with {opportunity.get('mission_focus', 'the funder focus')}.",
            "Needs Statement": f"Describe the need in {org_profile.get('region', 'our community')} for {org_profile.get('mission', 'our mission')}.",
            "Program Description": "Objectives, activities, timeline, and staffing.",
            "Budget": "Itemized budget with narrative justification.",
            "Outcomes": "Measurable outcomes and evaluation plan.",
        }
    }


@tool("report_to_funder_tool",
      description="Generate a funder report based on outcomes and award data.")
def report_to_funder_tool(
    award_id: str,
    outcomes: List[Dict[str, Any]],
    award_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Return a minimal text report and summary fields suitable for sending to a funder."""
    total_beneficiaries = sum(int(o.get("beneficiaries", 0)) for o in outcomes)
    key_outcomes = ", ".join(o.get("outcome", "") for o in outcomes if o.get("outcome"))
    report_text = (
        f"Award {award_id} Report:\n"
        f"- Total beneficiaries: {total_beneficiaries}\n"
        f"- Key outcomes: {key_outcomes}\n"
        f"- Amount used: ${award_data.get('amount_used', 0)} of ${award_data.get('amount_awarded', 0)}\n"
    )
    return {
        "award_id": award_id,
        "summary_text": report_text,
        "beneficiaries": total_beneficiaries,
        "outcomes_count": len(outcomes),
    }


@tool("task_reminder_tool",
      description="Check tasks and return reminders for items due within the next N days.")
def task_reminder_tool(
    tasks: List[Dict[str, Any]],
    days_ahead: int = 7,
    now_iso: Optional[str] = None
) -> Dict[str, Any]:
    """Each task dict may include: title, deadline (ISO date), owner, status."""
    try:
        now = datetime.fromisoformat(now_iso) if now_iso else datetime.now()
    except Exception:
        now = datetime.now()
    soon = now + timedelta(days=max(0, int(days_ahead)))
    upcoming = []
    for t in tasks:
        try:
            dl = t.get("deadline")
            if dl:
                dld = datetime.fromisoformat(str(dl))
                if now <= dld <= soon and str(t.get("status", "")).lower() not in {"done", "completed"}:
                    upcoming.append(t)
        except Exception:
            continue
    return {"now": now.isoformat(), "due_within_days": days_ahead, "upcoming": upcoming}


@tool("data_import_tool",
      description="Import CSV/JSON data for donors or opportunities. For CSV provide filepath; for JSON provide either filepath or raw JSON string.")
def data_import_tool(
    source_type: str,
    content_or_path: str
) -> Dict[str, Any]:
    """Simple import helper returning parsed rows. Not secure for untrusted input; for demo use only."""
    try:
        if source_type.lower() == "csv":
            rows: List[Dict[str, Any]] = []
            with open(content_or_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(dict(row))
            return {"type": "csv", "count": len(rows), "rows": rows}
        elif source_type.lower() == "json":
            # Try file path first; if fails, treat as raw JSON
            try:
                with open(content_or_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = json.loads(content_or_path)
            return {"type": "json", "data": data}
        else:
            return {"error": f"Unsupported source_type: {source_type}"}
    except Exception as e:
        return {"error": str(e)}


# Simple in-process cache
_CACHE: Dict[str, Any] = {}


@tool("cache_tool", description="Get/Set cached values by key to avoid recomputation costs.")
def cache_tool(action: str, key: str, value: Any = None, ttl_seconds: Optional[int] = None) -> Dict[str, Any]:
    """Supported actions: get, set, delete, clear. TTL is accepted but not enforced in this stub."""
    action_l = action.lower()
    if action_l == "get":
        return {"hit": key in _CACHE, "key": key, "value": _CACHE.get(key)}
    elif action_l == "set":
        _CACHE[key] = value
        return {"ok": True, "key": key}
    elif action_l == "delete":
        _CACHE.pop(key, None)
        return {"ok": True, "key": key}
    elif action_l == "clear":
        _CACHE.clear()
        return {"ok": True, "cleared": True}
    else:
        return {"error": f"Unsupported action: {action}"}


@tool("audit_log_tool", description="Record agent/tool usage with timestamp and metadata.")
def audit_log_tool(user: str, action: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
    """Return a log entry that could be persisted by the caller as needed."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "user": user,
        "action": action,
        "details": details or {},
    }
    return {"logged": True, "entry": entry}


__all__ = [
    "generate_outreach_letter",
    "dashboard_summary",
    "generate_grant_application_outline",
    "report_to_funder_tool",
    "task_reminder_tool",
    "data_import_tool",
    "audit_log_tool",
    "cache_tool",
]