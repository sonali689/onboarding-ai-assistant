import SourceCard from './SourceCard'
import type { Message as MessageType } from '../types'

interface Props {
  message: MessageType
}

export default function Message({ message }: Props) {
  const isUser = message.role === 'user'

  if (message.loading) {
    return (
      <div className="flex items-start gap-3 px-4 py-3">
        <div className="w-8 h-8 rounded-full bg-autoliv-blue
                        flex-shrink-0 flex items-center justify-center
                        text-white text-xs font-bold">
          A
        </div>
        <div className="bg-white border border-autoliv-border
                        rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
          <div className="flex gap-1 items-center h-5">
            {[0, 1, 2].map(i => (
              <span key={i}
                className="w-2 h-2 bg-autoliv-blue rounded-full animate-bounce"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`flex items-start gap-3 px-4 py-2
      ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>

      {/* Avatar */}
      <div className={`w-8 h-8 rounded-full flex-shrink-0
        flex items-center justify-center
        text-white text-xs font-bold mt-0.5
        ${isUser
          ? 'bg-autoliv-blue'
          : 'bg-autoliv-blue ring-2 ring-white ring-offset-1 ring-offset-autoliv-blue'
        }`}>
        {isUser ? 'U' : 'A'}
      </div>

      {/* Bubble + sources */}
      <div className={`max-w-[75%] space-y-1 flex flex-col
        ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm
          ${isUser
            ? 'bg-autoliv-blue text-white rounded-tr-sm'
            : 'bg-white text-autoliv-charcoal border border-autoliv-border rounded-tl-sm'
          }`}>
          {message.content.split('\n').map((line, i, arr) => (
            <span key={i}>
              {line}
              {i < arr.length - 1 && <br />}
            </span>
          ))}
        </div>

        {!isUser && (
          <div className="px-1 w-full">
            <SourceCard
              sources={message.sources}
              source_type={message.source_type}
            />
          </div>
        )}

        <p className="text-xs text-gray-400 px-1">
          {message.timestamp.toLocaleTimeString([], {
            hour: '2-digit', minute: '2-digit'
          })}
        </p>
      </div>
    </div>
  )
}