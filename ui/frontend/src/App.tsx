import { useState, useCallback, useEffect } from 'react'
import Sidebar    from './components/Sidebar'
import ChatWindow from './components/ChatWindow'
import InputBar   from './components/InputBar'
import { askQuestion } from './api/chat'
import { useLang }     from './contexts/LanguageContext'
import { Globe }        from 'lucide-react'
import type { Message as Msg, ChatSession } from './types'

const uid = () => Math.random().toString(36).slice(2)

const newSession = (): ChatSession => ({
  id: uid(), title: 'New conversation', messages: [], date: new Date(),
})

const buildHistory = (msgs: Msg[]): { role: 'user' | 'assistant'; content: string }[] => {
  return msgs
    .filter(m => !m.loading)
    .slice(-6) // last 3 exchanges
    .map(m => ({ role: m.role, content: m.content }))
}

export default function App() {
  const { t, lang, toggleLang }                        = useLang()
  const [sessions,  setSessions]     = useState<ChatSession[]>([])
  const [activeId,  setActiveId]     = useState('')
  const [isLoading, setIsLoading]    = useState(false)

  useEffect(() => {
    const s = newSession()
    setSessions([s])
    setActiveId(s.id)
  }, [])

  const active   = sessions.find(s => s.id === activeId)
  const messages = active?.messages ?? []

  const patch = useCallback((
    id: string,
    fn: (s: ChatSession) => ChatSession,
  ) => {
    setSessions(prev => prev.map(s => s.id === id ? fn(s) : s))
  }, [])

  const handleSend = async (question: string) => {
    if (!activeId || isLoading) return
    setIsLoading(true)

    const historyForRequest = buildHistory(messages) // snapshot BEFORE adding new message

    const userMsg: Msg = {
      id: uid(), role: 'user', content: question,
      sources: [], source_type: null, timestamp: new Date(),
    }
    const loadingMsg: Msg = {
      id: uid(), role: 'assistant', content: '',
      sources: [], source_type: null,
      timestamp: new Date(), loading: true,
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
        id: uid(), role: 'assistant',
        content: t.error,
        sources: [], source_type: null,
        timestamp: new Date(), loading: false,
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

  const handleDelete = (chatId: string) => {
    setSessions(prev => {
      const next = prev.filter(s => s.id !== chatId)
      if (activeId === chatId) {
        if (next.length > 0) {
          setActiveId(next[0].id)
          return next
        } else {
          const s = newSession()
          setActiveId(s.id)
          return [s]
        }
      }
      return next
    })
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

        {/* Top bar */}
        <div className="h-12 bg-white px-6 flex items-center
                        justify-between shrink-0"
             style={{ borderBottom: '1px solid #E5E7EB',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>

          {/* Left — chat title */}
          <p className="text-xs font-medium text-gray-600 truncate">
            {active?.title ?? t.newConversation}
          </p>

          {/* Right — language toggle + status */}
          <div className="flex items-center gap-3 shrink-0">

            {/* Language toggle */}
            <button
              onClick={toggleLang}
              title={lang === 'en' ? 'Switch to Japanese' : '英語に切り替え'}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full
                         text-xs font-semibold transition-all duration-150
                         active:scale-95"
              style={{
                border:     '1.5px solid #003DA5',
                color:      '#003DA5',
                background: 'transparent',
              }}
              onMouseEnter={e => {
                const el = e.currentTarget
                el.style.background = '#003DA5'
                el.style.color      = '#ffffff'
              }}
              onMouseLeave={e => {
                const el = e.currentTarget
                el.style.background = 'transparent'
                el.style.color      = '#003DA5'
              }}
            >
              <Globe size={12} />
              {lang === 'en' ? '日本語' : 'English'}
            </button>

            {/* Status indicator */}
            <div className="flex items-center gap-1.5">
              <div className={`w-1.5 h-1.5 rounded-full
                ${isLoading ? 'bg-amber-400' : 'bg-green-400'}`} />
              <span className="text-xs" style={{ color: '#9CA3AF' }}>
                {isLoading ? t.thinking : t.ready}
              </span>
            </div>
          </div>
        </div>

        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          onSuggestion={handleSend}
        />

        <InputBar onSend={handleSend} disabled={isLoading} />
      </div>
    </div>
  )
}
