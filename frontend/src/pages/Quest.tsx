import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { App, Button, Input, Modal, Progress } from 'antd'
import { motion, AnimatePresence } from 'framer-motion'
import { api, ApiError } from '../api/client'
import { useAuth } from '../store/auth'
import type { AnswerResult, QuestQuestion, Settlement } from '../types'

export default function Quest() {
  const { levelCode } = useParams<{ levelCode: string }>()
  const navigate = useNavigate()
  const { message } = App.useApp()
  const { refreshCharacter, character } = useAuth()

  const [runId, setRunId] = useState<string | null>(null)
  const [levelName, setLevelName] = useState('')
  const [question, setQuestion] = useState<QuestQuestion | null>(null)
  const [total, setTotal] = useState(10)
  const [hp, setHp] = useState(3)
  const [maxHp, setMaxHp] = useState(3)
  const [answer, setAnswer] = useState<number | string>(-1)
  const [result, setResult] = useState<AnswerResult | null>(null)
  const [settle, setSettle] = useState<Settlement | null>(null)
  const [loading, setLoading] = useState(false)
  const [reviveOpen, setReviveOpen] = useState(false)
  const startedRef = useRef(false)

  const start = useCallback(async () => {
    setLoading(true)
    try {
      const r = await api.post<{ run_id: string; total: number; hp: number; level_code: string }>(
        '/api/quests/start',
        { level_code: levelCode, mode: 'normal' },
      )
      setRunId(r.run_id)
      setTotal(r.total)
      setHp(r.hp)
      setMaxHp(r.hp)
      const q = await api.get<QuestQuestion>(`/api/quests/question/${r.run_id}`)
      setQuestion(q)
    } catch (e) {
      message.error((e as Error).message)
      navigate('/levels')
    } finally {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [levelCode])

  useEffect(() => {
    if (!startedRef.current) {
      startedRef.current = true
      api
        .get<{ levels: { code: string; name: string }[] }>('/api/levels/map')
        .then((d) => setLevelName(d.levels.find((l) => l.code === levelCode)?.name || '关卡'))
        .catch(() => setLevelName('关卡'))
      start()
    }
  }, [start, levelCode])

  const loadNext = async () => {
    if (!runId) return
    const q = await api.get<QuestQuestion>(`/api/quests/question/${runId}`)
    setQuestion(q)
    setAnswer(-1)
    setResult(null)
  }

  const submitAnswer = async () => {
    if (!runId || !question) return
    if (answer === -1 || (typeof answer === 'string' && !answer.trim())) {
      message.warning('请先作答')
      return
    }
    setLoading(true)
    try {
      const r = await api.post<AnswerResult>('/api/quests/answer', {
        run_id: runId,
        question_id: question.question_id,
        answer,
      })
      setHp(r.hp_left)
      setResult(r)
      if (r.level_failed) {
        setReviveOpen(true)
      }
      await refreshCharacter()
    } catch (e) {
      message.error((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  const nextQuestion = async () => {
    if (!result) return
    if (result.finished) {
      // 结算
      try {
        const s = await api.post<Settlement>(`/api/quests/settle?run_id=${runId}`)
        setSettle(s)
        await refreshCharacter()
      } catch (e) {
        message.error((e as Error).message)
      }
    } else {
      loadNext().catch((e) => message.error((e as Error).message))
    }
  }

  const revive = async () => {
    if (!runId) return
    try {
      await api.post(`/api/quests/revive?run_id=${runId}`)
      setReviveOpen(false)
      message.success('复活成功！❤️ 生命值已恢复')
      await refreshCharacter()
      let q: QuestQuestion | null = null
      try {
        q = await api.get<QuestQuestion>(`/api/quests/question/${runId}`)
      } catch (e) {
        if (!(e instanceof ApiError && e.status === 409)) throw e
        q = null // 409 = 题目已答完，直接进入结算
      }
      if (q?.question_id) {
        setQuestion(q)
        setAnswer(-1)
        setResult(null)
      } else {
        // 已答完 → 结算
        const s = await api.post<Settlement>(`/api/quests/settle?run_id=${runId}`)
        setSettle(s)
      }
    } catch (e) {
      message.warning((e as Error).message)
    }
  }

  const exitToMap = () => navigate('/levels')

  // ---------- 结算视图 ----------
  if (settle) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="game-panel w-full max-w-lg p-8 text-center"
        >
          <div className="text-6xl mb-3">{settle.level_completed ? '🏆' : '💔'}</div>
          <h1 className="text-2xl font-bold text-indigo-200">
            {settle.level_completed ? '关卡通关！' : '本次挑战结束'}
          </h1>
          <div className="text-slate-400 text-sm mt-1">{levelName}</div>

          <div className="grid grid-cols-3 gap-3 my-6">
            <div className="p-3 rounded-xl bg-white/5">
              <div className="text-2xl font-bold text-emerald-400">{settle.correct_count}</div>
              <div className="text-[11px] text-slate-400">答对</div>
            </div>
            <div className="p-3 rounded-xl bg-white/5">
              <div className="text-2xl font-bold text-rose-400">{settle.wrong_count}</div>
              <div className="text-[11px] text-slate-400">答错</div>
            </div>
            <div className="p-3 rounded-xl bg-white/5">
              <div className="text-2xl font-bold text-amber-300">{settle.accuracy}%</div>
              <div className="text-[11px] text-slate-400">正确率</div>
            </div>
          </div>

          <div className="flex justify-center gap-6 text-sm mb-6">
            <span className="text-purple-300">✨ +{settle.total_exp} EXP</span>
            <span className="text-amber-300">🪙 +{settle.total_coins} 代码币</span>
          </div>

          <AnimatePresence>
            {settle.new_achievements.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-6 p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30"
              >
                <div className="text-amber-300 font-medium mb-2">🎉 解锁新成就</div>
                {settle.new_achievements.map((a) => (
                  <div key={a.code} className="text-sm text-slate-200">
                    {a.icon} {a.name} — {a.description}
                  </div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>

          {settle.unlocked_next && (
            <div className="text-sm text-emerald-400 mb-4">🔓 已解锁新关卡！</div>
          )}

          <div className="flex gap-3 justify-center">
            <Button onClick={exitToMap}>返回地图</Button>
            <Button
              type="primary"
              onClick={() => {
                setSettle(null)
                startedRef.current = false
                start()
              }}
            >
              再来一次
            </Button>
            {settle.unlocked_next && (
              <Button
                type="primary"
                onClick={() => navigate(`/quest/${settle.unlocked_next}`)}
                className="glow-btn"
              >
                挑战下一关 →
              </Button>
            )}
          </div>
        </motion.div>
      </div>
    )
  }

  // ---------- 复活弹窗 ----------
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="game-panel w-full max-w-3xl p-6 md:p-8">
        {/* HUD */}
        <div className="flex items-center justify-between flex-wrap gap-3 mb-5">
          <div>
            <button onClick={exitToMap} className="text-slate-400 hover:text-indigo-300 text-sm">
              ← 返回地图
            </button>
            <h1 className="font-bold text-indigo-100 mt-1">{levelName || '闯关挑战'}</h1>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex gap-1" title="生命值">
              {Array.from({ length: maxHp }).map((_, i) => (
                <span key={i} className={`text-xl ${i < hp ? '' : 'opacity-25 grayscale'}`}>
                  ❤️
                </span>
              ))}
            </div>
            <div className="text-sm text-slate-300 w-16 text-right">
              {question?.index ?? 0} / {total}
            </div>
          </div>
        </div>

        <Progress
          percent={Math.round(((question?.index ?? 1) - 1 + (result ? 0 : 0)) * 10)}
          showInfo={false}
          strokeColor="#818cf8"
          trailColor="#2a2d52"
          className="mb-6"
        />

        {loading && !question ? (
          <div className="py-20 text-center text-slate-500">冒险加载中…</div>
        ) : question ? (
          <AnimatePresence mode="wait">
            <motion.div
              key={question.question_id + String(result?.correct ?? '')}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              <div className="mb-2 flex items-center gap-2 text-xs">
                <span className="px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300">
                  {question.subject}
                </span>
                <span className="px-2 py-0.5 rounded-full bg-white/10 text-slate-400">
                  难度 ★{question.difficulty}
                </span>
                <span className="px-2 py-0.5 rounded-full bg-white/10 text-slate-400">
                  {question.type === 'choice' ? '选择题' : question.type === 'blank' ? '填空题' : question.type === 'code' ? '编程题' : '简答题'}
                </span>
              </div>
              <div className="text-lg text-slate-100 leading-relaxed mb-5 whitespace-pre-wrap">
                {question.stem}
              </div>

              {question.type === 'choice' && (
                <div className="grid gap-2.5">
                  {question.options.map((opt, i) => (
                    <button
                      key={i}
                      disabled={!!result}
                      onClick={() => setAnswer(i)}
                      className={`text-left px-4 py-3 rounded-xl border text-sm transition-all disabled:opacity-60 ${
                        result
                          ? result.correct && answer === i
                            ? 'border-emerald-400 bg-emerald-500/15 text-emerald-200'
                            : !result.correct && answer === i
                              ? 'border-rose-400 bg-rose-500/15 text-rose-200'
                              : 'border-indigo-500/20 text-slate-400'
                          : answer === i
                            ? 'border-indigo-400 bg-indigo-500/20 text-indigo-100'
                            : 'border-indigo-500/20 text-slate-300 hover:border-indigo-400/60'
                      }`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              )}

              {(question.type === 'blank' || question.type === 'short') && (
                <Input.TextArea
                  disabled={!!result}
                  rows={question.type === 'short' ? 4 : 2}
                  placeholder={question.type === 'blank' ? '在此输入答案…' : '简述你的答案…'}
                  value={typeof answer === 'number' ? '' : answer}
                  onChange={(e) => setAnswer(e.target.value)}
                />
              )}

              {question.type === 'code' && (
                <div className="rounded-xl overflow-hidden border border-indigo-500/20">
                  <div className="bg-[#12142e] px-3 py-1.5 text-xs text-slate-400 flex justify-between">
                    <span>Python 代码</span>
                    {!result && <span className="text-indigo-300">闯关模式按思路判定，正式评测请去 Bug 猎人</span>}
                  </div>
                  <Input.TextArea
                    disabled={!!result}
                    rows={10}
                    value={typeof answer === 'number' ? '' : answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    placeholder={question.starter_code || '# 在此编写你的代码'}
                    style={{ fontFamily: 'Consolas, monospace', background: '#12142e' }}
                  />
                </div>
              )}

              {/* 答题结果 */}
              {result && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`mt-5 p-4 rounded-2xl border ${
                    result.correct
                      ? 'border-emerald-500/30 bg-emerald-500/10'
                      : 'border-rose-500/30 bg-rose-500/10'
                  }`}
                >
                  <div className={`font-medium mb-2 ${result.correct ? 'text-emerald-300' : 'text-rose-300'}`}>
                    {result.correct ? '✅ 回答正确！' : '❌ 回答错误'}
                    <span className="ml-3 text-xs text-slate-400">
                      +{result.exp_gained} EXP · +{result.coins_gained}🪙
                    </span>
                  </div>
                  <div className="text-sm text-slate-200 leading-relaxed">
                    <span className="text-indigo-300">考点：</span>
                    {result.knowledge_point}
                  </div>
                  <div className="text-sm text-slate-300 leading-relaxed mt-1.5">
                    <span className="text-indigo-300">解析：</span>
                    {result.explanation}
                  </div>
                  {result.ai_analysis && (
                    <div className="text-sm text-purple-300 leading-relaxed mt-1.5">
                      <span>🤖 AI 分析：</span>
                      {result.ai_analysis}
                    </div>
                  )}
                  <Button type="primary" className="mt-3" onClick={nextQuestion} loading={loading}>
                    {result.finished ? '结算本次挑战' : '下一题 →'}
                  </Button>
                </motion.div>
              )}

              {!result && (
                <Button
                  type="primary"
                  size="large"
                  block
                  className="mt-5 glow-btn"
                  onClick={submitAnswer}
                  loading={loading}
                >
                  提交答案
                </Button>
              )}
            </motion.div>
          </AnimatePresence>
        ) : (
          <div className="py-20 text-center text-slate-500">闯关已结束</div>
        )}
      </div>

      <Modal
        open={reviveOpen}
        onCancel={() => {
          setReviveOpen(false)
          exitToMap()
        }}
        onOk={revive}
        okText="用 20 币复活"
        cancelText="离开关卡"
        title="❤️ 生命值耗尽"
        centered
      >
        <p className="text-slate-300">
          你已阵亡……可以用 <span className="text-amber-300">{character?.coins ?? 0} 代码币</span> 复活并恢复全部生命值，
          继续完成挑战。离开后进度将保留，可重新挑战。
        </p>
      </Modal>
    </div>
  )
}
