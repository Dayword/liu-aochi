import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'

/**
 * 收藏题目的全局缓存。
 *
 * 为什么要模块级缓存：一页里可能有 10 道题、每道题一个星标，逐个问后端
 * 就是 10 个请求。这里只在第一次拉一次 id 列表，之后 toggle 直接改本地集合。
 */
let cache: Set<number> | null = null
let inflight: Promise<Set<number>> | null = null

function load(): Promise<Set<number>> {
  if (cache) return Promise.resolve(cache)
  if (!inflight) {
    inflight = api
      .get<number[]>('/api/growth/favorites/ids')
      .then((ids) => {
        cache = new Set(ids)
        return cache
      })
      .catch(() => new Set<number>())
      .finally(() => {
        inflight = null
      })
  }
  return inflight
}

/** 退出登录时清掉，避免下一个账号看到上一个人的星标 */
export function clearFavoriteCache() {
  cache = null
  inflight = null
}

export function useFavorites() {
  const [ids, setIds] = useState<Set<number>>(() => new Set(cache ?? []))

  useEffect(() => {
    let alive = true
    load().then((s) => {
      if (alive) setIds(new Set(s))
    })
    return () => {
      alive = false
    }
  }, [])

  const toggle = useCallback(async (qid: number) => {
    const r = await api.post<{ favored: boolean }>(`/api/growth/favorites/${qid}`)
    setIds((prev) => {
      const next = new Set(prev)
      if (r.favored) next.add(qid)
      else next.delete(qid)
      cache = next
      return next
    })
    return r.favored
  }, [])

  return { ids, toggle }
}
