import { useMemo } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { Avatar, Progress, Tooltip, message } from 'antd'
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
  const { character, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const expPct = useMemo(() => {
    if (!character) return 0
    return Math.min(100, Math.round((character.exp / character.exp_to_next) * 100))
  }, [character])

  const isQuest = location.pathname.startsWith('/quest')

  return (
    <div className="min-h-screen flex">
      {/* 侧边导航 */}
      {!isQuest && (
        <aside className="w-20 md:w-60 shrink-0 border-r border-indigo-200 bg-[#ffffff]/80 backdrop-blur flex flex-col sticky top-0 h-screen z-20">
          <div className="p-4 md:px-5 flex items-center gap-2">
            <span className="text-3xl">⚔️</span>
            <div className="hidden md:block">
              <div className="font-bold text-indigo-700">代码冒险者</div>
              <div className="text-[11px] text-slate-500">软件工程 · 游戏化学习</div>
            </div>
          </div>
          <nav className="flex-1 px-2 md:px-3 space-y-1 overflow-y-auto">
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
                <span className="hidden md:inline">{item.label}</span>
              </NavLink>
            ))}
          </nav>
          {character && (
            <div className="p-3 border-t border-indigo-200 hidden md:block">
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
                onClick={() => {
                  logout()
                  navigate('/login')
                }}
                className="mt-2 w-full flex items-center justify-center gap-1 text-[11px] text-slate-500 hover:text-rose-600 transition-colors"
              >
                <LogoutOutlined /> 退出登录
              </button>
            </div>
          )}
        </aside>
      )}

      {/* 主内容 */}
      <main className="flex-1 min-w-0">
        {!isQuest && character && (
          <div className="sticky top-0 z-10 bg-[#f6f7fb]/80 backdrop-blur border-b border-indigo-100 px-4 md:px-8 py-2 flex items-center gap-3 md:hidden">
            <span className="text-xl">⚔️</span>
            <span className="text-sm font-medium text-indigo-700">{character.name}</span>
            <span className="text-xs text-amber-600 ml-auto">Lv.{character.level}</span>
            <span className="text-xs text-slate-600">🪙 {character.coins}</span>
            <Tooltip title="退出登录">
              <button
                onClick={() => {
                  logout()
                  navigate('/login')
                }}
                className="text-slate-500 hover:text-rose-600"
              >
                <LogoutOutlined />
              </button>
            </Tooltip>
          </div>
        )}
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className={isQuest ? '' : 'p-4 md:p-8 max-w-6xl mx-auto'}
        >
          {children}
        </motion.div>
      </main>
    </div>
  )
}
