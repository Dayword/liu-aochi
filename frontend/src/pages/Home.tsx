import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { App, Button, Progress } from 'antd'
import { motion } from 'framer-motion'
import { api } from '../api/client'
import { useAuth } from '../store/auth'
import type { DailyTask, LeaderEntry, LevelItem, Scene } from '../types'

/** 首页四宫格入口：点一下在原位撑成通栏（不跳页），再点收回 */
const ENTRIES = [
  { to: '/chat', icon: '💬', title: 'AI 导师', desc: '概念讲解 / 代码答疑 / 学习路径规划' },
  { to: '/interview', icon: '🎤', title: '面试闯关', desc: '一面到 HR 面，四维评分与追问链' },
  { to: '/bugs', icon: '🐛', title: 'Bug 猎人', desc: '读码找 Bug，改完实时运行验证' },
  { to: '/profile', icon: '📊', title: '个人中心', desc: '成就墙 / 错题本 / 能力雷达 / 排行榜' },
]

export default function Home() {
  const { character, refreshCharacter } = useAuth()
  const { message } = App.useApp()
  const navigate = useNavigate()
  const [dailyTasks, setDailyTasks] = useState<DailyTask[]>([])
  const [levels, setLevels] = useState<LevelItem[]>([])
  const [scenes, setScenes] = useState<Scene[]>([])
  const [leaderboard, setLeaderboard] = useState<LeaderEntry[]>([])
  const [signing, setSigning] = useState(false)
  const [expanded, setExpanded] = useState<string | null>(null)

  const load = async () => {
    const [tasks, map, lb] = await Promise.all([
      api.get<DailyTask[]>('/api/growth/daily-tasks'),
      api.get<{ scenes: Scene[]; levels: LevelItem[] }>('/api/levels/map'),
      api.get<LeaderEntry[]>('/api/growth/leaderboard?board=total&limit=3'),
    ])
    setDailyTasks(tasks)
    setScenes(map.scenes)
    setLevels(map.levels)
    setLeaderboard(lb)
  }

  useEffect(() => {
    load().catch((e) => message.error((e as Error).message))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const signin = async () => {
    setSigning(true)
    try {
      const r = await api.post<{ streak: number; exp: number; coins: number; msg: string }>(
        '/api/user/signin',
      )
      message.success(`签到成功！+${r.exp} EXP +${r.coins} 币，连续 ${r.streak} 天`)
      await refreshCharacter()
      await load()
    } catch (e) {
      message.info((e as Error).message)
    } finally {
      setSigning(false)
    }
  }

  const claim = async (code: string) => {
    try {
      const r = await api.post<{ exp: number; coins: number }>(`/api/growth/daily-tasks/${code}/claim`)
      message.success(`领取成功！+${r.exp} EXP +${r.coins} 币`)
      await refreshCharacter()
      await load()
    } catch (e) {
      message.warning((e as Error).message)
    }
  }

  const share = async () => {
    try {
      await api.post('/api/growth/share')
      await load()
      message.success('分享成功！每日任务已记录 📣')
    } catch (e) {
      message.error((e as Error).message)
    }
  }

  if (!character) return null
  const expPct = Math.min(100, Math.round((character.exp / character.exp_to_next) * 100))
  const unlockedCount = levels.filter((l) => l.status !== 'locked').length
  const completedCount = levels.filter((l) => l.completed).length
  const claimable = dailyTasks.filter((t) => t.done && !t.claimed).length

  return (
    <div className="space-y-3">
      {/* ===== 角色 HUD：压成 3 行小卡，手机上不至于一屏只看到它 ===== */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="game-panel p-3 relative overflow-hidden"
      >
        <div className="absolute -right-6 -top-6 text-[6rem] opacity-[0.07] select-none">⚔️</div>

        <div className="flex items-center gap-2.5 relative z-10">
          <div className="text-3xl leading-none shrink-0">{character.identity === '求职中' ? '💼' : '🎓'}</div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-base font-bold text-indigo-800 truncate">{character.name}</span>
              <span className="px-1.5 py-0.5 rounded-full bg-indigo-100 text-indigo-600 text-[10px]">
                {character.class_name}
              </span>
              <span className="px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-600 text-[10px]">
                {character.title}
              </span>
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5 truncate">
              {character.identity} · 🔥 连续 {character.streak_days} 天
            </div>
          </div>
          <Button size="small" type="primary" onClick={signin} loading={signing} className="glow-btn shrink-0">
            📅 签到
          </Button>
        </div>

        <div className="mt-2.5 flex items-center gap-2 relative z-10">
          <span className="text-sm font-black text-indigo-600 shrink-0">Lv.{character.level}</span>
          <Progress
            percent={expPct}
            size="small"
            strokeColor="#7c3aed"
            trailColor="#e2e8f0"
            showInfo={false}
            className="flex-1"
          />
          <span className="text-[10px] text-slate-400 shrink-0">
            {character.exp}/{character.exp_to_next}
          </span>
        </div>

        <div className="mt-2 grid grid-cols-3 gap-1.5 relative z-10">
          {[
            { icon: '🪙', v: character.coins, l: '代码币', c: 'text-amber-600' },
            { icon: '❤️', v: `${character.hp}/${character.max_hp}`, l: '生命', c: 'text-rose-600' },
            { icon: '🔥', v: character.streak_days, l: '连续天', c: 'text-orange-600' },
          ].map((x) => (
            <div key={x.l} className="rounded-lg bg-slate-50 py-1 text-center">
              <div className={`text-[13px] font-bold leading-tight ${x.c}`}>
                {x.icon} {x.v}
              </div>
              <div className="text-[9px] text-slate-400 leading-tight">{x.l}</div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* ===== 四宫格入口：点一格撑成通栏，其余自动重排（不跳页） ===== */}
      {/* grid-flow-row-dense：撑开后剩下的小格会回填到前面的空位，洞留在末尾而不是中间 */}
      <div className="grid grid-cols-2 grid-flow-row-dense gap-2 md:grid-cols-4">
        {ENTRIES.map((item) => {
          const on = expanded === item.to
          return (
            <motion.div
              layout
              transition={{ type: 'spring', stiffness: 380, damping: 32 }}
              key={item.to}
              role="button"
              tabIndex={0}
              onClick={() => setExpanded(on ? null : item.to)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') setExpanded(on ? null : item.to)
              }}
              className={`game-panel relative overflow-hidden text-left px-3 py-2.5 cursor-pointer active:bg-slate-50 ${
                on ? 'col-span-2 md:col-span-4' : ''
              }`}
            >
              <div className={`flex items-center gap-2 ${on ? '' : 'flex-col text-center'}`}>
                <span className={on ? 'text-2xl' : 'text-xl'}>{item.icon}</span>
                <span className={`font-medium text-indigo-700 ${on ? 'text-sm' : 'text-[11px]'}`}>
                  {item.title}
                </span>
                {on && <span className="ml-auto text-indigo-400">›</span>}
              </div>

              {on ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="mt-1.5 flex items-center gap-2"
                >
                  <span className="text-[11px] text-slate-500 flex-1">{item.desc}</span>
                  <Button
                    size="small"
                    type="primary"
                    onClick={(e) => {
                      e.stopPropagation()
                      navigate(item.to)
                    }}
                  >
                    进入
                  </Button>
                </motion.div>
              ) : (
                <div className="text-[9px] text-slate-400 mt-0.5 truncate w-full text-center">
                  {item.desc.split(' / ')[0]}
                </div>
              )}
            </motion.div>
          )
        })}
      </div>

      {/* ===== 三块数据：手机两列小卡，桌面三列 ===== */}
      <div className="grid grid-cols-2 gap-2 md:grid-cols-3 md:gap-3">
        {/* 每日任务 */}
        <div className="game-panel p-2.5 col-span-2 md:col-span-1">
          <div className="flex items-center gap-1.5 mb-1.5">
            <span className="text-sm">📋</span>
            <span className="text-xs font-medium text-indigo-700">每日任务</span>
            {claimable > 0 && (
              <span className="ml-auto text-[9px] px-1.5 py-0.5 rounded-full bg-rose-100 text-rose-600">
                {claimable} 个可领
              </span>
            )}
          </div>
          <div className="space-y-1.5">
            {dailyTasks.map((t) => (
              <div key={t.code} className="rounded-lg bg-slate-50 px-2 py-1.5">
                <div className="flex items-center gap-1.5">
                  <span className="text-[11px] text-slate-700 flex-1 truncate">{t.name}</span>
                  <span className="text-[9px] text-amber-600 shrink-0">
                    +{t.exp_reward}EXP
                  </span>
                  {t.done && !t.claimed ? (
                    <button
                      onClick={() => claim(t.code)}
                      className="shrink-0 text-[9px] px-1.5 py-0.5 rounded bg-indigo-600 text-white"
                    >
                      领取
                    </button>
                  ) : t.claimed ? (
                    <span className="shrink-0 text-[9px] text-emerald-600">✓</span>
                  ) : (
                    <span className="shrink-0 text-[9px] text-slate-400">
                      {t.progress}/{t.target}
                    </span>
                  )}
                </div>
                <Progress
                  percent={Math.min(100, (t.progress / t.target) * 100)}
                  size="small"
                  showInfo={false}
                  strokeColor={t.done ? '#34d399' : '#6366f1'}
                  trailColor="#e2e8f0"
                  className="!mb-0"
                />
              </div>
            ))}
          </div>
        </div>

        {/* 冒险进度 */}
        <button
          onClick={() => navigate('/levels')}
          className="game-panel p-2.5 text-left active:bg-slate-50"
        >
          <div className="flex items-center gap-1.5 mb-1">
            <span className="text-sm">🗺️</span>
            <span className="text-xs font-medium text-indigo-700">冒险进度</span>
            <span className="ml-auto text-[10px] text-slate-400">›</span>
          </div>
          <div className="text-center py-1">
            <div className="text-2xl font-black text-indigo-600 leading-none">
              {completedCount}
              <span className="text-xs text-slate-400 font-normal"> / {levels.length}</span>
            </div>
            <div className="text-[9px] text-slate-400 mt-0.5">已通关关卡</div>
          </div>
          <div className="space-y-1">
            {scenes.slice(0, 3).map((s) => (
              <div key={s.name} className="flex items-center gap-1 text-[10px]">
                <span className="shrink-0">{s.icon}</span>
                <span className="text-slate-500 flex-1 truncate">{s.name}</span>
                <span className="text-slate-400 shrink-0">
                  {s.completed_count}/{s.level_count}
                </span>
              </div>
            ))}
          </div>
          <div className="mt-1 text-[9px] text-slate-400">已解锁 {unlockedCount} 关</div>
        </button>

        {/* 排行榜：跟冒险进度凑成一行，只露前三名 */}
        <div className="game-panel p-2.5">
          <div className="flex items-center gap-1.5 mb-1.5">
            <span className="text-sm">🏆</span>
            <span className="text-xs font-medium text-indigo-700">冒险者总榜</span>
            <Link to="/profile" className="ml-auto text-[10px] text-indigo-500">
              全部 ›
            </Link>
          </div>
          <div className="space-y-1">
            {leaderboard.map((e) => (
              <div key={e.rank} className="flex items-center gap-1.5 text-[11px] px-1.5 py-1 rounded-lg bg-slate-50">
                <span
                  className={`w-4 text-center font-bold shrink-0 ${
                    e.rank <= 3 ? 'text-amber-600' : 'text-slate-400'
                  }`}
                >
                  {e.rank}
                </span>
                <span className="flex-1 truncate text-slate-700">{e.character_name}</span>
                <span className="text-[9px] text-indigo-600 shrink-0">Lv.{e.level}</span>
                <span className="text-[9px] text-amber-600 shrink-0">{e.total_exp}</span>
              </div>
            ))}
            {leaderboard.length === 0 && (
              <div className="text-[10px] text-slate-400 text-center py-3">还没有排名，去闯关吧</div>
            )}
          </div>
        </div>
      </div>

      <div className="text-center">
        <Button size="small" type="text" onClick={share} className="!text-slate-400 !text-[11px]">
          📣 分享战绩（计入每日任务）
        </Button>
      </div>
    </div>
  )
}
