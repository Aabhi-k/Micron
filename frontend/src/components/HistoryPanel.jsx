import { useState, useEffect } from "react";
import { MessageSquare, Clock } from "lucide-react";

export default function HistoryPanel({ projectId, onSelectHistory }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!projectId) return;

    fetch(`http://localhost:8000/api/v1/chat/history/${projectId}`, {
      headers: {
        "X-Tenant-ID": "default-tenant"
      }
    })
      .then(res => res.json())
      .then(data => {
        setHistory(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch history:", err);
        setLoading(false);
      });
  }, [projectId]);

  if (loading) {
    return <div className="p-4 text-[#ececec] text-sm animate-pulse">Loading history...</div>;
  }

  if (history.length === 0) {
    return (
      <div className="p-4 text-[#ececec] text-sm text-center flex flex-col items-center opacity-50 mt-10">
        <Clock size={24} className="mb-2" />
        No past audits found.
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      <div className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-[#10a37f] border-b border-[#ececec]/10 flex items-center gap-2">
        <MessageSquare size={14} />
        Past Audits
      </div>
      <div className="flex flex-col divide-y divide-[#ececec]/5">
        {history.map((item) => (
          <button
            key={item.id}
            onClick={() => onSelectHistory(item)}
            className="text-left px-4 py-3 hover:bg-[#2a2b32] transition-colors focus:outline-none"
          >
            <div className="text-sm font-semibold text-[#ececec] truncate mb-1">
              {item.query}
            </div>
            <div className="text-[10px] text-[#ececec]/50 flex justify-between items-center">
              <span>{item.ast_metadata?.function_name || "General"}</span>
              <span>{new Date(item.created_at).toLocaleDateString()}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
