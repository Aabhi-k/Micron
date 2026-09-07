import { useState } from "react"
import {
  LayoutDashboard,
  Database,
  ShieldAlert,
  Zap,
  Activity,
  FileText,
  Upload,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Search,
  Sliders,
  Server,
  Lock,
  ArrowUpRight,
  TrendingUp,
  FileCode,
  Users,
  Eye,
  Plus
} from "lucide-react"

export default function AdminDashboard({ onClose }) {
  const [activeTab, setActiveTab] = useState("overview")
  const [searchTerm, setSearchTerm] = useState("")
  
  // State for new BPD document form
  const [newBpdTitle, setNewBpdTitle] = useState("")
  const [newBpdCategory, setNewBpdCategory] = useState("Finance & Audit")
  const [newBpdContent, setNewBpdContent] = useState("")
  const [bpdSuccessMsg, setBpdSuccessMsg] = useState("")

  // Mock initial indexed documents
  const [bpdList, setBpdList] = useState([
    { id: "BPD-101", title: "Transaction Processing Rules v2", category: "Finance & Audit", vectors: 142, date: "2026-09-01", status: "Indexed" },
    { id: "BPD-102", title: "PCI-DSS Data Redaction Mandate", category: "Security & Compliance", vectors: 88, date: "2026-09-03", status: "Indexed" },
    { id: "BPD-103", title: "Legacy COBOL Conversion Workflow", category: "Engineering", vectors: 210, date: "2026-09-05", status: "Indexed" },
    { id: "BPD-104", title: "Employee Data Privacy Directive", category: "HR & Operations", vectors: 64, date: "2026-09-06", status: "Indexed" },
  ])

  // Security Toggles
  const [settings, setSettings] = useState({
    autoRedact: true,
    langfuseTracing: true,
    hybridSearch: true,
    cacheResponses: false,
    strictRbac: true,
  })

  const toggleSetting = (key) => {
    setSettings((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const handleIndexBpd = (e) => {
    e.preventDefault()
    if (!newBpdTitle.trim() || !newBpdContent.trim()) return

    const newDoc = {
      id: `BPD-${105 + bpdList.length}`,
      title: newBpdTitle.trim(),
      category: newBpdCategory,
      vectors: Math.floor(Math.random() * 80) + 20,
      date: new Date().toISOString().split("T")[0],
      status: "Indexed",
    }

    setBpdList([newDoc, ...bpdList])
    setNewBpdTitle("")
    setNewBpdContent("")
    setBpdSuccessMsg(`Successfully indexed "${newDoc.title}" into Qdrant Vector Store!`)
    setTimeout(() => setBpdSuccessMsg(""), 4000)
  }

  // Mock activity logs
  const logs = [
    { traceId: "tr-9a8b1c", user: "Employee #402", path: "src/api/auth.js", query: "Explain legacy auth token validation", citations: 2, status: "Success", latency: "1.12s", time: "10 mins ago" },
    { traceId: "tr-7d6e5f", user: "Employee #118", path: "backend/main.py", query: "Check database transaction isolation", citations: 3, status: "Success", latency: "0.98s", time: "25 mins ago" },
    { traceId: "tr-4c3b2a", user: "Employee #205", path: "config/secrets.json", query: "Extract API access keys", citations: 0, status: "Redacted", latency: "0.45s", time: "1 hour ago" },
    { traceId: "tr-1f2e3d", user: "Employee #509", path: "services/billing.go", query: "Generate payment processing flow diagram", citations: 4, status: "Success", latency: "1.45s", time: "2 hours ago" },
    { traceId: "tr-8e9f0a", user: "Employee #312", path: "legacy/db_connect.cpp", query: "Audit hardcoded credentials", citations: 1, status: "Redacted", latency: "0.62s", time: "3 hours ago" },
  ]

  const filteredLogs = logs.filter(
    (l) =>
      l.query.toLowerCase().includes(searchTerm.toLowerCase()) ||
      l.path.toLowerCase().includes(searchTerm.toLowerCase()) ||
      l.traceId.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 overflow-y-auto">
      {/* Header Bar */}
      <div className="bg-white border-b border-slate-200 px-8 py-5 flex items-center justify-between sticky top-0 z-20 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shadow-sm">
            <LayoutDashboard size={20} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900">Micron Admin Control Center</h1>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Operational
              </span>
            </div>
            <p className="text-xs text-slate-500">System Monitoring, RAG Vector Base & MCP Governance</p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveTab("knowledge")}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-[#10a37f] hover:bg-[#0d8f6f] text-white text-xs font-semibold transition-colors shadow-xs"
          >
            <Plus size={14} />
            Index BPD Document
          </button>
          <button
            onClick={onClose}
            className="px-3.5 py-2 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-100 text-xs font-semibold transition-colors"
          >
            Back to Chat
          </button>
        </div>
      </div>

      {/* Main Container */}
      <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-200 pb-3">
          <button
            onClick={() => setActiveTab("overview")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "overview"
                ? "bg-slate-900 text-white shadow-xs"
                : "text-slate-600 hover:bg-slate-200/60"
            }`}
          >
            <Activity size={15} />
            System Overview
          </button>
          <button
            onClick={() => setActiveTab("knowledge")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "knowledge"
                ? "bg-slate-900 text-white shadow-xs"
                : "text-slate-600 hover:bg-slate-200/60"
            }`}
          >
            <Database size={15} />
            Knowledge Base (BPDs)
          </button>
          <button
            onClick={() => setActiveTab("traces")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "traces"
                ? "bg-slate-900 text-white shadow-xs"
                : "text-slate-600 hover:bg-slate-200/60"
            }`}
          >
            <FileText size={15} />
            Activity & Traces
          </button>
        </div>

        {/* TAB 1: OVERVIEW */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* KPI Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
                <div className="flex items-center justify-between text-slate-500">
                  <span className="text-xs font-medium uppercase tracking-wider">Total Queries</span>
                  <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600">
                    <Zap size={16} />
                  </div>
                </div>
                <div className="flex items-baseline justify-between">
                  <span className="text-2xl font-bold text-slate-900">1,428</span>
                  <span className="text-xs font-semibold text-emerald-600 flex items-center gap-0.5">
                    <TrendingUp size={12} /> +18.4%
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">Queries processed this week</p>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
                <div className="flex items-center justify-between text-slate-500">
                  <span className="text-xs font-medium uppercase tracking-wider">Indexed BPD Rules</span>
                  <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
                    <Database size={16} />
                  </div>
                </div>
                <div className="flex items-baseline justify-between">
                  <span className="text-2xl font-bold text-slate-900">342</span>
                  <span className="text-xs font-semibold text-blue-600 flex items-center gap-0.5">
                    <ArrowUpRight size={12} /> Qdrant
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">Business Process Documents in Vector DB</p>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
                <div className="flex items-center justify-between text-slate-500">
                  <span className="text-xs font-medium uppercase tracking-wider">Auto-Redactions</span>
                  <div className="p-2 rounded-lg bg-amber-50 text-amber-600">
                    <ShieldAlert size={16} />
                  </div>
                </div>
                <div className="flex items-baseline justify-between">
                  <span className="text-2xl font-bold text-slate-900">892</span>
                  <span className="text-xs font-semibold text-emerald-600">99.4% Safe</span>
                </div>
                <p className="text-[11px] text-slate-400">Sensitive tokens filtered by MCP</p>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
                <div className="flex items-center justify-between text-slate-500">
                  <span className="text-xs font-medium uppercase tracking-wider">Avg Latency</span>
                  <div className="p-2 rounded-lg bg-purple-50 text-purple-600">
                    <Server size={16} />
                  </div>
                </div>
                <div className="flex items-baseline justify-between">
                  <span className="text-2xl font-bold text-slate-900">1.18s</span>
                  <span className="text-xs font-semibold text-emerald-600">-85ms</span>
                </div>
                <p className="text-[11px] text-slate-400">Mean pipeline generation time</p>
              </div>
            </div>

            {/* System Services Status & Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Pipeline Components Health */}
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4 md:col-span-1">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Server size={16} className="text-[#10a37f]" />
                  Pipeline Service Health
                </h3>

                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-100">
                    <div className="flex items-center gap-2.5">
                      <CheckCircle2 size={16} className="text-emerald-500" />
                      <div>
                        <p className="text-xs font-semibold text-slate-800">FastAPI Backend</p>
                        <p className="text-[10px] text-slate-400">http://localhost:8000</p>
                      </div>
                    </div>
                    <span className="text-[11px] font-mono font-medium text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded">
                      200 OK
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-100">
                    <div className="flex items-center gap-2.5">
                      <CheckCircle2 size={16} className="text-emerald-500" />
                      <div>
                        <p className="text-xs font-semibold text-slate-800">Qdrant Vector DB</p>
                        <p className="text-[10px] text-slate-400">Collection: bpd_rules</p>
                      </div>
                    </div>
                    <span className="text-[11px] font-mono font-medium text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded">
                      Connected
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-100">
                    <div className="flex items-center gap-2.5">
                      <CheckCircle2 size={16} className="text-emerald-500" />
                      <div>
                        <p className="text-xs font-semibold text-slate-800">MCP Code Redactor</p>
                        <p className="text-[10px] text-slate-400">AST Security Masking</p>
                      </div>
                    </div>
                    <span className="text-[11px] font-mono font-medium text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded">
                      Active
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-100">
                    <div className="flex items-center gap-2.5">
                      <CheckCircle2 size={16} className="text-emerald-500" />
                      <div>
                        <p className="text-xs font-semibold text-slate-800">Langfuse Tracing</p>
                        <p className="text-[10px] text-slate-400">Observability API</p>
                      </div>
                    </div>
                    <span className="text-[11px] font-mono font-medium text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded">
                      Logging
                    </span>
                  </div>
                </div>
              </div>

              {/* Category Volume & Usage Distribution */}
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4 md:col-span-2">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <TrendingUp size={16} className="text-blue-600" />
                  Documentation Category Requests
                </h3>

                <div className="space-y-4 pt-1">
                  <div>
                    <div className="flex justify-between text-xs font-medium text-slate-700 mb-1">
                      <span>Compliance & Audit Rules</span>
                      <span>42% (600 requests)</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div className="bg-[#10a37f] h-2 rounded-full" style={{ width: "42%" }} />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs font-medium text-slate-700 mb-1">
                      <span>Legacy Refactoring Guidance</span>
                      <span>28% (400 requests)</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div className="bg-blue-500 h-2 rounded-full" style={{ width: "28%" }} />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs font-medium text-slate-700 mb-1">
                      <span>Security & Secret Audit</span>
                      <span>18% (257 requests)</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div className="bg-amber-500 h-2 rounded-full" style={{ width: "18%" }} />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs font-medium text-slate-700 mb-1">
                      <span>API Schema & Integration</span>
                      <span>12% (171 requests)</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div className="bg-purple-500 h-2 rounded-full" style={{ width: "12%" }} />
                    </div>
                  </div>
                </div>

                <div className="border-t border-slate-100 pt-4 flex items-center justify-between text-xs text-slate-500">
                  <span>Total System Tokens Consumed: <strong>1.42M tokens</strong></span>
                  <span>Est. Cloud API Cost: <strong>$4.12</strong></span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: KNOWLEDGE BASE INDEXING */}
        {activeTab === "knowledge" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Form */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs md:col-span-1 space-y-4">
              <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
                <Upload size={16} className="text-[#10a37f]" />
                <h3 className="text-sm font-bold text-slate-900">Index New BPD Rule</h3>
              </div>

              {bpdSuccessMsg && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs flex items-center gap-2">
                  <CheckCircle2 size={16} className="text-emerald-600 shrink-0" />
                  <span>{bpdSuccessMsg}</span>
                </div>
              )}

              <form onSubmit={handleIndexBpd} className="space-y-3.5">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Document Title
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Fraud Detection Policy 2026"
                    value={newBpdTitle}
                    onChange={(e) => setNewBpdTitle(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#10a37f]/50"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Business Domain Category
                  </label>
                  <select
                    value={newBpdCategory}
                    onChange={(e) => setNewBpdCategory(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#10a37f]/50 bg-white"
                  >
                    <option>Finance & Audit</option>
                    <option>Security & Compliance</option>
                    <option>Engineering</option>
                    <option>HR & Operations</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Business Rules / Policy Text
                  </label>
                  <textarea
                    rows={5}
                    placeholder="Enter business logic requirements or markdown content to vectorize..."
                    value={newBpdContent}
                    onChange={(e) => setNewBpdContent(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#10a37f]/50 font-mono"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full py-2.5 bg-[#10a37f] hover:bg-[#0d8f6f] text-white text-xs font-semibold rounded-lg transition-colors shadow-xs flex items-center justify-center gap-2"
                >
                  <Database size={14} />
                  Generate Embeddings & Index
                </button>
              </form>
            </div>

            {/* Document List Table */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs md:col-span-2 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <Database size={16} className="text-blue-600" />
                  <h3 className="text-sm font-bold text-slate-900">Indexed Business Process Documents</h3>
                </div>
                <span className="text-xs text-slate-500 font-mono">Qdrant DB • {bpdList.length} Entries</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-50/70 text-[11px] font-semibold text-slate-500 uppercase">
                      <th className="py-2.5 px-3">ID</th>
                      <th className="py-2.5 px-3">Title</th>
                      <th className="py-2.5 px-3">Category</th>
                      <th className="py-2.5 px-3">Embeddings</th>
                      <th className="py-2.5 px-3">Date</th>
                      <th className="py-2.5 px-3 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-xs">
                    {bpdList.map((doc) => (
                      <tr key={doc.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="py-3 px-3 font-mono text-slate-500">{doc.id}</td>
                        <td className="py-3 px-3 font-semibold text-slate-800">{doc.title}</td>
                        <td className="py-3 px-3 text-slate-600">
                          <span className="px-2 py-0.5 rounded-full text-[10px] bg-slate-100 text-slate-700 border border-slate-200">
                            {doc.category}
                          </span>
                        </td>
                        <td className="py-3 px-3 font-mono text-slate-600">{doc.vectors} vectors</td>
                        <td className="py-3 px-3 text-slate-500">{doc.date}</td>
                        <td className="py-3 px-3 text-right">
                          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                            <CheckCircle2 size={11} /> {doc.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: ACTIVITY TRACES */}
        {activeTab === "traces" && (
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <FileText size={16} className="text-purple-600" />
                  Langfuse Generation Traces
                </h3>
                <p className="text-xs text-slate-500">Real-time audit log of incoming queries & MCP redactions</p>
              </div>

              {/* Search Bar */}
              <div className="relative w-full sm:w-64">
                <Search size={14} className="absolute left-3 top-2.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Filter by query or path..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#10a37f]/50"
                />
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50/70 text-[11px] font-semibold text-slate-500 uppercase">
                    <th className="py-2.5 px-3">Trace ID</th>
                    <th className="py-2.5 px-3">User</th>
                    <th className="py-2.5 px-3">Query</th>
                    <th className="py-2.5 px-3">Target File Path</th>
                    <th className="py-2.5 px-3">Latency</th>
                    <th className="py-2.5 px-3">Time</th>
                    <th className="py-2.5 px-3 text-right">Security Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs">
                  {filteredLogs.map((log) => (
                    <tr key={log.traceId} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3 px-3 font-mono font-medium text-purple-600">{log.traceId}</td>
                      <td className="py-3 px-3 text-slate-700 font-medium">{log.user}</td>
                      <td className="py-3 px-3 text-slate-900 max-w-xs truncate">{log.query}</td>
                      <td className="py-3 px-3 font-mono text-slate-500 text-[11px]">
                        {log.path || "<None>"}
                      </td>
                      <td className="py-3 px-3 font-mono text-slate-600">{log.latency}</td>
                      <td className="py-3 px-3 text-slate-400">{log.time}</td>
                      <td className="py-3 px-3 text-right">
                        {log.status === "Redacted" ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-800 bg-amber-50 px-2 py-0.5 rounded-md border border-amber-200">
                            <Lock size={11} /> Redacted
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                            <CheckCircle2 size={11} /> Passed
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
