import { useState, useCallback, useEffect } from 'react'
import Sidebar    from './components/Sidebar'
import ChatWindow from './components/ChatWindow'
import InputBar   from './components/InputBar'
import { askQuestion } from './api/chat'
import type { Message as Msg, ChatSession } from './types'

const uid = () => Math.random().toString(36).slice(2)

const newSession = (): ChatSession => ({
  id: uid(), title: 'New conversation', messages: [], date: new Date(),
})

export default function App() {
  const [sessions,  setSessions]  = useState<ChatSession[]>([])
  const [activeId,  setActiveId]  = useState('')
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    const s = newSession()
    setSessions([s])
    setActiveId(s.id)
  }, [])

  const active   = sessions.find(s => s.id === activeId)
  const messages = active?.messages ?? []

  const patch = useCallback((id: string, fn: (s: ChatSession) => ChatSession) => {
    setSessions(prev => prev.map(s => s.id === id ? fn(s) : s))
  }, [])

  const handleSend = async (question: string) => {
    if (!activeId || isLoading) return
    setIsLoading(true)

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
      const data = await askQuestion(question)
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
        content: 'Sorry, something went wrong. Please try again.',
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

  return (
    <div className="flex h-screen overflow-hidden">

      <Sidebar
        sessions={sessions}
        activeId={activeId}
        onNewChat={handleNew}
        onSelectSession={setActiveId}
      />

      <div className="flex flex-col flex-1 overflow-hidden">

        {/* Top bar */}
        <div className="h-14 bg-white px-6 flex items-center
                        justify-between shrink-0"
             style={{ borderBottom: '1px solid #E5E7EB',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
          <div>
            <h1 className="text-sm font-semibold text-gray-900 leading-tight">
              {active?.title ?? 'New conversation'}
            </h1>
            <p className="text-xs mt-0.5" style={{ color: '#003DA5' }}>
              Ask in English or Japanese | 日本語または英語で質問
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full
              ${isLoading ? 'bg-amber-400' : 'bg-green-400'}`}
                 style={{ boxShadow: isLoading
                   ? '0 0 6px rgba(251,191,36,0.6)'
                   : '0 0 6px rgba(74,222,128,0.6)' }}
            />
            <span className="text-xs text-gray-400">
              {isLoading ? 'Thinking...' : 'Ready'}
            </span>
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