import { useEffect, useMemo, useRef, useState } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { Avatar, Progress } from 'antd'
import {
  BookOutlined,
  BugOutlined,
  CommentOutlined,
  CrownOutlined,
  EnvironmentOutlined,
  HomeOutlined,
  LogoutOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import { useAuth } from '../store/auth'
import IcpFooter from './IcpFooter'

const NAV = [
  { to: '/', label: '首页', icon: <HomeOutlined /> },
  { to: '/learn', label: '引导式学习', icon: <BookOutlined /> },
  { to: '/levels', label: '关卡地图', icon: <EnvironmentOutlined /> },
  { to: '/chat', label: 'AI 导师', icon: <CommentOutlined /> },
  { to: '/interview', label: '面试闯关', icon: <CrownOutlined /> },
  { to: '/bugs', label: 'Bug 猎人', icon: <BugOutlined /> },
  { to: '/profile', label: '个人中心', icon: <UserOutlined /> },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const { character, offline, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const expPct = useMemo(() => {
    if (!character) return 0
    return Math.min(100, Math.round((character.exp / character.exp_to_next) * 100))
  }, [character])

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  /**
   * 「沉浸页」：这些页面要吃满整屏、自己带返回按钮，所以不叠顶部导航和页脚。
   * - /quest/:code        闯关答题
   * - /sandbox            独立代码沙箱
   * - /learn/:code/practice  动手任务（题目 + 编辑器 + 结果分屏）
   */
  const isFullScreen =
    location.pathname.startsWith('/quest') ||
    location.pathname.startsWith('/sandbox') ||
    /^\/learn\/[^/]+\/practice$/.test(location.pathname)
  const hideChrome = isFullScreen

  // 手机端导航是横向滚动的：切页时把当前项滚到可见位置，并给右侧留个「还有更多」的渐隐提示
  const navRef = useRef<HTMLElement | null>(null)
  const [edge, setEdge] = useState({ left: false, right: false })

  const syncEdge = () => {
    const el = navRef.current
    if (!el) return
    const max = el.scrollWidth - el.clientWidth
    setEdge({ left: el.scrollLeft > 4, right: max > 4 && el.scrollLeft < max - 4 })
  }

  useEffect(() => {
    syncEdge()
    const raf = requestAnimationFrame(syncEdge)
    return () => cancelAnimationFrame(raf)
  }, [location.pathname])

  useEffect(() => {
    const el = navRef.current
    const active = el?.querySelector<HTMLElement>('[data-active="true"]')
    if (!el || !active) return
    const target = active.offsetLeft - (el.clientWidth - active.clientWidth) / 2
    el.scrollTo({ left: Math.max(0, target), behavior: 'smooth' })
  }, [location.pathname])

  return (
    <div className="min-h-screen md:flex">
      {/* ===== 手机 / 平板竖屏：顶部导航（品牌条 + 可横滑的导航胶囊） ===== */}
      {!hideChrome && (
        <header className="md:hidden sticky top-0 z-30 bg-white/95 backdrop-blur border-b border-indigo-200">
          <div className="flex items-center gap-2 px-3 h-12">
            <span className="text-xl leading-none">⚔️</span>
            <span className="font-bold text-[15px] text-indigo-700 truncate">代码冒险者</span>
            {character && (
              <div className="ml-auto flex items-center gap-2 shrink-0">
                <span className="text-[11px] text-amber-600 font-medium">
                  Lv.{character.level}
                </span>
                <span className="text-[11px] text-slate-600">🪙 {character.coins}</span>
              </div>
            )}
            <button
              onClick={handleLogout}
              aria-label="退出登录"
              className="shrink-0 ml-1 w-8 h-8 flex items-center justify-center rounded-lg text-slate-400 active:bg-slate-100"
            >
              <LogoutOutlined />
            </button>
          </div>
          <div className="relative">
            <nav
              ref={navRef}
              onScroll={syncEdge}
              className="flex gap-1.5 overflow-x-auto no-scrollbar px-2 pb-2"
            >
              {NAV.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  data-active={location.pathname === item.to}
                  className={({ isActive }) =>
                    `flex items-center gap-1 px-3 py-1.5 rounded-full text-[12px] whitespace-nowrap shrink-0 transition-colors ${
                      isActive
                        ? 'bg-indigo-600 text-white font-medium shadow-sm'
                        : 'bg-slate-100 text-slate-600 active:bg-slate-200'
                    }`
                  }
                >
                  <span className="text-[13px] leading-none">{item.icon}</span>
                  {item.label}
                </NavLink>
              ))}
            </nav>
            {/* 横滑提示：左侧/右侧还有内容时渐隐，纯装饰不挡点击 */}
            {edge.left && (
              <div className="pointer-events-none absolute inset-y-0 left-0 w-6 bg-gradient-to-r from-white to-transparent" />
            )}
            {edge.right && (
              <div className="pointer-events-none absolute inset-y-0 right-0 w-6 bg-gradient-to-l from-white to-transparent" />
            )}
          </div>
        </header>
      )}

      {/* ===== 桌面：左侧固定导航 ===== */}
      {!hideChrome && (
        <aside className="hidden md:flex w-60 shrink-0 border-r border-indigo-200 bg-[#ffffff]/80 backdrop-blur flex-col sticky top-0 h-screen z-20">
          <div className="px-5 py-4 flex items-center gap-2">
            <span className="text-3xl">⚔️</span>
            <div>
              <div className="font-bold text-indigo-700">代码冒险者</div>
              <div className="text-[11px] text-slate-500">软件工程 · 游戏化学习</div>
            </div>
          </div>
          <nav className="flex-1 px-3 space-y-1 overflow-y-auto">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all ${
                    isActive
                      ? 'bg-indigo-100 text-indigo-700 font-medium shadow-sm'
                      : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'
                  }`
                }
              >
                <span className="text-lg">{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>
          {character && (
            <div className="p-3 border-t border-indigo-200">
              <div className="flex items-center gap-2 mb-2">
                <Avatar className="bg-indigo-500">{character.class_name.slice(0, 1)}</Avatar>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium truncate">{character.name}</div>
                  <div className="text-[11px] text-amber-600">
                    {character.class_name} · Lv.{character.level} {character.title}
                  </div>
                </div>
              </div>
              <Progress
                percent={expPct}
                size="small"
                strokeColor="#7c3aed"
                trailColor="#e2e8f0"
                format={() => `${character.exp}/${character.exp_to_next}`}
              />
              <div className="flex justify-between text-[11px] text-slate-500 mt-1">
                <span>🪙 {character.coins}</span>
                <span>❤️ {character.hp}/{character.max_hp}</span>
              </div>
              <button
                onClick={handleLogout}
                className="mt-2 w-full text-[11px] text-slate-400 hover:text-slate-600 transition-colors"
              >
                退出登录
              </button>
            </div>
          )}
        </aside>
      )}

      {/* 主内容 */}
      <main className="flex-1 min-w-0">
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className={isFullScreen ? '' : 'px-3 py-4 md:p-8 max-w-6xl mx-auto'}
        >
          {children}
        </motion.div>
        {!hideChrome && <IcpFooter />}
      </main>

      {offline && (
        <div className="fixed bottom-3 right-3 z-50 text-[11px] text-slate-500 bg-white/90 border border-slate-200 rounded-full px-3 py-1 shadow-sm">
          离线演示模式 · 后端未连接
        </div>
      )}
    </div>
  )
}
