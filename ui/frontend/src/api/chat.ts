import type { Source } from '../types'
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

export async function askQuestion(
  question: string,
  history: HistoryItem[] = [],
): Promise<AskResponse> {
  const res = await fetch('/ask', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body:    JSON.stringify({ question, history }),
  })
  if (!res.ok) throw new Error(`Server error: ${res.status}`)
  return res.json()
}

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