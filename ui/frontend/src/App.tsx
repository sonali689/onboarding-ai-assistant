import { useState, useCallback, useEffect, useRef } from 'react'
import { Globe, Loader2 } from 'lucide-react'
import Sidebar    from './components/Sidebar'
import ChatWindow from './components/ChatWindow'
import InputBar   from './components/InputBar'
import LoginPage  from './components/LoginPage'
import { askQuestion, loadChats, saveChat, deleteChat } from './api/chat'
import { useLang } from './contexts/LanguageContext'
import { useAuth } from './contexts/AuthContext'
import type { Message as Msg, ChatSession } from './types'

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

export default function App() {
  const { t, lang, toggleLang }        = useLang()
  const { user, loading: authLoading } = useAuth()

  const [sessions,  setSessions]  = useState<ChatSession[]>([])
  const [activeId,  setActiveId]  = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(false)
  const saveTimer = useRef<ReturnType<typeof setTimeout>|undefined>(undefined)

  // ── Load chat history when user logs in ────────────────────────────────────
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

  const handleSend = async (question: string) => {
    if (!activeId || isLoading) return
    setIsLoading(true)

    const historyForRequest = buildHistory(messages)

    const userMsg: Msg = {
      id: uid(), role: 'user', content: question,
      sources: [], source_type: null, timestamp: new Date(),
    }
    const loadingMsg: Msg = {
      id: uid(), role: 'assistant', content: '',
      sources: [], source_type: null, timestamp: new Date(), loading: true,
    }

    patch(activeId, s => ({
      ...s,
      title:    s.messages.length === 0 ? question.slice(0, 44) : s.title,
      messages: [...s.messages, userMsg, loadingMsg],
    }))

    try {
      const data = await askQuestion(question, historyForRequest)
      const reply: Msg = {
        id: uid(), role: 'assistant', content: data.answer,
        sources: data.sources, source_type: data.source_type,
        timestamp: new Date(), loading: false,
      }
      patch(activeId, s => ({
        ...s,
        messages: [...s.messages.filter(m => !m.loading), reply],
      }))
    } catch {
      const err: Msg = {
        id: uid(), role: 'assistant', content: t.error,
        sources: [], source_type: null, timestamp: new Date(), loading: false,
      }
      patch(activeId, s => ({
        ...s,
        messages: [...s.messages.filter(m => !m.loading), err],
      }))
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
        sessions={sessions}
        activeId={activeId}
        onNewChat={handleNew}
        onSelectSession={setActiveId}
        onDeleteSession={handleDelete}
      />

      <div className="flex flex-col flex-1 overflow-hidden">

        <div className="h-12 bg-white px-6 flex items-center justify-between shrink-0"
             style={{ borderBottom: '1px solid #E5E7EB', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>

          <p className="text-xs font-medium text-gray-600 truncate">
            {active?.title ?? t.newConversation}
          </p>

          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={toggleLang}
              title={lang === 'en' ? 'Switch to Japanese' : '英語に切り替え'}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full
                         text-xs font-semibold transition-all duration-150 active:scale-95"
              style={{ border: '1.5px solid #003DA5', color: '#003DA5', background: 'transparent' }}
              onMouseEnter={e => { e.currentTarget.style.background = '#003DA5'; e.currentTarget.style.color = '#ffffff' }}
              onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#003DA5' }}
            >
              <Globe size={12} />
              {lang === 'en' ? '日本語' : 'English'}
            </button>

            <div className="flex items-center gap-1.5">
              <div className={`w-1.5 h-1.5 rounded-full ${isLoading ? 'bg-amber-400' : 'bg-green-400'}`} />
              <span className="text-xs" style={{ color: '#9CA3AF' }}>
                {isLoading ? t.thinking : t.ready}
              </span>
            </div>
          </div>
        </div>

        <ChatWindow messages={messages} isLoading={isLoading} onSuggestion={handleSend} />
        <InputBar onSend={handleSend} disabled={isLoading} />
      </div>
    </div>
  )
}