import logging

logger = logging.getLogger("diagnostic_service")

class DiagnosticService:
    """Service for managing diagnostic slots (MRI, CT SCAN, LAB) and resource allocation auctions."""
    
    def __init__(self):
        self.resource_slots = {
            "MRI": {"total": 5, "available": 1, "cost_per_slot": 120},
            "CT_SCAN": {"total": 8, "available": 2, "cost_per_slot": 80},
            "LAB": {"total": 20, "available": 4, "cost_per_slot": 45}
        }

    def get_slot_availability(self, resource_type: str) -> dict:
        return self.resource_slots.get(resource_type.upper(), {"total": 0, "available": 0, "cost_per_slot": 0})
