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
          colorBgContainer: '#1a1c3b',
          colorText: '#e2e8f0',
          colorTextSecondary: '#94a3b8',
          // 深色底上必须补这三个别名色：默认沿用浅色主题的近黑色，
          // 会导致占位符/图标/禁用文字在深色输入框上几乎看不见。
          colorTextPlaceholder: '#64748b',
          colorTextDisabled: '#64748b',
          colorIcon: '#94a3b8',
          // 浮层（Select 下拉、Modal、Dropdown）默认还是浅色主题的白色底，
          // 配近白色文字会整块看不见，必须显式给深色。
          colorBgElevated: '#1f2147',
          colorBorder: 'rgba(99,102,241,0.25)',
          borderRadius: 10,
          fontFamily: "'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif",
        },
        components: {
          Button: { defaultBg: '#1a1c3b', defaultBorderColor: 'rgba(99,102,241,0.3)', defaultColor: '#e2e8f0' },
          Modal: { contentBg: '#1a1c3b', headerBg: '#1a1c3b' },
          Card: { colorBgContainer: '#1a1c3b' },
          Input: { colorBgContainer: '#12142e', colorText: '#e2e8f0' },
          Select: {
            colorBgContainer: '#12142e',
            colorText: '#e2e8f0',
            optionSelectedBg: 'rgba(99,102,241,0.28)',
          },
          Table: { colorBgContainer: '#1a1c3b', headerBg: '#12142e', colorText: '#e2e8f0' },
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
