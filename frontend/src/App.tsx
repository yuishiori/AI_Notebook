import React, { useEffect, useState } from 'react'
import { useAppStore } from './store'
import axios from 'axios'
import { MessageCircle, Briefcase, Settings, Plus, Send, MoreVertical, Paperclip, LogOut } from 'lucide-react'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { GoogleLogin, googleLogout } from '@react-oauth/google'

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8765/api'

interface Message {
  id: string;
  role: string;
  content: string;
}

function App() {
  const { user, token, setAuth, logout, currentWorkspace, setCurrentWorkspace, workspaces, setWorkspaces, projects, setProjects } = useAppStore()
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

  // Axios Interceptor for Auth
  useEffect(() => {
    const interceptor = axios.interceptors.request.use((config) => {
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
    return () => axios.interceptors.request.eject(interceptor);
  }, [token]);

  const handleLoginSuccess = async (credentialResponse: any) => {
    console.log('Google Login Success, received credential');
    try {
      const res = await axios.post(`${API_BASE}/auth/google`, {
        id_token: credentialResponse.credential
      });
      console.log('Backend Auth Success:', res.data);
      const { access_token } = res.data;
      
      // Get user info
      const userRes = await axios.get(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${access_token}` }
      });
      console.log('User Profile Fetched:', userRes.data);
      
      setAuth(userRes.data, access_token);
    } catch (error: any) {
      console.error('Backend Login failed:', error.response?.data || error.message);
      alert(`Login failed: ${error.response?.data?.detail || error.message}`);
    }
  };

  // 取得專案日誌
  useEffect(() => {
    if (token && selectedProjectId && activeView === 'project') {
      axios.get(`${API_BASE}/work-logs/?project_id=${selectedProjectId}`).then(res => {
        setProjectLogs(res.data)
      }).catch(err => {
        if (err.response?.status === 401) logout();
      });
    }
  }, [selectedProjectId, activeView, token]);

  // 捲動到底部
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  useEffect(() => {
    if (!token) return;
    // Initial data fetch
    axios.get(`${API_BASE}/workspaces/`)
      .then(res => {
        setWorkspaces(res.data)
        if (res.data.length > 0 && !currentWorkspace) {
          setCurrentWorkspace(res.data[0])
        }
      })
      .catch(err => {
        console.error('Failed to fetch workspaces:', err);
        if (err.response?.status === 401) logout();
      });
  }, [token])

  useEffect(() => {
    if (token && currentWorkspace && !isCreatingInitial) {
      axios.get(`${API_BASE}/projects/?workspace_id=${currentWorkspace.id}`).then(res => {
        setProjects(res.data)
      })
      
      axios.get(`${API_BASE}/conversations/?workspace_id=${currentWorkspace.id}`).then(res => {
        setConversations(res.data)
        if (res.data.length > 0) {
          setCurrentConversationId(res.data[0].id)
        } else if (!isCreatingInitial) {
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
  }, [currentWorkspace, token])

  useEffect(() => {
    if (token && currentConversationId) {
      axios.get(`${API_BASE}/conversations/${currentConversationId}/messages/`).then(res => {
        setMessages(res.data)
      })
    }
  }, [currentConversationId, token])

  const handleSend = async () => {
    if (loading || !token) return;
    if (!input.trim()) return;
    if (!currentConversationId || !currentWorkspace) return;

    const currentInput = input;
    const userMsg = { id: Date.now().toString(), role: 'user', content: currentInput }
    setMessages(prev => [...prev, userMsg as Message])
    setInput('')
    setLoading(true)

    try {
      const res = await axios.post(`${API_BASE}/chat/`, {
        conversation_id: currentConversationId,
        message: currentInput,
        workspace_id: currentWorkspace.id
      })
      if (res.data) {
        setMessages(prev => [...prev, res.data])
      }
    } catch (error: any) {
      console.error('API Error:', error.response?.data || error.message);
      setInput(currentInput);
      if (error.response?.status === 401) logout();
      else alert(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-muted/20">
        <div className="p-8 bg-card border rounded-2xl shadow-xl max-w-md w-full text-center">
          <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-blue-200">
             <MessageCircle className="text-white w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold mb-2">個人 AI 工作助理</h1>
          <p className="text-muted-foreground mb-8">請先登入以開始管理您的工作與生活</p>
          <div className="flex justify-center">
            <GoogleLogin 
              onSuccess={handleLoginSuccess}
              onError={() => alert('Login Failed')}
              useOneTap
            />
          </div>
          <p className="mt-8 text-xs text-muted-foreground">
            登入即代表您同意服務條款與隱私權政策
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar */}
      <div className="w-64 border-r bg-muted/30 flex flex-col">
        <div className="p-4 border-b flex items-center justify-between">
          <select 
            className="bg-transparent font-bold focus:outline-none max-w-[120px] truncate"
            value={currentWorkspace?.id}
            onChange={(e) => {
              const ws = workspaces.find(w => w.id === e.target.value)
              if (ws) {
                setCurrentWorkspace(ws);
                setActiveView('chat');
              }
            }}
          >
            {workspaces.map(ws => (
              <option key={ws.id} value={ws.id}>{ws.name}</option>
            ))}
          </select>
          <div className="flex items-center gap-2">
            <Settings 
              className={cn(
                "w-4 h-4 cursor-pointer transition-colors",
                activeView === 'settings' ? "text-blue-600" : "text-muted-foreground hover:text-foreground"
              )}
              onClick={() => setActiveView('settings')}
            />
          </div>
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
        
        {/* User Profile Area */}
        <div className="p-4 border-t flex items-center gap-3">
           <img src={user?.picture_url || ''} alt="" className="w-8 h-8 rounded-full border bg-muted" />
           <div className="flex-1 overflow-hidden">
              <p className="text-sm font-medium truncate">{user?.name}</p>
              <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
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
                <textarea 
                  placeholder="Ask anything..." 
                  className="flex-1 bg-transparent border-none focus:outline-none p-2 text-foreground resize-none max-h-40 overflow-y-auto"
                  rows={1}
                  value={input}
                  onChange={e => {
                    setInput(e.target.value);
                    // Auto resize
                    e.target.style.height = 'auto';
                    e.target.style.height = e.target.scrollHeight + 'px';
                  }}
                  onCompositionStart={() => setIsComposing(true)}
                  onCompositionEnd={() => setIsComposing(false)}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
                      e.preventDefault();
                      handleSend();
                      e.currentTarget.style.height = 'auto'; // Reset height
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
                <h3 className="font-semibold mb-4">帳戶管理</h3>
                <div className="flex items-center justify-between">
                   <div className="flex items-center gap-3">
                      <img src={user?.picture_url || ''} className="w-10 h-10 rounded-full" alt="" />
                      <div>
                         <p className="font-medium">{user?.name}</p>
                         <p className="text-sm text-muted-foreground">{user?.email}</p>
                      </div>
                   </div>
                   <button 
                     onClick={() => {
                        googleLogout();
                        logout();
                     }}
                     className="flex items-center gap-2 px-3 py-1.5 text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition-colors text-sm"
                   >
                     <LogOut className="w-4 h-4" />
                     登出
                   </button>
                </div>
              </div>

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
                <h3 className="font-semibold mb-2">關於系統</h3>
                <p className="text-sm text-muted-foreground">
                  個人 AI 工作助理 v1.1.0 (Multi-User Cloud Sync)
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
                  <div className="flex items-center gap-3">
                    <button 
                      onClick={() => {
                        if (currentWorkspace && selectedProjectId) {
                          const projectName = projects.find(p => p.id === selectedProjectId)?.name;
                          axios.post(`${API_BASE}/conversations/`, { 
                            workspace_id: currentWorkspace.id, 
                            project_id: selectedProjectId,
                            title: `${projectName} 專屬對話` 
                          }).then(c => {
                             setConversations(prev => [c.data, ...conversations])
                             setCurrentConversationId(c.data.id)
                             setActiveView('chat')
                          })
                        }
                      }}
                      className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                    >
                      <MessageCircle className="w-4 h-4" />
                      開啟專屬對話
                    </button>
                    <div className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium uppercase">
                      {projects.find(p => p.id === selectedProjectId)?.status}
                    </div>
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
