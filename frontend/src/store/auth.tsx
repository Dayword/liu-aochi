import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { api, clearToken, setToken } from '../api/client'
import type { Character } from '../types'

export interface MeInfo {
  id: number
  username: string
  nickname: string
  /** 11 位学号（老账号可能为空字符串） */
  student_id: string
  real_name: string
  grade: string
  class_code: string
  onboarding_done: boolean
}

interface AuthState {
  user: MeInfo | null
  character: Character | null
  loading: boolean
  /** 后端不可达（静态托管 / 服务未启动）时为 true */
  backendDown: boolean
  /** 用户主动进入的只读演示模式（GitHub Pages 这类没有后端的场景） */
  offline: boolean
  refreshCharacter: () => Promise<void>
  refreshMe: () => Promise<MeInfo>
  logout: () => void
  enterOfflineDemo: () => void
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
  const [backendDown, setBackendDown] = useState(false)
  const [offline, setOffline] = useState(false)

  const refreshMe = async (): Promise<MeInfo> => {
    const me = await api.get<MeInfo>('/api/auth/me')
    setUser(me)
    if (me.onboarding_done) {
      const c = await api.get<Character>('/api/user/character')
      setCharacter(c)
    } else {
      setCharacter(null)
    }
    return me
  }

  const refreshCharacter = async () => {
    try {
      const c = await api.get<Character>('/api/user/character')
      setCharacter(c)
    } catch {
      /* ignore */
    }
  }

  const logout = () => {
    clearToken()
    setUser(null)
    setCharacter(null)
    setOffline(false)
  }

  const enterOfflineDemo = () => {
    setOffline(true)
    setUser({
      id: 0,
      username: 'demo',
      nickname: '冒险者',
      student_id: '20230000000',
      real_name: '演示同学',
      grade: '2023',
      class_code: '00000',
      onboarding_done: true,
    })
    setCharacter(DEMO_CHARACTER)
  }

  // 有 token 就校验并复用；没有就停在登录页（不再自动直通登录）。
  // 后端不可达时只标记 backendDown，让登录页显示「离线演示」入口，
  // 这样静态托管（GitHub Pages）下也不会白屏。
  const ensureSession = async () => {
    if (!localStorage.getItem('ca_token')) {
      // 没有 token 时顺手探一次后端：静态托管（无后端）下据此显示「离线演示」入口
      try {
        await api.get('/api/health')
      } catch {
        setBackendDown(true)
      }
      return
    }
    try {
      await refreshMe()
    } catch {
      clearToken()
      setBackendDown(true)
    }
  }

  useEffect(() => {
    ensureSession().finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <AuthCtx.Provider value={{
      user, character, loading, backendDown, offline,
      refreshCharacter, refreshMe, logout, enterOfflineDemo,
    }}>
      {children}
    </AuthCtx.Provider>
  )
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthCtx)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
