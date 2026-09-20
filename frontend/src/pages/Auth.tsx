import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button, Input, App } from 'antd'
import { motion } from 'framer-motion'
import { useAuth } from '../store/auth'

export default function Auth({ mode }: { mode: 'login' | 'register' }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [nickname, setNickname] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { login, register } = useAuth()
  const { message } = App.useApp()
  const navigate = useNavigate()

  const submit = async () => {
    if (!username.trim() || !password.trim()) {
      message.warning('请输入用户名和密码')
      return
    }
    if (mode === 'register' && password.length < 6) {
      message.warning('密码至少 6 位')
      return
    }
    setSubmitting(true)
    try {
      if (mode === 'login') await login(username.trim(), password)
      else await register(username.trim(), password, nickname.trim() || username.trim())
      message.success(mode === 'login' ? '欢迎回来！' : '注册成功，开始冒险吧！')
      navigate('/')
    } catch (e) {
      message.error((e as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none opacity-20 text-[10rem] md:text-[16rem] select-none flex items-center justify-center">
        ⚔️
      </div>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="game-panel w-full max-w-md p-8 relative z-10"
      >
        <div className="text-center mb-6">
          <div className="text-5xl mb-2 animate-float inline-block">🗺️</div>
          <h1 className="text-2xl font-bold text-indigo-700">代码冒险者</h1>
          <p className="text-slate-500 text-sm mt-1">软件工程游戏化 AI 问答系统</p>
        </div>

        <div className="space-y-3">
          {mode === 'register' && (
            <Input
              size="large"
              placeholder="昵称（可选）"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              maxLength={32}
            />
          )}
          <Input
            size="large"
            placeholder="用户名"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            maxLength={32}
          />
          <Input.Password
            size="large"
            placeholder="密码"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onPressEnter={submit}
          />
          <Button
            type="primary"
            size="large"
            block
            loading={submitting}
            onClick={submit}
            className="glow-btn"
          >
            {mode === 'login' ? '登录 · 继续冒险' : '创建账号 · 开始冒险'}
          </Button>
        </div>

        <div className="text-center mt-5 text-sm text-slate-500">
          {mode === 'login' ? (
            <>
              还没有账号？<Link to="/register" className="text-indigo-600 hover:text-indigo-700">立即注册</Link>
            </>
          ) : (
            <>
              已有账号？<Link to="/login" className="text-indigo-600 hover:text-indigo-700">直接登录</Link>
            </>
          )}
        </div>

        <div className="mt-6 p-3 rounded-xl bg-indigo-50 border border-indigo-200 text-xs text-slate-500">
          💡 边玩边学：注册后选择职业分支，闯关答题、AI 导师答疑、模拟面试，一路升级拿到「虚拟 Offer」。
        </div>
      </motion.div>
    </div>
  )
}
