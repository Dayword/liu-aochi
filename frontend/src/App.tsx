import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { Spin } from 'antd'
import { useAuth } from './store/auth'
import Layout from './components/Layout'
import Auth from './pages/Auth'
import Home from './pages/Home'
import LevelMap from './pages/LevelMap'
import Quest from './pages/Quest'
import Game from './pages/Game'
import Learn from './pages/Learn'
import LearnPractice from './pages/LearnPractice'
import Sandbox from './pages/Sandbox'
import Chat from './pages/Chat'
import Interview from './pages/Interview'
import BugHunter from './pages/BugHunter'
import Profile from './pages/Profile'
import Leaderboard from './pages/Leaderboard'
import WrongBook from './pages/WrongBook'
import Favorites from './pages/Favorites'

function FullScreenSpin() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <Spin size="large" />
    </div>
  )
}

/** 未登录 → 去登录页，并记住原本想去的地址。 */
function RequireAuth() {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <FullScreenSpin />
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <Outlet />
}

function Routing() {
  const { loading, user } = useAuth()
  if (loading) return <FullScreenSpin />

  return (
    <Routes>
      {/* 无需登录 */}
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Auth />} />

      {/* 需要登录 */}
      <Route element={<RequireAuth />}>
        <Route
          element={
            <Layout>
              <Outlet />
            </Layout>
          }
        >
          <Route path="/" element={<Home />} />
          <Route path="/learn" element={<Learn />} />
          {/* 动手任务页：题目 + 编辑器 + 运行判定都在这一页 */}
          <Route path="/learn/:code/practice" element={<LearnPractice />} />
          {/* 独立代码沙箱页：AI 导师里的 🧪 图标跳到这里 */}
          <Route path="/sandbox" element={<Sandbox />} />
          <Route path="/levels" element={<LevelMap />} />
          {/* 知识小游戏：4 种玩法由关卡场景决定（见后端 routers/games.py） */}
          <Route path="/game/:levelCode" element={<Game />} />
          {/* 刷题模式：10 道题的答题闯关，也是「收藏题目」的主要入口 */}
          <Route path="/quest/:levelCode" element={<Quest />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/interview" element={<Interview />} />
          <Route path="/bugs" element={<BugHunter />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/wrong" element={<WrongBook />} />
          <Route path="/favorites" element={<Favorites />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default Routing
