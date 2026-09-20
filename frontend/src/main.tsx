import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider, App as AntApp } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import '@ant-design/v5-patch-for-react-19'
import './index.css'
import App from './App'
import { AuthProvider } from './store/auth'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#6366f1',
          colorBgContainer: '#ffffff',
          colorText: '#1f2430',
          colorTextSecondary: '#64748b',
          colorBgElevated: '#ffffff',
          colorBorder: 'rgba(99,102,241,0.22)',
          borderRadius: 10,
          fontFamily: "'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif",
        },
        components: {
          Button: { defaultBg: '#ffffff', defaultBorderColor: 'rgba(99,102,241,0.28)', defaultColor: '#334155' },
          Modal: { contentBg: '#ffffff', headerBg: '#ffffff' },
          Card: { colorBgContainer: '#ffffff' },
          Input: { colorBgContainer: '#ffffff', colorText: '#1f2430' },
          Select: {
            colorBgContainer: '#ffffff',
            colorText: '#1f2430',
            optionSelectedBg: 'rgba(99,102,241,0.12)',
          },
          Table: { colorBgContainer: '#ffffff', headerBg: '#f4f6fa', colorText: '#1f2430' },
        },
      }}
    >
      <AntApp>
        <AuthProvider>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </AuthProvider>
      </AntApp>
    </ConfigProvider>
  </StrictMode>,
)
