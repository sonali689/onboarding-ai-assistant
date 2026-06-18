import {
  createContext, useContext, useState, useEffect, useCallback,
} from 'react'
import type { ReactNode } from 'react'
import { saveToken, clearAuth, getSavedUser, apiVerifyToken } from '../api/auth'
import type { User } from '../api/auth'

interface AuthContextType {
  user:    User | null
  loading: boolean
  setAuth: (token: string, user: User) => void
  signOut: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user,    setUser]    = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const init = async () => {
      const saved = getSavedUser()
      if (saved) {
        setUser(saved)
        const verified = await apiVerifyToken()
        if (!verified) {
          clearAuth()
          setUser(null)
        } else {
          setUser(verified)
        }
      }
      setLoading(false)
    }
    init()
  }, [])

  const setAuth = useCallback((token: string, user: User) => {
    saveToken(token, user)
    setUser(user)
  }, [])

  const signOut = useCallback(() => {
    clearAuth()
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, setAuth, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}