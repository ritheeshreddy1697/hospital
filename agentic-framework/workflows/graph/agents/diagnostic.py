"""Diagnostic agent execution body and bidding hook for agentic framework."""

async def run_diagnostic_body(sid: str, ctx: dict) -> dict:
    """Executes diagnostic slot allocation logic."""
    resource = ctx.get("diagnostic_resource", "MRI")
    return {
        "status": "completed",
        "resource": resource,
        "allocated": True,
        "slot_id": f"SLOT-{resource}-1300",
        "output": f"Diagnostic slot allocated for {resource}"
    }

async def bid_diagnostic(sid: str, ctx: dict) -> dict:
    """Bidding hook for diagnostic resource allocation strategy."""
    utility = ctx.get("utility_ceiling", 140.0)
    current_highest = ctx.get("highest_bid", 85.0)
    
    if utility < current_highest:
        return {"score": 0.0, "action": "WITHDRAW", "reason": "Utility ceiling below market bid"}
    
    bid_value = current_highest + min(20.0, (utility - current_highest) * 0.6)
    return {
        "score": bid_value,
        "action": "BID",
        "bid_value": bid_value,
        "utility_ceiling": utility
    }
