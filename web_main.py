from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables for local development (Render will inject env vars at runtime)
load_dotenv()

app = FastAPI(title="Scholarship Ball Agent API", version="0.1.0")


@app.get("/")
def read_root():
    return {"message": "Welcome to the Scholarship Ball Agent API!"}


@app.get("/health")
def health():
    return {"status": "ok"}


# --- Tool endpoints (wrap existing no-code tools) ---
from tools_no_code import grant_search, donor_prospect, deposit_tracker
from tools_no_code_extra import generate_outreach_letter, dashboard_summary


class GrantSearchRequest(BaseModel):
    mission_keywords: List[str]
    region: str
    max_results: int = 10


@app.post("/tools/grant_search")
def api_grant_search(req: GrantSearchRequest):
    return grant_search(req.mission_keywords, req.region, req.max_results)


class DonorProspectRequest(BaseModel):
    past_donors: List[Dict[str, Any]]
    industry_filter: Optional[List[str]] = None
    region: Optional[str] = None
    top_n: int = 5


@app.post("/tools/donor_prospect")
def api_donor_prospect(req: DonorProspectRequest):
    return donor_prospect(req.past_donors, req.industry_filter, req.region, req.top_n)


class OutreachRequest(BaseModel):
    prospect: Dict[str, Any]
    mission_statement: str
    event_name: str
    sponsorship_tier: str


@app.post("/tools/generate_outreach_letter")
def api_generate_outreach_letter(req: OutreachRequest):
    # Returns a string (email/letter body)
    return generate_outreach_letter(req.prospect, req.mission_statement, req.event_name, req.sponsorship_tier)


class DashboardSummaryRequest(BaseModel):
    opportunities: List[Dict[str, Any]]
    donor_prospects: List[Dict[str, Any]]
    event_projection: Dict[str, Any]


@app.post("/tools/dashboard_summary")
def api_dashboard_summary(req: DashboardSummaryRequest):
    return dashboard_summary(req.opportunities, req.donor_prospects, req.event_projection)


class DepositActionRequest(BaseModel):
    award_id: str
    action: str
    details: Optional[Dict[str, Any]] = None


@app.post("/tools/deposit_tracker")
def api_deposit_tracker(req: DepositActionRequest):
    return deposit_tracker(req.award_id, req.action, req.details)


# --- Agent endpoint (included in MVP per decision) ---
# We import the agent runner from the existing CLI-oriented main.py.
# This will not trigger the CLI loop because it's guarded by if __name__ == "__main__":
try:
    from main import run_agent, HumanMessage, AIMessage  # type: ignore
    HAS_AGENT = True
except Exception:
    HAS_AGENT = False


class AgentRequest(BaseModel):
    input: str
    history: Optional[List[Dict[str, Any]]] = None


@app.post("/agent/invoke")
def api_agent_invoke(req: AgentRequest):
    if not HAS_AGENT:
        raise HTTPException(status_code=503, detail="Agent not available. Ensure dependencies are installed and main.run_agent exists.")
    history_msgs = []
    if req.history:
        for m in req.history:
            role = (m.get("role") or m.get("type") or "user").lower()
            content = m.get("content", "")
            if role in ("user", "human"):
                history_msgs.append(HumanMessage(content=content))
            else:
                history_msgs.append(AIMessage(content=content))
    response_msg = run_agent(req.input, history_msgs)
    return {"content": response_msg.content}
