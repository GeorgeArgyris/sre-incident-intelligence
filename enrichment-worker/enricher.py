import os
import json
from groq import Groq
from dotenv import load_dotenv
from models import EnrichedIncident

load_dotenv("../.env")

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def enrich_incident(incident: dict) -> EnrichedIncident:
    prompt = f"""
You are an SRE expert. Analyze this incident and respond ONLY with valid JSON, no extra text.

Incident:
{json.dumps(incident, indent=2)}

Respond with exactly this structure:
{{
    "incident_id": "{incident['incident_id']}",
    "service": "{incident['service']}",
    "severity": "{incident['severity']}",
    "error_type": "{incident['error_type']}",
    "root_cause": "one sentence explanation",
    "recommended_actions": ["action 1", "action 2", "action 3"],
    "estimated_impact": "one sentence about user/business impact",
    "resolution_time_minutes": 30
}}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()
    data = json.loads(raw)
    return EnrichedIncident(**data)