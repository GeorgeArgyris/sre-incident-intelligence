import os
import psycopg2
from psycopg2.extras import RealDictCursor
from models import EnrichedIncident

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def run_migration():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            incident_id TEXT PRIMARY KEY,
            service TEXT,
            severity TEXT,
            error_type TEXT,
            root_cause TEXT,
            recommended_actions TEXT[],
            estimated_impact TEXT,
            resolution_time_minutes INTEGER,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("Migration complete")

def save_incident(incident: EnrichedIncident):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO incidents (
            incident_id, service, severity, error_type,
            root_cause, recommended_actions, estimated_impact, resolution_time_minutes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (incident_id) DO NOTHING
    """,
    (
        incident.incident_id,
        incident.service,
        incident.severity,
        incident.error_type,
        incident.root_cause,
        incident.recommended_actions,
        incident.estimated_impact,
        incident.resolution_time_minutes,
    ))
    conn.commit()
    cur.close()
    conn.close()