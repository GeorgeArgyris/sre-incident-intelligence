import { useState, useEffect, useRef } from "react"
import "./App.css"

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const WS_BASE_URL = import.meta.env.VITE_WS_URL || "ws://127.0.0.1:8000";

function StatCard({ label, value, colorClass }) {
  return (
    <div className="bg-slate-800/80 border border-slate-700/50 rounded-xl p-4 min-w-[120px] text-center flex-1 shadow-sm backdrop-blur-sm transition-all hover:bg-slate-800">
      <div className={`text-3xl font-extrabold ${colorClass}`}>{value}</div>
      <div className="text-xs font-semibold text-slate-400 mt-2 tracking-widest uppercase">{label}</div>
    </div>
  )
}

function IncidentCard({ incident }) {
  const sev = incident.severity?.toUpperCase()
  
  const severityStyles = {
    CRITICAL: { wrapper: "bg-red-950/20 border-red-500/30 hover:border-red-500/50", badge: "bg-red-500 text-white", text: "text-red-400" },
    HIGH:     { wrapper: "bg-orange-950/20 border-orange-500/30 hover:border-orange-500/50", badge: "bg-orange-500 text-white", text: "text-orange-400" },
    MEDIUM:   { wrapper: "bg-green-950/20 border-green-500/30 hover:border-green-500/50", badge: "bg-green-500 text-white", text: "text-green-400" },
    LOW:      { wrapper: "bg-blue-950/20 border-blue-500/30 hover:border-blue-500/50", badge: "bg-blue-500 text-white", text: "text-blue-400" },
  }
  
  const style = severityStyles[sev] || severityStyles.LOW

  return (
    <div className={`rounded-lg border p-4 flex flex-col gap-3 transition-colors duration-200 ${style.wrapper}`}>
      {/* top row */}
      <div className="flex justify-between items-center">
        <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-widest uppercase shadow-sm ${style.badge}`}>
          {sev}
        </span>
        <span className="text-xs font-medium text-slate-400">
          {new Date(incident.created_at).toLocaleTimeString()}
        </span>
      </div>

      {/* service + error */}
      <div className="flex gap-2 items-baseline mt-1">
        <span className="font-semibold text-slate-100 text-lg">{incident.service}</span>
        <span className={`text-xs font-medium ${style.text}`}>{incident.error_type}</span>
      </div>

      {/* root cause */}
      <div className="text-sm text-slate-300 leading-relaxed">
        {incident.root_cause}
      </div>

      {/* actions */}
      {incident.recommended_actions?.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-1">
          {incident.recommended_actions.map((action, i) => (
            <span key={i} className="bg-slate-900 border border-slate-700/50 rounded-md px-2 py-1 text-xs text-slate-400">
              {action}
            </span>
          ))}
        </div>
      )}

      {/* footer */}
      <div className="flex gap-6 mt-2 pt-3 border-t border-slate-800/50">
        <span className="text-xs text-slate-500 font-medium">
          Impact: <span className="text-slate-300">{incident.estimated_impact}</span>
        </span>
        <span className="text-xs text-slate-500 font-medium">
          ETA: <span className="text-slate-300">{incident.resolution_time_minutes}m</span>
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

  useEffect(() => {
    function connect() {
      const ws = new WebSocket(`${WS_BASE_URL}/ws/incidents`)
      wsRef.current = ws

      ws.onopen = () => setConnected(true)

      ws.onmessage = (event) => {
        const incident = JSON.parse(event.data)
        setIncidents(prev => {
          if (prev.find(i => i.incident_id === incident.incident_id)) return prev
          return [incident, ...prev].slice(0, 100)
        })
      }

      ws.onclose = () => {
        setConnected(false)
        setTimeout(connect, 3000)
      }

      ws.onerror = () => ws.close()
    }

    connect()
    return () => wsRef.current?.close()
  }, [])

  return (
    <div className="min-h-screen bg-slate-950 font-sans selection:bg-indigo-500/30 text-slate-200">

      {/* header */}
      <header className="sticky top-0 z-50 flex items-center justify-between border-b border-slate-800 bg-slate-950/80 px-6 py-4 backdrop-blur-md">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            SRE Incident Intelligence
          </h1>
          <p className="text-xs font-medium text-slate-500 mt-1">Live enrichment pipeline</p>
        </div>
        
        <div className="flex items-center gap-2 bg-slate-900/50 px-3 py-1.5 rounded-full border border-slate-800">
          <div className={`h-2.5 w-2.5 rounded-full ${connected ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" : "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]"}`} />
          <span className={`text-xs font-bold uppercase tracking-wider ${connected ? "text-green-500" : "text-red-500"}`}>
            {connected ? "live" : "reconnecting..."}
          </span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6 space-y-6">

        {/* stats bar */}
        {stats && (
          <section className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <StatCard label="Total" value={stats.total} colorClass="text-indigo-400" />
            <StatCard label="Critical" value={stats.critical} colorClass="text-red-500" />
            <StatCard label="High" value={stats.high} colorClass="text-orange-500" />
            <StatCard label="Medium" value={stats.medium} colorClass="text-green-500" />
            <StatCard label="Low" value={stats.low} colorClass="text-blue-500" />
          </section>
        )}

        {/* incident feed */}
        <section className="flex flex-col gap-4 pb-12 mt-4">
          {incidents.length === 0 && (
            <div className="text-slate-500 text-center py-16 text-sm font-medium border border-dashed border-slate-800 rounded-xl">
              Waiting for incidents...
            </div>
          )}
          {incidents.map(incident => (
            <IncidentCard key={incident.incident_id} incident={incident} />
          ))}
        </section>

      </main>

    </div>
  )
}