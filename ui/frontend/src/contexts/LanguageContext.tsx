import {
  createContext, useContext,
  useState, useCallback,
} from 'react'
import type { ReactNode }        from 'react'
import { strings }               from '../i18n/strings'
import type { Lang, Strings }    from '../i18n/strings'

interface LanguageContextType {
  lang:       Lang
  t:          Strings
  toggleLang: () => void
}

const LanguageContext = createContext<LanguageContextType | null>(null)

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>('en')

  const toggleLang = useCallback(() => {
    setLang(prev => prev === 'en' ? 'ja' : 'en')
  }, [])

  const t = strings[lang] as Strings

  return (
    <LanguageContext.Provider value={{ lang, t, toggleLang }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLang() {
  const ctx = useContext(LanguageContext)
  if (!ctx) throw new Error('useLang must be used inside LanguageProvider')
  return ctx
}