import { useEffect, useRef, useState } from 'react'
import { App, Button, Progress, Segmented, Tabs } from 'antd'
import * as echarts from 'echarts'
import { motion } from 'framer-motion'
import { api } from '../api/client'
import type { Achievement, DailyTask, LeaderEntry, Profile, WrongItem } from '../types'

const DIFF_LABELS = ['L1', 'L2', 'L3', 'L4', 'L5']

function RadarChart({ subjects, scores }: { subjects: string[]; scores: number[] }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!ref.current) return
    const chart = echarts.init(ref.current)
    chart.setOption({
      backgroundColor: 'transparent',
      radar: {
        indicator: subjects.map((s, i) => ({ name: s, max: 100 })),
        radius: '65%',
        axisName: { color: '#94a3b8', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(99,102,241,0.25)' } },
        splitArea: { areaStyle: { color: ['rgba(99,102,241,0.03)', 'rgba(99,102,241,0.08)'] } },
        axisLine: { lineStyle: { color: 'rgba(99,102,241,0.3)' } },
      },
      series: [
        {
          type: 'radar',
          data: [
            {
              value: scores,
              name: '能力值',
              areaStyle: { color: 'rgba(129,140,248,0.3)' },
              lineStyle: { color: '#818cf8', width: 2 },
              itemStyle: { color: '#a78bfa' },
            },
          ],
        },
      ],
    })
    const onResize = () => chart.resize()
    window.addEventListener('resize', onResize)
    return () => {
      window.removeEventListener('resize', onResize)
      chart.dispose()
    }
  }, [subjects, scores])
  return <div ref={ref} className="h-64 w-full" />
}

export default function Profile() {
  const { message } = App.useApp()
  const [profile, setProfile] = useState<Profile | null>(null)
  const [wrongBook, setWrongBook] = useState<WrongItem[]>([])
  const [leaderboard, setLeaderboard] = useState<LeaderEntry[]>([])
  const [lbBoard, setLbBoard] = useState('total')

  const load = async () => {
    try {
      const [p, w, lb] = await Promise.all([
        api.get<Profile>('/api/user/profile'),
        api.get<WrongItem[]>('/api/growth/wrong-book'),
        api.get<LeaderEntry[]>('/api/growth/leaderboard?board=total&limit=20'),
      ])
      setProfile(p)
      setWrongBook(w)
      setLeaderboard(lb)
    } catch (e) {
      message.error((e as Error).message)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const switchBoard = async (board: string) => {
    setLbBoard(board)
    try {
      const lb = await api.get<LeaderEntry[]>(`/api/growth/leaderboard?board=${board}&limit=20`)
      setLeaderboard(lb)
    } catch (e) {
      message.error((e as Error).message)
    }
  }

  const resolveWrong = async (id: number) => {
    try {
      await api.post(`/api/growth/wrong-book/${id}/resolve`)
      setWrongBook((w) => w.map((x) => (x.id === id ? { ...x, resolved: true } : x)))
      message.success('已标记为已掌握')
    } catch (e) {
      message.error((e as Error).message)
    }
  }

  if (!profile) {
    return <div className="text-center py-20 text-slate-500">加载中…</div>
  }

  const { character, achievements, daily_tasks, radar } = profile
  const unlockedCount = achievements.filter((a) => a.unlocked).length
  const expPct = Math.min(100, Math.round((character.exp / character.exp_to_next) * 100))

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-indigo-200">📊 个人中心</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* 角色卡 */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="game-panel p-6">
          <div className="flex items-center gap-4">
            <div className="text-6xl">{character.identity === '求职中' ? '💼' : '🎓'}</div>
            <div>
              <div className="text-xl font-bold text-indigo-100">{character.name}</div>
              <div className="text-sm text-amber-300 mt-0.5">{character.class_name} · {character.title}</div>
              <div className="text-xs text-slate-400 mt-0.5">{character.identity} · 🔥 连续 {character.streak_days} 天</div>
            </div>
          </div>
          <div className="mt-4">
            <div className="flex justify-between text-xs text-slate-400 mb-1">
              <span>Lv.{character.level}</span>
              <span>{character.exp}/{character.exp_to_next} EXP</span>
            </div>
            <Progress percent={expPct} strokeColor="#a78bfa" trailColor="#2a2d52" showInfo={false} />
          </div>
          <div className="grid grid-cols-3 gap-2 mt-4 text-center">
            {[
              { v: character.coins, l: '代码币', c: 'text-amber-300' },
              { v: character.hp + '/' + character.max_hp, l: '生命值', c: 'text-rose-300' },
              { v: character.total_exp, l: '累计EXP', c: 'text-purple-300' },
            ].map((x) => (
              <div key={x.l} className="p-2 bg-white/5 rounded-xl">
                <div className={`font-bold ${x.c}`}>{x.v}</div>
                <div className="text-[10px] text-slate-400">{x.l}</div>
              </div>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-2 mt-2 text-center text-[11px] text-slate-400">
            <div className="p-2 bg-white/5 rounded-xl">闯关 {character.total_quests} 次</div>
            <div className="p-2 bg-white/5 rounded-xl">对话 {character.total_chats} 次</div>
            <div className="p-2 bg-white/5 rounded-xl">面试 {character.total_interviews} 场</div>
            <div className="p-2 bg-white/5 rounded-xl">抓 Bug {character.total_bugs} 次</div>
          </div>
        </motion.div>

        {/* 能力雷达 */}
        <div className="game-panel p-6">
          <h3 className="font-semibold text-indigo-200 mb-2">🧠 能力雷达</h3>
          <RadarChart subjects={radar.subjects} scores={radar.scores} />
          <div className="text-center text-xs text-slate-500">按各学科答题正确率生成 · 多闯关提升</div>
        </div>

        {/* 学习数据 */}
        <div className="game-panel p-6">
          <h3 className="font-semibold text-indigo-200 mb-4">📈 学习数据</h3>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">累计答题</span>
              <span className="text-slate-200 font-medium">{character.total_correct + character.total_wrong} 题</span>
            </div>
            <Progress
              percent={Math.round((character.total_correct / Math.max(1, character.total_correct + character.total_wrong)) * 100)}
              strokeColor="#34d399"
              trailColor="#2a2d52"
              format={() => `正确率 ${character.total_correct}/${character.total_correct + character.total_wrong}`}
            />
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">错题本</span>
              <span className="text-rose-300 font-medium">{profile.wrong_count} 题</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">本周 EXP</span>
              <span className="text-purple-300 font-medium">{character.weekly_exp}</span>
            </div>
            <div className="pt-2">
              <div className="text-xs text-slate-500 mb-2">最近通关</div>
              <div className="flex gap-2 flex-wrap">
                {profile.recent_levels.map((l) => (
                  <span key={l.code} className="px-2 py-1 rounded-lg bg-white/5 text-[11px] text-slate-300">
                    {l.icon} {l.name} · {l.best_score}/10
                  </span>
                ))}
                {profile.recent_levels.length === 0 && (
                  <span className="text-[11px] text-slate-500">还没有通关记录，去闯关吧！</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <Tabs
        defaultActiveKey="achievements"
        items={[
          {
            key: 'achievements',
            label: `🏅 成就墙 (${unlockedCount}/${achievements.length})`,
            children: (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {achievements.map((a) => (
                  <div
                    key={a.code}
                    className={`p-4 rounded-2xl border text-center ${
                      a.unlocked
                        ? 'border-amber-500/40 bg-amber-500/10'
                        : 'border-slate-700/40 bg-slate-800/20 opacity-50 grayscale'
                    }`}
                  >
                    <div className="text-3xl mb-1">{a.icon}</div>
                    <div className="text-sm font-medium text-slate-200">{a.name}</div>
                    <div className="text-[10px] text-slate-400 mt-1">{a.description}</div>
                    {a.unlocked && (
                      <div className="text-[10px] text-amber-300/80 mt-1">
                        +{a.exp_reward} EXP · +{a.coin_reward}🪙
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ),
          },
          {
            key: 'wrongbook',
            label: `📕 错题本 (${wrongBook.length})`,
            children: (
              <div className="space-y-3">
                {wrongBook.length === 0 && (
                  <div className="text-center text-slate-500 py-12">错题本是空的，答题错误会自动收录 🎉</div>
                )}
                {wrongBook.map((w) => (
                  <div key={w.id} className={`game-panel p-4 ${w.resolved ? 'opacity-50' : ''}`}>
                    <div className="flex items-center gap-2 text-xs mb-2">
                      <span className="px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300">{w.subject}</span>
                      <span className="px-2 py-0.5 rounded-full bg-white/10 text-slate-400">{DIFF_LABELS[w.difficulty - 1]}</span>
                      <span className="px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300">错因：{w.reason || '未分类'}</span>
                      {w.resolved && <span className="text-emerald-400 text-[11px]">✓ 已掌握</span>}
                    </div>
                    <div className="text-sm text-slate-200 mb-2">{w.stem}</div>
                    <div className="text-xs text-slate-400 mb-1">
                      你的答案：<span className="text-rose-300">{String(w.user_answer) || '（空）'}</span>
                    </div>
                    <div className="text-xs text-slate-400 mb-2">
                      正确答案：<span className="text-emerald-300">{String(w.correct_answer)}</span>
                    </div>
                    <div className="text-xs text-slate-300 leading-relaxed">
                      <span className="text-indigo-300">解析：</span>
                      {w.explanation}
                    </div>
                    {!w.resolved && (
                      <Button size="small" className="mt-2" onClick={() => resolveWrong(w.id)}>
                        标记为已掌握
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            ),
          },
          {
            key: 'leaderboard',
            label: '🏆 排行榜',
            children: (
              <div className="space-y-3">
                <Segmented
                  value={lbBoard}
                  onChange={(v) => switchBoard(v as string)}
                  options={[
                    { label: '总榜', value: 'total' },
                    { label: '周榜', value: 'week' },
                    { label: '方向榜', value: 'class' },
                  ]}
                />
                <div className="game-panel p-4">
                  {leaderboard.map((e) => (
                    <div
                      key={e.rank}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm ${
                        e.rank % 2 ? 'bg-white/5' : 'bg-white/2'
                      }`}
                    >
                      <span className={`w-7 text-center font-bold ${e.rank <= 3 ? 'text-amber-300' : 'text-slate-500'}`}>
                        {e.rank}
                      </span>
                      <span className="text-lg">{e.rank <= 3 ? ['🥇', '🥈', '🥉'][e.rank - 1] : ''}</span>
                      <span className="flex-1 truncate text-slate-200">
                        {e.character_name} <span className="text-[10px] text-slate-500">({e.nickname})</span>
                      </span>
                      <span className="text-[11px] text-slate-500">{e.class_name}</span>
                      <span className="text-[11px] text-indigo-300">Lv.{e.level}</span>
                      <span className="text-[11px] text-amber-300">
                        {lbBoard === 'week' ? `${e.weekly_exp} 周EXP` : `${e.total_exp} EXP`}
                      </span>
                    </div>
                  ))}
                  {leaderboard.length === 0 && <div className="text-center text-slate-500 py-8">暂无数据</div>}
                </div>
              </div>
            ),
          },
          {
            key: 'daily',
            label: '📋 每日任务',
            children: (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {daily_tasks.map((t: DailyTask) => (
                  <div key={t.code} className="game-panel p-4">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-200">{t.name}</span>
                      <span className="text-amber-300 text-xs">+{t.exp_reward} EXP +{t.coin_reward}🪙</span>
                    </div>
                    <div className="text-[11px] text-slate-500 mt-1">{t.description}</div>
                    <Progress
                      percent={Math.min(100, (t.progress / t.target) * 100)}
                      size="small"
                      className="mt-2"
                      strokeColor={t.done ? '#34d399' : '#818cf8'}
                      trailColor="#2a2d52"
                      format={() => `${t.progress}/${t.target}`}
                    />
                  </div>
                ))}
              </div>
            ),
          },
        ]}
      />
    </div>
  )
}
