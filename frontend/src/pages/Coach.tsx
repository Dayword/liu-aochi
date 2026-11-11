import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { App, Button, Input, Spin, Tag } from 'antd'
import { ArrowLeftOutlined, DownOutlined, ReloadOutlined, SendOutlined } from '@ant-design/icons'
import { api, ApiError } from '../api/client'
import type { CoachAnswer, CoachQuestion } from '../types'

/**
 * 选择题教练 —— 一页到底的消息流。
 *
 * 交互只有一条主线：**底部一个输入框 → 输入知识点 → 一题一题往下接**。
 * 没有「下一题」按钮：判完分就把新题追加到流末尾，答过的题和解析留在原地，
 * 往上滚能回看整场练习。换知识点也只是往下接一条分隔 + 新题，不清屏。
 *
 * 几个刻意的设计：
 * - 底部输入框常驻：随时能换知识点，不用退出去重进。
 * - 答错的反馈先给「你以为」，再给解析。顺序反了就没人在乎前半句。
 * - 反向题（问「哪个错误」）答完后逐项标 ✅/❌，否则学生记住的是「我选错了」，
 *   而不是「哪三句是对的」。
 * - 出题要 3~5 秒，这期间在流末尾给「正在出下一题…」，否则会被当成卡死。
 * - 自动追加只在用户本来就贴着底部时拉滚动条；正在回看历史时只给一个
 *   「新题 ↓」浮标，不把人硬拽回来。
 */

const LEVEL_TAG: Record<number, { t: string; c: string }> = {
  1: { t: '基础', c: 'default' },
  3: { t: '中级', c: 'blue' },
  4: { t: '进阶', c: 'purple' },
}

const PRESETS = ['Python 列表切片', 'Python 闭包', 'MySQL 索引', 'HTTP 状态码']

type Card = {
  sid: number
  q: CoachQuestion
  picked: number | null
  res: CoachAnswer | null
}

type Entry =
  | { kind: 'divider'; key: string; text: string }
  | { kind: 'card'; key: number; num: number; card: Card }

function QuestionCard({ num, card, currentSid, onPick }: {
  num: number
  card: Card
  currentSid: number | null
  onPick: (i: number) => void
}) {
  const { q, picked, res } = card
  // 只有「当前会话里还没提交过的那张卡」能点；历史题只读
  const active = card.sid === currentSid && !res && picked === null

  // 模型有时把同一段代码既写进题干、又填进 code 字段，两处都渲染就是重复。
  // 题干里能对上这段代码（前 16 个非空白字符）就不再画代码块。
  const codeInStem = !!q.code &&
    q.stem.replace(/\s/g, '').includes(q.code.replace(/\s/g, '').slice(0, 16))
  const showCode = !!q.code && !codeInStem

  const optClass = (i: number) => {
    const base =
      'w-full text-left px-4 py-3 rounded-xl border transition-colors flex gap-3 items-start '
    if (!res) {
      if (picked === i) return base + 'border-indigo-400 bg-indigo-50 '
      if (!active) return base + 'border-slate-200 bg-white opacity-60 '
      return base +
        'border-slate-200 bg-white hover:border-indigo-300 hover:bg-indigo-50/40 '
    }
    if (i === res.answer_index) return base + 'border-emerald-400 bg-emerald-50 '
    if (i === picked) return base + 'border-rose-400 bg-rose-50 '
    return base + 'border-slate-200 bg-white opacity-60 '
  }

  return (
    <div
      data-coach-card={num}
      className="rounded-2xl border border-slate-200 bg-white px-4 py-4 mb-4 shadow-sm"
    >
      <div className="flex items-center gap-2 mb-2 flex-wrap">
        <span className="text-[11.5px] font-medium text-slate-400">#{num}</span>
        <Tag color={LEVEL_TAG[q.level]?.c}>
          {LEVEL_TAG[q.level]?.t || '基础'}
        </Tag>
        {q.reverse && <Tag color="orange">反向题</Tag>}
        <span className="text-[11.5px] text-slate-400">{q.point}</span>
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

      <div data-coach-stem="1"
           className="text-[15px] leading-relaxed text-slate-800 whitespace-pre-wrap">
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
            onClick={() => onPick(i)}
            disabled={!active}
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
        <>
          {/* 我的作答单独成一条右对齐气泡，整页读起来才是对话流而不是表单 */}
          <div className="flex justify-end mt-3">
            <div className={`rounded-2xl border px-3.5 py-2 text-[12.5px] ${
              res.correct
                ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                : 'bg-rose-50 border-rose-200 text-rose-700'
            }`}>
              我选 {String.fromCharCode(65 + (picked ?? 0))}
              <span className="ml-1 opacity-70">
                {res.correct ? '· 答对' : '· 答错'}
              </span>
            </div>
          </div>

          <div data-coach-result="1" className="mt-3">
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
          </div>
        </>
      )}
    </div>
  )
}

export default function Coach() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const [topic, setTopic] = useState('')
  const [sid, setSid] = useState<number | null>(null)
  const sidRef = useRef<number | null>(null)
  const [cur, setCur] = useState('')
  const [items, setItems] = useState<Entry[]>([])
  const [busy, setBusy] = useState(false)
  const [appending, setAppending] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [stat, setStat] = useState({ total: 0, right: 0 })
  const [sessionTotal, setSessionTotal] = useState(0)
  const [hasNew, setHasNew] = useState(false)
  const scroller = useRef<HTMLDivElement>(null)
  const stick = useRef(true)
  const seqRef = useRef(0)

  // 必须在往流里追加内容「之前」记下是否贴底：追加后 scrollHeight 变高，
  // 再用 scrollHeight - scrollTop 判断，本来贴底的人也会被误判成在回看。
  const markStick = () => {
    const el = scroller.current
    stick.current = !el || el.scrollHeight - el.scrollTop - el.clientHeight < 180
  }

  /** 流里任何一次改动都要先采样，否则「判分结果出现」这类变更
   *  会沿用上一次的贴底状态，把正在回看的人硬拽回底部。 */
  const mutate = (fn: (prev: Entry[]) => Entry[], force = false) => {
    if (!force) markStick()
    setItems(fn)
  }

  useEffect(() => {
    const el = scroller.current
    if (!el) return
    if (!stick.current) {
      setHasNew(true)
      return
    }
    // 瞬时跟随：用 smooth 的话，动画中途再采样会被判成「用户已滚走」
    el.scrollTop = el.scrollHeight
    setHasNew(false)
  }, [items, appending, busy, err])

  const toBottom = () => {
    const el = scroller.current
    el?.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
    setHasNew(false)
  }

  const onScroll = () => {
    const el = scroller.current
    if (el && el.scrollHeight - el.scrollTop - el.clientHeight < 60) setHasNew(false)
  }

  const appendQuestion = (sessionId: number, r: CoachQuestion, force = false) => {
    // 出题这 3~5 秒里用户可能换了知识点，旧 session 的题不能串进新话题
    if (sidRef.current !== sessionId) return
    const num = seqRef.current + 1
    mutate(prev => [...prev, {
      kind: 'card', key: r.attempt_id, num,
      card: { sid: sessionId, q: r, picked: null, res: null },
    }], force)
    seqRef.current = num
    setSessionTotal(num)
    setErr(null)
  }

  /** 判完分自动接下一题。失败不静默：流末尾留一条可重试的提示。 */
  const next = async (sessionId: number) => {
    if (sidRef.current !== sessionId) return
    markStick()
    setAppending(true)
    setErr(null)
    try {
      const r = await api.post<CoachQuestion>(
        `/api/coach/next?session_id=${sessionId}`)
      appendQuestion(sessionId, r)
    } catch (e) {
      if (sidRef.current === sessionId) {
        setErr(e instanceof ApiError ? e.message : '出题失败，稍后重试')
      }
    } finally {
      if (sidRef.current === sessionId) setAppending(false)
    }
  }

  const start = async (text?: string) => {
    const t = (text ?? topic).trim()
    if (!t) {
      message.warning('先输入一个知识点')
      return
    }
    if (busy) return
    setBusy(true)
    // 换话题时上一次「自动接下一题」可能还在飞：它的响应会被 sidRef 丢掉，
    // finally 也不会再清 appending，这里必须自己收尾，否则转圈永不消失。
    setAppending(false)
    setErr(null)
    stick.current = true            // 主动发起新话题，一定拉到最新
    try {
      const s = await api.post<{ session_id: number; topic: string }>(
        '/api/coach/start', { topic: t })
      sidRef.current = s.session_id
      setSid(s.session_id)
      setCur(s.topic)
      setTopic('')
      setStat({ total: 0, right: 0 })
      setSessionTotal(0)
      seqRef.current = 0
      markStick()
      mutate(prev => [...prev, {
        kind: 'divider',
        key: `d-${s.session_id}-${Date.now()}`,
        text: prev.some(x => x.kind === 'card')
          ? `换知识点 · ${s.topic}` : `开始练习 · ${s.topic}`,
      }], true)
      const r = await api.post<CoachQuestion>(
        `/api/coach/next?session_id=${s.session_id}`)
      appendQuestion(s.session_id, r, true)
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : '出题失败，稍后重试')
      message.error(e instanceof Error ? e.message : '出题失败')
    } finally {
      setBusy(false)
    }
  }

  const pick = async (key: number, i: number) => {
    const target = items.find(x => x.kind === 'card' && x.key === key)
    if (!target || target.kind !== 'card') return
    const { card } = target
    if (card.res || card.picked !== null) return

    // picked 先落下去：既是「提交中」的视觉，也防止连点两次判分（后端会 409）
    const update = (c: Partial<Card>) =>
      mutate(prev => prev.map(x => x.kind === 'card' && x.key === key
        ? { ...x, card: { ...x.card, ...c } } : x))
    update({ picked: i })
    try {
      const a = await api.post<CoachAnswer>(
        '/api/coach/answer', { attempt_id: card.q.attempt_id, chosen: i })
      update({ res: a })
      setStat({ total: a.total, right: a.right })
      if (a.level_changed === 'up') message.success('连对 2 题，难度升到下一档')
      // 没有「下一题」按钮：判完分直接把新题接到流末尾
      if (sidRef.current === card.sid) void next(card.sid)
    } catch (e) {
      update({ picked: null })
      message.error((e as Error).message)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100dvh-136px)] md:h-[calc(100dvh-96px)]">
      {/* 顶栏：知识点 + 正确率。没有它，连练十几题后完全不知道自己在练什么 */}
      <div className="shrink-0 flex items-center gap-2 pb-3">
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
              ? `第 ${sessionTotal} 题 · 答对 ${stat.right}/${stat.total} · 往下划可回看`
              : '输入一个知识点，一题一题练到会'}
          </div>
        </div>
        {stat.total > 0 && (
          <Tag color="blue" className="shrink-0">
            {Math.round((stat.right / stat.total) * 100)}%
          </Tag>
        )}
      </div>

      {/* 题区：一条不断往下长的流，整个页面只有这一处滚动 */}
      <div className="relative flex-1 min-h-0">
        <div
          ref={scroller}
          onScroll={onScroll}
          className="h-full overflow-y-auto min-h-0 pr-1"
        >
          {items.length === 0 && !busy && (
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

          {items.map(e => e.kind === 'divider' ? (
            <div key={e.key}
                 className="flex items-center gap-3 py-3 text-[11.5px] text-slate-400">
              <span className="flex-1 border-t border-dashed border-slate-200" />
              <span className="shrink-0">{e.text}</span>
              <span className="flex-1 border-t border-dashed border-slate-200" />
            </div>
          ) : (
            <QuestionCard
              key={e.key}
              num={e.num}
              card={e.card}
              currentSid={sid}
              onPick={(i) => void pick(e.key, i)}
            />
          ))}

          {(busy || appending) && (
            <div className="flex items-center justify-center gap-2 py-6
                            text-slate-400 text-[12.5px]">
              <Spin size="small" />
              <span>{items.length ? '正在出下一题…' : '正在出题…'}</span>
            </div>
          )}

          {err && !busy && !appending && (
            <div className="mb-4 flex items-center gap-3 rounded-xl border
                            border-amber-200 bg-amber-50 px-4 py-3
                            text-[12.5px] text-amber-700">
              <span className="flex-1">{err}</span>
              <Button size="small" icon={<ReloadOutlined />}
                      onClick={() => sidRef.current && void next(sidRef.current)}>
                重试
              </Button>
            </div>
          )}
        </div>

        {/* 回看历史时不硬拽滚动条，只给一个跳回最新的入口 */}
        {hasNew && (
          <button
            onClick={toBottom}
            className="absolute bottom-3 right-4 rounded-full bg-indigo-600 text-white
                       text-[12px] px-3 py-1.5 shadow-lg flex items-center gap-1"
          >
            新题 <DownOutlined />
          </button>
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
