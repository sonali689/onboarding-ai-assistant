import { MessageSquare, Plus, ChevronRight } from 'lucide-react'
import type { ChatSession } from '../types'

interface Props {
  sessions:        ChatSession[]
  activeId:        string
  onNewChat:       () => void
  onSelectSession: (id: string) => void
}

export default function Sidebar({
  sessions, activeId, onNewChat, onSelectSession
}: Props) {
  return (
    <div className="w-64 bg-autoliv-blue flex flex-col h-full flex-shrink-0">

      {/* Logo header */}
      <div className="px-5 py-5 border-b border-white/20">
        <div className="flex items-center gap-3">
          {/* Autoliv wordmark style */}
          <div className="flex flex-col">
            <span className="text-white font-black text-xl tracking-tight
                             leading-none">
              Autoliv
            </span>
            {/* Blue underline — matches logo */}
            <div className="h-0.5 bg-white/60 mt-1 w-full rounded-full" />
          </div>
        </div>
        <p className="text-white/50 text-xs mt-2 leading-tight">
          Onboarding Assistant · 研修アシスタント
        </p>
      </div>

      {/* New chat button */}
      <div className="px-3 py-3">
        <button
          onClick={onNewChat}
          className="w-full flex items-center gap-2 px-3 py-2.5
                     rounded-xl border border-white/30 text-white/90
                     text-sm hover:bg-white/15 hover:text-white
                     transition-all active:scale-98 font-medium">
          <Plus size={16} />
          New conversation
        </button>
      </div>

      {/* Chat history */}
      <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-1">
        {sessions.length === 0 && (
          <p className="text-white/30 text-xs text-center mt-4 px-2">
            Your conversations will appear here
          </p>
        )}
        {sessions.map(session => (
          <button
            key={session.id}
            onClick={() => onSelectSession(session.id)}
            className={`w-full flex items-center gap-2 px-3 py-2.5
              rounded-xl text-left text-xs transition-all group
              ${activeId === session.id
                ? 'bg-white text-autoliv-blue font-semibold'
                : 'text-white/70 hover:bg-white/15 hover:text-white'
              }`}>
            <MessageSquare size={13} className="flex-shrink-0" />
            <span className="truncate flex-1">{session.title}</span>
            <ChevronRight size={11}
              className="flex-shrink-0 opacity-0 group-hover:opacity-60
                         transition-opacity" />
          </button>
        ))}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-white/20">
        <p className="text-white/40 text-xs">Bilingual EN · JA</p>
        <p className="text-white/25 text-xs mt-0.5">v2.0 · Local AI</p>
      </div>
    </div>
  )
}