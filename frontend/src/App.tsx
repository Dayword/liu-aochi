import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
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
import Chat from './pages/Chat'
import Interview from './pages/Interview'
import BugHunter from './pages/BugHunter'
import Profile from './pages/Profile'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Spin size="large" />
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

function RequireOnboard({ children }: { children: React.ReactNode }) {
  const { user, character } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (user && !user.onboarding_done && !character) return <Navigate to="/onboarding" replace />
  return <>{children}</>
}

function Routing() {
  const location = useLocation()
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register'

  if (isAuthPage) {
    return (
      <Routes>
        <Route path="/login" element={<Auth mode="login" />} />
        <Route path="/register" element={<Auth mode="register" />} />
      </Routes>
    )
  }

  return (
    <Layout>
      <Routes>
        <Route
          path="/onboarding"
          element={
            <RequireAuth>
              <Onboarding />
            </RequireAuth>
          }
        />
        <Route
          path="/"
          element={
            <RequireAuth>
              <RequireOnboard>
                <Home />
              </RequireOnboard>
            </RequireAuth>
          }
        />
        <Route
          path="/learn"
          element={
            <RequireAuth>
              <RequireOnboard>
                <Learn />
              </RequireOnboard>
            </RequireAuth>
          }
        />
        <Route
          path="/levels"
          element={
            <RequireAuth>
              <RequireOnboard>
                <LevelMap />
              </RequireOnboard>
            </RequireAuth>
          }
        />
        <Route
          path="/quest/:levelCode"
          element={
            <RequireAuth>
              <RequireOnboard>
                <Quest />
              </RequireOnboard>
            </RequireAuth>
          }
        />
        <Route
          path="/match3/:levelCode"
          element={
            <RequireAuth>
              <RequireOnboard>
                <Match3 />
              </RequireOnboard>
            </RequireAuth>
          }
        />
        <Route
          path="/chat"
          element={
            <RequireAuth>
              <RequireOnboard>
                <Chat />
              </RequireOnboard>
            </RequireAuth>
          }
        />
        <Route
          path="/interview"
          element={
            <RequireAuth>
              <RequireOnboard>
                <Interview />
              </RequireOnboard>
            </RequireAuth>
          }
        />
        <Route
          path="/bugs"
          element={
            <RequireAuth>
              <RequireOnboard>
                <BugHunter />
              </RequireOnboard>
            </RequireAuth>
          }
        />
        <Route
          path="/profile"
          element={
            <RequireAuth>
              <RequireOnboard>
                <Profile />
              </RequireOnboard>
            </RequireAuth>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}

export default Routing
