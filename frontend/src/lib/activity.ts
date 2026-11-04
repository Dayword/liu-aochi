import { emit } from './bus'

/**
 * 本机行为记录：最近 10 次答对/答错、最近一次学习时间、今日答题数。
 *
 * 这些值只用于机器人表情与「今天学了多久」的即时反馈，**不参与任何
 * 经验/等级计算**（经验只认课程完成，见 MEMORY 里的约定）。
 * 换设备会归零，这是刻意的：表情本来就是个本机的小东西。
 */
const RING = 'ca_answer_ring'
const LAST = 'ca_last_active'
const TODAY = 'ca_today'

interface TodayRec {
  date: string
  answers: number
  correct: number
}

const todayStr = () => {
  const d = new Date()
  return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`
}

export function answerRing(): number[] {
  try {
    const raw = localStorage.getItem(RING)
    if (!raw) return []
    const arr = JSON.parse(raw)
    return Array.isArray(arr) ? arr.filter((n) => n === 0 || n === 1).slice(-10) : []
  } catch {
    return []
  }
}

export function todayStat(): TodayRec {
  try {
    const raw = localStorage.getItem(TODAY)
    const rec = raw ? (JSON.parse(raw) as TodayRec) : null
    if (rec && rec.date === todayStr()) return rec
  } catch {
    /* 坏数据按空处理 */
  }
  return { date: todayStr(), answers: 0, correct: 0 }
}

/** 记一次作答：环形缓冲 + 今日计数 + 活跃时间，并广播出去 */
export function recordAnswer(correct: boolean) {
  const ring = answerRing()
  ring.push(correct ? 1 : 0)
  if (ring.length > 10) ring.shift()

  const t = todayStat()
  t.answers += 1
  if (correct) t.correct += 1

  try {
    localStorage.setItem(RING, JSON.stringify(ring))
    localStorage.setItem(TODAY, JSON.stringify(t))
    localStorage.setItem(LAST, String(Date.now()))
  } catch {
    /* 隐私模式下写不进去，不影响判题 */
  }
  emit({ type: 'answer', correct })
}

/** 距上次作答过了几天；从没作答返回 null */
export function idleDays(): number | null {
  try {
    const raw = localStorage.getItem(LAST)
    if (!raw) return null
    const ms = Date.now() - Number(raw)
    if (!Number.isFinite(ms) || ms < 0) return null
    return Math.floor(ms / 86_400_000)
  } catch {
    return null
  }
}

/** 最近 10 题正确率；没有记录返回 null */
export function recentAccuracy(): number | null {
  const ring = answerRing()
  if (!ring.length) return null
  return ring.reduce((a, b) => a + b, 0) / ring.length
}

/** 连续答对次数（从末尾往前数），给连击用 */
export function streak(): number {
  const ring = answerRing()
  let n = 0
  for (let i = ring.length - 1; i >= 0; i--) {
    if (ring[i] !== 1) break
    n++
  }
  return n
}
