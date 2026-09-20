/**
 * 生命值系统：上限 10 颗，每 1 分钟恢复 1 颗。
 *
 * 恢复不是靠定时器累加，而是存「上次变动的时间戳」，读取时按流逝时间计算应恢复几颗。
 * 这样关掉页面、隔天再打开也是准的，也不会因为页面在后台而停摆。
 */
import { useCallback, useEffect, useState } from 'react'

const KEY = 'ca_match3_lives'
export const MAX_LIVES = 10
export const REGEN_MS = 60_000

interface LivesState {
  lives: number
  /** 上一次「恢复到当前颗数」的时刻；满血时记为 now */
  ts: number
}

function recover(s: LivesState): LivesState {
  if (s.lives >= MAX_LIVES) return { lives: MAX_LIVES, ts: Date.now() }
  const gained = Math.floor((Date.now() - s.ts) / REGEN_MS)
  if (gained <= 0) return s
  return { lives: Math.min(MAX_LIVES, s.lives + gained), ts: s.ts + gained * REGEN_MS }
}

function read(): LivesState {
  try {
    const raw = localStorage.getItem(KEY)
    if (raw) return recover(JSON.parse(raw) as LivesState)
  } catch {
    /* 数据损坏就当满血 */
  }
  return { lives: MAX_LIVES, ts: Date.now() }
}

function write(s: LivesState) {
  try {
    localStorage.setItem(KEY, JSON.stringify(s))
  } catch {
    /* 隐私模式下写不进去，忽略即可 */
  }
}

export function useLives() {
  const [state, setState] = useState<LivesState>(read)
  const [, setTick] = useState(0)

  useEffect(() => {
    write(state)
  }, [state])

  // 每 5 秒重算一次，足够让倒计时走动，又不至于频繁渲染
  useEffect(() => {
    const id = window.setInterval(() => {
      setState(read())
      setTick((t) => t + 1)
    }, 5000)
    return () => window.clearInterval(id)
  }, [])

  /** 扣一颗生命；返回扣除后的剩余数 */
  const consume = useCallback((): number => {
    let left = 0
    setState((prev) => {
      const cur = recover(prev)
      if (cur.lives <= 0) {
        left = 0
        return cur
      }
      left = cur.lives - 1
      // 保持原有时间戳，未攒满一分钟的进度不会丢
      return { lives: left, ts: cur.ts }
    })
    return left
  }, [])

  /** 距离下一颗恢复还有多少毫秒；满血时为 0 */
  const nextInMs = state.lives >= MAX_LIVES ? 0 : REGEN_MS - ((Date.now() - state.ts) % REGEN_MS)

  return { lives: state.lives, nextInMs, consume }
}

export function formatCountdown(ms: number): string {
  const total = Math.max(0, Math.ceil(ms / 1000))
  return `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`
}
