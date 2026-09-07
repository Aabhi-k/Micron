import { ChevronDown, LayoutDashboard, MessageSquare } from "lucide-react"

export default function ChatHeader({ viewMode, onToggleView }) {
  return (
    <div className="flex items-center justify-between h-12 px-4 border-b border-gray-200 shrink-0 bg-white">
      <button className="flex items-center gap-1 font-semibold text-gray-900 hover:bg-gray-100 rounded-lg px-2 py-1 transition-colors">
        <span className="text-base">Micron</span>
        <ChevronDown size={14} className="text-gray-500 ml-0.5" />
      </button>

      <button
        onClick={onToggleView}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-gray-100 hover:bg-gray-200 text-gray-800 transition-colors border border-gray-200"
      >
        {viewMode === "chat" ? (
          <>
            <LayoutDashboard size={14} className="text-[#10a37f]" />
            <span>Admin Dashboard</span>
          </>
        ) : (
          <>
            <MessageSquare size={14} className="text-[#10a37f]" />
            <span>Chat View</span>
          </>
        )}
      </button>
    </div>
  )
}

