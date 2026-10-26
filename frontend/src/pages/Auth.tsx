import { useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { App, Button, Input, Segmented } from 'antd'
import { motion } from 'framer-motion'
import { api, setToken } from '../api/client'
import { useAuth } from '../store/auth'
import IcpFooter from '../components/IcpFooter'

type Mode = 'login' | 'register'

/** 密码四类字符规则：与后端 app/schemas.py 的 password_problems() 保持一致 */
const PWD_RULES = [
  { key: 'len', label: '8~64 位', test: (p: string) => p.length >= 8 && p.length <= 64 },
  { key: 'upper', label: '大写字母', test: (p: string) => /[A-Z]/.test(p) },
  { key: 'lower', label: '小写字母', test: (p: string) => /[a-z]/.test(p) },
  { key: 'digit', label: '数字', test: (p: string) => /\d/.test(p) },
  { key: 'special', label: '特殊符号', test: (p: string) => /[^A-Za-z0-9\s]/.test(p) },
]

/**
 * 登录 / 注册页。
 *
 * 2026-10-26 改版：账号 = 11 位学号（前 4 位年级 / 5~9 位班级 / 后 2 位座号），
 * 姓名进入排行榜展示。登录状态存在 localStorage，下次打开直接进站。
 */
export default function Auth() {
  const [mode, setMode] = useState<Mode>('login')
  const [studentId, setStudentId] = useState('')
  const [realName, setRealName] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { refreshMe, backendDown, enterOfflineDemo } = useAuth()
  const { message } = App.useApp()
  const navigate = useNavigate()
  const location = useLocation()

  const sid = studentId.trim()
  const pwdOk = useMemo(() => PWD_RULES.every((r) => r.test(password)), [password])
  /** 学号 11 位后实时回显年级/班级，帮学生确认自己没输错 */
  const parsed = useMemo(() => {
    if (!/^\d{11}$/.test(sid)) return null
    return { grade: sid.slice(0, 4), cls: sid.slice(4, 9), seat: sid.slice(9, 11) }
  }, [sid])

  const submit = async () => {
    if (!/^\d{11}$/.test(sid)) {
      message.warning('学号必须是 11 位数字')
      return
    }
    if (mode === 'register') {
      if (!realName.trim()) {
        message.warning('请填写姓名')
        return
      }
      if (!pwdOk) {
        message.warning('密码需同时包含大写字母、小写字母、数字、特殊符号（8~64 位）')
        return
      }
      if (password !== confirm) {
        message.warning('两次输入的密码不一致')
        return
      }
    } else if (!password) {
      message.warning('请输入密码')
      return
    }

    setSubmitting(true)
    try {
      const path = mode === 'login' ? '/api/auth/login' : '/api/auth/register'
      const body = mode === 'login'
        ? { student_id: sid, password }
        : { student_id: sid, real_name: realName.trim(), password, confirm_password: confirm }
      const r = await api.post<{ access_token: string }>(path, body)
      setToken(r.access_token)
      await refreshMe()
      // 新手引导已下线：注册/登录后直接进首页（或回到原本想去的页面）
      const from = (location.state as { from?: string } | null)?.from
      navigate(from && from !== '/login' ? from : '/', { replace: true })
    } catch (e) {
      message.error((e as Error).message || '操作失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="game-panel w-full max-w-md p-6 md:p-8"
      >
        <div className="text-center mb-5">
          <div className="text-4xl mb-2">⚔️</div>
          <h1 className="text-xl font-bold text-indigo-700">代码冒险者</h1>
          <p className="text-slate-500 text-xs mt-1">软件工程 · 游戏化 AI 学习</p>
        </div>

        <Segmented
          block
          className="mb-5"
          value={mode}
          onChange={(v) => setMode(v as Mode)}
          options={[
            { label: '登录', value: 'login' },
            { label: '注册', value: 'register' },
          ]}
        />

        <div className="space-y-3">
          <div>
            <div className="text-xs text-slate-500 mb-1">学号</div>
            <Input
              size="large"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value.replace(/\D/g, '').slice(0, 11))}
              placeholder="11 位学号，例如 20230614224"
              inputMode="numeric"
              maxLength={11}
              onPressEnter={() => mode === 'login' && submit()}
            />
            {parsed ? (
              <div className="text-[11px] text-emerald-600 mt-1">
                {parsed.grade} 级 · 班级 {parsed.cls} · 座号 {parsed.seat}
              </div>
            ) : (
              <div className="text-[11px] text-slate-400 mt-1">
                前 4 位年级 / 5~9 位班级 / 后 2 位座号
              </div>
            )}
          </div>

          {mode === 'register' && (
            <div>
              <div className="text-xs text-slate-500 mb-1">姓名</div>
              <Input
                size="large"
                value={realName}
                onChange={(e) => setRealName(e.target.value)}
                placeholder="真实姓名，会显示在排行榜上"
                maxLength={20}
              />
            </div>
          )}

          <div>
            <div className="text-xs text-slate-500 mb-1">密码</div>
            <Input.Password
              size="large"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={mode === 'login' ? '请输入密码' : '大写+小写+数字+特殊符号'}
              maxLength={64}
              onPressEnter={mode === 'login' ? submit : undefined}
            />
            {mode === 'register' && (
              <div className="flex flex-wrap gap-1 mt-1.5">
                {PWD_RULES.map((r) => {
                  const ok = r.test(password)
                  return (
                    <span
                      key={r.key}
                      className={`text-[10px] px-1.5 py-0.5 rounded border ${
                        ok
                          ? 'border-emerald-300 bg-emerald-50 text-emerald-600'
                          : 'border-slate-200 bg-slate-50 text-slate-400'
                      }`}
                    >
                      {ok ? '✓' : '·'} {r.label}
                    </span>
                  )
                })}
              </div>
            )}
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
                status={confirm && confirm !== password ? 'error' : undefined}
              />
              {confirm && confirm !== password && (
                <div className="text-[11px] text-rose-500 mt-1">两次输入的密码不一致</div>
              )}
            </div>
          )}
        </div>

        <Button
          type="primary"
          size="large"
          block
          className="mt-5"
          loading={submitting}
          onClick={submit}
        >
          {mode === 'login' ? '进入冒险' : '注册'}
        </Button>

        <p className="text-center text-[11px] text-slate-400 mt-3 leading-relaxed">
          {mode === 'login'
            ? '登录状态会保存在本机，下次打开直接进入。'
            : '注册后请完成一次角色创建，随后即可开始学习。'}
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
