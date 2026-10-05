import { Navigate, Route, Routes } from 'react-router-dom'
import { Spin } from 'antd'
import { useAuth } from './store/auth'
import Layout from './components/Layout'
import Home from './pages/Home'
import LevelMap from './pages/LevelMap'
import Quest from './pages/Quest'
import Match3 from './pages/Match3'
import Learn from './pages/Learn'
import Chat from './pages/Chat'
import Interview from './pages/Interview'
import BugHunter from './pages/BugHunter'
import Profile from './pages/Profile'

// 已移除登录/注册页与新手引导页：启动即完成访客直通，所有页面直接可用。
function Routing() {
  const { loading } = useAuth()
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Spin size="large" />
      </div>
    )
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/learn" element={<Learn />} />
        <Route path="/levels" element={<LevelMap />} />
        <Route path="/quest/:levelCode" element={<Quest />} />
        <Route path="/match3/:levelCode" element={<Match3 />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/interview" element={<Interview />} />
        <Route path="/bugs" element={<BugHunter />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}

export default Routing
