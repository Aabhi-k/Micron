import { useState, useRef, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import ChatHeader from './components/ChatHeader'
import GreetingSection from './components/GreetingSection'
import MessageInput from './components/MessageInput'
import AdminDashboard from './components/AdminDashboard'
import ActivityView from './components/ActivityView'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { FileCode, Tag, CheckCircle2, AlertCircle } from 'lucide-react'

// Initial pre-populated history items for demonstration
const initialHistory = [
  {
    id: 'hist-1',
    query: 'Explain legacy authentication token validation',
    filePath: 'src/api/auth.js',
    timestamp: '10 mins ago',
    response: {
      markdown: '# Legacy Authentication Analysis\n\nThe legacy authentication routine checks Bearer tokens against hardcoded session keys.',
      sanitized_code: 'function validateToken(token) {\n    // Redacted secret verification\n    return token.startsWith("eyJhbGci");\n}',
      citations: ['BPD Rule 1: Validate input query', 'BPD Rule 2: Enforce Token Expiry Policy'],
      trace_id: 'tr-9a8b1c4d-5e6f-7a8b'
    }
  },
  {
    id: 'hist-2',
    query: 'Check database transaction isolation level',
    filePath: 'backend/main.py',
    timestamp: '25 mins ago',
    response: {
      markdown: '# Transaction Isolation Audit\n\nThe database connection operates under standard Read Committed isolation level.',
      sanitized_code: 'async font_db_connect():\n    # Redacted credentials\n    conn = await pool.acquire()\n    return conn',
      citations: ['BPD Rule 4: Data Concurrency Standard'],
      trace_id: 'tr-7d6e5f4c-3b2a-1f0e'
    }
  }
]

function App() {
  const [viewMode, setViewMode] = useState('chat') // 'chat' | 'dashboard' | 'activity'
  const [selectedPath, setSelectedPath] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activityHistory, setActivityHistory] = useState(initialHistory)
  const chatEndRef = useRef(null)

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    if (viewMode === 'chat') {
      scrollToBottom()
    }
  }, [messages, loading, viewMode])

  const handleSendMessage = async (queryText) => {
    if (!queryText.trim() || loading) return

    const userMessage = { role: 'user', content: queryText }
    setMessages((prev) => [...prev, userMessage])
    setLoading(true)
    setError(null)

    try {
      const response = await fetch('http://localhost:8000/api/v1/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-ID': 'default-tenant'
        },
        body: JSON.stringify({
          project_id: 'passman-main',
          query: queryText,
          file_path: selectedPath || undefined,
        }),
      })

      if (!response.ok) {
        throw new Error(`Server returned status ${response.status}`)
      }

      const data = await response.json()
      
      // Map the backend's response format to what the UI expects
      const formattedData = {
        markdown: data.response,
        sanitized_code: data.ast_metadata ? `// Extracted from: ${data.ast_metadata.file}\n// Function: ${data.ast_metadata.function_name}\n// Redactions applied: ${data.ast_metadata.redactions.join(', ') || 'None'}` : null,
        citations: [],
        trace_id: data.tenant_id
      }

      const assistantMessage = {
        role: 'assistant',
        data: formattedData,
      }
      setMessages((prev) => [...prev, assistantMessage])

      // Record query + response in Activity history log
      const historyItem = {
        id: Date.now().toString(),
        query: queryText,
        filePath: selectedPath || '',
        timestamp: 'Just now',
        response: formattedData,
      }
      setActivityHistory((prev) => [historyItem, ...prev])
    } catch (err) {
      console.error('API call error:', err)
      setError(err.message || 'Failed to connect to backend service')
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          error: err.message || 'Could not reach backend server at http://localhost:8000/api/v1/chat/generate',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleNewChat = () => {
    setMessages([])
    setError(null)
    setViewMode('chat')
  }

  const handleSelectHistory = (hist) => {
    // Clear current chat
    setMessages([])
    setSelectedPath('')

    // Insert the historic query
    const userMessage = { role: 'user', content: hist.query }
    
    // Format the historic response to match backend endpoint output
    const formattedData = {
      markdown: hist.response,
      sanitized_code: hist.ast_metadata ? `// Extracted from: ${hist.ast_metadata.file}\n// Function: ${hist.ast_metadata.function_name}\n// Redactions applied: ${hist.ast_metadata.redactions.join(', ') || 'None'}` : null,
      citations: [],
      trace_id: null
    }

    const assistantMessage = {
      role: 'assistant',
      data: formattedData,
    }

    setMessages([userMessage, assistantMessage])
    setViewMode('chat')
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-white">
      {/* Left dark sidebar */}
      <Sidebar
        selectedPath={selectedPath}
        onSelectFile={(path) => setSelectedPath(path)}
        onNewChat={handleNewChat}
        onOpenDashboard={() => setViewMode('dashboard')}
        onOpenActivity={() => setViewMode('activity')}
        onSelectHistory={handleSelectHistory}
      />

      {/* Main content area */}
      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        {viewMode === 'dashboard' ? (
          <AdminDashboard onClose={() => setViewMode('chat')} />
        ) : viewMode === 'activity' ? (
          <ActivityView
            history={activityHistory}
            onClearHistory={() => setActivityHistory([])}
            onClose={() => setViewMode('chat')}
          />
        ) : (
          <>
            {/* Green radial glow background */}
            <div
              className="absolute inset-0 pointer-events-none"
              style={{
                background:
                  'radial-gradient(ellipse 60% 70% at 85% 20%, rgba(167,243,208,0.45) 0%, transparent 70%)',
              }}
            />

            {/* Top header */}
            <ChatHeader
              viewMode={viewMode}
              onToggleView={() => setViewMode((v) => (v === 'chat' ? 'dashboard' : 'chat'))}
            />

            {/* Main scrollable content area */}
            <div className="flex flex-col flex-1 overflow-y-auto relative z-10">
              {messages.length === 0 ? (
                /* Greeting section */
                <GreetingSection />
              ) : (
                <div className="flex-1 px-8 py-6 max-w-4xl mx-auto w-full space-y-6">
                  {messages.map((msg, index) => (
                    <div key={index} className="space-y-3">
                      {msg.role === 'user' ? (
                        <div className="flex justify-end">
                          <div className="bg-[#202123] text-white px-4 py-2.5 rounded-2xl max-w-[80%] text-sm shadow-sm">
                            {msg.content}
                          </div>
                        </div>
                      ) : (
                        <div className="flex gap-4 items-start">
                          <div className="w-8 h-8 rounded-full bg-[#10a37f] flex items-center justify-center text-white text-xs font-bold shrink-0 mt-1 shadow-sm">
                            M
                          </div>
                          <div className="flex-1 bg-white/80 backdrop-blur-sm border border-gray-200/80 rounded-2xl p-5 shadow-sm space-y-4 text-sm text-gray-800">
                            {msg.error ? (
                              <div className="flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-lg border border-red-200">
                                <AlertCircle size={16} />
                                <span>{msg.error}</span>
                              </div>
                            ) : (
                              <>
                                {/* Markdown text output */}
                                <div className="prose prose-sm max-w-none">
                                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                    {msg.data?.markdown}
                                  </ReactMarkdown>
                                </div>

                                {/* Sanitized Code Box if present */}
                                {msg.data?.sanitized_code && (
                                  <div className="bg-gray-900 text-gray-100 rounded-xl p-4 font-mono text-xs overflow-x-auto border border-gray-800 shadow-inner">
                                    <div className="flex items-center justify-between text-gray-400 border-b border-gray-800 pb-2 mb-3">
                                      <div className="flex items-center gap-1.5 font-sans text-[11px]">
                                        <FileCode size={14} className="text-[#10a37f]" />
                                        <span>Sanitized Code Context</span>
                                      </div>
                                    </div>
                                    <pre>{msg.data.sanitized_code}</pre>
                                  </div>
                                )}

                                {/* Applied rules / citations if present */}
                                {msg.data?.citations && msg.data.citations.length > 0 && (
                                  <div className="bg-emerald-50/70 border border-emerald-200/70 rounded-xl p-3 text-xs space-y-1.5">
                                    <div className="font-semibold text-emerald-900 flex items-center gap-1.5">
                                      <CheckCircle2 size={14} className="text-[#10a37f]" />
                                      <span>Applied Rules & Citations</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1.5 pt-1">
                                      {msg.data.citations.map((cite, i) => (
                                        <span
                                          key={i}
                                          className="inline-flex items-center gap-1 bg-emerald-100/80 text-emerald-800 px-2 py-0.5 rounded-md font-mono text-[11px]"
                                        >
                                          <Tag size={10} />
                                          {cite}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Trace ID footer */}
                                {msg.data?.trace_id && (
                                  <div className="text-[10px] text-gray-400 font-mono pt-2 border-t border-gray-100">
                                    Trace ID: {msg.data.trace_id}
                                  </div>
                                )}
                              </>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}

                  {loading && (
                    <div className="flex gap-4 items-start animate-pulse">
                      <div className="w-8 h-8 rounded-full bg-[#10a37f] flex items-center justify-center text-white text-xs font-bold shrink-0">
                        M
                      </div>
                      <div className="bg-white/80 border border-gray-200 rounded-2xl p-4 text-sm text-gray-500 flex items-center gap-2 shadow-sm">
                        <div className="w-2 h-2 rounded-full bg-[#10a37f] animate-ping" />
                        <span>Micron is thinking and fetching documentation rules...</span>
                      </div>
                    </div>
                  )}

                  <div ref={chatEndRef} />
                </div>
              )}

              {/* Message input */}
              <MessageInput onSendMessage={handleSendMessage} loading={loading} />
            </div>
          </>
        )}
      </main>
    </div>
  )
}

export default App



