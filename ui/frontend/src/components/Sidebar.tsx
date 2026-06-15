import { useState }          from 'react'
import { Plus, MessageSquare,
         ChevronRight, Trash2 }            from 'lucide-react'
import { useLang }           from '../contexts/LanguageContext'
import type { ChatSession }  from '../types'

interface Props {
  sessions:        ChatSession[]
  activeId:        string
  onNewChat:       () => void
  onSelectSession: (id: string) => void
  onDeleteSession: (id: string) => void
}

export default function Sidebar({
  sessions, activeId,
  onNewChat, onSelectSession, onDeleteSession,
}: Props) {
  const { lang, t } = useLang()
  const [hoverId, setHoverId]   = useState<string | null>(null)

  return (
    <div style={{ background: '#003DA5' }}
         className="w-64 flex flex-col h-full shrink-0 select-none">

      {/* ── Brand + language toggle ─────────────────────── */}
      <div className="px-5 pt-5 pb-4"
           style={{ borderBottom: '1px solid rgba(255,255,255,0.12)' }}>
        <div className="flex items-center justify-between">

          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white rounded-lg flex items-center
                            justify-center shrink-0 shadow-sm">
              <span style={{ color: '#003DA5' }}
                    className="font-black text-lg leading-none">
                A
              </span>
            </div>
            <div>
              <div className="text-white font-black text-lg
                              tracking-tight leading-none">
                Autoliv
              </div>
              <div style={{ background: 'rgba(255,255,255,0.4)' }}
                   className="h-px mt-1" />
              <div className="text-white text-xs mt-0.5"
                   style={{ opacity: 0.5 }}>
                Onboarding Assistant
              </div>
            </div>
          </div>

           
        </div>

        <p className="text-xs mt-3"
           style={{ color: 'rgba(255,255,255,0.3)' }}>
          研修アシスタント · Japan Technical Center
        </p>
      </div>

      {/* ── New chat button ─────────────────────────────── */}
      <div className="px-3 py-3">
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
            (e.currentTarget as HTMLButtonElement).style.background =
              'rgba(255,255,255,0.12)'
          }}
          onMouseLeave={e => {
            (e.currentTarget as HTMLButtonElement).style.background =
              'transparent'
          }}
        >
          <Plus size={15} strokeWidth={2.5} />
          {t.newConversation}
        </button>
      </div>

      {/* ── Recent label ────────────────────────────────── */}
      <div className="px-4 mb-1">
        <p className="text-xs uppercase tracking-widest font-semibold"
           style={{ color: 'rgba(255,255,255,0.3)' }}>
          {t.recent}
        </p>
      </div>

      {/* ── Chat history ─────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-0.5">
        {sessions.length === 0 ? (
          <p className="text-center text-xs px-4 mt-4 leading-relaxed"
             style={{ color: 'rgba(255,255,255,0.25)' }}>
            {t.noChats}
          </p>
        ) : (
          sessions.map(s => (
            <div
              key={s.id}
              className="flex items-center rounded-xl transition-all
                         duration-150"
              style={{
                background: activeId === s.id
                  ? 'rgba(255,255,255,1)'
                  : hoverId === s.id
                    ? 'rgba(255,255,255,0.1)'
                    : 'transparent',
              }}
              onMouseEnter={() => setHoverId(s.id)}
              onMouseLeave={() => setHoverId(null)}
            >
              {/* Session button */}
              <button
                onClick={() => onSelectSession(s.id)}
                className="flex items-center gap-2 px-3 py-2.5
                           text-left text-xs flex-1 min-w-0"
                style={{
                  color: activeId === s.id
                    ? '#003DA5'
                    : 'rgba(255,255,255,0.7)',
                  fontWeight: activeId === s.id ? 600 : 400,
                }}
              >
                <MessageSquare size={12} className="shrink-0" />
                <span className="truncate">{s.title}</span>
              </button>

              {/* Delete — show on hover */}
              {hoverId === s.id && (
                <button
                  onClick={e => {
                    e.stopPropagation()
                    onDeleteSession(s.id)
                  }}
                  className="p-1.5 mr-1.5 rounded-lg transition-all"
                  style={{ color: 'rgba(255,255,255,0.4)' }}
                  onMouseEnter={e => {
                    const el = e.currentTarget as HTMLButtonElement
                    el.style.color      = '#ffffff'
                    el.style.background = 'rgba(255,255,255,0.15)'
                  }}
                  onMouseLeave={e => {
                    const el = e.currentTarget as HTMLButtonElement
                    el.style.color      = 'rgba(255,255,255,0.4)'
                    el.style.background = 'transparent'
                  }}
                >
                  <Trash2 size={11} />
                </button>
              )}
            </div>
          ))
        )}
      </div>

      {/* ── Footer ──────────────────────────────────────── */}
      <div className="px-5 py-3"
           style={{ borderTop: '1px solid rgba(255,255,255,0.1)' }}>
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-green-400" />
          <span className="text-xs"
                style={{ color: 'rgba(255,255,255,0.3)' }}>
            {t.localAI}
          </span>
        </div>
      </div>
    </div>
  )
}