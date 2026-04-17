import React, { useEffect, useState } from 'react'
import { useAppStore } from './store'
import axios from 'axios'
import { MessageCircle, Briefcase, Settings, Plus, Send, MoreVertical, Paperclip } from 'lucide-react'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8765/api'
console.log('Final API_BASE being used:', API_BASE);

interface Message {
  id: string;
  role: string;
  content: string;
}

function App() {
  const { currentWorkspace, setCurrentWorkspace, workspaces, setWorkspaces, projects, setProjects } = useAppStore()
  const [activeView, setActiveView] = useState<'chat' | 'settings' | 'project'>('chat')
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const [conversations, setConversations] = useState<any[]>([])
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [isCreatingInitial, setIsCreatingInitial] = useState(false)
  const [isComposing, setIsComposing] = useState(false)
  const [projectLogs, setProjectLogs] = useState<any[]>([])
  const scrollRef = React.useRef<HTMLDivElement>(null)

  // 取得專案日誌
  useEffect(() => {
    if (selectedProjectId && activeView === 'project') {
      axios.get(`${API_BASE}/work-logs/?project_id=${selectedProjectId}`).then(res => {
        setProjectLogs(res.data)
      })
    }
  }, [selectedProjectId, activeView])

  // 捲動到底部
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  useEffect(() => {
    // Initial data fetch
    console.log('Fetching workspaces from:', `${API_BASE}/workspaces/`);
    axios.get(`${API_BASE}/workspaces/`)
      .then(res => {
        setWorkspaces(res.data)
        if (res.data.length > 0 && !currentWorkspace) {
          setCurrentWorkspace(res.data[0])
        }
      })
      .catch(err => console.error('Failed to fetch workspaces:', err));
  }, [])

  useEffect(() => {
    if (currentWorkspace && !isCreatingInitial) {
      axios.get(`${API_BASE}/projects/?workspace_id=${currentWorkspace.id}`).then(res => {
        setProjects(res.data)
      })
      
      axios.get(`${API_BASE}/conversations/?workspace_id=${currentWorkspace.id}`).then(res => {
        setConversations(res.data)
        if (res.data.length > 0) {
          setCurrentConversationId(res.data[0].id)
        } else if (!isCreatingInitial) {
          // 防止重複建立
          setIsCreatingInitial(true)
          axios.post(`${API_BASE}/conversations/`, { 
            workspace_id: currentWorkspace.id, 
            title: 'New Conversation' 
          }).then(c => {
             setConversations([c.data])
             setCurrentConversationId(c.data.id)
          }).finally(() => {
             setIsCreatingInitial(false)
          })
        }
      })
    }
  }, [currentWorkspace])

  useEffect(() => {
    if (currentConversationId) {
      axios.get(`${API_BASE}/conversations/${currentConversationId}/messages/`).then(res => {
        setMessages(res.data)
      })
    }
  }, [currentConversationId])

  const handleSend = async () => {
    if (loading) return;
    console.log('handleSend triggered');
    if (!input.trim()) {
      console.log('Input is empty');
      return;
    }
    if (!currentConversationId || !currentWorkspace) {
      console.log('Missing conversation or workspace', { currentConversationId, currentWorkspace });
      return;
    }

    const currentInput = input;
    const userMsg = { id: Date.now().toString(), role: 'user', content: currentInput }
    setMessages(prev => [...prev, userMsg as Message])
    setInput('')
    setLoading(true)

    console.log('Sending request to:', `${API_BASE}/chat/`);
    try {
      const res = await axios.post(`${API_BASE}/chat/`, {
        conversation_id: currentConversationId,
        message: currentInput,
        workspace_id: currentWorkspace.id
      })
      console.log('Response status:', res.status);
      console.log('Response full data:', res.data);
      if (res.data) {
        setMessages(prev => [...prev, res.data])
      }
    } catch (error: any) {
      console.error('API Error:', error.response?.data || error.message);
      // 如果失敗，把訊息還給輸入框
      setInput(currentInput);
      alert(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar */}
      <div className="w-64 border-r bg-muted/30 flex flex-col">
        <div className="p-4 border-b flex items-center justify-between">
          <select 
            className="bg-transparent font-bold focus:outline-none"
            value={currentWorkspace?.id}
            onChange={(e) => {
              const ws = workspaces.find(w => w.id === e.target.value)
              if (ws) setCurrentWorkspace(ws)
            }}
          >
            {workspaces.map(ws => (
              <option key={ws.id} value={ws.id}>{ws.name}</option>
            ))}
          </select>
          <Settings 
            className={cn(
              "w-4 h-4 cursor-pointer transition-colors",
              activeView === 'settings' ? "text-blue-600" : "text-muted-foreground hover:text-foreground"
            )}
            onClick={() => setActiveView('settings')}
          />
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          <div className="mb-4">
            <div className="flex items-center justify-between px-2 mb-2 text-xs font-semibold text-muted-foreground uppercase">
              <span>Conversations</span>
              <Plus className="w-4 h-4 cursor-pointer" onClick={() => {
                 if (currentWorkspace) {
                   axios.post(`${API_BASE}/conversations/`, { workspace_id: currentWorkspace.id, title: 'New Conversation' }).then(c => {
                      setConversations(prev => [c.data, ...prev])
                      setCurrentConversationId(c.data.id)
                      setActiveView('chat')
                   })
                 }
              }}/>
            </div>
            {conversations.map(c => (
              <div 
                key={c.id}
                onClick={() => {
                  setCurrentConversationId(c.id)
                  setActiveView('chat')
                }}
                className={cn(
                  "px-2 py-1.5 rounded-md cursor-pointer text-sm mb-1 truncate",
                  currentConversationId === c.id && activeView === 'chat' ? "bg-accent text-accent-foreground" : "hover:bg-accent/50"
                )}
              >
                {c.title || 'Untitled'}
              </div>
            ))}
          </div>

          <div>
            <div className="flex items-center justify-between px-2 mb-2 text-xs font-semibold text-muted-foreground uppercase">
              <span>Projects</span>
              <Plus className="w-4 h-4 cursor-pointer" onClick={() => {
                if (currentWorkspace) {
                  const name = prompt('Project Name?');
                  if (name) {
                    axios.post(`${API_BASE}/projects/`, { 
                      workspace_id: currentWorkspace.id, 
                      name: name 
                    }).then(res => {
                      setProjects([...projects, res.data]);
                    });
                  }
                }
              }}/>
            </div>
            {projects.length > 0 ? (
              projects.map(p => (
                <div 
                  key={p.id} 
                  onClick={() => {
                    console.log('Project clicked:', p.name, p.id);
                    setSelectedProjectId(p.id)
                    setActiveView('project')
                  }}
                  className={cn(
                    "px-2 py-1.5 text-sm flex items-center gap-2 rounded-md cursor-pointer transition-colors",
                    selectedProjectId === p.id && activeView === 'project' ? "bg-accent text-accent-foreground" : "hover:bg-accent/50"
                  )}
                >
                  <Briefcase className="w-3 h-3" />
                  <span className="truncate">{p.name}</span>
                </div>
              ))
            ) : (
              <div className="px-2 py-1.5 text-xs text-muted-foreground italic">
                No projects yet. Click + to create.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Area */}
      <div className="flex-1 flex flex-col">
        {activeView === 'chat' ? (
          <>
            <div className="p-4 border-b flex items-center justify-between">
              <h2 className="font-semibold">{conversations.find(c => c.id === currentConversationId)?.title || 'Chat'}</h2>
              <MoreVertical className="w-4 h-4 text-muted-foreground" />
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4" ref={scrollRef}>
              {messages.map((m, idx) => (
                <div key={m.id || idx} className={cn("flex", m.role === 'user' ? "justify-end" : "justify-start")}>
                  <div className={cn(
                    "max-w-[80%] rounded-lg px-4 py-2",
                    m.role === 'user' ? "bg-blue-600 text-white" : "bg-muted"
                  )}>
                    {m.content || (m.role === 'assistant' ? "..." : "")}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-muted rounded-lg px-4 py-2 animate-pulse">
                    Assistant is thinking...
                  </div>
                </div>
              )}
            </div>

            <div className="p-4 border-t relative z-50">
              <div className="flex items-center gap-2 max-w-4xl mx-auto bg-muted rounded-xl p-2 focus-within:ring-1 ring-ring relative">
                <Paperclip className="w-5 h-5 text-muted-foreground cursor-pointer ml-2" />
                <input 
                  type="text" 
                  placeholder="Ask anything..." 
                  className="flex-1 bg-transparent border-none focus:outline-none p-2 text-foreground"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onCompositionStart={() => setIsComposing(true)}
                  onCompositionEnd={() => setIsComposing(false)}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && !isComposing) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  disabled={loading}
                />
                <button 
                  onClick={(e) => {
                    e.preventDefault();
                    handleSend();
                  }}
                  disabled={loading}
                  className={cn(
                    "bg-blue-600 text-white p-2 rounded-lg transition-colors relative z-50 cursor-pointer",
                    loading ? "opacity-50 cursor-not-allowed" : "hover:bg-blue-700"
                  )}
                  style={{ minWidth: '40px', minHeight: '40px' }}
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </>
        ) : activeView === 'settings' ? (
          <div className="flex-1 overflow-y-auto p-8">
            <h2 className="text-2xl font-bold mb-6">系統設定</h2>
            <div className="max-w-2xl space-y-6">
              <div className="p-4 border rounded-lg bg-muted/20">
                <h3 className="font-semibold mb-2">模型資訊</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">LLM Model:</span>
                    <span className="font-mono">gemini-2.0-flash-exp</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Embedding Model:</span>
                    <span className="font-mono">BAAI/bge-m3</span>
                  </div>
                </div>
              </div>

              <div className="p-4 border rounded-lg bg-muted/20">
                <h3 className="font-semibold mb-2">API 狀態</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Backend API:</span>
                    <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs">Connected</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Gemini API Key:</span>
                    <span>{import.meta.env.VITE_API_BASE_URL ? 'Cloud Configured' : 'Local .env'}</span>
                  </div>
                </div>
              </div>

              <div className="p-4 border rounded-lg bg-muted/20">
                <h3 className="font-semibold mb-2">關於系統</h3>
                <p className="text-sm text-muted-foreground">
                  個人 AI 工作助理 v1.0.0 (Local-First Architecture)
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto p-8">
            {projects.find(p => p.id === selectedProjectId) ? (
              <div className="max-w-4xl mx-auto">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-3xl font-bold">{projects.find(p => p.id === selectedProjectId)?.name}</h2>
                    <p className="text-muted-foreground">專案詳情與工作日誌</p>
                  </div>
                  <div className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium uppercase">
                    {projects.find(p => p.id === selectedProjectId)?.status}
                  </div>
                </div>

                <div className="space-y-8">
                  <section>
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                      <MessageCircle className="w-5 h-5" />
                      工作日誌
                    </h3>
                    <div className="space-y-4">
                      {projectLogs.length > 0 ? (
                        projectLogs.map(log => (
                          <div key={log.id} className="p-4 border rounded-lg bg-card shadow-sm">
                            <div className="flex justify-between items-start mb-2">
                              <span className="text-sm font-medium text-muted-foreground">{log.log_date}</span>
                              <span className="text-xs px-2 py-0.5 bg-muted rounded">{log.iso_week}</span>
                            </div>
                            <p className="text-sm whitespace-pre-wrap">{log.content}</p>
                          </div>
                        ))
                      ) : (
                        <div className="text-center py-12 border border-dashed rounded-lg text-muted-foreground">
                          尚無工作日誌。您可以透過對話請 AI 幫您記錄！
                        </div>
                      )}
                    </div>
                  </section>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                請選擇一個專案以查看詳情
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default App
