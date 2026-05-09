import os
import json
from groq import Groq
from dotenv import load_dotenv
from models import EnrichedIncident

load_dotenv("../.env")

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SEVERITY_MAP = {
    "p1": "CRITICAL",
    "p2": "HIGH", 
    "p3": "MEDIUM",
    "p4": "LOW",
}

def enrich_incident(incident: dict) -> EnrichedIncident:
    incident["severity"] = SEVERITY_MAP.get(incident["severity"].lower(), incident["severity"])

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

    max_retries = 3
    base_delay = 10

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            raw = response.choices[0].message.content.strip()
            data = json.loads(raw)
            return EnrichedIncident(**data)
            
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "rate" in error_str:
                if attempt == max_retries - 1:
                    raise e
                sleep_time = base_delay * (2 ** attempt)
                print(f"Rate limited by Groq. Retrying in {sleep_time} seconds...")
                import time
                time.sleep(sleep_time)
            else:
                raise e