import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { App, Button, Input, Segmented } from 'antd'
import { motion } from 'framer-motion'
import { api, setToken } from '../api/client'
import { useAuth } from '../store/auth'
import IcpFooter from '../components/IcpFooter'

type Mode = 'login' | 'register'

/** 登录 / 注册页。公网部署后每个访客用独立账号，进度互不影响。 */
export default function Auth() {
  const [mode, setMode] = useState<Mode>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [nickname, setNickname] = useState('')
  const [confirm, setConfirm] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { refreshMe, backendDown, enterOfflineDemo } = useAuth()
  const { message } = App.useApp()
  const navigate = useNavigate()
  const location = useLocation()

  const submit = async () => {
    const name = username.trim()
    if (name.length < 3) {
      message.warning('用户名至少 3 个字符')
      return
    }
    if (password.length < 6) {
      message.warning('密码至少 6 位')
      return
    }
    if (mode === 'register' && password !== confirm) {
      message.warning('两次输入的密码不一致')
      return
    }
    setSubmitting(true)
    try {
      const path = mode === 'login' ? '/api/auth/login' : '/api/auth/register'
      const body = mode === 'login'
        ? { username: name, password }
        : { username: name, password, nickname: nickname.trim() || name }
      const r = await api.post<{ access_token: string }>(path, body)
      setToken(r.access_token)
      const me = await refreshMe()
      if (!me.onboarding_done) {
        navigate('/welcome', { replace: true })
      } else {
        const from = (location.state as { from?: string } | null)?.from
        navigate(from && from !== '/login' ? from : '/', { replace: true })
      }
    } catch (e) {
      message.error((e as Error).message || '操作失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-10">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="game-panel w-full max-w-md p-8"
      >
        <div className="text-center mb-6">
          <div className="text-4xl mb-2">⚔️</div>
          <h1 className="text-xl font-bold text-indigo-700">代码冒险者</h1>
          <p className="text-slate-500 text-xs mt-1">软件工程 · 游戏化 AI 学习</p>
        </div>

        <Segmented
          block
          className="mb-6"
          value={mode}
          onChange={(v) => setMode(v as Mode)}
          options={[
            { label: '登录', value: 'login' },
            { label: '注册', value: 'register' },
          ]}
        />

        <div className="space-y-3">
          <div>
            <div className="text-xs text-slate-500 mb-1">用户名</div>
            <Input
              size="large"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="3-32 位，登录用"
              maxLength={32}
              onPressEnter={submit}
            />
          </div>
          {mode === 'register' && (
            <div>
              <div className="text-xs text-slate-500 mb-1">昵称（可选）</div>
              <Input
                size="large"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                placeholder="展示在排行榜上的名字"
                maxLength={16}
              />
            </div>
          )}
          <div>
            <div className="text-xs text-slate-500 mb-1">密码</div>
            <Input.Password
              size="large"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="至少 6 位"
              maxLength={64}
              onPressEnter={mode === 'login' ? submit : undefined}
            />
          </div>
          {mode === 'register' && (
            <div>
              <div className="text-xs text-slate-500 mb-1">确认密码</div>
              <Input.Password
                size="large"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                placeholder="再输一次"
                maxLength={64}
                onPressEnter={submit}
              />
            </div>
          )}
        </div>

        <Button
          type="primary"
          size="large"
          block
          className="mt-6"
          loading={submitting}
          onClick={submit}
        >
          {mode === 'login' ? '进入冒险' : '注册并创建角色'}
        </Button>

        <p className="text-center text-[11px] text-slate-400 mt-4 leading-relaxed">
          首次使用请先注册，注册后会引导你创建角色。
          <br />
          账号只保存在本站数据库中，不会用于其他用途。
        </p>

        {backendDown && (
          <div className="mt-4 pt-4 border-t border-indigo-100 text-center">
            <p className="text-[11px] text-amber-600 mb-2">
              当前未连接后端服务，登录与数据功能不可用。
            </p>
            <Button size="small" onClick={enterOfflineDemo}>
              以离线演示模式浏览界面
            </Button>
          </div>
        )}
      </motion.div>
      <IcpFooter />
    </div>
  )
}
