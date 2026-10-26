// 轻量 API 客户端
// 本地开发走 vite 代理（BASE 为空，请求 /api/* 由 dev server 转发）；
// 部署到 GitHub Pages 等静态托管时，用 VITE_API_BASE 指向后端地址。
const BASE = import.meta.env.VITE_API_BASE ?? ''

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export function getToken(): string | null {
  return localStorage.getItem('ca_token')
}

// 登录态失效：清空 Token 并跳到登录页（不再整页重载 + 静默直通）。
// `ca_relogin` 标记避免多个并发请求同时跳转造成闪烁。
// /api/auth/* 自身的 401 不跳转，交给调用方（登录页）展示错误。
const RELOGIN_FLAG = 'ca_relogin'

export function setToken(token: string) {
  localStorage.setItem('ca_token', token)
  sessionStorage.removeItem(RELOGIN_FLAG)
}

export function clearToken() {
  localStorage.removeItem('ca_token')
}

/** 跳登录页，兼容部署在子路径的情况（GitHub Pages /xxx/）。 */
function gotoLogin() {
  if (sessionStorage.getItem(RELOGIN_FLAG)) return
  sessionStorage.setItem(RELOGIN_FLAG, '1')
  const base = import.meta.env.BASE_URL || '/'
  const current = location.pathname + location.search
  if (current.replace(base, '/') === 'login') return
  location.replace(`${base}login`)
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  const resp = await fetch(BASE + path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  if (!resp.ok) {
    let detail = `请求失败 (${resp.status})`
    try {
      const data = await resp.json()
      const d = data?.detail
      if (typeof d === 'string') {
        detail = d
      } else if (Array.isArray(d) && d.length) {
        // FastAPI 校验错误：[{loc, msg}]，取第一条并去掉 "Value error, " 前缀
        const msg = String(d[0]?.msg ?? '')
        if (msg) detail = msg.replace(/^Value error,\s*/, '')
      } else if (d) {
        detail = JSON.stringify(d)
      }
    } catch {
      /* ignore */
    }
    if (resp.status === 401 && !path.startsWith('/api/auth/')) {
      clearToken()
      gotoLogin()
    }
    throw new ApiError(resp.status, detail)
  }
  if (resp.status === 204) return undefined as T
  return (await resp.json()) as T
}

export const api = {
  get: <T>(path: string) => request<T>('GET', path),
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
}
