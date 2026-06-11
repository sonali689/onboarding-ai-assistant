import { useState, useCallback, useEffect } from 'react'
import Sidebar     from './components/Sidebar'
import ChatWindow  from './components/ChatWindow'
import InputBar    from './components/InputBar'
import { askQuestion } from './api/chat'
import type { Message as MessageType, ChatSession } from './types'

function generateId() {
  return Math.random().toString(36).slice(2)
}

function createSession(): ChatSession {
  return {
    id:       generateId(),
    title:    'New conversation',
    messages: [],
    date:     new Date(),
  }
}

export default function App() {
  const [sessions, setSessions]   = useState<ChatSession[]>([])
  const [activeId, setActiveId]   = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    const session = createSession()
    setSessions([session])
    setActiveId(session.id)
  }, [])

  const activeSession = sessions.find(s => s.id === activeId)
  const messages      = activeSession?.messages ?? []

  const updateSession = useCallback((
    id: string,
    updater: (s: ChatSession) => ChatSession
  ) => {
    setSessions(prev => prev.map(s => s.id === id ? updater(s) : s))
  }, [])

  const handleSend = async (question: string) => {
    if (!activeId || isLoading) return

    const userMsg: MessageType = {
      id:          generateId(),
      role:        'user',
      content:     question,
      sources:     [],
      source_type: null,
      timestamp:   new Date(),
    }

    const loadingMsg: MessageType = {
      id:          generateId(),
      role:        'assistant',
      content:     '',
      sources:     [],
      source_type: null,
      timestamp:   new Date(),
      loading:     true,
    }

    updateSession(activeId, s => ({
      ...s,
      title:    s.messages.length === 0
                  ? question.slice(0, 42)
                  : s.title,
      messages: [...s.messages, userMsg, loadingMsg],
    }))

    setIsLoading(true)

    try {
      const data = await askQuestion(question)

      const assistantMsg: MessageType = {
        id:          generateId(),
        role:        'assistant',
        content:     data.answer,
        sources:     data.sources,
        source_type: data.source_type,
        timestamp:   new Date(),
        loading:     false,
      }

      updateSession(activeId, s => ({
        ...s,
        messages: [
          ...s.messages.filter(m => !m.loading),
          assistantMsg,
        ],
      }))

    } catch {
      const errorMsg: MessageType = {
        id:          generateId(),
        role:        'assistant',
        content:     'Sorry, something went wrong. Please try again. | エラーが発生しました。',
        sources:     [],
        source_type: null,
        timestamp:   new Date(),
        loading:     false,
      }
      updateSession(activeId, s => ({
        ...s,
        messages: [
          ...s.messages.filter(m => !m.loading),
          errorMsg,
        ],
      }))
    }

    setIsLoading(false)
  }

  const handleNewChat = () => {
    const session = createSession()
    setSessions(prev => [session, ...prev])
    setActiveId(session.id)
  }

  return (
    <div className="flex h-screen bg-white overflow-hidden">

      {/* Sidebar */}
      <Sidebar
        sessions={sessions}
        activeId={activeId}
        onNewChat={handleNewChat}
        onSelectSession={setActiveId}
      />

      {/* Main area */}
      <div className="flex flex-col flex-1 overflow-hidden">

        {/* Top bar */}
        <div className="h-14 border-b border-autoliv-border
                        flex items-center justify-between
                        px-6 bg-white flex-shrink-0 shadow-sm">
          <div>
            <h1 className="text-sm font-semibold text-autoliv-charcoal">
              {activeSession?.title ?? 'New conversation'}
            </h1>
            <p className="text-xs text-autoliv-blue">
              Ask in English or Japanese | 日本語または英語で質問
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full transition-colors
              ${isLoading
                ? 'bg-amber-400 animate-pulse'
                : 'bg-green-400 animate-pulse'
              }`}
            />
            <span className="text-xs text-gray-400">
              {isLoading ? 'Thinking... | 考え中...' : 'Ready'}
            </span>
          </div>
        </div>

        {/* Chat window */}
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          onSuggestion={handleSend}
        />

        {/* Input */}
        <InputBar
          onSend={handleSend}
          disabled={isLoading}
        />

      </div>
    </div>
  )
}