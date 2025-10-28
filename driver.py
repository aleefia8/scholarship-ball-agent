import json
from typing import Any, Dict
from tools_no_code import grant_search, donor_prospect, deposit_tracker
from tools_no_code_extra import generate_outreach_letter, dashboard_summary


def _call_tool(obj, **kwargs):
    """Call either a plain function or a LangChain Tool/StructuredTool in a unified way."""
    # LangChain tools often expose .invoke(input_dict) or .run for string inputs
    if hasattr(obj, "invoke") and callable(getattr(obj, "invoke")):
        return obj.invoke(kwargs)
    elif hasattr(obj, "run") and callable(getattr(obj, "run")):
        return obj.run(kwargs)
    else:
        return obj(**kwargs)


def load_mock_data():
    """
    Load mock data for donors and event projection.
    For a no-coder: you can edit these lists directly or load from CSV/JSON files.
    """
    past_donors = [
        {"name": "TechCorp Inc.", "type": "organization", "industry": "Technology", "last_gift_amount": 20000, "last_gift_date": "2024-08-15", "region": "NY, USA"},
        {"name": "FinanceWorks LLC", "type": "organization", "industry": "Finance", "last_gift_amount": 15000, "last_gift_date": "2023-11-20", "region": "NY, USA"},
        {"name": "Alumni Jane Doe", "type": "individual", "industry": "Education", "last_gift_amount": 5000, "last_gift_date": "2024-05-30", "region": "NY, USA"}
    ]

    event_projection = {
        "event_name": "Annual Scholarship Ball 2026",
        "target_revenue": 100000,
        "projected_revenue": 65000,
        "tickets_sold": 150,
        "sponsorships_sold": 3
    }

    return past_donors, event_projection


def main():
    # Step 1: Define your organisation mission and region
    mission_keywords = ["women leadership scholarships", "undergraduate education"]
    region = "NY, USA"

    # Step 2: Load mock data
    past_donors, event_projection = load_mock_data()

    # Step 3: Use the grant_search tool to find opportunities
    print("🔎 Searching for grant/funding opportunities...")
    opportunities = _call_tool(grant_search, mission_keywords=mission_keywords, region=region, max_results=5)

    print("\nFound opportunities:")
    for opp in opportunities:
        print(f" • {opp['funder_name']}, Award size: ${opp['award_size_min']:,}-${opp['award_size_max']:,}, Deadline: {opp['deadline']}")

    # Step 4: Use donor_prospect tool to identify top sponsors/donors
    print("\n🎯 Identifying top donor/sponsor prospects...")
    donor_prospects = _call_tool(donor_prospect, past_donors=past_donors, industry_filter=None, region=region, top_n=3)
    print("\nTop donor prospects:")
    for p in donor_prospects:
        print(f" • {p['name']} (Industry: {p['industry']}, Last Gift: ${p['last_gift_amount']}, Score: {p['potential_score']})")

    # Step 5: Generate an outreach letter for the top prospect
    top_prospect = donor_prospects[0]
    print("\n✉️ Generating outreach letter for top prospect...")
    letter = _call_tool(
        generate_outreach_letter,
        prospect=top_prospect,
        mission_statement="Empowering undergraduate women through leadership scholarships in NY",
        event_name=event_projection["event_name"],
        sponsorship_tier="Platinum Sponsor"
    )
    print("\n--- Outreach Letter ---")
    print(letter)

    # Step 6: Generate dashboard summary of pipeline + event projection
    # We assume we add a fit_score into each opportunity (if your tool doesn’t yet do it, you can manually add)
    for i, opp in enumerate(opportunities):
        opp["fit_score"] = 80 - i * 10  # simple example: score decreasing
    summary = _call_tool(
        dashboard_summary,
        opportunities=opportunities,
        donor_prospects=donor_prospects,
        event_projection=event_projection
    )
    print("\n📊 Dashboard Summary")
    print(summary)

    # Step 7: Example of deposit tracker usage (simulate awarding and deposit)
    print("\n💰 Tracking funding award & deposit example...")
    award_id = "AWD-001"
    # Register the award
    reg = _call_tool(deposit_tracker, award_id=award_id, action="register_award", details={"amount_awarded": 25000})
    print("Registered award:", reg)
    # Record a deposit
    dep = _call_tool(deposit_tracker, award_id=award_id, action="record_deposit", details={"deposit_amount": 25000})
    print("Deposit recorded:", dep)
    # Allocate funds
    alloc = _call_tool(deposit_tracker, award_id=award_id, action="allocate_funds", details={"allocation_details": "Scholarship recipient A – $25,000"})
    print("Funds allocated:", alloc)


if __name__ == "__main__":
    main()
