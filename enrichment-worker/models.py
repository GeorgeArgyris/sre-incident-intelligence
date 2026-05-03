from pydantic import BaseModel
from typing import List

class EnrichedIncident(BaseModel):
    incident_id: str
    service: str
    severity: str
    error_type: str
    root_cause: str
    recommended_actions: List[str]
    estimated_impact: str
    resolution_time_minutes: int