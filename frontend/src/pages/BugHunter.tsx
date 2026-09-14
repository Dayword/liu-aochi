import { useEffect, useState } from 'react'
import { App, Button, Input, Modal, Progress, Segmented } from 'antd'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '../api/client'
import { useAuth } from '../store/auth'
import type { BugChallenge, BugSubmit } from '../types'

const DIFF_LABELS: Record<number, string> = { 1: '入门', 2: '进阶', 3: '困难' }
const DIFF_COLORS: Record<number, string> = { 1: '#34d399', 2: '#fbbf24', 3: '#f87171' }

export default function BugHunter() {
  const { message } = App.useApp()
  const { refreshCharacter } = useAuth()
  const [challenges, setChallenges] = useState<BugChallenge[]>([])
  const [filter, setFilter] = useState<string>('all')
  const [current, setCurrent] = useState<BugChallenge | null>(null)
  const [code, setCode] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<BugSubmit | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)
  const [leaderboard, setLeaderboard] = useState<{ rank: number; nickname: string; character_name: string; bug_code: string; score: number; accuracy: number }[]>([])

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const load = async () => {
    try {
      const [chs, lb] = await Promise.all([
        api.get<BugChallenge[]>('/api/bugs/challenges'),
        api.get<{ rank: number; nickname: string; character_name: string; bug_code: string; score: number; accuracy: number }[]>('/api/bugs/leaderboard'),
      ])
      setChallenges(chs)
      setLeaderboard(lb)
    } catch (e) {
      message.error((e as Error).message)
    }
  }

  const openChallenge = async (c: BugChallenge) => {
    try {
      const full = await api.get<BugChallenge>(`/api/bugs/challenges/${c.code}`)
      setCurrent(full)
      setCode(full.buggy_code || '')
      setResult(null)
      setDetailOpen(true)
    } catch (e) {
      message.error((e as Error).message)
    }
  }

  const submit = async () => {
    if (!current) return
    if (!code.trim()) {
      message.warning('请先提交修复后的代码')
      return
    }
    setSubmitting(true)
    try {
      const r = await api.post<BugSubmit>('/api/bugs/submit', {
        bug_code: current.code,
        code,
      })
      setResult(r)
      await refreshCharacter()
      await load()
    } catch (e) {
      message.error((e as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  const filtered = challenges.filter((c) => (filter === 'all' ? true : String(c.difficulty) === filter))

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-indigo-200">🐛 Bug 猎人</h1>
          <p className="text-slate-400 text-sm mt-1">阅读代码、找出 Bug、提交修复，AI 实时运行验证</p>
        </div>
        <Segmented
          value={filter}
          onChange={(v) => setFilter(v as string)}
          options={[
            { label: '全部', value: 'all' },
            { label: '入门', value: '1' },
            { label: '进阶', value: '2' },
            { label: '困难', value: '3' },
          ]}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* 挑战列表 */}
        <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-3">
          {filtered.map((c, i) => (
            <motion.button
              key={c.code}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              whileHover={{ y: -3 }}
              onClick={() => openChallenge(c)}
              className="game-panel p-4 text-left"
            >
              <div className="flex items-center justify-between">
                <span className="text-2xl">{c.done ? '✅' : '🐛'}</span>
                <span
                  className="px-2 py-0.5 rounded-full text-[10px]"
                  style={{ background: `${DIFF_COLORS[c.difficulty]}22`, color: DIFF_COLORS[c.difficulty] }}
                >
                  {DIFF_LABELS[c.difficulty]} · {c.bug_type}
                </span>
              </div>
              <div className="mt-2 font-medium text-slate-100">{c.title}</div>
              <div className="text-[11px] text-slate-400 mt-1 line-clamp-2">{c.description}</div>
              <div className="text-[11px] text-indigo-300/70 mt-2">{c.language} · 点击修复 →</div>
            </motion.button>
          ))}
          {filtered.length === 0 && <div className="text-slate-500 py-10 text-center col-span-2">暂无挑战</div>}
        </div>

        {/* Bug 猎人排行榜 */}
        <div className="game-panel p-5 h-fit">
          <h3 className="font-semibold text-indigo-200 mb-4">🏆 Bug 猎人排行榜</h3>
          <div className="space-y-2">
            {leaderboard.slice(0, 10).map((e) => (
              <div key={e.rank} className="flex items-center gap-2 text-sm px-2 py-1.5 rounded-lg bg-white/5">
                <span className={`w-5 text-center font-bold ${e.rank <= 3 ? 'text-amber-300' : 'text-slate-500'}`}>
                  {e.rank}
                </span>
                <span className="flex-1 truncate text-slate-200">{e.character_name}</span>
                <span className="text-[10px] text-slate-500">{e.bug_code}</span>
                <span className="text-[11px] text-amber-300">{e.score}分</span>
              </div>
            ))}
            {leaderboard.length === 0 && (
              <div className="text-center text-slate-500 text-sm py-8">暂无战绩，来当第一个 Bug 猎手！</div>
            )}
          </div>
        </div>
      </div>

      {/* 挑战详情 */}
      <Modal
        open={detailOpen}
        onCancel={() => setDetailOpen(false)}
        width={860}
        title={
          current ? (
            <span>
              🐛 {current.title}{' '}
              <span className="text-xs text-slate-500">
                {DIFF_LABELS[current.difficulty]} · {current.bug_type}
              </span>
            </span>
          ) : (
            ''
          )
        }
        footer={null}
        centered
      >
        {current && (
          <div className="space-y-4">
            {!result && (
              <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200/90">
                💡 提示：{current.hint}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="rounded-xl overflow-hidden border border-indigo-500/20">
                <div className="bg-[#12142e] px-3 py-1.5 text-xs text-slate-400">原始代码（含 Bug）</div>
                <pre className="p-3 text-xs text-rose-300/90 overflow-x-auto bg-[#12142e] whitespace-pre-wrap font-mono leading-relaxed">
                  {current.buggy_code}
                </pre>
              </div>
              <div className="rounded-xl overflow-hidden border border-indigo-500/20">
                <div className="bg-[#12142e] px-3 py-1.5 text-xs text-slate-400 flex justify-between">
                  <span>你的修复代码</span>
                  <span className="text-emerald-400">● 实时运行验证</span>
                </div>
                <Input.TextArea
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  rows={12}
                  style={{ fontFamily: 'Consolas, monospace', background: '#12142e', border: 'none' }}
                />
              </div>
            </div>

            {/* 测试用例预览 */}
            <div className="text-xs text-slate-400">
              测试用例预览：
              {(current.test_cases_preview || []).map((tc, i) => (
                <span key={i} className="ml-2 px-2 py-0.5 bg-white/5 rounded">
                  输入 "{tc.input}" → 期望 "{tc.expected}"
                </span>
              ))}
              <span className="ml-2 text-slate-500">（隐藏部分用例）</span>
            </div>

            <AnimatePresence>
              {result && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`p-4 rounded-2xl border ${
                    result.passed ? 'border-emerald-500/40 bg-emerald-500/10' : 'border-rose-500/40 bg-rose-500/10'
                  }`}
                >
                  <div className="flex items-center justify-between flex-wrap gap-2 mb-2">
                    <div className={`font-bold ${result.passed ? 'text-emerald-300' : 'text-rose-300'}`}>
                      {result.passed ? '🎉 修复成功！' : '❌ 仍有 Bug'}
                    </div>
                    <div className="text-sm text-amber-300">综合评分 {result.score} 分</div>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-center text-xs mb-3">
                    <div className="p-2 bg-white/5 rounded-lg">
                      <div className="text-lg font-bold text-emerald-400">{result.accuracy}%</div>
                      <div className="text-slate-400">测试通过率</div>
                    </div>
                    <div className="p-2 bg-white/5 rounded-lg">
                      <div className="text-lg font-bold text-indigo-300">{result.tests_passed}/{result.tests_total}</div>
                      <div className="text-slate-400">通过用例</div>
                    </div>
                    <div className="p-2 bg-white/5 rounded-lg">
                      <div className="text-lg font-bold text-purple-300">{result.speed_ms}ms</div>
                      <div className="text-slate-400">运行耗时</div>
                    </div>
                    <div className="p-2 bg-white/5 rounded-lg">
                      <div className="text-lg font-bold text-amber-300">{result.quality}</div>
                      <div className="text-slate-400">代码质量</div>
                    </div>
                  </div>
                  <div className="text-sm text-slate-300 leading-relaxed">{result.explanation}</div>
                  <div className="text-xs text-slate-400 mt-2">
                    ✨ +{result.exp_gained} EXP · 🪙 +{result.coins_gained}
                  </div>
                  {result.new_achievements.map((a) => (
                    <div key={a.code} className="text-xs text-amber-300 mt-1">
                      🎉 解锁成就：{a.icon} {a.name}
                    </div>
                  ))}
                  <Button
                    className="mt-3"
                    onClick={() => {
                      setResult(null)
                      setDetailOpen(false)
                    }}
                  >
                    完成
                  </Button>
                </motion.div>
              )}
            </AnimatePresence>

            {!result && (
              <Button type="primary" block loading={submitting} onClick={submit} className="glow-btn">
                提交修复 · 运行验证
              </Button>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
