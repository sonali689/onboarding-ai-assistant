import ReactMarkdown from 'react-markdown'
import SourceCard    from './SourceCard'
import type { Message as MessageType } from '../types'

interface Props { message: MessageType }

export default function Message({ message }: Props) {
  const isUser = message.role === 'user'

  /* ── Typing indicator ── */
  if (message.loading) {
    return (
      <div className="flex items-end gap-3 px-6 py-2 msg-animate">
        <div className="w-8 h-8 rounded-full shrink-0 flex items-center
                        justify-center text-white text-xs font-bold shadow-sm"
             style={{ background: '#003DA5' }}>
          A
        </div>
        <div className="bg-white rounded-2xl rounded-bl-sm px-5 py-4 shadow-sm"
             style={{ border: '1px solid #E5E7EB' }}>
          <div className="flex gap-1.5 items-center">
            <span className="w-2 h-2 rounded-full dot-1"
                  style={{ background: '#003DA5', display: 'block' }} />
            <span className="w-2 h-2 rounded-full dot-2"
                  style={{ background: '#003DA5', display: 'block' }} />
            <span className="w-2 h-2 rounded-full dot-3"
                  style={{ background: '#003DA5', display: 'block' }} />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`flex items-end gap-3 px-6 py-2 msg-animate
                     ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>

      {/* Avatar */}
      <div className="w-8 h-8 rounded-full shrink-0 flex items-center
                      justify-center text-white text-xs font-bold
                      shadow-sm mb-5"
           style={{ background: '#003DA5' }}>
        {isUser ? 'U' : 'A'}
      </div>

      {/* Content */}
      <div className={`flex flex-col gap-1 max-w-[75%]
                       ${isUser ? 'items-end' : 'items-start'}`}>

        {/* Bubble */}
        <div
          className="px-4 py-3 rounded-2xl text-sm leading-relaxed"
          style={isUser ? {
            background:            '#003DA5',
            color:                 '#FFFFFF',
            borderBottomRightRadius: '4px',
            boxShadow:             '0 1px 3px rgba(0,61,165,0.3)',
          } : {
            background:           '#FFFFFF',
            color:                '#111827',
            borderBottomLeftRadius: '4px',
            border:               '1px solid #E5E7EB',
            boxShadow:            '0 1px 4px rgba(0,0,0,0.06)',
          }}
        >
          {isUser ? (
            /* User messages — plain text */
            <span>{message.content}</span>
          ) : (
            /* Assistant messages — render markdown */
            <div className="prose prose-sm max-w-none"
                 style={{ color: 'inherit' }}>
              <ReactMarkdown
                components={{
                  /* Headers */
                  h2: ({ children }) => (
                    <h2 style={{
                      fontSize:     '13px',
                      fontWeight:   700,
                      color:        '#003DA5',
                      marginTop:    '12px',
                      marginBottom: '6px',
                      paddingBottom:'4px',
                      borderBottom: '1px solid #E5E7EB',
                    }}>
                      {children}
                    </h2>
                  ),
                  /* Horizontal rule — separator between sections */
                  hr: () => (
                    <hr style={{
                      border:    'none',
                      borderTop: '1px solid #E5E7EB',
                      margin:    '12px 0',
                    }} />
                  ),
                  /* Paragraphs */
                  p: ({ children }) => (
                    <p style={{ marginBottom: '8px', lineHeight: '1.6' }}>
                      {children}
                    </p>
                  ),
                  /* Bold */
                  strong: ({ children }) => (
                    <strong style={{
                      fontWeight: 600,
                      color:      '#003DA5',
                    }}>
                      {children}
                    </strong>
                  ),
                  /* Bullet lists */
                  ul: ({ children }) => (
                    <ul style={{
                      paddingLeft:  '16px',
                      marginBottom: '8px',
                      listStyle:    'disc',
                    }}>
                      {children}
                    </ul>
                  ),
                  li: ({ children }) => (
                    <li style={{
                      marginBottom: '4px',
                      lineHeight:   '1.5',
                    }}>
                      {children}
                    </li>
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Sources */}
        {!isUser && (
          <div className="w-full px-1">
            <SourceCard
              sources={message.sources}
              source_type={message.source_type}
            />
          </div>
        )}

        {/* Timestamp */}
        <p className="text-xs px-1" style={{ color: '#9CA3AF' }}>
          {message.timestamp.toLocaleTimeString([], {
            hour: '2-digit', minute: '2-digit',
          })}
        </p>
      </div>
    </div>
  )
}