import type { Source } from '../types'

export interface AskResponse {
  answer:      string
  sources:     Source[]
  source_type: 'company_data' | 'general_knowledge'
  status:      'ok' | 'error'
}

export async function askQuestion(question: string): Promise<AskResponse> {
  const response = await fetch('/ask', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ question }),
  })

  if (!response.ok) {
    throw new Error(`Server error: ${response.status}`)
  }

  return response.json()
}