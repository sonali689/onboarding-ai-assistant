import { useState, useCallback, useEffect, useRef } from 'react'
import { Loader2 } from 'lucide-react'
import Sidebar       from './components/Sidebar'
import ChatWindow    from './components/ChatWindow'
import InputBar      from './components/InputBar'
import LoginPage     from './components/LoginPage'
import ResizeHandle  from './components/ResizeHandle'
import { askQuestionStream, loadChats, saveChat, deleteChat } from './api/chat'
import { useLang } from './contexts/LanguageContext'
import { useAuth } from './contexts/AuthContext'
import type { Message as Msg, ChatSession, ThinkingLevel, Source } from './types'

const uid = () => Math.random().toString(36).slice(2)

const newSession = (): ChatSession => ({
  id: uid(), title: 'New conversation', messages: [], date: new Date(),
})

const buildHistory = (msgs: Msg[]): { role: 'user' | 'assistant'; content: string }[] => {
  return msgs
    .filter(m => !m.loading)
    .slice(-6)
    .map(m => ({ role: m.role, content: m.content }))
}

const SIDEBAR_MIN     = 200
const SIDEBAR_MAX     = 420
const SIDEBAR_DEFAULT = 256

export default function App() {
  const { t, lang }                   = useLang()
  const { user, loading: authLoading } = useAuth()

  const [sessions,  setSessions]  = useState<ChatSession[]>([])
  const [activeId,  setActiveId]  = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [sidebarWidth, setSidebarWidth]     = useState(SIDEBAR_DEFAULT)
  const saveTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  const handleSidebarResize = useCallback((delta: number) => {
    setSidebarWidth(prev => {
      const next = prev + delta
      return Math.min(SIDEBAR_MAX, Math.max(SIDEBAR_MIN, next))
    })
  }, [])

  useEffect(() => {
    if (!user) {
      setSessions([])
      setActiveId('')
      return
    }

    const init = async () => {
      setHistoryLoading(true)
      const saved = await loadChats()

      if (saved.length > 0) {
        const restored: ChatSession[] = saved.map(c => ({
          id:       c.id,
          title:    c.title,
          date:     new Date(c.created_at),
          messages: (JSON.parse(c.messages) as Msg[]).map(m => ({
            ...m,
            timestamp: new Date(m.timestamp),
          })),
        }))
        setSessions(restored)
        setActiveId(restored[0].id)
      } else {
        const s = newSession()
        setSessions([s])
        setActiveId(s.id)
      }
      setHistoryLoading(false)
    }

    init()
  }, [user])

  const active   = sessions.find(s => s.id === activeId)
  const messages = active?.messages ?? []

  const autoSave = useCallback((session: ChatSession) => {
    if (!user || session.messages.length === 0) return
    clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(() => {
      saveChat(session.id, session.title, session.messages)
    }, 1000)
  }, [user])

  const patch = useCallback((id: string, fn: (s: ChatSession) => ChatSession) => {
    setSessions(prev => prev.map(s => {
      if (s.id !== id) return s
      const updated = fn(s)
      autoSave(updated)
      return updated
    }))
  }, [autoSave])

  const handleSend = async (question: string, level: ThinkingLevel) => {
    if (!activeId || isLoading) return
    setIsLoading(true)

    const historyForRequest = buildHistory(messages)

    const userMsg: Msg = {
      id: uid(), role: 'user', content: question,
      sources: [], source_type: null, timestamp: new Date(),
    }
    const assistantId = uid()
    const assistantMsg: Msg = {
      id: assistantId, role: 'assistant', content: '',
      sources: [], source_type: null, timestamp: new Date(), loading: true,
    }

    patch(activeId, s => ({
      ...s,
      title:    s.messages.length === 0 ? question.slice(0, 44) : s.title,
      messages: [...s.messages, userMsg, assistantMsg],
    }))

    const appendToken = (textChunk: string) => {
      patch(activeId, s => ({
        ...s,
        messages: s.messages.map(m =>
          m.id === assistantId
            ? { ...m, content: m.content + textChunk, loading: false }
            : m
        ),
      }))
    }

    const finalize = (sources: Source[], sourceType: 'company_data' | 'general_knowledge') => {
      patch(activeId, s => ({
        ...s,
        messages: s.messages.map(m =>
          m.id === assistantId
            ? { ...m, sources, source_type: sourceType, loading: false }
            : m
        ),
      }))
    }

    const fail = (_message: string) => {
      patch(activeId, s => ({
        ...s,
        messages: s.messages.map(m =>
          m.id === assistantId
            ? { ...m, content: m.content || t.error, loading: false }
            : m
        ),
      }))
    }

    try {
      await askQuestionStream(question, historyForRequest, level, appendToken, finalize, fail)
    } catch {
      fail(t.error)
    }

    setIsLoading(false)
  }

  const handleNew = () => {
    const s = newSession()
    setSessions(prev => [s, ...prev])
    setActiveId(s.id)
  }

  const handleDelete = async (chatId: string) => {
    await deleteChat(chatId)
    setSessions(prev => {
      const next = prev.filter(s => s.id !== chatId)
      if (activeId === chatId) {
        if (next.length > 0) {
          setActiveId(next[0].id)
          return next
        }
        const s = newSession()
        setActiveId(s.id)
        return [s]
      }
      return next
    })
  }

  if (authLoading) {
    return (
      <div className="h-screen flex items-center justify-center" style={{ background: '#F0F4FA' }}>
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 rounded-2xl flex flex-col items-center
                          justify-center shadow-md" style={{ background: '#003DA5' }}>
            <span className="text-white font-black text-xl leading-none">A</span>
          </div>
          <Loader2 size={20} className="animate-spin" style={{ color: '#003DA5' }} />
        </div>
      </div>
    )
  }

  if (!user) return <LoginPage />

  if (historyLoading) {
    return (
      <div className="h-screen flex items-center justify-center" style={{ background: '#F0F4FA' }}>
        <div className="flex flex-col items-center gap-3">
          <Loader2 size={24} className="animate-spin" style={{ color: '#003DA5' }} />
          <p className="text-sm text-gray-500">
            {lang === 'en' ? 'Loading your chats...' : '会話を読み込み中...'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        width={sidebarWidth}
        sessions={sessions}
        activeId={activeId}
        onNewChat={handleNew}
        onSelectSession={setActiveId}
        onDeleteSession={handleDelete}
      />

      <ResizeHandle onResize={handleSidebarResize} />

      <div className="flex flex-col flex-1 overflow-hidden min-w-0">
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          onSuggestion={(text) => handleSend(text, 'standard')}
        />
        <InputBar onSend={handleSend} disabled={isLoading} />
      </div>
    </div>
  )
}