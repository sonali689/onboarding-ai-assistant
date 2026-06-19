import { useEffect, useRef } from 'react'
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
      // Initial load (restored chat) — jump straight to the bottom, no animation
      didMountRef.current = true
      requestAnimationFrame(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'auto', block: 'end' })
      })
      return
    }

    const addedNewMessage = messages.length > prevCount

    if (addedNewMessage) {
      // New question sent — scroll to the start of the new exchange,
      // not past it to the bottom (which would skip straight to sources)
      stickToBottomRef.current = true
      const anchor = messages[messages.length - 2] ?? messages[messages.length - 1]
      requestAnimationFrame(() => {
        const el = document.getElementById(`msg-${anchor.id}`)
        el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      })
    } else if (stickToBottomRef.current) {
      // Content streaming in and user hasn't scrolled away — keep following
      bottomRef.current?.scrollIntoView({ behavior: 'auto', block: 'end' })
    }
  }, [messages])

  /* ── Welcome state ── */
  if (messages.length === 0) {
    return (
      <div className="flex-1 overflow-y-auto flex flex-col items-center
                      justify-center px-6 pb-12"
           style={{ background: '#F8F9FB' }}>

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
    <div ref={containerRef} className="flex-1 overflow-y-auto py-6" style={{ background: '#F8F9FB' }}>
      <div className="max-w-3xl mx-auto">
        {messages.map(msg => (
          <Message key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} className="h-2" />
      </div>
    </div>
  )
}