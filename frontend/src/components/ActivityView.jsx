import { useState } from "react"
import {
  Activity,
  Search,
  Trash2,
  ChevronDown,
  ChevronUp,
  FileCode,
  Tag,
  CheckCircle2,
  Clock,
  FileText,
  MessageSquare,
  ArrowLeft
} from "lucide-react"

export default function ActivityView({ history, onClearHistory, onClose }) {
  const [searchTerm, setSearchTerm] = useState("")
  const [expandedId, setExpandedId] = useState(null)

  const toggleExpand = (id) => {
    setExpandedId((prev) => (prev === id ? null : id))
  }

  const filteredHistory = history.filter(
    (item) =>
      item.query.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.filePath && item.filePath.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (item.response?.markdown && item.response.markdown.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 overflow-y-auto">
      {/* Header Bar */}
      <div className="bg-white border-b border-slate-200 px-8 py-5 flex items-center justify-between sticky top-0 z-20 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-600 flex items-center justify-center text-white shadow-sm">
            <Activity size={20} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900">Activity & Query History</h1>
              <span className="px-2 py-0.5 rounded-full text-xs font-mono font-medium bg-purple-50 text-purple-700 border border-purple-200">
                {history.length} Queries Tracked
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Audit log of all queries submitted to Micron, generated markdown & MCP code sanitization
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {history.length > 0 && (
            <button
              onClick={onClearHistory}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 text-slate-600 hover:text-red-600 hover:bg-red-50 hover:border-red-200 text-xs font-semibold transition-colors"
            >
              <Trash2 size={13} />
              Clear History
            </button>
          )}
          <button
            onClick={onClose}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold transition-colors shadow-xs"
          >
            <ArrowLeft size={14} />
            Back to Chat
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="p-8 max-w-5xl mx-auto w-full space-y-6">
        {/* Search & Stats Bar */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="relative flex-1 w-full">
            <Search size={15} className="absolute left-3.5 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search query history, target paths or responses..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#10a37f]/50"
            />
          </div>
          <div className="text-xs text-slate-500 font-medium whitespace-nowrap">
            Showing <strong>{filteredHistory.length}</strong> of <strong>{history.length}</strong> items
          </div>
        </div>

        {/* Query History List */}
        {filteredHistory.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center space-y-3 shadow-xs">
            <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-400 mx-auto">
              <MessageSquare size={20} />
            </div>
            <h3 className="text-sm font-semibold text-slate-800">No activity logs found</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              {searchTerm
                ? "No queries match your search term. Try resetting the filter."
                : "Submit queries in the chat view to start recording activity history."}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredHistory.map((item, index) => {
              const isExpanded = expandedId === item.id || index === 0
              return (
                <div
                  key={item.id}
                  className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden transition-all"
                >
                  {/* Header Row (Click to toggle expand) */}
                  <div
                    onClick={() => toggleExpand(item.id)}
                    className="p-4 flex items-center justify-between cursor-pointer hover:bg-slate-50/80 transition-colors"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-8 h-8 rounded-lg bg-[#10a37f]/10 text-[#10a37f] flex items-center justify-center font-semibold text-xs shrink-0">
                        #{filteredHistory.length - index}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="text-sm font-bold text-slate-900 truncate">{item.query}</h3>
                          {item.filePath && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-100 text-slate-600 border border-slate-200 truncate max-w-[200px]">
                              {item.filePath}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-3 text-[11px] text-slate-400 mt-0.5">
                          <span className="flex items-center gap-1">
                            <Clock size={11} /> {item.timestamp}
                          </span>
                          {item.response?.trace_id && (
                            <span className="font-mono text-purple-600">
                              Trace: {item.response.trace_id.slice(0, 8)}...
                            </span>
                          )}
                          {item.response?.citations && (
                            <span className="text-emerald-700 font-medium">
                              {item.response.citations.length} Citations Applied
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button className="p-1 text-slate-400 hover:text-slate-600">
                        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </button>
                    </div>
                  </div>

                  {/* Expanded Response Details Body */}
                  {isExpanded && item.response && (
                    <div className="border-t border-slate-100 bg-slate-50/50 p-5 space-y-4 text-xs text-slate-800">
                      {/* Response Markdown */}
                      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-2">
                        <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                          Generated Documentation Response
                        </p>
                        <div className="prose prose-sm max-w-none text-slate-800 whitespace-pre-wrap leading-relaxed font-sans">
                          {item.response.markdown}
                        </div>
                      </div>

                      {/* Sanitized Code Box */}
                      {item.response.sanitized_code && (
                        <div className="bg-slate-900 text-slate-100 p-4 rounded-xl font-mono text-[11px] overflow-x-auto shadow-inner border border-slate-800">
                          <div className="flex items-center gap-1.5 text-slate-400 border-b border-slate-800 pb-2 mb-2">
                            <FileCode size={13} className="text-[#10a37f]" />
                            <span>MCP Sanitized Code Context</span>
                          </div>
                          <pre>{item.response.sanitized_code}</pre>
                        </div>
                      )}

                      {/* Applied Citations & Rules */}
                      {item.response.citations && item.response.citations.length > 0 && (
                        <div className="bg-emerald-50 border border-emerald-200/80 p-3 rounded-lg space-y-2">
                          <p className="font-semibold text-emerald-900 flex items-center gap-1.5">
                            <CheckCircle2 size={13} className="text-[#10a37f]" />
                            <span>Applied RAG Business Process Rules</span>
                          </p>
                          <div className="flex flex-wrap gap-1.5">
                            {item.response.citations.map((cite, i) => (
                              <span
                                key={i}
                                className="inline-flex items-center gap-1 bg-white text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded font-mono text-[10px]"
                              >
                                <Tag size={10} />
                                {cite}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
