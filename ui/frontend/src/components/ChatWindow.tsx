import { useEffect, useRef } from 'react'
import Message from './Message'
import type { Message as MessageType } from '../types'

// ── Dynamic greeting ────────────────────────────────────────────────────────
function getGreeting(): { headline: string } {
  const hour = new Date().getHours()
  const day  = new Date().toLocaleDateString('en-US', { weekday: 'long' })

  const greetings = {
    earlyMorning: [
      { headline: "Early bird! " },
      { headline: "Rise and shine " },
    ],
    morning: [
      { headline: "Good morning! " },
      { headline: "Morning! Let's get started 🚀" },
      { headline: `Happy ${day}! ` },
    ],
    afternoon: [
      { headline: "Good afternoon! " },
      { headline: "Welcome back " },
      { headline: "Hey there! " },
    ],
    evening: [
      { headline: "Good evening! " },
      { headline: "Evening check-in " },
      { headline: "Almost done for the day? " },
    ],
    night: [
      { headline: "Hello, night owl! " },
      { headline: "Late night learning " },
      { headline: "Still at it! " },
    ],
  }

  let pool
  if (hour >= 0 && hour < 6)  pool = greetings.earlyMorning
  else if (hour < 12)          pool = greetings.morning
  else if (hour < 17)          pool = greetings.afternoon
  else if (hour < 20)          pool = greetings.evening
  else                         pool = greetings.night

  return pool[Math.floor(Math.random() * pool.length)]
}

// ── Suggestions ─────────────────────────────────────────────────────────────
const SUGGESTIONS = [
  { text: 'What are inflators and their various types?',     lang: 'EN' },
  { text: 'インフレーターとその種類について教えてください',   lang: 'JA' },
]

interface Props {
  messages:     MessageType[]
  isLoading:    boolean
  onSuggestion: (text: string) => void
}

export default function ChatWindow({ messages, isLoading, onSuggestion }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const greeting  = useRef(getGreeting())

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  /* ── Welcome state ── */
  if (messages.length === 0) {
    const { headline } = greeting.current

    return (
      <div className="flex-1 overflow-y-auto flex flex-col items-center
                      justify-center px-6 pb-12"
           style={{ background: '#F8F9FB' }}>

        {/* Logo mark */}
        <div className="mb-6 text-center">
          <div className="w-14 h-14 rounded-2xl mx-auto mb-5 flex flex-col
                          items-center justify-center shadow-md"
               style={{ background: '#003DA5' }}>
            <span className="text-white font-black text-xl leading-none">
              A
            </span>
            <div className="w-7 mt-1 rounded-full"
                 style={{ height: '2px',
                          background: 'rgba(255,255,255,0.45)' }} />
          </div>

          {/* Greeting headline */}
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">
            {headline}
          </h1>

          {/* Single clean subtitle — no duplicate */}
          <p className="text-sm text-gray-400 mt-2 max-w-xs mx-auto
                        leading-relaxed">
            Ask anything about Autoliv's products and processes —
            in English or Japanese.
          </p>
        </div>

        {/* Try asking label */}
        <p className="text-xs uppercase tracking-widest font-semibold mb-3"
           style={{ color: '#9CA3AF' }}>
          Try asking
        </p>

        {/* Two suggestion chips side by side */}
        <div className="flex gap-2.5 flex items-stretch"
             style={{ maxWidth: '720px' }}>
          {SUGGESTIONS.map((s, i) => (
            <button
              key={i}
              onClick={() => onSuggestion(s.text)}
              disabled={isLoading}
              className="flex items-center gap-2.5 text-left px-4 py-3
                         bg-white rounded-xl text-sm text-gray-600
                         transition-all duration-150 shadow-sm
                         hover:shadow-md active:scale-[0.98]
                         disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ border: '1px solid #E5E7EB',
                        maxWidth: '280px',
               }}
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
              <span className="text-xs px-2 py-0.5 rounded-md font-bold shrink-0"
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
    <div className="flex-1 overflow-y-auto py-6"
         style={{ background: '#F8F9FB' }}>
      <div className="max-w-3xl mx-auto">
        {messages.map(msg => (
          <Message key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} className="h-2" />
      </div>
    </div>
  )
}