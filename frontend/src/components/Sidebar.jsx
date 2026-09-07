import { useState, useEffect } from "react"
import { LayoutDashboard, Activity, PenSquare, Plus, FolderOpen, RefreshCw, Loader2 } from "lucide-react"
import FileTree from "./FileTree"

export default function Sidebar({ selectedPath, onSelectFile, onNewChat, onOpenDashboard, onOpenActivity }) {
  const [rootName, setRootName]   = useState("passman-main")
  const [tree, setTree]           = useState(null)
  const [loading, setLoading]     = useState(false)

  const loadProjectFiles = async () => {
    try {
      setLoading(true)
      const res = await fetch("http://localhost:8000/api/v1/projects/passman-main/files", {
        headers: { "X-Tenant-ID": "default-tenant" }
      })
      if (res.ok) {
        const data = await res.json()
        setTree(data)
      }
    } catch (err) {
      console.error("Failed to load project files", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProjectFiles()
  }, [])

  return (
    <aside className="w-[220px] shrink-0 bg-[#202123] flex flex-col h-full text-[#ececec]">
      {/* Top: New Chat */}
      <div className="flex items-center justify-between px-3 pt-3 pb-2">
        <button
          onClick={onNewChat}
          className="flex items-center gap-2 text-sm text-[#ececec] hover:bg-white/10 rounded-md px-2 py-1.5 transition-colors font-medium"
        >
          <PenSquare size={16} />
          New Chat
        </button>
        <button onClick={onNewChat} className="p-1.5 rounded-md hover:bg-white/10 transition-colors">
          <Plus size={16} />
        </button>
      </div>

      {/* Directory section */}
      <div className="flex flex-col px-3 py-2 flex-1 min-h-0">
        {/* Header row */}
        <div className="flex items-center justify-between mb-2">
          <p className="text-[10px] uppercase tracking-widest text-[#8e8ea0] font-semibold px-1">
            Directory
          </p>
          <button
            onClick={loadProjectFiles}
            title="Refresh folder"
            className="p-1 rounded hover:bg-white/10 text-[#8e8ea0] hover:text-[#ececec] transition-colors"
          >
            <RefreshCw size={11} className={loading ? "animate-spin" : ""} />
          </button>
        </div>

        {/* Loading spinner */}
        {loading && (
          <div className="flex items-center gap-2 px-2 py-3">
            <Loader2 size={14} className="text-[#10a37f] animate-spin" />
            <span className="text-xs text-[#8e8ea0]">Reading folder…</span>
          </div>
        )}

        {/* Root label + tree */}
        {rootName && !loading && tree && (
          <div className="flex flex-col min-h-0 flex-1">
            {/* Root folder row */}
            <div className="flex items-center gap-1.5 px-1 py-1 mb-0.5">
              <FolderOpen size={13} className="text-[#10a37f] shrink-0" />
              <span className="text-[11px] font-semibold text-[#ececec] truncate">{rootName}</span>
            </div>
            {/* Scrollable tree */}
            <div className="overflow-y-auto flex-1 pr-1">
              <FileTree tree={tree} selectedPath={selectedPath} onSelectFile={onSelectFile} />
            </div>
          </div>
        )}
      </div>

      {/* Bottom nav */}
      <div className="border-t border-white/10 pt-2 pb-1 px-2 space-y-0.5">
        {/* Admin Dashboard Trigger */}
        <button
          onClick={onOpenDashboard}
          className="flex items-center gap-3 w-full text-sm text-[#10a37f] font-semibold hover:bg-white/10 rounded-md px-2 py-2 transition-colors"
        >
          <LayoutDashboard size={16} />
          Admin Dashboard
        </button>

        <button
          onClick={onOpenActivity}
          className="flex items-center gap-3 w-full text-sm text-[#ececec] hover:bg-white/10 rounded-md px-2 py-2 transition-colors"
        >
          <Activity size={16} className="opacity-80" />
          Activity
        </button>

        {/* User profile */}
        <div className="flex items-center gap-2 px-2 py-2 mt-1 rounded-md hover:bg-white/10 cursor-pointer transition-colors">
          <div className="w-7 h-7 rounded-full bg-[#3d5afb] flex items-center justify-center text-white text-xs font-bold shrink-0">
            E
          </div>
          <span className="text-sm truncate">Employee</span>
        </div>
      </div>
    </aside>
  )
}



