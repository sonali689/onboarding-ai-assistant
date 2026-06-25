export interface Source {
  file:      string
  subfolder: string
  lang_hint: string
}

export interface Message {
  id:          string
  role:        'user' | 'assistant'
  content:     string
  sources:     Source[]
  source_type: 'company_data' | 'general_knowledge' | null
  timestamp:   Date
  loading?:    boolean
}

export interface ChatSession {
  id:       string
  title:    string
  messages: Message[]
  date:     Date
}

export type ThinkingLevel = 'standard' | 'extended'