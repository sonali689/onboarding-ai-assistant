import { useState } from 'react'
import { Plus, MessageSquare, Trash2, LogOut } from 'lucide-react'
import { useLang } from '../contexts/LanguageContext'
import { useAuth } from '../contexts/AuthContext'
import type { ChatSession } from '../types'
import sidebarBg from '../assets/sidebar-bg.png'

interface Props {
  width:          number
  sessions:        ChatSession[]
  activeId:        string
  onNewChat:       () => void
  onSelectSession: (id: string) => void
  onDeleteSession: (id: string) => void
}

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  return name.slice(0, 2).toUpperCase()
}

export default function Sidebar({
  width, sessions, activeId, onNewChat, onSelectSession, onDeleteSession,
}: Props) {
  const { lang, t }           = useLang()
  const { user, signOut }     = useAuth()
  const [hoverId, setHoverId] = useState<string | null>(null)

  return (
    <div
      style={{
        width: `${width}px`,
        position: 'relative',
        overflow: 'hidden',
      }}
      className="flex flex-col h-full shrink-0 select-none"
    >
      {/* ── Background image layer ─────────────────────────────── */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `url(${sidebarBg})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          opacity: 0.15,
          zIndex: 0,
        }}
      />
      {/* ── Solid color overlay for readability ────────────────── */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'rgba(0, 61, 165, 0.92)',
          zIndex: 1,
        }}
      />

      {/* ── Content (above image layers) ──────────────────────── */}
      <div className="flex flex-col h-full relative" style={{ zIndex: 2 }}>

        {/* Header */}
        <div className="px-5 pt-5 pb-4" style={{ borderBottom: '1px solid rgba(255,255,255,0.15)' }}>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white rounded-lg flex items-center justify-center shrink-0 shadow-sm">
              <span style={{ color: '#003DA5' }} className="font-black text-lg leading-none">A</span>
            </div>
            <div>
              <div className="text-white font-black text-lg tracking-tight leading-none">Autoliv</div>
              <div style={{ background: 'rgba(255,255,255,0.4)' }} className="h-px mt-1" />
              <div className="text-white text-xs mt-0.5" style={{ opacity: 0.6 }}>Onboarding Assistant</div>
            </div>
          </div>
          <p className="text-xs mt-3 font-medium" style={{ color: 'rgba(255,255,255,0.45)' }}>
            研修アシスタント · Japan Technical Center
          </p>
        </div>

        {/* New chat button */}
        <div className="px-3 py-3">
          <button
            onClick={onNewChat}
            className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm font-semibold
                       rounded-xl transition-all duration-150 active:scale-95"
            style={{ color: '#ffffff', border: '1.5px solid rgba(255,255,255,0.3)',
                     background: 'rgba(255,255,255,0.08)' }}
            onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.18)' }}
            onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.08)' }}
          >
            <Plus size={15} strokeWidth={2.5} />
            {t.newConversation}
          </button>
        </div>

        {/* Section header */}
        <div className="px-4 mb-1">
          <p className="text-xs uppercase tracking-widest font-bold" style={{ color: 'rgba(255,255,255,0.4)' }}>
            {t.recent}
          </p>
        </div>

        {/* Chat list */}
        <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-0.5">
          {sessions.length === 0 ? (
            <p className="text-center text-xs px-4 mt-4 leading-relaxed" style={{ color: 'rgba(255,255,255,0.3)' }}>
              {t.noChats}
            </p>
          ) : (
            sessions.map(s => (
              <div
                key={s.id}
                className="flex items-center rounded-xl transition-all duration-150"
                style={{
                  background: activeId === s.id
                    ? 'rgba(255,255,255,1)'
                    : hoverId === s.id
                      ? 'rgba(255,255,255,0.12)'
                      : 'transparent',
                }}
                onMouseEnter={() => setHoverId(s.id)}
                onMouseLeave={() => setHoverId(null)}
              >
                <button
                  onClick={() => onSelectSession(s.id)}
                  className="flex items-center gap-2 px-3 py-2.5 text-left text-xs flex-1 min-w-0"
                  style={{
                    color:      activeId === s.id ? '#003DA5' : 'rgba(255,255,255,0.85)',
                    fontWeight: activeId === s.id ? 700 : 400,
                  }}
                >
                  <MessageSquare size={12} className="shrink-0" />
                  <span className="truncate">{s.title}</span>
                </button>

                {hoverId === s.id && (
                  <button
                    onClick={e => { e.stopPropagation(); onDeleteSession(s.id) }}
                    className="p-1.5 mr-1.5 rounded-lg transition-all"
                    style={{ color: activeId === s.id ? 'rgba(0,61,165,0.4)' : 'rgba(255,255,255,0.4)' }}
                    onMouseEnter={e => { const el = e.currentTarget as HTMLButtonElement; el.style.color = activeId === s.id ? '#003DA5' : '#ffffff'; el.style.background = activeId === s.id ? 'rgba(0,61,165,0.1)' : 'rgba(255,255,255,0.15)' }}
                    onMouseLeave={e => { const el = e.currentTarget as HTMLButtonElement; el.style.color = activeId === s.id ? 'rgba(0,61,165,0.4)' : 'rgba(255,255,255,0.4)'; el.style.background = 'transparent' }}
                  >
                    <Trash2 size={11} />
                  </button>
                )}
              </div>
            ))
          )}
        </div>

        {/* User section */}
        {user && (
          <div className="px-3 py-3" style={{ borderTop: '1px solid rgba(255,255,255,0.15)' }}>
            <div className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl" style={{ background: 'rgba(255,255,255,0.1)' }}>
              <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center shrink-0" style={{ color: '#003DA5' }}>
                <span className="text-xs font-black">{getInitials(user.name)}</span>
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-xs font-bold text-white leading-tight truncate">{user.name}</p>
                <p className="text-xs truncate mt-0.5" style={{ color: 'rgba(255,255,255,0.5)', fontSize: '10px' }}>
                  {user.email}
                </p>
              </div>

              <button
                onClick={signOut}
                title={lang === 'en' ? 'Sign out' : 'サインアウト'}
                className="p-1.5 rounded-lg transition-all shrink-0"
                style={{ color: 'rgba(255,255,255,0.5)' }}
                onMouseEnter={e => { const el = e.currentTarget as HTMLButtonElement; el.style.color = '#fff'; el.style.background = 'rgba(255,255,255,0.15)' }}
                onMouseLeave={e => { const el = e.currentTarget as HTMLButtonElement; el.style.color = 'rgba(255,255,255,0.5)'; el.style.background = 'transparent' }}
              >
                <LogOut size={13} />
              </button>
            </div>

            <p className="text-xs mt-2 text-center font-medium" style={{ color: 'rgba(255,255,255,0.3)', fontSize: '10px' }}>
              {t.localAI}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}