import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import '@ant-design/v5-patch-for-react-19'
import './index.css'
import App from './App'
import { AuthProvider } from './store/auth'
import { ThemeProvider } from './theme/ThemeProvider'

// ConfigProvider / AntApp 由 ThemeProvider 统一提供：
// 主题切换要同时改 AntD 的 token（弹窗、下拉、进度条），分成两层就接不上了。
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  </StrictMode>,
)
