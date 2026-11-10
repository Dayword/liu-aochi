import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { App as AntApp } from 'antd'
import { useAuth } from '../store/auth'
import { useSettings } from '../theme/ThemeProvider'
import type { RobotSize } from '../theme/ThemeProvider'
import { api } from '../api/client'
import { emit, onBus } from '../lib/bus'
import { idleDays, recentAccuracy, todayStat } from '../lib/activity'
import { startFocus, localFocusToday, useFocus } from '../focus/store'
import { buildLine, RARE_LINES } from './lines'
import type { LineCtx, Mood } from './lines'

/**
 * 伴学小机器人。
 *
 * 造型随等级分 5 段进化（13 级里 1-3 / 4-6 / 7-9 / 10-12 / 13），
 * 全部是内联 SVG —— 没有一个图片请求，换主题时颜色自动跟着变。
 *
 * 它只在「不打扰」的前提下出现：动手任务页（要盯着编辑器和运行按钮）
 * 直接不渲染；专注模式里它戴上耳机、不再弹任何气泡。
 */
const SIZE: Record<RobotSize, number> = { sm: 46, md: 62, lg: 82 }

function stageOf(level: number): 1 | 2 | 3 | 4 | 5 {
  if (level >= 13) return 5
  if (level >= 10) return 4
  if (level >= 7) return 3
  if (level >= 4) return 2
  return 1
}

/** 当前页面决定了它手上拿什么「装备」 */
function outfitOf(path: string): 'book' | 'mic' | 'pad' | 'glasses' | null {
  if (path.startsWith('/learn')) return 'book'
  if (path.startsWith('/chat')) return 'mic'
  if (path.startsWith('/game') || path.startsWith('/quest')) return 'pad'
  if (path.startsWith('/profile') || path.startsWith('/leaderboard')) return 'glasses'
  return null
}

export default function Robot() {
  const { settings } = useSettings()
  const { character } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const { message } = AntApp.useApp()
  const focus = useFocus()

  const [mood, setMood] = useState<Mood>('idle')
  const [open, setOpen] = useState(false)
  const [flash, setFlash] = useState<Mood | null>(null)
  const [line, setLine] = useState('')
  // 专注中不弹菜单，但必须给一句反馈 —— 否则点下去毫无反应，像坏了
  const [say, setSay] = useState<string | null>(null)
  const [stats, setStats] = useState({ total: 0, done: 0, wrong: 0 })
  const [walk, setWalk] = useState(0)
  const wrapRef = useRef<HTMLDivElement>(null)

  const level = character?.level ?? 1
  const stage = stageOf(level)
  const outfit = outfitOf(location.pathname)
  const size = SIZE[settings.robotSize]

  // 练习页有编辑器和运行按钮，机器人会挡住右下角，直接不出场。
  // 选择题教练页同理：右下角就是「换知识点」按钮，机器人正好压在上面。
  const hidden =
    /^\/learn\/[^/]+\/practice$/.test(location.pathname) ||
    location.pathname.startsWith('/coach')

  /** 基础情绪：专注 > 久未学习 > 正确率 > 平静 */
  const baseMood: Mood = useMemo(() => {
    if (focus.running) return 'focus'
    const days = idleDays()
    if (days !== null && days >= 3) return 'sleep'
    const acc = recentAccuracy()
    if (acc !== null && acc < 0.6) return 'worried'
    if (acc !== null && acc >= 0.9) return 'happy'
    return 'idle'
  }, [focus.running])

  useEffect(() => {
    setMood(flash ?? baseMood)
  }, [baseMood, flash])

  // 升级：先撒彩带，再让表情高兴两秒（等级变化也来自 /api/auth/me 的刷新）
  const prevLevel = useRef(level)
  useEffect(() => {
    if (level > prevLevel.current) {
      emit({ type: 'levelup', level })
      setFlash('happy')
      window.setTimeout(() => setFlash(null), 2200)
    }
    prevLevel.current = level
  }, [level])

  // 答题后给 1.2 秒的即时表情，然后回到基础情绪
  useEffect(() => {
    const off = onBus((e) => {
      if (e.type !== 'answer') return
      setFlash(e.correct ? 'happy' : 'worried')
      window.setTimeout(() => setFlash(null), 1200)
    })
    return off
  }, [])

  // 成长数据：主线进度与待处理错题，用于菜单顶部那句话
  const loadStats = useCallback(async () => {
    try {
      const [points, wrong] = await Promise.all([
        api.get<{ status: string }[]>('/api/learn/points'),
        api.get<{ resolved: boolean }[]>('/api/growth/wrong-book'),
      ])
      setStats({
        total: points.length,
        done: points.filter((p) => p.status === 'completed').length,
        wrong: wrong.filter((w) => !w.resolved).length,
      })
    } catch {
      /* 离线演示时保持 0，不影响机器人本身 */
    }
  }, [])

  useEffect(() => {
    void loadStats()
  }, [loadStats])

  // 每 20~40 秒自己挪两下，像在等指令；专注或睡觉时不动
  useEffect(() => {
    if (mood === 'focus' || mood === 'sleep') return
    const timer = window.setInterval(() => {
      setWalk(Math.random() > 0.5 ? 1 : -1)
      window.setTimeout(() => setWalk(0), 1600)
    }, 20_000 + Math.random() * 20_000)
    return () => window.clearInterval(timer)
  }, [mood])

  // 点到外面就收起气泡
  useEffect(() => {
    if (!open) return
    const onDown = (e: PointerEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('pointerdown', onDown)
    return () => document.removeEventListener('pointerdown', onDown)
  }, [open])

  const speak = () => {
    const ctx: LineCtx = {
      mood,
      level,
      levelTitle: character?.title ?? '拾荒者',
      learnTotal: stats.total,
      learnDone: stats.done,
      wrongOpen: stats.wrong,
      focusMinutes: localFocusToday(),
    }
    const base = buildLine(ctx)
    setLine(settings.easter && Math.random() > 0.7 ? RARE_LINES[(Math.random() * RARE_LINES.length) | 0] : base)
  }

  const toggle = () => {
    if (focus.running) {
      // 专注中不弹菜单，只小声说一句（2.4 秒后自己消失）
      setSay('专注中，结束后再聊')
      setOpen(false)
      window.setTimeout(() => setSay(null), 2400)
      return
    }
    if (!open) {
      speak()
      void loadStats()
    }
    setOpen((v) => !v)
  }

  const goResume = async () => {
    setOpen(false)
    try {
      const r = await api.get<{ code: string; title?: string }>('/api/learn/resume')
      if (!r.code) {
        message.info('还没有学习记录，先去选一课')
        navigate('/learn')
        return
      }
      sessionStorage.setItem('ca_learn_code', r.code)
      navigate('/learn')
    } catch {
      navigate('/learn')
    }
  }

  if (!settings.robot || hidden) return null

  const eyes = () => {
    const eyeFill = 'var(--t-brand-dark)'
    if (mood === 'sleep') {
      return (
        <g stroke={eyeFill} strokeWidth="2.4" strokeLinecap="round">
          <line x1="38" y1="62" x2="46" y2="62" />
          <line x1="54" y1="62" x2="62" y2="62" />
        </g>
      )
    }
    if (mood === 'happy') {
      return (
        <g stroke={eyeFill} strokeWidth="2.6" strokeLinecap="round" fill="none">
          <path d="M38 63 q4 -6 8 0" />
          <path d="M54 63 q4 -6 8 0" />
        </g>
      )
    }
    if (mood === 'worried') {
      return (
        <g>
          <g stroke={eyeFill} strokeWidth="1.8" strokeLinecap="round">
            <line x1="38" y1="55" x2="45" y2="57" />
            <line x1="62" y1="55" x2="55" y2="57" />
          </g>
          <rect x="38.5" y="59" width="5" height="7" rx="2.5" fill={eyeFill} />
          <rect x="56.5" y="59" width="5" height="7" rx="2.5" fill={eyeFill} />
        </g>
      )
    }
    if (mood === 'focus') {
      return (
        <g fill={eyeFill}>
          <rect x="38.5" y="60" width="6" height="4" rx="2" />
          <rect x="55.5" y="60" width="6" height="4" rx="2" />
        </g>
      )
    }
    return (
      <g fill={eyeFill} className="robo-eyes">
        <rect x="38.5" y="56" width="5" height="9" rx="2.5" />
        <rect x="56.5" y="56" width="5" height="9" rx="2.5" />
      </g>
    )
  }

  const gear = () => {
    if (!outfit) return null
    if (outfit === 'book') {
      return (
        <g transform="translate(66 66)">
          <rect x="0" y="0" width="16" height="18" rx="2" fill="var(--t-panel)" stroke="var(--t-brand-dark)" strokeWidth="1.6" />
          <line x1="4" y1="6" x2="12" y2="6" stroke="var(--t-ink-3)" strokeWidth="1.4" />
          <line x1="4" y1="10" x2="12" y2="10" stroke="var(--t-ink-3)" strokeWidth="1.4" />
        </g>
      )
    }
    if (outfit === 'mic') {
      return (
        <g transform="translate(72 64)">
          <rect x="0" y="0" width="7" height="12" rx="3.5" fill="var(--t-accent)" />
          <path d="M-3 9 a6 6 0 0 0 13 0" fill="none" stroke="var(--t-ink-3)" strokeWidth="1.6" />
          <line x1="3.5" y1="15" x2="3.5" y2="19" stroke="var(--t-ink-3)" strokeWidth="1.6" />
        </g>
      )
    }
    if (outfit === 'pad') {
      return (
        <g transform="translate(68 66)">
          <rect x="0" y="0" width="18" height="11" rx="4" fill="var(--t-ink-2)" />
          <circle cx="5" cy="5.5" r="1.8" fill="var(--t-panel)" />
          <circle cx="13" cy="5.5" r="1.8" fill="var(--t-panel)" />
        </g>
      )
    }
    return (
      <g transform="translate(30 52)" fill="none" stroke="var(--t-ink-2)" strokeWidth="1.8">
        <circle cx="8" cy="9" r="6" />
        <circle cx="24" cy="9" r="6" />
        <line x1="14" y1="9" x2="18" y2="9" />
      </g>
    )
  }

  return (
    <div
      ref={wrapRef}
      className="robo-wrap fixed z-[57] select-none bottom-[74px] md:bottom-[18px]"
      style={{
        width: size,
        ...(settings.robotCorner === 'br' ? { right: 10 } : { left: 10 }),
      }}
    >
      {say && !open && (
        <div
          className={`absolute bottom-full mb-2 w-[176px] rounded-xl border border-[var(--t-line)] bg-[var(--t-panel)] px-2.5 py-2 text-[11.5px] leading-relaxed text-[var(--t-ink-2)] shadow-lg ${
            settings.robotCorner === 'br' ? 'right-0' : 'left-0'
          }`}
        >
          {say}
        </div>
      )}

      {open && (
        <div
          role="dialog"
          aria-label="小机器人快捷菜单"
          className={`absolute bottom-full mb-2 w-[220px] rounded-2xl border border-[var(--t-line)] bg-[var(--t-panel)] shadow-xl overflow-hidden ${
            settings.robotCorner === 'br' ? 'right-0' : 'left-0'
          }`}
        >
          <div className="px-3 pt-2.5 pb-2 text-[11.5px] leading-relaxed text-[var(--t-ink-2)] border-b border-[var(--t-line)]">
            {line || '有什么要做的？'}
          </div>
          <button onClick={goResume} className="w-full text-left px-3 py-2 text-[12px] text-[var(--t-ink)] hover:bg-[var(--t-panel-alt)]">
            继续上次的课
          </button>
          <button
            onClick={() => {
              setOpen(false)
              navigate('/wrong')
            }}
            className="w-full text-left px-3 py-2 text-[12px] text-[var(--t-ink)] hover:bg-[var(--t-panel-alt)]"
          >
            错题本{stats.wrong ? `（${stats.wrong}）` : ''}
          </button>
          <button
            onClick={() => {
              setOpen(false)
              startFocus(settings.focusMinutes)
            }}
            className="w-full text-left px-3 py-2 text-[12px] text-[var(--t-ink)] hover:bg-[var(--t-panel-alt)]"
          >
            开始专注 {settings.focusMinutes} 分钟
          </button>
          <button
            onClick={() => {
              setOpen(false)
              navigate('/report')
            }}
            className="w-full text-left px-3 py-2 text-[12px] text-[var(--t-ink)] hover:bg-[var(--t-panel-alt)]"
          >
            本周学习报告
          </button>
          <div className="px-3 py-1.5 text-[10px] text-[var(--t-ink-3)] border-t border-[var(--t-line)]">
            今天 {todayStat().answers} 题 · 专注 {localFocusToday()} 分钟
          </div>
        </div>
      )}

      <button
        onClick={toggle}
        aria-label="伴学小机器人"
        className="block w-full outline-none"
        style={{
          transform: `translateX(${walk}px) translateY(${mood === 'sleep' ? 3 : 0}px)`,
          transition: 'transform .6s ease',
        }}
      >
        <svg
          viewBox="0 0 100 124"
          width={size}
          height={(size * 124) / 100}
          className={mood === 'sleep' ? 'opacity-80' : ''}
          style={{ overflow: 'visible' }}
        >
          <defs>
            <linearGradient id="roboBody" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--t-brand)" />
              <stop offset="100%" stopColor="var(--t-brand-dark)" />
            </linearGradient>
          </defs>

          <ellipse cx="50" cy="117" rx="24" ry="5" fill="rgba(0,0,0,.16)" />

          {stage >= 5 && (
            <ellipse cx="50" cy="12" rx="19" ry="4.5" fill="none" stroke="var(--t-accent)" strokeWidth="2.2" opacity="0.85" />
          )}

          {stage >= 2 && (
            <g>
              <rect x="48" y="26" width="4" height="11" rx="2" fill="var(--t-brand-dark)" />
              <circle cx="50" cy="22" r="5" fill="var(--t-accent)" />
            </g>
          )}

          {/* 脚 */}
          <rect x="33" y="94" width="12" height="12" rx="4" fill="var(--t-brand-dark)" />
          <rect x="55" y="94" width="12" height="12" rx="4" fill="var(--t-brand-dark)" />

          {/* 身体：一级也是圆角方而不是胶囊，否则看着像果冻不像机器 */}
          <rect x="20" y="36" width="60" height="60" rx="18" fill="url(#roboBody)" />

          {/* 两侧的铆钉耳朵：最小的那一级也有，是「机器」感的主要来源 */}
          <g fill="var(--t-brand-dark)" opacity="0.9">
            <circle cx="20" cy="62" r="4" />
            <circle cx="80" cy="62" r="4" />
          </g>

          {/* 手臂：1~2 级是短桩，3 级起变长 */}
          <g fill="var(--t-brand)">
            <rect x={stage >= 3 ? 9 : 13} y={stage >= 3 ? 52 : 58} width="9" height={stage >= 3 ? 24 : 16} rx="4.5" />
            <rect x={stage >= 3 ? 82 : 78} y={stage >= 3 ? 52 : 58} width="9" height={stage >= 3 ? 24 : 16} rx="4.5" />
          </g>

          {stage >= 4 && (
            <g fill="var(--t-accent)" opacity="0.75">
              <circle cx="22" cy="52" r="5" />
              <circle cx="78" cy="52" r="5" />
            </g>
          )}

          {/* 脸 */}
          <rect x="30" y="46" width="40" height="28" rx="12" fill="var(--t-panel)" opacity="0.94" />
          {eyes()}

          {mood === 'focus' && (
            <g>
              <path d="M24 52 q26 -26 52 0" fill="none" stroke="var(--t-brand-dark)" strokeWidth="4.5" strokeLinecap="round" />
              <rect x="18" y="48" width="9" height="14" rx="4.5" fill="var(--t-brand-dark)" />
              <rect x="73" y="48" width="9" height="14" rx="4.5" fill="var(--t-brand-dark)" />
            </g>
          )}

          {mood === 'sleep' && (
            <g fill="var(--t-ink-3)" fontSize="9" fontWeight="700">
              <text x="78" y="40">z</text>
              <text x="86" y="30" fontSize="11">z</text>
            </g>
          )}

          {gear()}

          {stage >= 5 && (
            <g fill="var(--t-accent)">
              <circle cx="16" cy="30" r="1.6" />
              <circle cx="86" cy="22" r="2" />
              <circle cx="90" cy="66" r="1.4" />
            </g>
          )}
        </svg>
      </button>

      <style>{`
        @keyframes robo-bob { 0%,100% { transform: translateY(0) } 50% { transform: translateY(-2.5px) } }
        @keyframes robo-blink { 0%,92%,100% { transform: scaleY(1) } 95% { transform: scaleY(.08) } }
        .robo-wrap svg { animation: robo-bob 3.4s ease-in-out infinite; }
        .robo-eyes { transform-box: fill-box; transform-origin: center; animation: robo-blink 5.6s infinite; }
        @media (prefers-reduced-motion: reduce) {
          .robo-wrap svg, .robo-eyes { animation: none !important; }
        }
      `}</style>
    </div>
  )
}
