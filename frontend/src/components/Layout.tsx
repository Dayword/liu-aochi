import { useCallback, useEffect, useMemo, useState } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { App, Progress } from 'antd'
import { MenuOutlined } from '@ant-design/icons'
import { motion } from 'framer-motion'
import { useAuth } from '../store/auth'
import BrandMark from '../boot/BrandMark'
import IcpFooter from './IcpFooter'
import MobileDrawer, { useEdgeSwipe } from './MobileDrawer'
import { ALL_ENTRIES, NAV_GROUPS } from '../nav'

/**
 * 底部四 Tab：手机端的高频导航。
 * 只放最常用的四个；知识地图 / 面试闯关 / Bug 猎人 / 错题本 / 收藏
 * 都在左侧抽屉里（点 ☰ 或从左边缘右滑唤出）。
 *
 * 「AI 导师」这一栏把 /sandbox 也算进来，因为沙箱是从导师页跳过去的；
 * 「我的」吃掉 /leaderboard /wrong /favorites，因为这三个都从我的页进。
 */
const TAB_LABEL: Record<string, string> = {
  '/': '首页',
  '/learn': '引导式学习',
  '/chat': 'AI导师',
  '/profile': '我的',
}

const TABS = ['/', '/learn', '/chat', '/profile'].map((to) => {
  const entry = ALL_ENTRIES.find((e) => e.to === to)!
  return {
    to,
    label: TAB_LABEL[to] || entry.label,
    icon: entry.icon,
    match: (p: string) => {
      if (to === '/') return p === '/'
      if (to === '/learn') return p.startsWith('/learn')
      if (to === '/chat') return p.startsWith('/chat') || p.startsWith('/sandbox')
      return (
        p.startsWith('/profile') ||
        p.startsWith('/leaderboard') ||
        p.startsWith('/wrong') ||
        p.startsWith('/favorites')
      )
    },
  }
})

/** 桌面端左侧栏：按 学习 / 陪练 / 我的 分组（清单见 src/nav.tsx，与手机抽屉同源） */

export default function Layout({ children }: { children: React.ReactNode }) {
  const { character, user, offline, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const { modal } = App.useApp()
  // 手机抽屉：☰ 打开，左边缘右滑也能打开
  const [drawer, setDrawer] = useState(false)
  const openDrawer = useCallback(() => setDrawer(true), [])
  const closeDrawer = useCallback(() => setDrawer(false), [])
  useEdgeSwipe(openDrawer)
  // 换页面就收起抽屉（比如抽屉里点了某个入口）
  useEffect(() => {
    setDrawer(false)
  }, [location.pathname])

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
  // ⚠️ /quest 要按「整段」匹配：用 startsWith 会把 /questions（面试考题）一起吃掉，
  //    表现为面试考题页没有顶栏也没有底部 Tab，看起来像页面坏了。
  const hideChrome =
    location.pathname === '/quest' ||
    location.pathname.startsWith('/quest/') ||
    location.pathname.startsWith('/game') ||
    location.pathname.startsWith('/sandbox') ||
    /^\/learn\/[^/]+\/practice$/.test(location.pathname)

  // 知识地图要尽量大的画布，不套 max-w-6xl（否则 12 棵树只能缩着看）
  const wide = location.pathname.startsWith('/mindmap')

  return (
    <div className="min-h-screen md:flex">
      {/* ===== 手机：极简品牌条（导航在底部） ===== */}
      {!hideChrome && (
        <header data-boot-wave="bar" className="md:hidden sticky top-0 z-30 bg-white/95 backdrop-blur border-b border-indigo-200">
          <div className="flex items-center gap-2 px-2 h-11">
            <button
              data-menu-btn="1"
              onClick={openDrawer}
              aria-label="全部功能"
              className="w-9 h-9 -ml-0.5 shrink-0 rounded-lg text-slate-600 active:bg-slate-100 flex items-center justify-center"
            >
              <MenuOutlined className="text-[17px]" />
            </button>
            <BrandMark size={22} level={character?.level} tone="dark" />
            <span className="font-bold text-[15px] text-indigo-700 truncate">码境 CodeRealm</span>
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
        <aside data-boot-wave="bar" className="hidden md:flex w-56 shrink-0 border-r border-indigo-200 bg-white/80 backdrop-blur flex-col sticky top-0 h-screen z-20">
          <div className="px-4 py-4 flex items-center gap-2">
            <BrandMark size={34} level={character?.level} tone="dark" />
            <div>
              <div className="font-bold text-indigo-700">码境 CodeRealm</div>
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
                {user?.student_id ? `学号 ${user.student_id}` : character.identity}
              </div>
              <div className="text-[11px] text-amber-600 mt-0.5">
                Lv.{character.level} {character.title}
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
      <main data-boot-wave="main" className="flex-1 min-w-0 pb-16 md:pb-0">
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className={
            hideChrome
              ? ''
              : wide
                ? 'px-2 py-2 md:px-4 md:py-4'
                : 'px-3 py-3 md:p-8 max-w-6xl mx-auto'
          }
        >
          {children}
        </motion.div>
        {!hideChrome && <IcpFooter />}
      </main>

      {/* ===== 手机：底部四 Tab（首页 / 引导式学习 / AI 导师 / 我的） ===== */}
      {!hideChrome && (
        <nav data-boot-wave="bar" className="md:hidden fixed bottom-0 inset-x-0 z-40 bg-white/95 backdrop-blur border-t border-indigo-200">
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

      {/* ===== 手机：左侧抽屉（全站入口都在这） ===== */}
      {!hideChrome && (
        <MobileDrawer open={drawer} onClose={closeDrawer} onLogout={askLogout} />
      )}

      {offline && (
        <div className="fixed bottom-20 md:bottom-3 right-3 z-50 text-[11px] text-slate-500 bg-white/90 border border-slate-200 rounded-full px-3 py-1 shadow-sm">
          离线演示模式 · 后端未连接
        </div>
      )}
    </div>
  )
}
