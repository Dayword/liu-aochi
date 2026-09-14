import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { App, Button, Progress } from 'antd'
import { motion } from 'framer-motion'
import { api } from '../api/client'
import { useAuth } from '../store/auth'
import type { DailyTask, LeaderEntry, LevelItem, Scene } from '../types'

export default function Home() {
  const { character, refreshCharacter } = useAuth()
  const { message } = App.useApp()
  const [dailyTasks, setDailyTasks] = useState<DailyTask[]>([])
  const [levels, setLevels] = useState<LevelItem[]>([])
  const [scenes, setScenes] = useState<Scene[]>([])
  const [leaderboard, setLeaderboard] = useState<LeaderEntry[]>([])
  const [signing, setSigning] = useState(false)

  const load = async () => {
    const [tasks, map, lb] = await Promise.all([
      api.get<DailyTask[]>('/api/growth/daily-tasks'),
      api.get<{ scenes: Scene[]; levels: LevelItem[] }>('/api/levels/map'),
      api.get<LeaderEntry[]>('/api/growth/leaderboard?board=total&limit=8'),
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
      const r = await api.post<{ streak: number; exp: number; coins: number; msg: string }>('/api/user/signin')
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

  return (
    <div className="space-y-6">
      {/* 角色 HUD */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="game-panel p-6 relative overflow-hidden"
      >
        <div className="absolute -right-8 -top-8 text-[8rem] opacity-10 select-none">⚔️</div>
        <div className="flex flex-wrap items-center gap-6 relative z-10">
          <div className="text-6xl">{character.identity === '求职中' ? '💼' : '🎓'}</div>
          <div className="flex-1 min-w-[220px]">
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-xl font-bold text-indigo-100">{character.name}</h2>
              <span className="px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 text-xs">
                {character.class_name}
              </span>
              <span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-xs">
                {character.title}
              </span>
            </div>
            <div className="mt-3 flex items-center gap-3">
              <div className="text-3xl font-black text-indigo-300">Lv.{character.level}</div>
              <div className="flex-1">
                <Progress
                  percent={expPct}
                  strokeColor="#a78bfa"
                  trailColor="#2a2d52"
                  format={() => `${character.exp}/${character.exp_to_next} EXP`}
                />
              </div>
            </div>
            <div className="flex gap-5 mt-2 text-sm">
              <span className="text-amber-300">🪙 {character.coins} 代码币</span>
              <span className="text-rose-300">❤️ {character.hp}/{character.max_hp}</span>
              <span className="text-slate-400">🔥 连续 {character.streak_days} 天</span>
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <Button onClick={signin} loading={signing} className="glow-btn">
              📅 每日签到
            </Button>
            <Button onClick={share} className="glow-btn">
              📣 分享战绩
            </Button>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 每日任务 */}
        <div className="game-panel p-5">
          <h3 className="font-semibold text-indigo-200 mb-4 flex items-center gap-2">
            <span className="text-xl">📋</span> 每日任务
          </h3>
          <div className="space-y-3">
            {dailyTasks.map((t) => (
              <div key={t.code} className="p-3 rounded-xl bg-white/5 border border-indigo-500/10">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-200">{t.name}</span>
                  <span className="text-[11px] text-amber-300">
                    +{t.exp_reward} EXP · +{t.coin_reward}🪙
                  </span>
                </div>
                <div className="mt-1.5 flex items-center gap-2">
                  <Progress
                    percent={Math.min(100, (t.progress / t.target) * 100)}
                    size="small"
                    strokeColor={t.done ? '#34d399' : '#818cf8'}
                    trailColor="#2a2d52"
                    format={() => `${t.progress}/${t.target}`}
                  />
                  {t.done && !t.claimed ? (
                    <Button size="small" type="primary" onClick={() => claim(t.code)}>
                      领取
                    </Button>
                  ) : t.claimed ? (
                    <span className="text-[11px] text-emerald-400">✓ 已领取</span>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
          <p className="text-[11px] text-slate-500 mt-3">完成闯关/对话/签到自动推进任务进度</p>
        </div>

        {/* 中间：关卡进度 */}
        <div className="game-panel p-5">
          <h3 className="font-semibold text-indigo-200 mb-4 flex items-center gap-2">
            <span className="text-xl">🗺️</span> 冒险进度
          </h3>
          <div className="text-center py-4">
            <div className="text-5xl font-black text-indigo-300">
              {completedCount}
              <span className="text-xl text-slate-500"> / {levels.length}</span>
            </div>
            <div className="text-xs text-slate-400 mt-1">已通关关卡</div>
          </div>
          <div className="space-y-2">
            {scenes.slice(0, 4).map((s) => (
              <div key={s.name} className="flex items-center gap-2 text-sm">
                <span>{s.icon}</span>
                <span className="text-slate-300 flex-1 truncate">{s.name}</span>
                <span className="text-[11px] text-slate-500">
                  {s.completed_count}/{s.level_count}
                </span>
                <Progress
                  percent={Math.round((s.completed_count / s.level_count) * 100)}
                  size="small"
                  style={{ width: 60 }}
                  strokeColor="#34d399"
                  trailColor="#2a2d52"
                  showInfo={false}
                />
              </div>
            ))}
          </div>
          <div className="mt-4 text-xs text-slate-400">
            已解锁 <span className="text-emerald-400">{unlockedCount}</span> 个关卡，继续闯关解锁下一场景！
          </div>
          <Link to="/levels">
            <Button type="primary" block className="mt-3 glow-btn">
              进入关卡地图 →
            </Button>
          </Link>
        </div>

        {/* 排行榜 */}
        <div className="game-panel p-5">
          <h3 className="font-semibold text-indigo-200 mb-4 flex items-center gap-2">
            <span className="text-xl">🏆</span> 冒险者总榜
          </h3>
          <div className="space-y-2">
            {leaderboard.map((e) => (
              <div key={e.rank} className="flex items-center gap-3 text-sm px-2 py-1.5 rounded-lg bg-white/5">
                <span className={`w-6 text-center font-bold ${e.rank <= 3 ? 'text-amber-300' : 'text-slate-500'}`}>
                  {e.rank}
                </span>
                <span className="text-lg">{e.rank <= 3 ? ['🥇', '🥈', '🥉'][e.rank - 1] : ''}</span>
                <span className="flex-1 truncate text-slate-200">{e.character_name}</span>
                <span className="text-[11px] text-slate-500">{e.class_name}</span>
                <span className="text-[11px] text-indigo-300">Lv.{e.level}</span>
                <span className="text-[11px] text-amber-300">{e.total_exp}</span>
              </div>
            ))}
          </div>
          <Link to="/profile" className="block text-center text-xs text-indigo-300 hover:text-indigo-200 mt-3">
            查看完整排行榜与我的成就 →
          </Link>
        </div>
      </div>

      {/* 玩法入口 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { to: '/chat', icon: '💬', title: 'AI 导师对话', desc: '概念讲解 / 代码答疑 / 学习路径' },
          { to: '/interview', icon: '🎤', title: '面试闯关', desc: '一面到 HR 面 · 四维评分' },
          { to: '/bugs', icon: '🐛', title: 'Bug 猎人', desc: '读码找 Bug · 实时运行验证' },
          { to: '/profile', icon: '📊', title: '个人中心', desc: '成就墙 / 错题本 / 能力雷达' },
        ].map((item) => (
          <Link key={item.to} to={item.to}>
            <motion.div
              whileHover={{ y: -4 }}
              className="game-panel p-5 text-center h-full"
            >
              <div className="text-4xl mb-2">{item.icon}</div>
              <div className="font-medium text-indigo-200">{item.title}</div>
              <div className="text-[11px] text-slate-400 mt-1">{item.desc}</div>
            </motion.div>
          </Link>
        ))}
      </div>
    </div>
  )
}
