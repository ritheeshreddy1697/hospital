"""Temporal activities for Diagnostic Resource Agent"""

async def fetch_diagnostic_slots(resource_type: str = "MRI") -> dict:
    """Fetch availability for diagnostic resources (MRI, CT SCAN, LAB)."""
    return {
        "resource_type": resource_type,
        "available_slots": 1 if resource_type == "MRI" else 2,
        "urgency_threshold": 75
    }

async def evaluate_diagnostic_bid(department: str, utility_ceiling: float, current_highest_bid: float) -> dict:
    """Evaluates bidding strategy for diagnostic resources during multi-agent auctions."""
    if utility_ceiling < current_highest_bid:
        return {"action": "WITHDRAW", "bid": 0}
    increment = max(10, (utility_ceiling - current_highest_bid) * 0.5)
    return {"action": "BID", "bid": current_highest_bid + increment}
