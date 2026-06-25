import { useEffect, useRef } from 'react'
import { Globe } from 'lucide-react'
import Message from './Message'
import { useLang } from '../contexts/LanguageContext'
import type { Message as MessageType } from '../types'

function getGreeting(greetings: {
  earlyMorning: readonly string[]
  morning:      readonly string[]
  afternoon:    readonly string[]
  evening:      readonly string[]
  night:        readonly string[]
}): string {
  const hour = new Date().getHours()
  const day  = new Date().toLocaleDateString('en-US', { weekday: 'long' })

  let pool: readonly string[]
  if      (hour >= 0  && hour < 6) pool = greetings.earlyMorning
  else if (hour < 12)              pool = greetings.morning
  else if (hour < 17)              pool = greetings.afternoon
  else if (hour < 20)              pool = greetings.evening
  else                             pool = greetings.night

  const picked = pool[Math.floor(Math.random() * pool.length)]
  return picked.replace('{day}', day)
}

interface Props {
  messages:     MessageType[]
  isLoading:    boolean
  onSuggestion: (text: string) => void
}

/* ── Floating top-right controls (language toggle + status) ─────── */
function TopControls({ isLoading }: { isLoading: boolean }) {
  const { lang, toggleLang, t } = useLang()

  return (
    <div
      className="absolute top-3 right-4 z-10 flex items-center gap-3"
    >
      {/* Language segmented control */}
      <div className="flex items-center rounded-full overflow-hidden shadow-sm"
           style={{ border: '1.5px solid #003DA5', background: '#fff' }}>
        <button
          onClick={() => { if (lang !== 'en') toggleLang() }}
          className="flex items-center gap-1 px-3 py-1.5 text-xs font-bold
                     transition-all duration-150"
          style={{
            background: lang === 'en' ? '#003DA5' : 'transparent',
            color:      lang === 'en' ? '#ffffff' : '#003DA5',
          }}
        >
          <Globe size={11} />
          EN
        </button>
        <div style={{ width: '1px', height: '16px', background: '#003DA5', opacity: 0.3 }} />
        <button
          onClick={() => { if (lang !== 'ja') toggleLang() }}
          className="flex items-center gap-1 px-3 py-1.5 text-xs font-bold
                     transition-all duration-150"
          style={{
            background: lang === 'ja' ? '#003DA5' : 'transparent',
            color:      lang === 'ja' ? '#ffffff' : '#003DA5',
          }}
        >
          JA
        </button>
      </div>

      {/* Status dot */}
      <div className="flex items-center gap-1.5 bg-white px-2.5 py-1.5 rounded-full shadow-sm"
           style={{ border: '1px solid #E5E7EB' }}>
        <div className={`w-1.5 h-1.5 rounded-full ${isLoading ? 'bg-amber-400' : 'bg-green-400'}`} />
        <span className="text-xs font-medium" style={{ color: '#6B7280' }}>
          {isLoading ? t.thinking : t.ready}
        </span>
      </div>
    </div>
  )
}

export default function ChatWindow({ messages, isLoading, onSuggestion }: Props) {
  const containerRef     = useRef<HTMLDivElement>(null)
  const bottomRef         = useRef<HTMLDivElement>(null)
  const prevCountRef      = useRef(0)
  const stickToBottomRef  = useRef(true)
  const didMountRef       = useRef(false)
  const { t }             = useLang()
  const greeting          = getGreeting(t.greetings)

  // Track whether the user is near the bottom of the scroll area
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const handleScroll = () => {
      const distance = el.scrollHeight - el.scrollTop - el.clientHeight
      stickToBottomRef.current = distance < 120
    }
    el.addEventListener('scroll', handleScroll)
    return () => el.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    const prevCount = prevCountRef.current
    prevCountRef.current = messages.length

    if (!didMountRef.current) {
      didMountRef.current = true
      requestAnimationFrame(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'auto', block: 'end' })
      })
      return
    }

    const addedNewMessage = messages.length > prevCount

    if (addedNewMessage) {
      stickToBottomRef.current = true
      const anchor = messages[messages.length - 2] ?? messages[messages.length - 1]
      requestAnimationFrame(() => {
        const el = document.getElementById(`msg-${anchor.id}`)
        el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      })
    } else if (stickToBottomRef.current) {
      bottomRef.current?.scrollIntoView({ behavior: 'auto', block: 'end' })
    }
  }, [messages])

  /* ── Welcome state ── */
  if (messages.length === 0) {
    return (
      <div className="flex-1 overflow-y-auto flex flex-col items-center
                      justify-center px-6 pb-12 relative"
           style={{ background: '#F8F9FB' }}>

        <TopControls isLoading={isLoading} />

        <div className="mb-6 text-center">
          <div className="w-14 h-14 rounded-2xl mx-auto mb-5 flex flex-col
                          items-center justify-center shadow-md"
               style={{ background: '#003DA5' }}>
            <span className="text-white font-black text-xl leading-none">A</span>
            <div className="w-7 mt-1 rounded-full"
                 style={{ height: '2px', background: 'rgba(255,255,255,0.45)' }} />
          </div>

          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">
            {greeting}
          </h1>

          <p className="text-sm text-gray-400 mt-2 max-w-xs mx-auto leading-relaxed">
            {t.subtitle}
          </p>
        </div>

        <p className="text-xs uppercase tracking-widest font-semibold mb-3"
           style={{ color: '#9CA3AF' }}>
          {t.tryAsking}
        </p>

        <div className="flex gap-2 items-stretch">
          {t.suggestions.map((s, i) => (
            <button
              key={i}
              onClick={() => onSuggestion(s.text)}
              disabled={isLoading}
              className="flex items-start gap-2 text-left px-4 py-3
                         bg-white rounded-xl text-xs text-gray-600
                         transition-all duration-150 shadow-sm
                         hover:shadow-md active:scale-[0.98]
                         disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ border: '1px solid #E5E7EB', maxWidth: '280px' }}
              onMouseEnter={e => {
                const el = e.currentTarget
                el.style.borderColor = '#003DA5'
                el.style.color       = '#003DA5'
              }}
              onMouseLeave={e => {
                const el = e.currentTarget
                el.style.borderColor = '#E5E7EB'
                el.style.color       = '#4B5563'
              }}
            >
              <span className="text-xs px-1.5 py-0.5 rounded font-bold shrink-0 mt-0.5"
                    style={{ background: '#EEF3FC', color: '#003DA5' }}>
                {s.lang}
              </span>
              <span className="leading-snug">{s.text}</span>
            </button>
          ))}
        </div>

        <div ref={bottomRef} />
      </div>
    )
  }

  /* ── Messages ── */
  return (
    <div ref={containerRef} className="flex-1 overflow-y-auto py-6 relative"
         style={{ background: '#F8F9FB' }}>

      <TopControls isLoading={isLoading} />

      <div className="max-w-3xl mx-auto pt-6">
        {messages.map(msg => (
          <Message key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} className="h-2" />
      </div>
    </div>
  )
}