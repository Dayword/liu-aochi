import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BugOutlined,
  CommentOutlined,
  CrownOutlined,
  EnvironmentOutlined,
  BookOutlined,
  RightOutlined,
  TrophyOutlined,
} from '@ant-design/icons'
import { Progress } from 'antd'
import { motion } from 'framer-motion'
import { api } from '../api/client'
import { useAuth } from '../store/auth'
import type { Profile } from '../types'
import HomePoster from '../components/HomePoster'

/**
 * 首页 = 入口大厅。
 *
 * 顶部是一张纯 SVG 绘制的海报（见 components/HomePoster.tsx）。
 * 海报下面是**两个大卡片**（引导式学习 / AI 导师）——这两个是日常用得最多的入口，
 * 所以高度做得比下面四个小按钮明显大一截；再下面是四个快捷入口。
 *
 * 学习进度、排名、成就、错题都在「我的」页；主导航是底部四 Tab。
 */
const BIG_ENTRIES = [
  {
    to: '/learn',
    icon: <BookOutlined />,
    emoji: '📚',
    title: '引导式学习',
    desc: '12 科目 · 135 课时',
    tone: 'from-indigo-500 to-violet-500',
    glow: 'from-indigo-300 to-violet-300',
  },
  {
    to: '/chat',
    icon: <CommentOutlined />,
    emoji: '💬',
    title: 'AI 导师',
    desc: '随时提问 · 流式回答',
    tone: 'from-fuchsia-500 to-rose-500',
    glow: 'from-fuchsia-300 to-rose-300',
  },
]

const SMALL_ENTRIES = [
  {
    to: '/levels',
    icon: <EnvironmentOutlined />,
    emoji: '🗺️',
    title: '关卡地图',
    desc: '闯关刷题涨经验',
    tone: 'from-emerald-500 to-teal-500',
  },
  {
    to: '/interview',
    icon: <CrownOutlined />,
    emoji: '🎤',
    title: '面试闯关',
    desc: '9 分类 × 8 题',
    tone: 'from-amber-500 to-orange-500',
  },
  {
    to: '/bugs',
    icon: <BugOutlined />,
    emoji: '🐛',
    title: 'Bug 猎人',
    desc: '限时读码找 Bug',
    tone: 'from-rose-500 to-pink-500',
  },
  {
    to: '/leaderboard',
    icon: <TrophyOutlined />,
    emoji: '🏆',
    title: '排行榜',
    desc: '年级班级榜',
    tone: 'from-sky-500 to-blue-500',
  },
]

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
    : character?.class_name || '软件工程 · 游戏化学习'

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
                <span className="truncate">{e.title}</span>
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

      {/* ===== 四个快捷入口（2×2） ===== */}
      <div className="grid grid-cols-2 gap-2">
        {SMALL_ENTRIES.map((e) => (
          <motion.button
            key={e.to}
            whileTap={{ scale: 0.97 }}
            onClick={() => navigate(e.to)}
            className="game-panel relative overflow-hidden text-left p-3 active:bg-slate-50"
          >
            <div
              className={`pointer-events-none absolute -right-6 -top-6 w-16 h-16 rounded-full bg-gradient-to-br ${e.tone} opacity-[0.10]`}
            />
            <div className="relative flex items-start gap-2">
              <div
                className={`w-9 h-9 shrink-0 rounded-xl bg-gradient-to-br ${e.tone} text-white flex items-center justify-center text-base shadow-sm`}
              >
                {e.icon}
              </div>
              <div className="min-w-0 flex-1">
                <div className="font-semibold text-[14px] flex items-center gap-1">
                  <span>{e.emoji}</span>
                  <span className="truncate">{e.title}</span>
                </div>
                <div className="text-[11px] text-slate-500 mt-0.5 leading-snug">{e.desc}</div>
              </div>
              <RightOutlined className="text-[10px] text-slate-300 mt-1 shrink-0" />
            </div>
          </motion.button>
        ))}
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
