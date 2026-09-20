import { useCallback, useEffect, useRef, useState } from 'react'
import { App, Button, Spin } from 'antd'
import { motion } from 'framer-motion'
import { api } from '../api/client'
import Md from '../components/Md'
import type { GuideAnswerResult, GuidePointBrief, GuidePointDetail } from '../types'

function Section({ icon, title, children }: { icon: string; title: string; children: React.ReactNode }) {
  return (
    <div className="mt-4">
      <div className="text-sm font-medium text-indigo-700 mb-2">
        {icon} {title}
      </div>
      <div className="text-sm text-slate-600">{children}</div>
    </div>
  )
}

/**
 * 面试题引导式学习：题面是面试官原话，先看考察点和大白话，再自己写一段回答，
 * 踩中要点到阈值才算过关、才解锁同分类下一题。
 * 满分回答 / 踩坑 / 追问链都要**提交之后**才展示，否则等于直接看答案。
 */
export default function InterviewGuide({ onStartMock }: { onStartMock: () => void }) {
  const { message } = App.useApp()
  const alive = useRef(true)
  const [points, setPoints] = useState<GuidePointBrief[]>([])
  const [stage, setStage] = useState('')
  const [code, setCode] = useState('')
  const [detail, setDetail] = useState<GuidePointDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [answer, setAnswer] = useState('')
  const [result, setResult] = useState<GuideAnswerResult | null>(null)
  const [hint, setHint] = useState('')
  const [hintLoading, setHintLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [revealed, setRevealed] = useState(false)

  useEffect(() => {
    alive.current = true
    return () => {
      alive.current = false
    }
  }, [])

  const loadDetail = useCallback(
    async (c: string) => {
      setLoading(true)
      setResult(null)
      setHint('')
      try {
        const r = await api.get<GuidePointDetail>(`/api/interview/guide/points/${c}`)
        if (!alive.current) return
        setDetail(r)
        setCode(r.code)
        setStage(r.stage)
        setAnswer(r.last_answer || '')
        // 已经过关的题直接放开参考答案，免得再点一次
        setRevealed(r.status === 'completed')
      } catch (e) {
        if (alive.current) message.error((e as Error).message)
      } finally {
        if (alive.current) setLoading(false)
      }
    },
    [message],
  )

  useEffect(() => {
    api
      .get<GuidePointBrief[]>('/api/interview/guide/points')
      .then((list) => {
        if (!alive.current) return
        setPoints(list)
        // 默认停在第一道还没过关的题，全过了就停在最后一题
        const cur = list.find((p) => p.status !== 'completed') || list[list.length - 1]
        if (cur) void loadDetail(cur.code)
        else setLoading(false)
      })
      .catch((e) => {
        if (alive.current) message.error((e as Error).message)
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const refreshPoints = async () => {
    const list = await api.get<GuidePointBrief[]>('/api/interview/guide/points')
    if (alive.current) setPoints(list)
  }

  const pickStage = (s: string) => {
    if (s === stage) return
    setStage(s)
    const list = points.filter((p) => p.stage === s)
    const cur = list.find((p) => p.status !== 'completed') || list[0]
    if (cur) void loadDetail(cur.code)
  }

  const submit = async () => {
    if (!detail) return
    const text = answer.trim()
    if (!text) {
      message.warning('先写下你的回答再提交')
      return
    }
    setSubmitting(true)
    try {
      const r = await api.post<GuideAnswerResult>('/api/interview/guide/answer', {
        code: detail.code,
        answer: text,
      })
      if (!alive.current) return
      setResult(r)
      setRevealed(true)
      if (r.passed) {
        message.success(`过关！${r.score} 分`)
        await refreshPoints()
      }
    } catch (e) {
      if (alive.current) message.error((e as Error).message)
    } finally {
      if (alive.current) setSubmitting(false)
    }
  }

  const askHint = async () => {
    if (!detail) return
    setHintLoading(true)
    try {
      const r = await api.post<{ hint: string }>('/api/interview/guide/hint', {
        code: detail.code,
        answer: answer.trim(),
      })
      if (alive.current) setHint(r.hint)
    } catch (e) {
      if (alive.current) message.error((e as Error).message)
    } finally {
      if (alive.current) setHintLoading(false)
    }
  }

  const stages = [...new Set(points.map((p) => p.stage))]
  const stagePoints = points.filter((p) => p.stage === stage)
  const done = stagePoints.filter((p) => p.status === 'completed').length
  const totalDone = points.filter((p) => p.status === 'completed').length

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-indigo-700">🎯 AI Agent 面试题引导学习</h1>
          <p className="text-slate-500 text-sm mt-1">
            72 道面试官原话，按分类顺序解锁。先看「考察点」和「大白话」，再
            <span className="text-indigo-600 font-medium">自己写一段回答</span>
            提交 —— 踩中要点到 {stagePoints[0]?.min_score ?? 70} 分才过关，才解锁下一题。
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-slate-500">
            总进度 {totalDone}/{points.length || 72}
          </span>
          <Button size="small" onClick={onStartMock}>
            🎤 开始模拟面试
          </Button>
        </div>
      </div>

      {/* 分类切换 */}
      <div className="flex gap-1.5 flex-wrap">
        {stages.map((s) => {
          const all = points.filter((p) => p.stage === s)
          const ok = all.filter((p) => p.status === 'completed').length
          const active = s === stage
          return (
            <button
              key={s}
              onClick={() => pickStage(s)}
              className={`px-3 py-1.5 rounded-xl border text-xs transition-all ${
                active
                  ? 'border-indigo-400 bg-indigo-50 text-indigo-800 font-medium'
                  : 'border-slate-200 text-slate-600 hover:border-indigo-300 hover:text-indigo-700'
              }`}
            >
              {s}
              <span className={`ml-1.5 text-[10px] ${active ? 'text-indigo-500' : 'text-slate-400'}`}>
                {ok}/{all.length}
              </span>
            </button>
          )
        })}
      </div>

      {/* 分类内的题目：一题一个标签，按顺序解锁 */}
      <div className="game-panel p-3">
        <div className="flex items-center gap-2 flex-wrap mb-2">
          <span className="text-xs text-slate-500">
            {stage} 进度 {done}/{stagePoints.length}
          </span>
          <span className="text-[11px] text-slate-500">
            （上一题过关才会亮起下一题；分类之间互不阻塞）
          </span>
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          {stagePoints.map((p) => {
            const isCur = p.code === code
            const cls = isCur
              ? 'border-indigo-400 bg-indigo-100 text-indigo-800'
              : p.status === 'completed'
                ? 'border-emerald-300 bg-emerald-50 text-emerald-700 hover:border-emerald-500'
                : p.status === 'unlocked'
                  ? 'border-indigo-300 text-slate-600 hover:border-indigo-400'
                  : 'border-slate-300 text-slate-400 cursor-not-allowed'
            return (
              <button
                key={p.code}
                disabled={p.status === 'locked'}
                onClick={() => void loadDetail(p.code)}
                className={`px-2 py-1 rounded-lg border text-[11px] transition-all text-left ${cls}`}
                title={p.title}
              >
                {p.status === 'completed' ? '✓ ' : p.status === 'locked' ? '🔒 ' : ''}
                {p.order_no}. {p.summary || p.title.slice(0, 12)}
                {p.best_score > 0 && <span className="ml-1 opacity-70">{p.best_score}分</span>}
              </button>
            )
          })}
        </div>
      </div>

      {loading && (
        <div className="game-panel p-10 text-center">
          <Spin />
        </div>
      )}

      {!loading && detail && (
        <div className="grid gap-4 items-start lg:grid-cols-[minmax(0,1fr)_minmax(0,440px)]">
          {/* 左：讲解 */}
          <motion.div
            key={detail.code}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="game-panel p-5"
          >
            <div className="text-[11px] text-slate-500 mb-1">
              {detail.stage} · 第 {detail.order_no} 题
              {detail.status === 'completed' && <span className="ml-2 text-emerald-600">✓ 已过关（{detail.best_score} 分）</span>}
            </div>
            <div className="flex items-start gap-2">
              <span className="text-2xl shrink-0">🎤</span>
              <h2 className="text-lg font-bold text-slate-800 leading-relaxed">{detail.title}</h2>
            </div>

            <Section icon="🔍" title="考察点">
              <Md>{detail.definition}</Md>
            </Section>

            <Section icon="💡" title="大白话拆解">
              <Md>{detail.plain}</Md>
            </Section>

            {revealed ? (
              <>
                <Section icon="⭐" title="满分回答（照着背）">
                  <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-3">
                    <Md>{detail.example}</Md>
                  </div>
                </Section>

                <Section icon="⚠️" title="这么说会减分">
                  <ul className="list-disc pl-5 space-y-2">
                    {detail.pitfalls.map((p, i) => (
                      <li key={i} className="text-slate-600 leading-relaxed">
                        <Md>{p}</Md>
                      </li>
                    ))}
                  </ul>
                </Section>

                <Section icon="🔗" title="面试官会继续追问">
                  <div className="space-y-3">
                    {detail.followups.map((f, i) => (
                      <div key={i} className="rounded-xl border border-indigo-200 bg-indigo-50/50 p-3">
                        <div className="text-xs font-medium text-indigo-700 mb-1">追问 {i + 1}：{f.q}</div>
                        <div className="text-xs text-slate-600 leading-relaxed">
                          <Md>{f.a}</Md>
                        </div>
                      </div>
                    ))}
                  </div>
                </Section>
              </>
            ) : (
              <div className="mt-5 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-center">
                <div className="text-xs text-slate-500 mb-2">
                  满分回答 · 踩坑清单 · 追问链，提交后解锁
                </div>
                <Button size="small" type="link" onClick={() => setRevealed(true)}>
                  不想练了，直接看参考答案（会失去练习效果）
                </Button>
              </div>
            )}
          </motion.div>

          {/* 右：自己作答 */}
          <div className="game-panel p-4 lg:sticky lg:top-4 space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-emerald-700">✍️ 我的回答</span>
              <span className="text-[10px] text-slate-500">说出一段话，不是罗列要点词</span>
              {detail.best_score > 0 && (
                <span className="ml-auto text-[11px] text-slate-500">历史最高 {detail.best_score} 分</span>
              )}
            </div>

            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              rows={12}
              placeholder="结论先行 → 分点展开 → 举个例子。写成你面试时真会说出口的那段话。"
              className="w-full bg-[#f4f6fa] border border-indigo-300 rounded-lg p-3 text-sm text-slate-800 leading-relaxed outline-none focus:border-indigo-400 resize-y"
            />

            <div className="flex gap-2">
              <Button type="primary" loading={submitting} onClick={submit} className="flex-1 glow-btn">
                提交评分
              </Button>
              <Button loading={hintLoading} onClick={askHint}>
                💡 我卡住了
              </Button>
            </div>

            {hint && (
              <div className="rounded-lg border border-sky-300 bg-sky-50 p-3 text-xs text-sky-800 leading-relaxed">
                <span className="text-sky-700">💡 提示：</span>
                {hint}
              </div>
            )}

            {result && (
              <div
                className={`rounded-lg border p-3 text-xs space-y-2 ${
                  result.passed ? 'border-emerald-300 bg-emerald-50' : 'border-rose-300 bg-rose-50'
                }`}
              >
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`text-lg font-bold ${result.passed ? 'text-emerald-700' : 'text-rose-700'}`}>
                    {result.score}
                  </span>
                  <span className="text-slate-500">/ {result.min_score} 分过关线</span>
                  <span className={result.passed ? 'text-emerald-700' : 'text-rose-700'}>
                    {result.passed ? '✅ 过关，下一题已解锁' : '❌ 还没到线'}
                  </span>
                  {result.already_passed && <span className="text-slate-400">（这题此前已过）</span>}
                </div>

                <div className="text-slate-600 leading-relaxed">{result.comment}</div>

                {result.hit_keywords.length > 0 && (
                  <div className="leading-relaxed">
                    <span className="text-emerald-700">踩中的要点：</span>
                    {result.hit_keywords.map((k) => (
                      <span key={k} className="inline-block mr-1 mb-1 px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700">
                        {k}
                      </span>
                    ))}
                  </div>
                )}
                {result.missed_keywords.length > 0 && (
                  <div className="leading-relaxed">
                    <span className="text-amber-700">你漏了什么：</span>
                    {result.missed_keywords.map((k) => (
                      <span key={k} className="inline-block mr-1 mb-1 px-1.5 py-0.5 rounded bg-amber-100 text-amber-700">
                        {k}
                      </span>
                    ))}
                  </div>
                )}

                {result.passed && result.next_code && (
                  <Button type="primary" block onClick={() => void loadDetail(result.next_code as string)}>
                    进入下一题 →
                  </Button>
                )}
                {result.passed && !result.next_code && (
                  <div className="text-emerald-700 text-center">
                    🎉 这个分类的 8 道题都过了，换个分类继续。
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
