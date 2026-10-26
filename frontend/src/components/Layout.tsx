import { useEffect, useMemo } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { App, Progress } from 'antd'
import {
  BookOutlined,
  BugOutlined,
  CommentOutlined,
  CrownOutlined,
  EnvironmentOutlined,
  HomeOutlined,
  LogoutOutlined,
  TrophyOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import { useAuth } from '../store/auth'
import IcpFooter from './IcpFooter'

/**
 * 底部四 Tab：手机端的主要导航。
 * 顺序固定为 首页 / 引导式学习 / AI 导师 / 我的。
 * 「AI 导师」这一栏把 /sandbox 也算进来，因为沙箱是从导师页跳过去的；
 * 「我的」吃掉 /leaderboard，因为排行榜是从我的页进去的。
 */
const TABS = [
  { to: '/', label: '首页', match: (p: string) => p === '/', icon: <HomeOutlined /> },
  {
    to: '/learn',
    label: '引导式学习',
    match: (p: string) => p.startsWith('/learn'),
    icon: <BookOutlined />,
  },
  {
    to: '/chat',
    label: 'AI导师',
    match: (p: string) => p.startsWith('/chat') || p.startsWith('/sandbox'),
    icon: <CommentOutlined />,
  },
  {
    to: '/profile',
    label: '我的',
    match: (p: string) => p.startsWith('/profile') || p.startsWith('/leaderboard'),
    icon: <UserOutlined />,
  },
]

/** 桌面端左侧栏：按 学习 / 陪练 分组 */
const NAV_GROUPS = [
  { title: '', items: [{ to: '/', label: '首页', icon: <HomeOutlined /> }] },
  {
    title: '学习',
    items: [
      { to: '/learn', label: '引导式学习', icon: <BookOutlined /> },
      { to: '/levels', label: '关卡地图', icon: <EnvironmentOutlined /> },
      { to: '/leaderboard', label: '排行榜', icon: <TrophyOutlined /> },
    ],
  },
  {
    title: '陪练',
    items: [
      { to: '/chat', label: 'AI 导师', icon: <CommentOutlined /> },
      { to: '/interview', label: '面试闯关', icon: <CrownOutlined /> },
      { to: '/bugs', label: 'Bug 猎人', icon: <BugOutlined /> },
    ],
  },
  { title: '', items: [{ to: '/profile', label: '我的', icon: <UserOutlined /> }] },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const { character, user, offline, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const { modal } = App.useApp()
  const expPct = useMemo(() => {
    if (!character) return 0
    return Math.min(100, Math.round((character.exp / character.exp_to_next) * 100))
  }, [character])

  /** 退出登录：先弹确认框，避免误触把登录态清掉 */
  const askLogout = () => {
    modal.confirm({
      title: '确认退出登录？',
      content: '退出后需要重新用学号和密码登录，学习进度不会丢失。',
      okText: '退出登录',
      okButtonProps: { danger: true },
      cancelText: '再想想',
      onOk: () => {
        logout()
        navigate('/login', { replace: true })
      },
    })
  }

  /**
   * 「沉浸页」：这些页面要吃满整屏、自己带返回按钮，所以不叠导航和页脚。
   * - /quest/:code        闯关答题
   * - /sandbox            独立代码沙箱
   * - /learn/:code/practice  动手任务（题目 + 编辑器 + 结果分屏）
   */
  const hideChrome =
    location.pathname.startsWith('/quest') ||
    location.pathname.startsWith('/sandbox') ||
    /^\/learn\/[^/]+\/practice$/.test(location.pathname)

  return (
    <div className="min-h-screen md:flex">
      {/* ===== 手机：极简品牌条（导航在底部） ===== */}
      {!hideChrome && (
        <header className="md:hidden sticky top-0 z-30 bg-white/95 backdrop-blur border-b border-indigo-200">
          <div className="flex items-center gap-2 px-3 h-11">
            <span className="text-lg leading-none">⚔️</span>
            <span className="font-bold text-[15px] text-indigo-700 truncate">代码冒险者</span>
            {character && (
              <span className="ml-auto text-[11px] text-amber-600 font-medium shrink-0">
                Lv.{character.level} · {character.title}
              </span>
            )}
          </div>
        </header>
      )}

      {/* ===== 桌面：左侧固定导航 ===== */}
      {!hideChrome && (
        <aside className="hidden md:flex w-56 shrink-0 border-r border-indigo-200 bg-white/80 backdrop-blur flex-col sticky top-0 h-screen z-20">
          <div className="px-4 py-4 flex items-center gap-2">
            <span className="text-3xl">⚔️</span>
            <div>
              <div className="font-bold text-indigo-700">代码冒险者</div>
              <div className="text-[11px] text-slate-500">软件工程 · 游戏化学习</div>
            </div>
          </div>
          <nav className="flex-1 px-3 space-y-3 overflow-y-auto pb-3">
            {NAV_GROUPS.map((g, gi) => (
              <div key={gi} className="space-y-1">
                {g.title && (
                  <div className="px-3 pt-1 text-[10px] font-medium text-slate-400 tracking-wide">
                    {g.title}
                  </div>
                )}
                {g.items.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === '/'}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition-all ${
                        isActive
                          ? 'bg-indigo-100 text-indigo-700 font-medium shadow-sm'
                          : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'
                      }`
                    }
                  >
                    <span className="text-base">{item.icon}</span>
                    <span>{item.label}</span>
                  </NavLink>
                ))}
              </div>
            ))}
          </nav>
          {character && (
            <div className="p-3 border-t border-indigo-200">
              <div className="text-xs font-medium truncate">
                {user?.real_name || character.name}
              </div>
              <div className="text-[11px] text-slate-500 truncate">
                {user?.student_id ? `学号 ${user.student_id}` : character.class_name}
              </div>
              <div className="text-[11px] text-amber-600 mt-0.5">
                {character.class_name} · Lv.{character.level} {character.title}
              </div>
              <Progress
                className="mt-1"
                percent={expPct}
                size="small"
                strokeColor="#7c3aed"
                trailColor="#e2e8f0"
                format={() => `${character.exp}/${character.exp_to_next}`}
              />
              <button
                onClick={askLogout}
                className="mt-2 w-full text-[11px] text-slate-400 hover:text-slate-600 transition-colors"
              >
                退出登录
              </button>
            </div>
          )}
        </aside>
      )}

      {/* 主内容：手机端给底部 Tab 留出安全距离 */}
      <main className="flex-1 min-w-0 pb-16 md:pb-0">
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className={hideChrome ? '' : 'px-3 py-3 md:p-8 max-w-6xl mx-auto'}
        >
          {children}
        </motion.div>
        {!hideChrome && <IcpFooter />}
      </main>

      {/* ===== 手机：底部三 Tab ===== */}
      {!hideChrome && (
        <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 bg-white/95 backdrop-blur border-t border-indigo-200">
          <div className="flex items-stretch">
            {TABS.map((t) => {
              const active = t.match(location.pathname)
              return (
                <NavLink
                  key={t.to}
                  to={t.to}
                  className={`flex-1 flex flex-col items-center justify-center gap-1 py-1.5 text-[10px] leading-none whitespace-nowrap transition-colors ${
                    active ? 'text-indigo-600 font-medium' : 'text-slate-400'
                  }`}
                >
                  <span className={`text-[19px] leading-none ${active ? '' : 'opacity-70'}`}>
                    {t.icon}
                  </span>
                  {t.label}
                </NavLink>
              )
            })}
          </div>
          <div className="h-[env(safe-area-inset-bottom)]" />
        </nav>
      )}

      {offline && (
        <div className="fixed bottom-20 md:bottom-3 right-3 z-50 text-[11px] text-slate-500 bg-white/90 border border-slate-200 rounded-full px-3 py-1 shadow-sm">
          离线演示模式 · 后端未连接
        </div>
      )}
    </div>
  )
}
