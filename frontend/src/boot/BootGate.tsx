import { useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { useAuth } from '../store/auth'
import BootScreen from './BootScreen'

/**
 * 决定这次进入要不要播入场动画。
 *
 * 规则（2026-11-03 定的）：
 *   · 登录成功 → 播；已登录用户每次「进入」（新标签 / 重开浏览器 / 刷新）→ 播；
 *   · 站内跳转不播 —— 用内存里的 shownRef 锁死，不落 storage，
 *     这样刷新就是一次新进入，天然会重播；
 *   · 登录页不播；`?boot=0` 关掉，`?boot=1` 强制播（调试用）；
 *   · 系统开了「减少动态效果」就整段跳过，不为难人。
 */
export default function BootGate() {
  const { user, character, loading } = useAuth()
  const location = useLocation()
  const [show, setShow] = useState(false)
  const decidedRef = useRef(false)

  useEffect(() => {
    if (decidedRef.current || loading) return
    if (!user) return
    if (location.pathname === '/login') return
    decidedRef.current = true

    const params = new URLSearchParams(location.search)
    if (params.get('boot') === '0') return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

    setShow(true)
  }, [loading, user, location.pathname, location.search])

  if (!show) return null

  return (
    <BootScreen
      level={character?.level ?? 1}
      onDone={() => setShow(false)}
    />
  )
}
