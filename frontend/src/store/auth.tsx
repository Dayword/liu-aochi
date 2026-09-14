import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { api, clearToken, setToken } from '../api/client'
import type { Character } from '../types'

interface AuthState {
  user: { id: number; username: string; nickname: string; onboarding_done: boolean } | null
  character: Character | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (username: string, password: string, nickname: string) => Promise<void>
  logout: () => void
  refreshCharacter: () => Promise<void>
  refreshMe: () => Promise<void>
}

const AuthCtx = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthState['user']>(null)
  const [character, setCharacter] = useState<Character | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshMe = async () => {
    try {
      const me = await api.get<{ id: number; username: string; nickname: string; onboarding_done: boolean }>('/api/auth/me')
      setUser(me)
      if (me.onboarding_done) {
        const c = await api.get<Character>('/api/user/character')
        setCharacter(c)
      } else {
        setCharacter(null)
      }
    } catch {
      clearToken()
      setUser(null)
      setCharacter(null)
    }
  }

  const refreshCharacter = async () => {
    try {
      const c = await api.get<Character>('/api/user/character')
      setCharacter(c)
    } catch {
      /* ignore */
    }
  }

  useEffect(() => {
    const token = localStorage.getItem('ca_token')
    if (!token) {
      setLoading(false)
      return
    }
    refreshMe().finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const login = async (username: string, password: string) => {
    const r = await api.post<{ access_token: string }>('/api/auth/login', { username, password })
    setToken(r.access_token)
    await refreshMe()
  }

  const register = async (username: string, password: string, nickname: string) => {
    const r = await api.post<{ access_token: string }>('/api/auth/register', {
      username,
      password,
      nickname,
    })
    setToken(r.access_token)
    await refreshMe()
  }

  const logout = () => {
    clearToken()
    setUser(null)
    setCharacter(null)
  }

  return (
    <AuthCtx.Provider value={{ user, character, loading, login, register, logout, refreshCharacter, refreshMe }}>
      {children}
    </AuthCtx.Provider>
  )
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthCtx)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
