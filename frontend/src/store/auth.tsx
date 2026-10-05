import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { api, clearToken, setToken } from '../api/client'
import type { Character } from '../types'

interface AuthState {
  user: { id: number; username: string; nickname: string; onboarding_done: boolean } | null
  character: Character | null
  loading: boolean
  /** 后端不可达（静态托管 / 服务未启动）时为 true，此时用本地演示角色撑住界面。 */
  offline: boolean
  refreshCharacter: () => Promise<void>
  refreshMe: () => Promise<void>
}

const AuthCtx = createContext<AuthState | null>(null)

// 后端连不上时的演示角色：只用于让页面正常渲染，所有真实数据仍来自接口。
const DEMO_CHARACTER: Character = {
  name: '代码冒险者',
  identity: '在校学生',
  class_key: 'backend',
  class_name: '后端战士',
  level: 1,
  exp: 0,
  exp_to_next: 100,
  coins: 100,
  hp: 3,
  max_hp: 3,
  title: '实习生',
  weekly_exp: 0,
  total_exp: 0,
  total_quests: 0,
  total_correct: 0,
  total_wrong: 0,
  total_chats: 0,
  total_bugs: 0,
  total_interviews: 0,
  streak_days: 0,
  onboarding_done: true,
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthState['user']>(null)
  const [character, setCharacter] = useState<Character | null>(null)
  const [loading, setLoading] = useState(true)
  const [offline, setOffline] = useState(false)

  const refreshMe = async () => {
    const me = await api.get<{ id: number; username: string; nickname: string; onboarding_done: boolean }>('/api/auth/me')
    setUser(me)
    if (me.onboarding_done) {
      const c = await api.get<Character>('/api/user/character')
      setCharacter(c)
    } else {
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

  // 无登录页：有 token 就复用，没有（或已失效）就静默走访客直通换一个。
  const ensureSession = async () => {
    if (localStorage.getItem('ca_token')) {
      try {
        await refreshMe()
        return
      } catch {
        clearToken()
      }
    }
    try {
      const r = await api.post<{ access_token: string }>('/api/auth/guest')
      setToken(r.access_token)
      await refreshMe()
    } catch {
      setOffline(true)
      setUser({ id: 0, username: 'guest', nickname: '冒险者', onboarding_done: true })
      setCharacter(DEMO_CHARACTER)
    }
  }

  useEffect(() => {
    ensureSession().finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <AuthCtx.Provider value={{ user, character, loading, offline, refreshCharacter, refreshMe }}>
      {children}
    </AuthCtx.Provider>
  )
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthCtx)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
