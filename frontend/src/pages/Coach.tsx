import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { App, Button, Input, Spin, Tag } from 'antd'
import { ArrowLeftOutlined, ReloadOutlined, SendOutlined } from '@ant-design/icons'
import { api, ApiError } from '../api/client'
import type { CoachAnswer, CoachQuestion } from '../types'

/**
 * 选择题教练。
 *
 * 交互只有一条主线：**底部一个输入框 → 输入知识点 → 一直出题**。
 * 不分模块、不预设路线，难度靠「连对 2 题升一档、答错降一档」自动调。
 *
 * 几个刻意的设计：
 * - 底部输入框常驻：随时能换知识点，不用退出去重进。
 * - 答错的反馈先给「你以为」，再给解析。顺序反了就没人在乎前半句。
 * - 反向题（问「哪个错误」）答完后逐项标 ✅/❌，否则学生记住的是「我选错了」，
 *   而不是「哪三句是对的」。
 * - 出题要 3~5 秒，这期间必须给出明确的等待感，否则会被当成卡死。
 */

const LEVEL_TAG: Record<number, { t: string; c: string }> = {
  1: { t: '基础', c: 'default' },
  3: { t: '中级', c: 'blue' },
  4: { t: '进阶', c: 'purple' },
}

const PRESETS = ['Python 列表切片', 'Python 闭包', 'MySQL 索引', 'HTTP 状态码']

export default function Coach() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const [topic, setTopic] = useState('')
  const [sid, setSid] = useState<number | null>(null)
  const [cur, setCur] = useState<string>('')
  const [q, setQ] = useState<CoachQuestion | null>(null)
  const [res, setRes] = useState<CoachAnswer | null>(null)
  const [busy, setBusy] = useState(false)
  const [picked, setPicked] = useState<number | null>(null)
  const [stat, setStat] = useState({ total: 0, right: 0 })
  const bottom = useRef<HTMLDivElement>(null)

  // 换题后把视野拉回题目顶部，否则在手机上还停在上一题的解析里
  useEffect(() => {
    bottom.current?.scrollIntoView({ block: 'start', behavior: 'smooth' })
  }, [q?.attempt_id])

  const next = async (sessionId: number) => {
    setBusy(true)
    setRes(null)
    setPicked(null)
    try {
      const r = await api.post<CoachQuestion>(
        `/api/coach/next?session_id=${sessionId}`)
      setQ(r)
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : '出题失败，稍后重试'
      message.error(msg)
      setQ(null)
    } finally {
      setBusy(false)
    }
  }

  const start = async (text?: string) => {
    const t = (text ?? topic).trim()
    if (!t) {
      message.warning('先输入一个知识点')
      return
    }
    setBusy(true)
    setQ(null)
    setRes(null)
    setStat({ total: 0, right: 0 })
    try {
      const s = await api.post<{ session_id: number; topic: string }>(
        '/api/coach/start', { topic: t })
      setSid(s.session_id)
      setCur(s.topic)
      setTopic('')
      await next(s.session_id)
    } catch (e) {
      message.error((e as Error).message)
      setBusy(false)
    }
  }

  const pick = async (i: number) => {
    if (!q || res || busy) return
    setPicked(i)
    try {
      const a = await api.post<CoachAnswer>(
        '/api/coach/answer', { attempt_id: q.attempt_id, chosen: i })
      setRes(a)
      setStat({ total: a.total, right: a.right })
      if (a.level_changed === 'up') message.success('连对 2 题，难度升到下一档')
    } catch (e) {
      message.error((e as Error).message)
      setPicked(null)
    }
  }

  const optClass = (i: number) => {
    const base =
      'w-full text-left px-4 py-3 rounded-xl border transition-colors flex gap-3 items-start '
    if (!res) {
      return base +
        (picked === i
          ? 'border-indigo-400 bg-indigo-50 '
          : 'border-slate-200 bg-white hover:border-indigo-300 hover:bg-indigo-50/40 ')
    }
    if (i === res.answer_index) return base + 'border-emerald-400 bg-emerald-50 '
    if (i === picked) return base + 'border-rose-400 bg-rose-50 '
    return base + 'border-slate-200 bg-white opacity-60 '
  }

  // 模型有时把同一段代码既写进题干、又填进 code 字段，两处都渲染就是重复。
  // 题干里能对上这段代码（前 16 个非空白字符）就不再画代码块。
  const codeInStem = !!q?.code &&
    q.stem.replace(/\s/g, '').includes(q.code.replace(/\s/g, '').slice(0, 16))
  const showCode = !!q?.code && !codeInStem

  return (
    <div className="flex flex-col h-[calc(100dvh-136px)] md:h-[calc(100dvh-96px)]">
      {/* 顶栏：知识点 + 正确率。没有它，连练十几题后完全不知道自己在练什么 */}      <div className="shrink-0 flex items-center gap-2 pb-3">
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/')}
          className="shrink-0"
        />
        <div className="min-w-0 flex-1">
          <div className="truncate text-[15px] font-semibold text-slate-800">
            {cur || '选择题教练'}
          </div>
          <div className="text-[11.5px] text-slate-500">
            {cur
              ? `第 ${stat.total + (res ? 0 : 1)} 题 · 答对 ${stat.right}/${stat.total}`
              : '输入一个知识点，一题一题练到会'}
          </div>
        </div>
        {stat.total > 0 && (
          <Tag color="blue" className="shrink-0">
            {Math.round((stat.right / stat.total) * 100)}%
          </Tag>
        )}
      </div>

      {/* 题区 */}
      <div className="flex-1 overflow-y-auto min-h-0 pr-1">
        <div ref={bottom} />

        {!q && !busy && (
          <div className="pt-6 md:pt-16">
            <div className="text-center text-slate-500 text-[13px] mb-5">
              想练什么？说一个知识点就行，比如
            </div>
            <div className="flex flex-wrap gap-2 justify-center">
              {PRESETS.map((p) => (
                <button
                  key={p}
                  onClick={() => void start(p)}
                  className="px-3 py-1.5 rounded-full text-[12.5px] border border-indigo-200
                             bg-white text-indigo-700 hover:bg-indigo-50"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}

        {busy && (
          <div className="flex flex-col items-center gap-3 pt-16 text-slate-500">
            <Spin />
            <div className="text-[12.5px]">正在出题…</div>
          </div>
        )}

        {q && !busy && (
          <div className="pb-4">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <Tag color={LEVEL_TAG[q.level]?.c}>
                {LEVEL_TAG[q.level]?.t || '基础'}
              </Tag>
              {q.reverse && <Tag color="orange">反向题</Tag>}
              <span className="text-[11.5px] text-slate-400">
                {q.point}
              </span>
              {q.verified === true && (
                <span className="text-[11px] text-emerald-600">已执行校验</span>
              )}
              {q.fallback && (
                <span className="text-[11px] text-amber-600">题库题</span>
              )}
            </div>

            {q.reverse && (
              <div className="mb-2 text-[12.5px] text-amber-700 bg-amber-50
                              border border-amber-200 rounded-lg px-3 py-2">
                先逐项标 ✅/❌，再选那项 ❌ 的。
              </div>
            )}

            <div className="text-[15px] leading-relaxed text-slate-800 whitespace-pre-wrap">
              {q.stem}
            </div>

            {showCode && q.code && (
              <pre className="mt-3 mb-1 p-3 rounded-xl bg-slate-900 text-slate-100
                              text-[12.5px] leading-relaxed overflow-x-auto">
                <code>{q.code}</code>
              </pre>
            )}

            <div className="flex flex-col gap-2 mt-4">
              {q.options.map((o, i) => (
                <button
                  key={i}
                  data-coach-opt={i}
                  onClick={() => void pick(i)}
                  disabled={!!res}
                  className={optClass(i)}
                >
                  <span className="shrink-0 w-5 h-5 rounded-md bg-slate-100 text-slate-600
                                   text-[11.5px] font-medium flex items-center justify-center mt-[2px]">
                    {String.fromCharCode(65 + i)}
                  </span>
                  <span className="text-[13.5px] text-slate-700 whitespace-pre-wrap break-words">
                    {o}
                  </span>
                  {res && i === res.answer_index && (
                    <span className="ml-auto shrink-0 text-emerald-600 text-[12px]">✓</span>
                  )}
                  {res && i === picked && i !== res.answer_index && (
                    <span className="ml-auto shrink-0 text-rose-600 text-[12px]">✗</span>
                  )}
                </button>
              ))}
            </div>

            {res && (
              <div data-coach-result="1" className="mt-4">
                {/* 答错先给「你以为」，再给解析。顺序反了没人会在乎前半句 */}
                {!res.correct && (
                  <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3">
                    <div className="text-[13px] font-medium text-rose-700">
                      你选的是 {String.fromCharCode(65 + (picked ?? 0))}，正确答案是{' '}
                      {String.fromCharCode(65 + res.answer_index)}
                    </div>
                    {res.belief && (
                      <div className="mt-1 text-[12.5px] text-rose-600">
                        这道项对应的误解：{res.belief}
                      </div>
                    )}
                  </div>
                )}
                {res.correct && (
                  <div className="rounded-xl border border-emerald-200 bg-emerald-50
                                  px-4 py-3 text-[13px] font-medium text-emerald-700">
                    正确，答案是 {String.fromCharCode(65 + res.answer_index)}
                    {res.streak === 1 && res.level < 4 ? '（再对一题升难度）' : ''}
                  </div>
                )}

                {/* 反向题逐项对错：不复盘这一栏，学生只记住「我选错了」 */}
                {res.fact_check && (
                  <div className="mt-3 rounded-xl border border-slate-200 bg-white px-4 py-3">
                    <div className="text-[12px] text-slate-500 mb-1.5">逐项核对</div>
                    <div className="flex flex-col gap-1">
                      {res.fact_check.map((ok, i) => (
                        <div key={i} className="text-[12.5px] text-slate-700">
                          <span className={ok ? 'text-emerald-600' : 'text-rose-600'}>
                            {ok ? '✅ 正确说法' : '❌ 错误说法'}
                          </span>
                          <span className="text-slate-400 ml-1">
                            {String.fromCharCode(65 + i)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="mt-3 rounded-xl border border-slate-200 bg-white px-4 py-3">
                  <div className="text-[12px] text-slate-500 mb-1">解析</div>
                  <div className="text-[13px] text-slate-700 leading-relaxed whitespace-pre-wrap">
                    {res.explanation || '（暂无解析）'}
                  </div>
                </div>

                <Button
                  type="primary"
                  block
                  size="large"
                  icon={<ReloadOutlined />}
                  className="mt-3"
                  loading={busy}
                  onClick={() => sid && void next(sid)}
                >
                  下一题
                </Button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 底部输入框：任何时候都能换知识点 */}
      <div className="shrink-0 pt-3">
        <div className="flex gap-2">
          <Input
            size="large"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            onPressEnter={() => void start()}
            placeholder={cur ? '换个知识点，比如 Python 装饰器' : '输入知识点，比如 Python 列表切片'}
            maxLength={60}
            allowClear
          />
          <Button
            type="primary"
            size="large"
            icon={<SendOutlined />}
            loading={busy}
            onClick={() => void start()}
          >
            {cur ? '换' : '开始'}
          </Button>
        </div>
      </div>
    </div>
  )
}
