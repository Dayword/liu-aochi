import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Progress } from 'antd'
import { motion } from 'framer-motion'
import { api } from '../api/client'
import { useAuth } from '../store/auth'
import type { Profile } from '../types'
import HomePoster from '../components/HomePoster'
import { ALL_ENTRIES } from '../nav'

/**
 * 首页 = 入口大厅。
 *
 * 顶部是一张纯 SVG 绘制的海报（见 components/HomePoster.tsx）。
 * 海报下面分两层：
 *   1. 两张**大卡**（引导式学习 / AI 导师）——日常用得最多，所以高度明显大一截
 *   2. 「全部功能」宫格——把剩下的入口一次铺出来
 *
 * 入口数据全部来自 src/nav.tsx，不再在这里硬编码。
 * 之前这里是写死的 6 个入口，加了知识地图之后首页和底栏都没有它，
 * 手机上根本找不到——现在加页面只改 nav.tsx，首页自动跟上。
 */
const BIG_PATHS = ['/learn', '/chat']

/** 大卡右上角的光斑色，比小图标更明显，用来强化主入口层级 */
const GLOW: Record<string, string> = {
  '/learn': 'from-indigo-300 to-violet-300',
  '/chat': 'from-fuchsia-300 to-rose-300',
}

const BIG_ENTRIES = BIG_PATHS.map((p) => ({
  ...ALL_ENTRIES.find((e) => e.to === p)!,
  glow: GLOW[p],
}))

const MORE_ENTRIES = ALL_ENTRIES.filter((e) => e.to !== '/' && !BIG_PATHS.includes(e.to))

export default function Home() {
  const { character, user } = useAuth()
  const navigate = useNavigate()
  const [learn, setLearn] = useState<{ completed: number; total: number; pct: number } | null>(null)

  const expPct = useMemo(() => {
    if (!character) return 0
    return Math.min(100, Math.round((character.exp / character.exp_to_next) * 100))
  }, [character])

  // 首页只取学习进度这一小块，失败就静默（未完成引导 / 离线演示时不显示进度）
  useEffect(() => {
    api
      .get<Profile>('/api/user/profile')
      .then((p) => setLearn(p.learn))
      .catch(() => undefined)
  }, [])

  const subtitle = user?.student_id
    ? `学号 ${user.student_id} · ${user.grade} 级 · ${user.class_code} 班`
    : character?.identity || '软件工程 · 游戏化学习'

  return (
    <div className="space-y-3">
      {/* ===== 海报 ===== */}
      <HomePoster
        name={user?.real_name || character?.name || '冒险者'}
        subtitle={subtitle}
        level={character?.level ?? 1}
        title={character?.title ?? '实习生'}
        pct={expPct}
        exp={character?.exp ?? 0}
        expNext={character?.exp_to_next ?? 100}
      />

      {/* ===== 两个主入口（并排，比下面四个大） ===== */}
      <div className="grid grid-cols-2 gap-2.5">
        {BIG_ENTRIES.map((e, i) => (
          <motion.button
            key={e.to}
            whileTap={{ scale: 0.97 }}
            onClick={() => navigate(e.to)}
            className="game-panel relative overflow-hidden text-left p-3.5 pb-3 active:bg-slate-50 flex flex-col min-h-[118px] md:min-h-[104px] md:flex-row md:items-center md:gap-4 md:py-5 md:px-4"
          >
            {/* 角落光斑：比小按钮更明显，强化主入口层级 */}
            <div
              className={`pointer-events-none absolute -right-8 -top-8 w-24 h-24 rounded-full bg-gradient-to-br ${e.glow} opacity-25`}
            />
            <div
              className={`relative w-10 h-10 md:w-12 md:h-12 shrink-0 rounded-2xl bg-gradient-to-br ${e.tone} text-white flex items-center justify-center text-lg md:text-xl shadow-sm`}
            >
              {e.icon}
            </div>
            <div className="relative mt-2 md:mt-0 min-w-0 md:flex-1">
              <div className="font-bold text-[15px] leading-tight flex items-center gap-1">
                <span>{e.emoji}</span>
                <span className="truncate">{e.label}</span>
              </div>
              <div className="text-[11px] text-slate-500 leading-snug mt-0.5">{e.desc}</div>
            </div>

            {/* 底部（手机上）/ 右侧（桌面上）：学习卡显示真实进度，导师卡显示可聊的话题标签 */}
            <div className="relative mt-auto pt-2 md:mt-0 md:pt-0 md:w-36 md:shrink-0">
              {i === 0 ? (
                <>
                  <Progress
                    percent={learn?.pct ?? 0}
                    size="small"
                    showInfo={false}
                    strokeColor="#6366f1"
                    trailColor="#e2e8f0"
                  />
                  <div className="text-[10px] text-slate-400 leading-none mt-1">
                    已完成 {learn?.completed ?? 0} / {learn?.total ?? 135} 课时
                  </div>
                </>
              ) : (
                <div className="flex items-center gap-1 flex-wrap md:justify-end">
                  {[
                    { t: 'Python', c: 'bg-rose-50 text-rose-500' },
                    { t: '面试', c: 'bg-indigo-50 text-indigo-500' },
                    { t: '错题', c: 'bg-amber-50 text-amber-600' },
                  ].map((x) => (
                    <span
                      key={x.t}
                      className={`px-1.5 py-0.5 rounded text-[10px] leading-none ${x.c}`}
                    >
                      {x.t}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </motion.button>
        ))}
      </div>

      {/* ===== 全部功能宫格：其余入口一个不落 ===== */}
      <div className="game-panel p-3">
        <div className="flex items-baseline justify-between">
          <div className="text-[13px] font-semibold text-slate-700">🧭 全部功能</div>
          <div className="text-[10px] text-slate-400">{MORE_ENTRIES.length} 个入口都在这</div>
        </div>
        {/* 入口数会随功能增减变：9 个时 3 列正好 3+3+3 排满，4 列会剩一个孤零零的 */}
        <div data-entries className="mt-2.5 grid grid-cols-3 gap-1.5">
          {MORE_ENTRIES.map((e) => (
            <motion.button
              key={e.to}
              data-entry={e.to}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate(e.to)}
              className="flex flex-col items-center gap-1 py-2 rounded-xl border border-slate-200/90 bg-white active:bg-slate-50 transition-colors"
            >
              <span
                className={`w-8 h-8 rounded-lg bg-gradient-to-br ${e.tone} text-white flex items-center justify-center text-[14px] shadow-sm`}
              >
                {e.icon}
              </span>
              <span className="text-[11px] font-medium text-slate-600 leading-none whitespace-nowrap">
                {e.label}
              </span>
            </motion.button>
          ))}
        </div>
      </div>

      {/* ===== 小装饰：冒险路线（虚线路径 + 四个里程碑） ===== */}
      <div className="game-panel p-3">
        <div className="flex items-baseline justify-between">
          <div className="text-[13px] font-semibold text-slate-700">🗺️ 冒险路线</div>
          <div className="text-[10px] text-slate-400">从语法到上线，四步走完</div>
        </div>
        <div className="relative mt-3 mb-1">
          <svg
            viewBox="0 0 320 26"
            preserveAspectRatio="none"
            className="absolute inset-x-0 top-1.5 w-full h-5"
            aria-hidden="true"
          >
            <path
              d="M18 13 H302"
              stroke="#c7d2fe"
              strokeWidth="2"
              strokeDasharray="5 5"
              strokeLinecap="round"
            />
          </svg>
          <div className="relative flex items-start justify-between">
            {[
              { emoji: '🐍', label: '语言基础' },
              { emoji: '🗄️', label: '数据存储' },
              { emoji: '🌐', label: '网络与系统' },
              { emoji: '🤖', label: 'AI 工程' },
            ].map((n) => (
              <div key={n.label} className="flex flex-col items-center gap-1 w-1/4">
                <div className="w-8 h-8 rounded-full bg-white border-2 border-indigo-200 flex items-center justify-center text-sm shadow-sm">
                  {n.emoji}
                </div>
                <div className="text-[10px] text-slate-500 text-center leading-tight">{n.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ===== 小装饰：冒险者手记 ===== */}
      <div className="game-panel relative overflow-hidden p-3">
        <svg
          viewBox="0 0 320 60"
          preserveAspectRatio="none"
          className="absolute inset-0 w-full h-full opacity-50"
          aria-hidden="true"
        >
          <path
            d="M0 48 Q40 28 80 44 T160 40 T240 46 T320 38"
            fill="none"
            stroke="#c7d2fe"
            strokeWidth="2"
          />
          <circle cx="300" cy="16" r="10" fill="#eef2ff" />
          <circle cx="316" cy="30" r="5" fill="#f5f3ff" />
        </svg>
        <div className="relative flex items-start gap-2">
          <span className="text-lg leading-none">🧭</span>
          <div className="min-w-0">
            <div className="text-[11px] text-slate-400">冒险者手记</div>
            <div className="text-[12px] text-slate-600 leading-snug">
              把每一课亲手跑通一遍，比读完十篇教程更管用。
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
