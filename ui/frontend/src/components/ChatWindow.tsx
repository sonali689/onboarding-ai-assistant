import { useEffect, useRef } from 'react'
import Message from './Message'
import type { Message as MessageType } from '../types'

const SUGGESTIONS = [
  { text: "What does the TechCenter do?",          lang: "EN" },
  { text: "エアバッグの仕組みを教えてください",      lang: "JA" },
  { text: "What is an inflator?",                  lang: "EN" },
  { text: "インフレーターとは何ですか？",            lang: "JA" },
  { text: "What are the safety regulations?",      lang: "EN" },
  { text: "シートベルトの役割は何ですか？",          lang: "JA" },
]

interface Props {
  messages:  MessageType[]
  isLoading: boolean
  onSuggestion: (text: string) => void
}

export default function ChatWindow({
  messages,
  isLoading,
  onSuggestion,
}: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const isEmpty = messages.length === 0

  return (
    <div className="flex-1 overflow-y-auto bg-autoliv-grey-light">

      {/* ── Empty state — welcome screen ─────────────────────── */}
      {isEmpty && (
        <div className="h-full flex flex-col items-center
                        justify-center px-6 pb-8">

          {/* Logo block */}
          <div className="mb-6 text-center">
            <div className="w-16 h-16 bg-autoliv-blue rounded-2xl
                            mx-auto mb-4 flex flex-col items-center
                            justify-center shadow-lg">
              <span className="text-white font-black text-xl
                               tracking-tight leading-none">
                A
              </span>
              <div className="h-0.5 bg-white/60 w-8 mt-1 rounded-full" />
            </div>
            <h2 className="text-xl font-semibold text-autoliv-charcoal">
              Autoliv Onboarding Assistant
            </h2>
            <p className="text-sm text-autoliv-blue font-medium mt-1">
              研修アシスタント
            </p>
            <p className="text-sm text-gray-400 mt-3 max-w-sm mx-auto
                          leading-relaxed">
              Ask anything about Autoliv's products, processes, and
              training materials in English or Japanese.
            </p>
          </div>

          {/* Capability badges */}
          <div className="flex gap-2 mb-8 flex-wrap justify-center">
            {[
              "📂 26 training manuals",
              "🌐 English + 日本語",
              "🔒 Fully local",
              "📄 Cited sources",
            ].map((badge, i) => (
              <span key={i}
                className="text-xs px-3 py-1.5 bg-white border
                           border-autoliv-border rounded-full
                           text-autoliv-grey shadow-sm">
                {badge}
              </span>
            ))}
          </div>

          {/* Suggestion chips */}
          <div className="w-full max-w-2xl">
            <p className="text-xs text-gray-400 text-center mb-3
                          uppercase tracking-wider font-medium">
              Try asking
            </p>
            <div className="grid grid-cols-2 gap-2">
              {SUGGESTIONS.map((s, i) => (
                <button key={i}
                  onClick={() => onSuggestion(s.text)}
                  disabled={isLoading}
                  className="flex items-start gap-2 text-left px-4 py-3
                             rounded-xl border border-autoliv-border
                             text-sm text-autoliv-grey bg-white
                             hover:border-autoliv-blue
                             hover:text-autoliv-blue
                             hover:bg-autoliv-blue-light
                             transition-all shadow-sm
                             disabled:opacity-50
                             disabled:cursor-not-allowed group">
                  <span className="text-xs px-1.5 py-0.5 rounded
                                   bg-autoliv-blue-light
                                   text-autoliv-blue font-semibold
                                   flex-shrink-0 mt-0.5
                                   group-hover:bg-autoliv-blue
                                   group-hover:text-white transition-all">
                    {s.lang}
                  </span>
                  <span>{s.text}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Messages ──────────────────────────────────────────── */}
      {!isEmpty && (
        <div className="py-4 space-y-1 max-w-4xl mx-auto w-full">
          {messages.map(msg => (
            <Message key={msg.id} message={msg} />
          ))}
          <div ref={bottomRef} className="h-4" />
        </div>
      )}

      {/* Scroll anchor when empty */}
      {isEmpty && <div ref={bottomRef} />}
    </div>
  )
}