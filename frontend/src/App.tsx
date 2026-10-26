import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { Spin } from 'antd'
import { useAuth } from './store/auth'
import Layout from './components/Layout'
import Auth from './pages/Auth'
import Onboarding from './pages/Onboarding'
import Home from './pages/Home'
import LevelMap from './pages/LevelMap'
import Quest from './pages/Quest'
import Match3 from './pages/Match3'
import Learn from './pages/Learn'
import LearnPractice from './pages/LearnPractice'
import Sandbox from './pages/Sandbox'
import Chat from './pages/Chat'
import Interview from './pages/Interview'
import BugHunter from './pages/BugHunter'
import Profile from './pages/Profile'
import Leaderboard from './pages/Leaderboard'

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

/** 已登录但还没创建角色 → 先走新手引导。 */
function RequireOnboard() {
  const { user, loading } = useAuth()
  if (loading) return <FullScreenSpin />
  if (user && !user.onboarding_done) return <Navigate to="/welcome" replace />
  return <Outlet />
}

function Routing() {
  const { loading, user } = useAuth()
  if (loading) return <FullScreenSpin />

  return (
    <Routes>
      {/* 无需登录 */}
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Auth />} />

      {/* 已登录、待创建角色 */}
      <Route path="/welcome" element={user ? <Onboarding /> : <Navigate to="/login" replace />} />

      {/* 需要登录 + 已创建角色 */}
      <Route element={<RequireAuth />}>
        <Route element={<RequireOnboard />}>
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
            <Route path="/quest/:levelCode" element={<Quest />} />
            <Route path="/match3/:levelCode" element={<Match3 />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/interview" element={<Interview />} />
            <Route path="/bugs" element={<BugHunter />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default Routing
