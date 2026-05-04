
import os
from dotenv import load_dotenv
import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor

load_dotenv("../.env")

# Created once when the module loads, reused for every request.
_pool = None

def _get_pool():
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=5,
            dsn=os.environ["DATABASE_URL"]
        )
    return _pool

def fetch_recent_incidents(limit: int = 50, severity: str = None) -> list[dict]:
    pool = _get_pool()
    conn = pool.getconn()  # borrow a connection from the pool
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if severity:
                cur.execute("""
                    SELECT * FROM incidents
                    WHERE severity = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (severity.upper(), limit))
            else:
                cur.execute("""
                    SELECT * FROM incidents
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (limit,))
            return [dict(row) for row in cur.fetchall()]
    finally:
        pool.putconn(conn)  

def fetch_incident_by_id(incident_id: str) -> dict | None:
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM incidents WHERE incident_id = %s",
                (incident_id,)
            )
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        pool.putconn(conn)


def fetch_stats() -> dict:
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE UPPER(severity) = 'CRITICAL') AS critical,
                    COUNT(*) FILTER (WHERE UPPER(severity) = 'HIGH')     AS high,
                    COUNT(*) FILTER (WHERE UPPER(severity) = 'MEDIUM')   AS medium,
                    COUNT(*) FILTER (WHERE UPPER(severity) = 'LOW')      AS low,
                    MAX(created_at)                               AS last_event_at
                FROM incidents
            """)
            return dict(cur.fetchone())
    finally:
        pool.putconn(conn)