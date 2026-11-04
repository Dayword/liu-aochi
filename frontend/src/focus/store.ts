import { useSyncExternalStore } from 'react'
import { api } from '../api/client'
import { emit } from '../lib/bus'

/**
 * 番茄钟：25/45/50 分钟倒计时。
 *
 * 刻意不做的事：不发经验、不扣血、不写 learn_progress。
 * 经验只认「完成一节课」，这是全站唯一口径（见 MEMORY），
 * 番茄钟只是一个专注计时器，结束后记录时长用于周报。
 *
 * 时间用「结束时刻 - 现在」算，不用 setInterval 累加：
 * 后者在切到后台时会被浏览器降频（1 分钟只跑几次），
 * 回来一看表就慢了半截。用截止时间戳，切回来立刻是对的。
 */
export interface FocusState {
  running: boolean
  paused: boolean
  /** 本轮总时长（分钟） */
  minutes: number
  /** 剩余秒数 */
  remain: number
  /** 结束时间戳（暂停时为 null） */
  endsAt: number | null
}

const IDLE: FocusState = { running: false, paused: false, minutes: 25, remain: 0, endsAt: null }
let state: FocusState = IDLE
const subs = new Set<() => void>()
let timer: number | null = null

function set(patch: Partial<FocusState>) {
  state = { ...state, ...patch }
  for (const fn of subs) fn()
}

function stopTimer() {
  if (timer !== null) {
    window.clearInterval(timer)
    timer = null
  }
}

const FOCUS_TOTAL = 'ca_focus_total'

/** 本机累计（按天），用于「今天专注了多久」这种即时显示 */
function addLocalMinutes(min: number) {
  try {
    const d = new Date()
    const key = `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`
    const raw = localStorage.getItem(FOCUS_TOTAL)
    const rec = raw ? (JSON.parse(raw) as { date: string; minutes: number }) : null
    const next =
      rec && rec.date === key
        ? { date: key, minutes: rec.minutes + min }
        : { date: key, minutes: min }
    localStorage.setItem(FOCUS_TOTAL, JSON.stringify(next))
  } catch {
    /* 写不进去不影响计时 */
  }
}

export function localFocusToday(): number {
  try {
    const d = new Date()
    const key = `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`
    const raw = localStorage.getItem(FOCUS_TOTAL)
    const rec = raw ? (JSON.parse(raw) as { date: string; minutes: number }) : null
    return rec && rec.date === key ? rec.minutes : 0
  } catch {
    return 0
  }
}

function chime() {
  try {
    const ac = new AudioContext()
    const now = ac.currentTime
    // 两声上行的小铃：听起来像「叮—咚」，不是报警器
    ;[660, 880].forEach((f, i) => {
      const osc = ac.createOscillator()
      const g = ac.createGain()
      osc.type = 'sine'
      osc.frequency.value = f
      const t = now + i * 0.22
      g.gain.setValueAtTime(0.0001, t)
      g.gain.exponentialRampToValueAtTime(0.22, t + 0.02)
      g.gain.exponentialRampToValueAtTime(0.0001, t + 0.42)
      osc.connect(g).connect(ac.destination)
      osc.start(t)
      osc.stop(t + 0.5)
    })
    window.setTimeout(() => void ac.close(), 1400)
  } catch {
    /* 没有声音也能结束 */
  }
}

function logSession(minutes: number, startedAt: number) {
  addLocalMinutes(minutes)
  api
    .post('/api/focus/log', {
      minutes,
      started_at: new Date(startedAt).toISOString(),
    })
    .catch(() => {
      /* 离线时只记在本机，不打扰用户 */
    })
}

function finish(completed: boolean) {
  const spent = Math.max(0, Math.min(state.minutes, Math.round((state.minutes * 60 - state.remain) / 60)))
  const startedAt = Date.now() - spent * 60_000
  stopTimer()
  set({ ...IDLE, minutes: state.minutes })
  delete document.documentElement.dataset.pomodoro
  emit({ type: 'focus', running: false })
  if (completed) {
    chime()
    emit({ type: 'clear' })
  }
  if (spent >= 1) logSession(spent, startedAt)
}

function tick() {
  if (!state.endsAt) return
  const remain = Math.max(0, Math.round((state.endsAt - Date.now()) / 1000))
  if (remain <= 0) {
    set({ remain: 0 })
    finish(true)
    return
  }
  if (remain !== state.remain) set({ remain })
}

export function startFocus(minutes: FocusState['minutes']) {
  stopTimer()
  set({ running: true, paused: false, minutes, remain: minutes * 60, endsAt: Date.now() + minutes * 60_000 })
  // 不能用 data-focus：那是「键盘焦点描边」的开关
  document.documentElement.dataset.pomodoro = '1'
  emit({ type: 'focus', running: true })
  timer = window.setInterval(tick, 500)
}

export function pauseFocus() {
  if (!state.running || state.paused) return
  stopTimer()
  const remain = state.endsAt ? Math.max(0, Math.round((state.endsAt - Date.now()) / 1000)) : state.remain
  set({ paused: true, remain, endsAt: null })
}

export function resumeFocus() {
  if (!state.running || !state.paused || state.remain <= 0) return
  set({ paused: false, endsAt: Date.now() + state.remain * 1000 })
  timer = window.setInterval(tick, 500)
}

/** 手动结束：计入已专注的分钟（不足 1 分钟不计） */
export function stopFocus() {
  if (!state.running) return
  // 暂停状态下 remain 就是已算好的剩余，直接沿用
  if (state.endsAt) {
    set({ remain: Math.max(0, Math.round((state.endsAt - Date.now()) / 1000)) })
  }
  finish(false)
}

function subscribe(fn: () => void) {
  subs.add(fn)
  return () => {
    subs.delete(fn)
  }
}

export function useFocus(): FocusState {
  return useSyncExternalStore(subscribe, () => state, () => state)
}

export function focusTimeText(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}
