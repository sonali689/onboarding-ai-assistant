import { Plus, MessageSquare, ChevronRight } from 'lucide-react'
import type { ChatSession } from '../types'

interface Props {
  sessions:        ChatSession[]
  activeId:        string
  onNewChat:       () => void
  onSelectSession: (id: string) => void
}

export default function Sidebar({ sessions, activeId, onNewChat, onSelectSession }: Props) {
  return (
    <div style={{ background: '#003DA5' }}
         className="w-64 flex flex-col h-full shrink-0 select-none">

      {/* ── Brand header ───────────────────────────── */}
      <div className="px-5 pt-6 pb-5"
           style={{ borderBottom: '1px solid rgba(255,255,255,0.12)' }}>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-white rounded-lg flex items-center
                          justify-center shrink-0 shadow-sm">
            <span style={{ color: '#003DA5' }}
                  className="font-black text-lg leading-none">A</span>
          </div>
          <div>
            <div className="text-white font-black text-lg tracking-tight
                            leading-none">
              Autoliv
            </div>
            <div style={{ background: 'rgba(255,255,255,0.5)' }}
                 className="h-px mt-1 mb-1" />
            <div className="text-white text-xs"
                 style={{ opacity: 0.5 }}>
              Onboarding Assistant
            </div>
          </div>
        </div>
        <div className="text-xs mt-3 leading-tight"
             style={{ color: 'rgba(255,255,255,0.35)' }}>
          研修アシスタント · Japan Technical Center
        </div>
      </div>

      {/* ── New chat button ─────────────────────────── */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full flex items-center gap-2.5 px-4 py-2.5
                     text-sm font-medium rounded-xl transition-all
                     duration-150 active:scale-95"
          style={{
            color:  'rgba(255,255,255,0.9)',
            border: '1px solid rgba(255,255,255,0.2)',
          }}
          onMouseEnter={e => {
            (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.12)'
          }}
          onMouseLeave={e => {
            (e.currentTarget as HTMLButtonElement).style.background = 'transparent'
          }}
        >
          <Plus size={15} strokeWidth={2.5} />
          New conversation
        </button>
      </div>

      {/* ── History ────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-0.5">
        {sessions.length === 0 ? (
          <p className="text-center text-xs px-4 mt-6 leading-relaxed"
             style={{ color: 'rgba(255,255,255,0.25)' }}>
            Your conversations<br />will appear here
          </p>
        ) : (
          sessions.map(s => (
            <button
              key={s.id}
              onClick={() => onSelectSession(s.id)}
              className="w-full flex items-center gap-2.5 px-3 py-2.5
                         rounded-xl text-left text-xs transition-all
                         duration-150 group"
              style={{
                background: activeId === s.id
                  ? 'rgba(255,255,255,1)'
                  : 'transparent',
                color: activeId === s.id
                  ? '#003DA5'
                  : 'rgba(255,255,255,0.65)',
                fontWeight: activeId === s.id ? 600 : 400,
              }}
              onMouseEnter={e => {
                if (activeId !== s.id) {
                  (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.1)'
                  ;(e.currentTarget as HTMLButtonElement).style.color = 'rgba(255,255,255,0.9)'
                }
              }}
              onMouseLeave={e => {
                if (activeId !== s.id) {
                  (e.currentTarget as HTMLButtonElement).style.background = 'transparent'
                  ;(e.currentTarget as HTMLButtonElement).style.color = 'rgba(255,255,255,0.65)'
                }
              }}
            >
              <MessageSquare size={13} className="shrink-0" />
              <span className="truncate flex-1">{s.title}</span>
              <ChevronRight size={11}
                className="shrink-0 opacity-0 group-hover:opacity-50
                           transition-opacity" />
            </button>
          ))
        )}
      </div>

      {/* ── Footer ─────────────────────────────────── */}
      <div className="px-5 py-4"
           style={{ borderTop: '1px solid rgba(255,255,255,0.1)' }}>
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-green-400" />
          <span className="text-xs"
                style={{ color: 'rgba(255,255,255,0.35)' }}>
            Local AI · EN · JA · v2.0
          </span>
        </div>
      </div>
    </div>
  )
}