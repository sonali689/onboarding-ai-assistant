import type { Source, ThinkingLevel } from '../types'
import { authHeader } from './auth'

export interface AskResponse {
  answer:      string
  sources:     Source[]
  source_type: 'company_data' | 'general_knowledge'
  status:      'ok' | 'error'
}

export interface HistoryItem {
  role:    'user' | 'assistant'
  content: string
}

export interface SavedChat {
  id:         string
  user_email: string
  title:      string
  messages:   string
  created_at: string
  updated_at: string
}

// ── Non-streaming (kept as fallback) ─────────────────────────────────────────

export async function askQuestion(
  question: string,
  history: HistoryItem[] = [],
  level: ThinkingLevel = 'standard',
): Promise<AskResponse> {
  const res = await fetch('/ask', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body:    JSON.stringify({ question, history, level }),
  })
  if (!res.ok) throw new Error(`Server error: ${res.status}`)
  return res.json()
}

// ── Streaming ──────────────────────────────────────────────────────────────

export async function askQuestionStream(
  question: string,
  history: HistoryItem[],
  level: ThinkingLevel,
  onToken: (text: string) => void,
  onDone: (sources: Source[], sourceType: 'company_data' | 'general_knowledge') => void,
  onError: (message: string) => void,
): Promise<void> {
  const res = await fetch('/ask/stream', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body:    JSON.stringify({ question, history, level }),
  })

  if (!res.ok || !res.body) {
    onError(`Server error: ${res.status}`)
    return
  }

  const reader  = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  const handleLine = (line: string) => {
    const trimmed = line.trim()
    if (!trimmed) return
    try {
      const event = JSON.parse(trimmed)
      if (event.type === 'token') {
        onToken(event.text)
      } else if (event.type === 'done') {
        onDone(event.sources ?? [], event.source_type ?? 'general_knowledge')
      } else if (event.type === 'error') {
        onError(event.message ?? 'Unknown error')
      }
    } catch {
      // ignore malformed/partial line
    }
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) handleLine(line)
  }

  if (buffer.trim()) handleLine(buffer)
}

// ── Chat history ───────────────────────────────────────────────────────────

export async function loadChats(): Promise<SavedChat[]> {
  try {
    const res = await fetch('/api/chats', { headers: authHeader() })
    if (!res.ok) return []
    return res.json()
  } catch {
    return []
  }
}

export async function saveChat(chatId: string, title: string, messages: object[]): Promise<void> {
  try {
    await fetch('/api/chats', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', ...authHeader() },
      body:    JSON.stringify({ chat_id: chatId, title, messages: JSON.stringify(messages) }),
    })
  } catch {
    console.warn('Could not save chat')
  }
}

export async function deleteChat(chatId: string): Promise<void> {
  try {
    await fetch(`/api/chats/${chatId}`, { method: 'DELETE', headers: authHeader() })
  } catch {
    console.warn('Could not delete chat')
  }
}