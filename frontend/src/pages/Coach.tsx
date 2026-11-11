import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { App, Button, Input, Spin, Tag } from 'antd'
import { ArrowLeftOutlined, CloseOutlined, DownOutlined,
         ReloadOutlined, SendOutlined, UnorderedListOutlined } from '@ant-design/icons'
import { api, ApiError } from '../api/client'
import type { CoachAnswer, CoachPlan, CoachQuestion, CoachSummary } from '../types'

/**
 * 选择题教练 —— 一页到底的消息流。
 *
 * 一轮练习分两段，**不直接给题目**：
 * 1. 输入知识点后先让后端判断「这个范围还能不能再分」。范围大就拆成由易到难
 *    的若干知识点，规划卡片先落到流里；范围小就说明不用拆。
 * 2. 展示完才出第一题。每个知识点内题目由易到难，连对 3 题过关，
 *    最后一个过关就插总结卡片并停止出题。
 *
 * 知识点规划随时可看：题区右上角有一个常驻按钮（不随流滚动消失），
 * 显示「规划 已过/总数」；点开后规划浮层从右上角向左下角、由慢到快展开
 * （0.3s），再点一下或点浮层右上角的 × 收起。浮层跟随最新一轮规划。
 *
 * 答过的题和解析留在原地，往上滚能回看整场练习；换知识点只是往下接新的一段，
 * 不清屏。自动跟随只在用户本来就贴着底部时生效，回看历史时只给「新题 ↓」浮标。
 */

const LEVEL_TAG: Record<number, { t: string; c: string }> = {
  1: { t: '基础', c: 'default' },
  3: { t: '中级', c: 'blue' },
  4: { t: '进阶', c: 'purple' },
}

const PRESETS = ['Python', 'Python 列表切片', 'MySQL 索引', 'HTTP 状态码']
const PASS_STREAK = 3

/** 同一毫秒内可能连插两条（过关 + 总结），给个不会撞的 key */
let _seq = 0
function s_key(): string {
  _seq += 1
  return `${Date.now()}-${_seq}`
}

type Card = {
  sid: number
  q: CoachQuestion
  picked: number | null
  res: CoachAnswer | null
}

type Progress = { pointIndex: number; streak: number; finished: boolean }

type Head = Progress & { pointsTotal: number; pointName: string }

type Entry =
  | { kind: 'divider'; key: string; text: string }
  | { kind: 'plan'; key: string; plan: CoachPlan; progress: Progress }
  | { kind: 'passed'; key: string; from: string; to: string }
  | { kind: 'summary'; key: string; data: CoachSummary }
  | { kind: 'card'; key: number; num: number; card: Card }

/** 规划主体：说明 + 由易到难的知识点清单（含实时进度）。
 *  流内规划卡和右上角抽屉浮层共用这一块。 */
function PlanList({ plan, progress }: { plan: CoachPlan; progress: Progress }) {
  const pts = plan.points.length ? plan.points : [plan.topic]
  return (
    <>
      <div className="text-[13px] leading-relaxed text-slate-600 mb-2.5">
        {plan.note}
      </div>
      <div className="flex flex-col gap-1.5">
        {pts.map((p, i) => {
          const done = i < progress.pointIndex || progress.finished
          const cur = i === progress.pointIndex && !progress.finished
          return (
            <div
              key={i}
              className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-[12.5px] ${
                done
                  ? 'border-emerald-200 bg-white text-emerald-700'
                  : cur
                    ? 'border-indigo-300 bg-white text-indigo-700 font-medium'
                    : 'border-transparent text-slate-500'
              }`}
            >
              <span className="w-5 shrink-0 text-[11px] opacity-70">
                {String(i + 1).padStart(2, '0')}
              </span>
              <span className="flex-1 truncate">{p}</span>
              {done && <span className="shrink-0 text-[11px]">✅ 已过关</span>}
              {cur && (
                <span className="shrink-0 text-[11px]">
                  ▶ 连对 {progress.streak}/{PASS_STREAK}
                </span>
              )}
              {!done && !cur && (
                <span className="shrink-0 text-[11px] text-slate-400">待练</span>
              )}
            </div>
          )
        })}
      </div>
      <div className="mt-2.5 text-[11px] text-slate-400">
        由易到难 · 每个知识点连对 {PASS_STREAK} 题进入下一个，全部过关即结束
      </div>
    </>
  )
}

function PlanCard({ plan, progress }: { plan: CoachPlan; progress: Progress }) {
  const pts = plan.points.length ? plan.points : [plan.topic]
  return (
    <div
      data-coach-plan="1"
      data-coach-points={pts.length}
      className="mb-4 rounded-2xl border border-indigo-200 bg-indigo-50 px-4 py-4 shadow-sm"
    >
      <div className="flex items-center gap-2 mb-2 flex-wrap">
        <span className="text-[12px] font-medium text-indigo-700">范围还能再分吗？</span>
        <Tag color={plan.need_split ? 'blue' : 'default'}>
          {plan.need_split ? `拆成 ${pts.length} 个知识点` : '不用再分'}
        </Tag>
      </div>
      <PlanList plan={plan} progress={progress} />
    </div>
  )
}

/** 右上角常驻规划入口：按钮钉在题区右上角（absolute 于滚动容器之外，
 *  往下刷多少题它都不动），点开后规划浮层从右上角向左下角、
 *  由慢到快展开（0.3s，ca-drawer-unfold）——进度实时。 */
function PlanDock({ entry, open, onToggle }: {
  entry: { plan: CoachPlan; progress: Progress }
  open: boolean
  onToggle: () => void
}) {
  const { plan, progress } = entry
  const pts = plan.points.length ? plan.points : [plan.topic]
  const doneCount = progress.finished ? pts.length : progress.pointIndex
  return (
    <>
      <button
        data-coach-dock="1"
        aria-expanded={open}
        onClick={onToggle}
        className={`absolute right-3 top-2 z-40 inline-flex items-center gap-1.5 rounded-full
                    border px-3 py-1.5 text-[12px] shadow-md transition-colors ${
                      open
                        ? 'border-indigo-600 bg-indigo-600 text-white'
                        : 'border-indigo-200 bg-white/95 text-indigo-700 hover:bg-indigo-50'
                    }`}
      >
        <UnorderedListOutlined className="text-[11px]" />
        <span>规划 {doneCount}/{pts.length}</span>
        {open
          ? <CloseOutlined className="text-[10px]" />
          : <DownOutlined className="text-[10px]" />}
      </button>

      {open && (
        <div
          data-coach-drawer="1"
          className="ca-drawer-unfold absolute right-3 top-11 z-50 w-[300px] max-w-[85%]
                     max-h-[70%] overflow-y-auto rounded-2xl border border-indigo-200
                     bg-white px-4 py-4 shadow-xl"
        >
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[12px] font-medium text-indigo-700">知识点规划</span>
            <Tag color={plan.need_split ? 'blue' : 'default'}>
              {plan.need_split ? `拆成 ${pts.length} 个` : '不用再分'}
            </Tag>
            <button
              data-coach-drawer-close="1"
              aria-label="收起规划"
              onClick={onToggle}
              className="ml-auto inline-flex h-6 w-6 items-center justify-center rounded-md
                         border border-slate-200 text-[11px] text-slate-500
                         hover:border-slate-300 hover:text-slate-700"
            >
              <CloseOutlined />
            </button>
          </div>
          <PlanList plan={plan} progress={progress} />
        </div>
      )}
    </>
  )
}

function SummaryCard({ data }: { data: CoachSummary }) {
  const pct = data.total ? Math.round((data.right / data.total) * 100) : 0
  return (
    <div
      data-coach-summary="1"
      className="mb-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-4 shadow-sm"
    >
      <div className="text-[15px] font-semibold text-emerald-700 mb-1">
        本轮全部过关
      </div>
      <div className="text-[12.5px] text-slate-600 mb-3">
        「{data.topic}」· {data.points.length} 个知识点 · 共 {data.total} 题，
        答对 {data.right} 题（{pct}%）
      </div>
      <div className="flex flex-col gap-1">
        {data.points.map((p, i) => (
          <div key={i} className="flex items-center gap-2 text-[12.5px] text-slate-700">
            <span className="text-emerald-600">✅</span>
            <span className="flex-1 truncate">{p.name}</span>
            <span className="shrink-0 text-slate-500">{p.right}/{p.total}</span>
          </div>
        ))}
      </div>
      <div className="mt-3 text-[11.5px] text-slate-500">
        想继续？在下面输入一个新知识点就能再来一轮。
      </div>
    </div>
  )
}

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
      data-coach-attempt={q.attempt_id}
      className="rounded-2xl border border-slate-200 bg-white px-4 py-4 mb-4 shadow-sm"
    >
      <div className="flex items-center gap-2 mb-2 flex-wrap">
        <span className="text-[11.5px] font-medium text-slate-400">#{num}</span>
        <Tag color={LEVEL_TAG[q.level]?.c}>
          {LEVEL_TAG[q.level]?.t || '基础'}
        </Tag>
        {q.reverse && <Tag color="orange">反向题</Tag>}
        <span className="text-[11.5px] text-slate-500">
          知识点 {q.point_index + 1}/{q.points_total} · {q.point_name}
        </span>
        <span className="text-[11px] text-slate-400">本点第 {q.q_in_point} 题</span>
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
          反向题：四项里只有一项说法是错的，把它找出来。
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
                    选这项的人以为：{res.belief}
                  </div>
                )}
              </div>
            )}
            {res.correct && (
              <div className="rounded-xl border border-emerald-200 bg-emerald-50
                              px-4 py-3 text-[13px] font-medium text-emerald-700">
                正确，答案是 {String.fromCharCode(65 + res.answer_index)}
                {!res.finished && !res.passed && res.streak < PASS_STREAK
                  ? `（再连对 ${PASS_STREAK - res.streak} 题过关）` : ''}
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
  const [head, setHead] = useState<Head>({
    pointIndex: 0, pointsTotal: 1, pointName: '', streak: 0, finished: false,
  })
  const [hasNew, setHasNew] = useState(false)
  const [planOpen, setPlanOpen] = useState(false)
  const scroller = useRef<HTMLDivElement>(null)
  const stick = useRef(true)
  const seqRef = useRef(0)
  const planKeyRef = useRef('')

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

  // 最新一条规划（换知识点后跟随新的）：悬浮按钮和抽屉浮层的数据源，进度实时
  const lastPlan = useMemo(() => {
    for (let i = items.length - 1; i >= 0; i--) {
      const e = items[i]
      if (e.kind === 'plan') return e
    }
    return null
  }, [items])

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

  /** 出下一题。失败不静默：流末尾留一条可重试的提示。 */
  const fetchNext = async (sessionId: number, force = false) => {
    if (sidRef.current !== sessionId) return
    if (!force) markStick()
    setAppending(true)
    setErr(null)
    try {
      const r = await api.post<CoachQuestion>(
        `/api/coach/next?session_id=${sessionId}`)
      appendQuestion(sessionId, r, force)
    } catch (e) {
      if (sidRef.current === sessionId) {
        setErr(e instanceof ApiError ? e.message : '出题失败，稍后重试')
      }
    } finally {
      if (sidRef.current === sessionId) setAppending(false)
    }
  }

  /** 开始一轮：先规划（不出题），规划卡片落到流里之后才请求第一题。 */
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
    setPlanOpen(false)
    stick.current = true            // 主动发起新话题，一定拉到最新

    let s: CoachPlan
    try {
      s = await api.post<CoachPlan>('/api/coach/start', { topic: t })
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : '范围判断失败，稍后重试')
      message.error(e instanceof Error ? e.message : '范围判断失败')
      setBusy(false)
      return
    }

    sidRef.current = s.session_id
    setSid(s.session_id)
    setCur(s.topic)
    setTopic('')
    setStat({ total: 0, right: 0 })
    setSessionTotal(0)
    seqRef.current = 0
    const pts = s.points.length ? s.points : [s.topic]
    planKeyRef.current = `p-${s.session_id}`
    setHead({ pointIndex: 0, pointsTotal: pts.length,
              pointName: pts[0], streak: 0, finished: false })
    mutate(prev => [...prev,
      {
        kind: 'divider',
        key: `d-${s.session_id}-${Date.now()}`,
        text: prev.some(x => x.kind === 'card')
          ? `换知识点 · ${s.topic}` : `开始练习 · ${s.topic}`,
      },
      {
        kind: 'plan', key: planKeyRef.current, plan: s,
        progress: { pointIndex: 0, streak: 0, finished: false },
      },
    ], true)

    // 规划卡片已经进流、会先渲染出来；从这里才开始出第一题
    setBusy(false)
    await fetchNext(s.session_id, true)
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
      setHead({ pointIndex: a.point_index, pointsTotal: a.points_total,
                pointName: a.point_name, streak: a.streak, finished: a.finished })
      mutate(prev => prev.map(x => x.kind === 'plan' && x.key === planKeyRef.current
        ? { ...x, progress: { pointIndex: a.point_index, streak: a.streak,
                              finished: a.finished } }
        : x))

      if (a.finished) {
        if (a.summary) {
          const sm = a.summary
          mutate(prev => [...prev, { kind: 'summary',
                                    key: `s-${s_key()}`, data: sm }])
        }
        return                       // 全部过关，不再出题
      }
      if (a.passed) {
        const from = card.q.point_name || '上一个知识点'
        const to = a.point_name
        mutate(prev => [...prev, { kind: 'passed',
                                  key: `ps-${s_key()}`, from, to }])
      }
      if (sidRef.current === card.sid) void fetchNext(card.sid)
    } catch (e) {
      update({ picked: null })
      message.error((e as Error).message)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100dvh-136px)] md:h-[calc(100dvh-96px)]">
      {/* 顶栏：知识点 + 闯关进度。连练十几题后没它完全不知道自己在第几关 */}
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
              ? head.finished
                ? `本轮已全部过关 · 答对 ${stat.right}/${stat.total}`
                : `知识点 ${head.pointIndex + 1}/${head.pointsTotal} · 连对 ${head.streak}/${PASS_STREAK} · 答对 ${stat.right}/${stat.total}`
              : '输入一个知识点，先看范围怎么拆，再一题一题练'}
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
                想练什么？范围太大我会先帮你拆开，比如
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

          {items.map(e => {
            switch (e.kind) {
              case 'divider':
                return (
                  <div key={e.key}
                       className="flex items-center gap-3 py-3 text-[11.5px] text-slate-400">
                    <span className="flex-1 border-t border-dashed border-slate-200" />
                    <span className="shrink-0">{e.text}</span>
                    <span className="flex-1 border-t border-dashed border-slate-200" />
                  </div>
                )
              case 'plan':
                return <PlanCard key={e.key} plan={e.plan} progress={e.progress} />
              case 'passed':
                return (
                  <div key={e.key}
                       className="flex items-center gap-3 py-2.5 text-[11.5px]">
                    <span className="flex-1 border-t border-dashed border-emerald-300" />
                    <span className="shrink-0 text-emerald-600">
                      ✅ 已掌握「{e.from}」· 进入「{e.to}」
                    </span>
                    <span className="flex-1 border-t border-dashed border-emerald-300" />
                  </div>
                )
              case 'summary':
                return <SummaryCard key={e.key} data={e.data} />
              case 'card':
                return (
                  <QuestionCard
                    key={e.key}
                    num={e.num}
                    card={e.card}
                    currentSid={sid}
                    onPick={(i) => void pick(e.key, i)}
                  />
                )
            }
          })}

          {(busy || appending) && (
            <div className="flex items-center justify-center gap-2 py-6
                            text-slate-400 text-[12.5px]">
              <Spin size="small" />
              <span>{busy ? '正在判断这个范围还能不能再分…' : '正在出题…'}</span>
            </div>
          )}

          {err && !busy && !appending && (
            <div className="mb-4 flex items-center gap-3 rounded-xl border
                            border-amber-200 bg-amber-50 px-4 py-3
                            text-[12.5px] text-amber-700">
              <span className="flex-1">{err}</span>
              <Button size="small" icon={<ReloadOutlined />}
                      onClick={() => {
                        if (sidRef.current && !head.finished) void fetchNext(sidRef.current)
                      }}>
                重试
              </Button>
            </div>
          )}
        </div>

        {/* 右上角常驻规划入口：钉在题区右上角，不随内部滚动消失 */}
        {lastPlan && (
          <PlanDock
            entry={lastPlan}
            open={planOpen}
            onToggle={() => setPlanOpen(v => !v)}
          />
        )}

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
            placeholder={cur ? '换个知识点，比如 Python 装饰器' : '输入知识点，比如 Python'}
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
