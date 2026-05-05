import { useState, useEffect, useRef } from "react"
import "./App.css"

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const WS_BASE_URL = import.meta.env.VITE_WS_URL || "ws://127.0.0.1:8000";

const SEVERITY_STYLES = {
  CRITICAL: { bg: "#3b0a0a", border: "#ef4444", badge: "#ef4444", text: "#fca5a5" },
  HIGH:     { bg: "#3b1f0a", border: "#f97316", badge: "#f97316", text: "#fdba74" },
  MEDIUM:   { bg: "#1a2a1a", border: "#22c55e", badge: "#22c55e", text: "#86efac" },
  LOW:      { bg: "#0a1a2a", border: "#3b82f6", badge: "#3b82f6", text: "#93c5fd" },
}

const DEFAULT_STYLE = { bg: "#1a1a2a", border: "#6366f1", badge: "#6366f1", text: "#c4b5fd" }

function StatCard({ label, value, color }) {
  return (
    <div style={{
      background: "#1e2130",
      border: `1px solid ${color}`,
      borderRadius: 8,
      padding: "12px 20px",
      minWidth: 110,
      textAlign: "center",
    }}>
      <div style={{ fontSize: 28, fontWeight: 700, color }}>{value}</div>
      <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 2, letterSpacing: "0.08em", textTransform: "uppercase" }}>{label}</div>
    </div>
  )
}

function IncidentCard({ incident }) {
  const sev = incident.severity?.toUpperCase()
  const style = SEVERITY_STYLES[sev] || DEFAULT_STYLE

  return (
    <div style={{
      background: style.bg,
      border: `1px solid ${style.border}`,
      borderRadius: 8,
      padding: "14px 18px",
      display: "flex",
      flexDirection: "column",
      gap: 8,
    }}>
      {/* top row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{
          background: style.badge,
          color: "#fff",
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: "0.1em",
          padding: "2px 8px",
          borderRadius: 4,
          textTransform: "uppercase",
        }}>{sev}</span>
        <span style={{ fontSize: 11, color: "#64748b" }}>
          {new Date(incident.created_at).toLocaleTimeString()}
        </span>
      </div>

      {/* service + error */}
      <div style={{ display: "flex", gap: 8, alignItems: "baseline" }}>
        <span style={{ fontWeight: 600, color: style.text }}>{incident.service}</span>
        <span style={{ color: "#64748b", fontSize: 12 }}>{incident.error_type}</span>
      </div>

      {/* root cause */}
      <div style={{ color: "#cbd5e1", fontSize: 13, lineHeight: 1.5 }}>
        {incident.root_cause}
      </div>

      {/* actions */}
      {incident.recommended_actions?.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 2 }}>
          {incident.recommended_actions.map((a, i) => (
            <span key={i} style={{
              background: "#1e2130",
              border: "1px solid #334155",
              borderRadius: 4,
              padding: "2px 8px",
              fontSize: 11,
              color: "#94a3b8",
            }}>
              {a}
            </span>
          ))}
        </div>
      )}

      {/* footer */}
      <div style={{ display: "flex", gap: 16, marginTop: 4 }}>
        <span style={{ fontSize: 11, color: "#64748b" }}>
          Impact: <span style={{ color: "#94a3b8" }}>{incident.estimated_impact}</span>
        </span>
        <span style={{ fontSize: 11, color: "#64748b" }}>
          ETA: <span style={{ color: "#94a3b8" }}>{incident.resolution_time_minutes}m</span>
        </span>
      </div>
    </div>
  )
}

export default function App() {
  const [incidents, setIncidents] = useState([])
  const [stats, setStats] = useState(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)

  // fetch stats every 15 seconds
  useEffect(() => {
    const fetchStats = () =>
      fetch(`${API_BASE_URL}/stats`)
        .then(r => r.json())
        .then(setStats)
        .catch(console.error)

    fetchStats()
    const interval = setInterval(fetchStats, 15000)
    return () => clearInterval(interval)
  }, [])

  // websocket — live incident feed
  useEffect(() => {
    function connect() {
      const ws = new WebSocket(`${WS_BASE_URL}/ws/incidents`)
      wsRef.current = ws

      ws.onopen = () => setConnected(true)

      ws.onmessage = (event) => {
        const incident = JSON.parse(event.data)
        setIncidents(prev => {
          // avoid duplicates
          if (prev.find(i => i.incident_id === incident.incident_id)) return prev
          // newest first, keep last 100
          return [incident, ...prev].slice(0, 100)
        })
      }

      ws.onclose = () => {
        setConnected(false)
        // auto-reconnect after 3 seconds
        setTimeout(connect, 3000)
      }

      ws.onerror = () => ws.close()
    }

    connect()
    return () => wsRef.current?.close()
  }, [])

  return (
    <div style={{ minHeight: "100vh", background: "#0f1117" }}>

      {/* header */}
      <div style={{
        borderBottom: "1px solid #1e2130",
        padding: "16px 24px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        position: "sticky",
        top: 0,
        background: "#0f1117",
        zIndex: 10,
      }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: 18, letterSpacing: "-0.02em" }}>
            SRE Incident Intelligence
          </div>
          <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>
            Live enrichment pipeline
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{
            width: 8, height: 8, borderRadius: "50%",
            background: connected ? "#22c55e" : "#ef4444",
            boxShadow: connected ? "0 0 6px #22c55e" : "none",
          }} />
          <span style={{ fontSize: 12, color: connected ? "#22c55e" : "#ef4444" }}>
            {connected ? "live" : "reconnecting..."}
          </span>
        </div>
      </div>

      {/* stats bar */}
      {stats && (
        <div style={{ padding: "16px 24px", display: "flex", gap: 12, flexWrap: "wrap" }}>
          <StatCard label="Total" value={stats.total} color="#6366f1" />
          <StatCard label="Critical" value={stats.critical} color="#ef4444" />
          <StatCard label="High" value={stats.high} color="#f97316" />
          <StatCard label="Medium" value={stats.medium} color="#22c55e" />
          <StatCard label="Low" value={stats.low} color="#3b82f6" />
        </div>
      )}

      {/* incident feed */}
      <div style={{ padding: "0 24px 24px", display: "flex", flexDirection: "column", gap: 10 }}>
        {incidents.length === 0 && (
          <div style={{ color: "#475569", textAlign: "center", marginTop: 60, fontSize: 14 }}>
            Waiting for incidents...
          </div>
        )}
        {incidents.map(incident => (
          <IncidentCard key={incident.incident_id} incident={incident} />
        ))}
      </div>

    </div>
  )
}