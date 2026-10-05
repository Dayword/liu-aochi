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

// 登录页已移除：业务接口 401 时清空 Token 并整页重载，由「访客直通」重新换一个。
// 标记位避免接口持续 401 时反复刷新。会话引导自身的 /api/auth/* 不做重载，
// 交给 AuthProvider 直接降级为访客登录。
const RELOGIN_FLAG = 'ca_relogin'

export function setToken(token: string) {
  localStorage.setItem('ca_token', token)
  sessionStorage.removeItem(RELOGIN_FLAG)
}

export function clearToken() {
  localStorage.removeItem('ca_token')
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
      if (data?.detail) detail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
    } catch {
      /* ignore */
    }
    if (resp.status === 401 && !path.startsWith('/api/auth/')) {
      clearToken()
      if (!sessionStorage.getItem(RELOGIN_FLAG)) {
        sessionStorage.setItem(RELOGIN_FLAG, '1')
        location.reload()
      }
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
