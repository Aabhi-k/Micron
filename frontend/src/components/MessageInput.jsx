import { useState } from "react"
import { ArrowUp, Loader2 } from "lucide-react"

export default function MessageInput({ onSendMessage, loading }) {
  const [value, setValue] = useState("")

  const handleSubmit = (e) => {
    e?.preventDefault()
    if (!value.trim() || loading) return
    onSendMessage(value.trim())
    setValue("")
  }

  return (
    <div className="px-10 pb-6">
      <form onSubmit={handleSubmit} className="flex items-center bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm focus-within:ring-2 focus-within:ring-gray-300 transition-all">
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Message Micron..."
          disabled={loading}
          className="flex-1 bg-transparent outline-none text-sm text-gray-700 placeholder-gray-400 disabled:opacity-50"
        />
        <button
          type="submit"
          className={`ml-2 w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
            value.trim() && !loading
              ? "bg-gray-900 text-white hover:bg-gray-700"
              : "bg-gray-200 text-gray-400 cursor-not-allowed"
          }`}
          disabled={!value.trim() || loading}
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <ArrowUp size={16} />}
        </button>
      </form>
    </div>
  )
}
