import { useRef, useState } from 'react'
import { Send } from 'lucide-react'

interface Props {
  onSend:   (text: string) => void
  disabled: boolean
}

export default function InputBar({ onSend, disabled }: Props) {
  const [text, setText] = useState('')
  const ref = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText('')
    if (ref.current) ref.current.style.height = 'auto'
  }

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = () => {
    if (!ref.current) return
    ref.current.style.height = 'auto'
    ref.current.style.height =
      Math.min(ref.current.scrollHeight, 140) + 'px'
  }

  return (
    <div className="border-t border-autoliv-border bg-white px-4 py-4">
      <div className="max-w-3xl mx-auto">
        <div className={`flex items-end gap-2 border rounded-2xl
          px-4 py-2 transition-all bg-autoliv-grey-light
          ${disabled
            ? 'border-autoliv-border'
            : 'border-autoliv-border focus-within:border-autoliv-blue focus-within:bg-white'
          }`}>
          <textarea
            ref={ref}
            value={text}
            onChange={e => { setText(e.target.value); handleInput() }}
            onKeyDown={handleKey}
            disabled={disabled}
            rows={1}
            placeholder="Ask in English or Japanese... | 日本語または英語で質問..."
            className="flex-1 bg-transparent resize-none outline-none
                       text-sm text-autoliv-charcoal placeholder-gray-400
                       leading-relaxed py-1 max-h-36 font-sans"
          />
          <button
            onClick={handleSend}
            disabled={disabled || !text.trim()}
            className={`w-8 h-8 rounded-full flex items-center
              justify-center flex-shrink-0 mb-0.5 transition-all
              ${disabled || !text.trim()
                ? 'bg-gray-200 cursor-not-allowed'
                : 'bg-autoliv-blue hover:bg-autoliv-blue-dark active:scale-95 cursor-pointer'
              }`}>
            <Send size={14} className="text-white" />
          </button>
        </div>
        <p className="text-center text-xs text-gray-400 mt-2">
          Internal use only · All data stays on Autoliv servers ·
          社内利用限定
        </p>
      </div>
    </div>
  )
}