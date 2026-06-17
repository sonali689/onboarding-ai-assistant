import type { Source } from '../types'

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

export async function askQuestion(
  question: string,
  history: HistoryItem[] = [],
): Promise<AskResponse> {
  const res = await fetch('/ask', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ question, history }),
  })
  if (!res.ok) throw new Error(`Server error: ${res.status}`)
  return res.json()
}
