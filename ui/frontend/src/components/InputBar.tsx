import { useRef, useState } from 'react'
import { ArrowUp } from 'lucide-react'

interface Props {
  onSend:   (text: string) => void
  disabled: boolean
}

export default function InputBar({ onSend, disabled }: Props) {
  const [text, setText] = useState('')
  const ref = useRef<HTMLTextAreaElement>(null)

  const canSend = text.trim().length > 0 && !disabled

  const send = () => {
    if (!canSend) return
    onSend(text.trim())
    setText('')
    if (ref.current) ref.current.style.height = 'auto'
  }

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  const onInput = () => {
    if (!ref.current) return
    ref.current.style.height = 'auto'
    ref.current.style.height = Math.min(ref.current.scrollHeight, 140) + 'px'
  }

  return (
    <div className="bg-white px-6 py-4"
         style={{ borderTop: '1px solid #E5E7EB' }}>
      <div className="max-w-3xl mx-auto">

        {/* Input row */}
        <div className="flex items-end gap-3 bg-white rounded-2xl px-4 py-3
                        transition-all duration-150"
             style={{ border: '1.5px solid #E5E7EB',
                      boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}
             onFocus={() => {}}
        >
          <textarea
            ref={ref}
            value={text}
            onChange={e => { setText(e.target.value); onInput() }}
            onKeyDown={onKey}
            disabled={disabled}
            rows={1}
            placeholder="Ask in English or Japanese... | 日本語または英語で質問..."
            className="flex-1 resize-none outline-none text-sm
                       text-gray-800 placeholder-gray-400 leading-relaxed
                       py-0.5 bg-transparent max-h-36 font-sans"
          />

          {/* Send button */}
          <button
            onClick={send}
            disabled={!canSend}
            className="w-8 h-8 rounded-full flex items-center justify-center
                       shrink-0 transition-all duration-150 active:scale-90"
            style={{
              background: canSend ? '#003DA5' : '#E5E7EB',
              cursor:     canSend ? 'pointer' : 'not-allowed',
            }}>
            <ArrowUp size={15}
                     className={canSend ? 'text-white' : 'text-gray-400'} />
          </button>
        </div>

        <p className="text-center text-xs mt-2.5" style={{ color: '#9CA3AF' }}>
          Internal use only · Data stays on Autoliv servers · 社内利用限定
        </p>
      </div>
    </div>
  )
}