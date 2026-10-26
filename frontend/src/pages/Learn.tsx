import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { App, Button, Drawer, Input, Progress, Spin } from 'antd'
import ReactMarkdown from 'react-markdown'
import { api } from '../api/client'
import LessonVideo from '../components/LessonVideo'
import ProjectField from '../components/ProjectField'
import type {
  LearnPointBrief,
  LearnPointDetail,
  LearnQuizItem,
  LearnQuizResult,
} from '../types'

/** 记住当前停在那一课，从动手任务页返回时不会被「第一门没学完的课」抢走焦点 */
const LEARN_CODE_KEY = 'ca_learn_code'

/** 支持 `反引号` 和代码块的轻量 Markdown 渲染 */
function Md({ children }: { children: string }) {
  return (
    <ReactMarkdown
      components={{
        p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
        pre: ({ children }) => (
          <pre className="bg-[#f4f6fa] border border-slate-200 p-3 rounded-lg overflow-x-auto text-xs my-2 leading-relaxed">
            {children}
          </pre>
        ),
        code: ({ children, className }) =>
          className?.includes('language') ? (
            <code className={className}>{children}</code>
          ) : (
            <code className="bg-indigo-50 text-indigo-700 px-1 py-0.5 rounded text-[0.9em]">{children}</code>
          ),
        strong: ({ children }) => <strong className="text-indigo-700">{children}</strong>,
        ul: ({ children }) => <ul className="list-disc pl-5 space-y-1 my-2">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal pl-5 space-y-1 my-2">{children}</ol>,
      }}
    >
      {children}
    </ReactMarkdown>
  )
}

const QUIZ_LABEL: Record<string, string> = {
  choice: '单选题',
  judge: '判断题',
  blank: '填空题',
  short: '简答题',
  applied: '应用题',
}

function QuizBlock({
  q,
  answer,
  result,
  submitting,
  done,
  onPick,
  onSubmit,
}: {
  q: LearnQuizItem
  answer: string | number | undefined
  result?: LearnQuizResult
  submitting: boolean
  done: boolean
  onPick: (v: string | number) => void
  onSubmit: () => void
}) {
  const objective = q.type === 'choice' || q.type === 'judge' || q.type === 'blank'
  const settled = !!result
  const hasAnswer = answer !== undefined && answer !== ''

  const optionClass = (i: number) => {
    if (!result || q.type !== 'choice') {
      return i === answer
        ? 'border-indigo-400 bg-indigo-100 text-indigo-800'
        : 'border-indigo-200 text-slate-600 hover:border-indigo-400/60'
    }
    const right = result.correct_answer === q.options[i]
    if (right) return 'border-emerald-500 bg-emerald-50 text-emerald-700'
    if (i === answer) return 'border-rose-400 bg-rose-50 text-rose-700'
    return 'border-indigo-200 text-slate-500'
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 space-y-2">
      <div className="flex items-start gap-2 text-sm text-slate-700">
        <span className="shrink-0 text-[10px] px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700 mt-0.5">
          {QUIZ_LABEL[q.type] || '题目'}
        </span>
        <span className="leading-relaxed">{q.stem}</span>
        {done && <span className="ml-auto shrink-0 text-emerald-600 text-xs">✓ 已掌握</span>}
      </div>

      {q.type === 'choice' && (
        <div className="grid gap-1.5">
          {q.options.map((opt, i) => (
            <button
              key={i}
              disabled={settled}
              onClick={() => onPick(i)}
              className={`text-left px-3 py-2 rounded-lg border text-xs transition-all ${optionClass(i)}`}
            >
              <span className="text-slate-500 mr-1">{'ABCDEFGH'[i]}.</span>
              {opt}
            </button>
          ))}
        </div>
      )}

      {q.type === 'judge' && (
        <div className="flex gap-2">
          {[
            { v: 1, label: '对' },
            { v: 0, label: '错' },
          ].map((o) => {
            const picked = answer === o.v
            let cls = picked
              ? 'border-indigo-400 bg-indigo-100 text-indigo-800'
              : 'border-indigo-200 text-slate-600 hover:border-indigo-400/60'
            if (result) {
              const right = (result.correct_answer === '对') === (o.v === 1)
              if (right) cls = 'border-emerald-500 bg-emerald-50 text-emerald-700'
              else if (picked) cls = 'border-rose-400 bg-rose-50 text-rose-700'
              else cls = 'border-indigo-200 text-slate-500'
            }
            return (
              <button
                key={o.v}
                disabled={settled}
                onClick={() => onPick(o.v)}
                className={`px-5 py-1.5 rounded-lg border text-xs transition-all ${cls}`}
              >
                {o.label}
              </button>
            )
          })}
        </div>
      )}

      {q.type === 'blank' && (
        <Input
          size="small"
          value={(answer as string) || ''}
          disabled={settled}
          onChange={(e) => onPick(e.target.value)}
          onPressEnter={onSubmit}
          placeholder={q.hint || '填写答案'}
        />
      )}

      {(q.type === 'short' || q.type === 'applied') && (
        <textarea
          value={(answer as string) || ''}
          disabled={settled}
          onChange={(e) => onPick(e.target.value)}
          rows={q.type === 'applied' ? 4 : 3}
          placeholder={q.hint || '用自己的话写下来，不用和参考答案一字不差'}
          className="w-full bg-[#f4f6fa] border border-indigo-300 rounded-lg p-2 text-xs text-slate-800 outline-none focus:border-indigo-400 resize-y"
        />
      )}

      {!settled && (
        <Button size="small" type="primary" loading={submitting} disabled={!hasAnswer} onClick={onSubmit}>
          {objective ? '提交答案' : '写完看参考答案'}
        </Button>
      )}

      {result && (
        <div className="text-xs space-y-1.5 pt-1 border-t border-slate-200">
          {objective ? (
            <div className={result.correct ? 'text-emerald-600' : 'text-rose-600'}>
              {result.correct ? '✅ 回答正确' : `❌ 回答错误，正确答案是「${result.correct_answer}」`}
            </div>
          ) : (
            <div className="text-sky-700">
              {result.coverage !== null && (
                <span>
                  要点覆盖 {Math.round((result.coverage || 0) * 100)}%
                  {result.missing.length > 0 && (
                    <span className="text-amber-700 ml-2">还可以补充：{result.missing.join('、')}</span>
                  )}
                </span>
              )}
            </div>
          )}
          {result.explanation && (
            <div className="text-slate-600 leading-relaxed">
              <span className="text-indigo-600">解析：</span>
              {result.explanation}
            </div>
          )}
          {result.reference && (
            <div className="text-slate-600 leading-relaxed">
              <span className="text-indigo-600">参考答案：</span>
              <span className="whitespace-pre-wrap">{result.reference}</span>
            </div>
          )}
          <div className="text-slate-500">（不影响通过，自己对照一下就好）</div>
        </div>
      )}
    </div>
  )
}

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

export default function Learn() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const [points, setPoints] = useState<LearnPointBrief[]>([])
  const [subject, setSubject] = useState<string>('')
  const [code, setCode] = useState<string>('')
  const [detail, setDetail] = useState<LearnPointDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [hint, setHint] = useState('')
  const [hintLoading, setHintLoading] = useState(false)
  // 习题：当前作答 / 判分结果 / 正在提交哪一题
  const [answers, setAnswers] = useState<Record<number, string | number>>({})
  const [quizResults, setQuizResults] = useState<Record<number, LearnQuizResult>>({})
  const [submitting, setSubmitting] = useState<number | null>(null)
  const [completed, setCompleted] = useState(false)
  // 进度抽屉：科目 → 阶段 两级展开，默认展开当前所在的那一支
  const [navOpen, setNavOpen] = useState(false)
  const [openSubject, setOpenSubject] = useState<string | null>(null)
  const [openStages, setOpenStages] = useState<Record<string, boolean>>({})
  const [isMobile, setIsMobile] = useState(() => typeof window !== 'undefined' && window.innerWidth < 768)
  const alive = useRef(true)

  useEffect(() => {
    alive.current = true
    return () => {
      alive.current = false
    }
  }, [])

  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  const loadDetail = useCallback(
    async (target: string) => {
      setLoading(true)
      setCode(target)
      setHint('')
      sessionStorage.setItem(LEARN_CODE_KEY, target)
      try {
        const d = await api.get<LearnPointDetail>(`/api/learn/points/${target}`)
        if (!alive.current) return
        setDetail(d)
        setAnswers({})
        setQuizResults({})
        setCompleted(d.status === 'completed')
      } catch (e) {
        message.error((e as Error).message)
      } finally {
        if (alive.current) setLoading(false)
      }
    },
    [message],
  )

  useEffect(() => {
    api
      .get<LearnPointBrief[]>('/api/learn/points')
      .then((list) => {
        if (!alive.current) return
        setPoints(list)
        // 优先回到上次停留的那一课（从动手任务页返回时会用到）；
        // 否则停在第一个还没掌握的（科目之间互不阻塞），全学完了停最后一课。
        const remembered = sessionStorage.getItem(LEARN_CODE_KEY)
        const cur =
          list.find((p) => p.code === remembered && p.status !== 'locked') ||
          list.find((p) => p.status !== 'completed') ||
          list[list.length - 1]
        if (cur) {
          setSubject(cur.subject)
          void loadDetail(cur.code)
        } else setLoading(false)
      })
      .catch((e) => {
        if (alive.current) message.error((e as Error).message)
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const refreshPoints = async () => {
    const list = await api.get<LearnPointBrief[]>('/api/learn/points')
    if (alive.current) setPoints(list)
  }

  /** 切科目时自动跳到该科目第一个还没掌握的知识点 */
  const pickSubject = (s: string) => {
    if (s === subject) return
    setSubject(s)
    const list = points.filter((p) => p.subject === s)
    const cur = list.find((p) => p.status !== 'completed') || list[0]
    if (cur) void loadDetail(cur.code)
  }

  /** 打开抽屉时直接展开当前科目 + 当前阶段，省一次点击 */
  const openNav = () => {
    setOpenSubject(subject)
    if (detail) setOpenStages((prev) => ({ ...prev, [`${subject}|${detail.stage}`]: true }))
    setNavOpen(true)
  }

  const submitQuiz = async (q: LearnQuizItem) => {
    if (!detail) return
    const a = answers[q.index]
    if (a === undefined || a === '') return
    setSubmitting(q.index)
    try {
      const r = await api.post<LearnQuizResult>('/api/learn/quiz', {
        code: detail.code,
        index: q.index,
        answer: a,
      })
      if (!alive.current) return
      setQuizResults((prev) => ({ ...prev, [q.index]: r }))
      setCompleted(r.lesson_completed)
      if (r.lesson_completed) await refreshPoints()
    } catch (e) {
      if (alive.current) message.error((e as Error).message)
    } finally {
      if (alive.current) setSubmitting(null)
    }
  }

  /** 客观题必须全对才算掌握；主观题只要作答过就算过（只给对照，不阻塞） */
  const quizDone = (q: LearnQuizItem) => {
    const s = detail?.quiz_state?.[String(q.index)]
    if (!s) return false
    return q.type === 'choice' || q.type === 'judge' || q.type === 'blank'
      ? s.correct === true
      : s.seen === true
  }

  const askHint = async () => {
    if (!detail) return
    setHintLoading(true)
    try {
      const r = await api.post<{ hint: string }>('/api/learn/hint', { code: detail.code, reason: '' })
      if (alive.current) setHint(r.hint)
    } catch (e) {
      if (alive.current) message.error((e as Error).message)
    } finally {
      if (alive.current) setHintLoading(false)
    }
  }

  const subjects = useMemo(() => [...new Set(points.map((p) => p.subject))], [points])
  const subjectPoints = points.filter((p) => p.subject === subject)
  const done = subjectPoints.filter((p) => p.status === 'completed').length
  const totalDone = points.filter((p) => p.status === 'completed').length

  return (
    <div className="space-y-3">
      {/* 标题行：进度收进抽屉，右上角一个入口 */}
      <div className="flex items-center gap-2">
        <div className="min-w-0">
          <h1 className="text-xl font-bold text-indigo-700 leading-tight">📘 引导式学习</h1>
          <p className="text-[11px] text-slate-500 mt-0.5 hidden sm:block">
            十二个科目独立解锁，互不阻塞；写完点「运行判定」解锁下一课
          </p>
        </div>
        <button
          onClick={openNav}
          className="ml-auto shrink-0 flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl border border-indigo-300 bg-white text-[11px] text-indigo-700 active:bg-indigo-50"
        >
          <span>📚 进度</span>
          <span className="text-indigo-500 font-medium">
            {totalDone}/{points.length || '—'}
          </span>
          <span className="text-[9px] text-slate-400">▾</span>
        </button>
      </div>

      {/* 科目快切：一行横滑，主力导航；完整目录在抽屉里 */}
      <div className="flex gap-1.5 overflow-x-auto no-scrollbar -mx-3 px-3 md:mx-0 md:px-0 md:flex-wrap md:overflow-visible">
        {subjects.map((s) => {
          const all = points.filter((p) => p.subject === s)
          const ok = all.filter((p) => p.status === 'completed').length
          const active = s === subject
          return (
            <button
              key={s}
              onClick={() => pickSubject(s)}
              className={`px-2.5 py-1 rounded-full border text-[11px] whitespace-nowrap shrink-0 transition-all ${
                active
                  ? 'border-indigo-400 bg-indigo-50 text-indigo-800 font-medium'
                  : 'border-slate-200 bg-white text-slate-600'
              }`}
            >
              {s}
              <span className={`ml-1 text-[10px] ${active ? 'text-indigo-500' : 'text-slate-400'}`}>
                {ok}/{all.length}
              </span>
            </button>
          )
        })}
      </div>

      {/* 当前科目进度条：一行搞定，不再占一整块 */}
      <div className="flex items-center gap-2 px-1">
        <span className="text-[11px] text-slate-500 shrink-0">
          {subject || '—'} {done}/{subjectPoints.length}
        </span>
        <Progress
          percent={subjectPoints.length ? Math.round((done / subjectPoints.length) * 100) : 0}
          size="small"
          strokeColor="#6366f1"
          trailColor="#e2e8f0"
          showInfo={false}
          className="flex-1"
        />
        <span className="text-[10px] text-slate-400 shrink-0">本科目上一课通过才解锁下一课</span>
      </div>

      {loading && (
        <div className="game-panel p-10 text-center">
          <Spin />
        </div>
      )}

      {!loading && detail && (
        <div className="game-panel p-3 md:p-5">
          <div className="flex items-baseline gap-2 flex-wrap">
            <h2 className="text-base md:text-lg font-bold text-indigo-700">
              {detail.subject} · 第 {detail.order_no} 课 · {detail.title}
            </h2>
            {detail.status === 'completed' && <span className="text-xs text-emerald-600">✓ 已掌握</span>}
          </div>
          <p className="text-slate-500 text-[11px] mt-1">{detail.summary}</p>

          {/* 讲解视频：分镜脚本由后端构建期生成，缺脚本时组件自己返回 null */}
          {detail.video && detail.video.scenes.length > 0 && (
            <LessonVideo video={detail.video} code={detail.code} />
          )}

          <Section icon="📖" title="定义">
            <Md>{detail.definition}</Md>
          </Section>

          <Section icon="💡" title="通俗理解">
            <Md>{detail.plain}</Md>
          </Section>

          <Section icon="💻" title="例子">
            <pre className="bg-[#f4f6fa] border border-slate-200 p-3 rounded-lg overflow-x-auto text-xs leading-relaxed">
              <code>{detail.example}</code>
            </pre>
            <div className="mt-1.5 text-xs text-slate-500">
              运行结果：
              <pre className="mt-1 text-emerald-600/90 whitespace-pre-wrap font-mono">
                {detail.example_output}
              </pre>
            </div>
          </Section>

          <Section icon="⚠️" title="易错点">
            <ul className="list-disc pl-5 space-y-1.5">
              {detail.pitfalls.map((p, i) => (
                <li key={i} className="text-slate-600 leading-relaxed">
                  <Md>{p}</Md>
                </li>
              ))}
            </ul>
          </Section>

          {/* 动手任务：题目本身搬进沙箱页了，这里只留入口 */}
          {detail.has_task && (
            <div className="mt-4">
              <button
                onClick={() => navigate(`/learn/${detail.code}/practice`)}
                className="w-full flex items-center gap-3 rounded-xl border border-emerald-300 bg-emerald-50 px-3 py-3 text-left active:bg-emerald-100"
              >
                <span className="text-xl shrink-0">✍️</span>
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-medium text-emerald-800">
                    动手任务{detail.code_passed ? ' · 已通过' : ''}
                  </span>
                  <span className="block text-[11px] text-emerald-700/80 truncate">
                    打开代码沙箱，题目、编写、运行判定都在一页里
                  </span>
                </span>
                <span className="shrink-0 text-emerald-600 text-lg">›</span>
              </button>
              <div className="mt-1.5 px-1">
                <Button size="small" type="link" loading={hintLoading} onClick={askHint} className="!px-0">
                  💡 我卡住了，先给个提示
                </Button>
                {hint && (
                  <div className="mt-1 rounded-lg border border-sky-300 bg-sky-50 p-2.5 text-xs text-sky-800 leading-relaxed">
                    {hint}
                  </div>
                )}
              </div>
            </div>
          )}

          {detail.quizzes.length > 0 && (
            <Section
              icon="🧩"
              title={`练习题（${
                detail.quizzes.filter((q) => q.type === 'choice' || q.type === 'judge' || q.type === 'blank')
                  .length
              } 道客观题 + ${
                detail.quizzes.filter((q) => q.type === 'short' || q.type === 'applied').length
              } 道主观题）`}
            >
              <div className="space-y-3 mt-1">
                {detail.quizzes.map((q) => (
                  <QuizBlock
                    key={q.index}
                    q={q}
                    answer={answers[q.index]}
                    result={quizResults[q.index]}
                    submitting={submitting === q.index}
                    done={quizDone(q)}
                    onPick={(v) => setAnswers((prev) => ({ ...prev, [q.index]: v }))}
                    onSubmit={() => void submitQuiz(q)}
                  />
                ))}
              </div>
            </Section>
          )}

          {completed && (
            <div className="mt-5 rounded-xl border border-emerald-300 bg-emerald-50 p-3 text-sm text-emerald-700 flex items-center gap-3 flex-wrap">
              <span>🎉 这一课你已经掌握了</span>
              {detail.next_code ? (
                <Button
                  size="small"
                  type="primary"
                  onClick={() => void loadDetail(detail.next_code as string)}
                >
                  进入下一个知识点 →
                </Button>
              ) : (
                <span className="text-emerald-700/80">本科目已是最后一课</span>
              )}
            </div>
          )}

          {/* 项目实战固定压在最底部：它是「拓展对照」，不该挡在讲解和练习中间 */}
          {detail.project && (
            <Section icon="🏗" title="项目实战（鸭先知 RAG）">
              <ProjectField data={detail.project} />
            </Section>
          )}
        </div>
      )}

      {/* ===== 进度抽屉：科目 → 阶段 → 课时，逐层展开 ===== */}
      <Drawer
        title={
          <div className="flex items-baseline gap-2">
            <span className="text-sm font-medium text-indigo-700">学习进度</span>
            <span className="text-[11px] text-slate-500">
              {totalDone}/{points.length} 课已掌握
            </span>
          </div>
        }
        placement={isMobile ? 'bottom' : 'right'}
        height={isMobile ? '78vh' : undefined}
        width={360}
        open={navOpen}
        onClose={() => setNavOpen(false)}
        styles={{ body: { padding: '8px 12px 12px' } }}
      >
        <div>
          {subjects.map((s) => {
            const all = points.filter((p) => p.subject === s)
            const ok = all.filter((p) => p.status === 'completed').length
            const stages = [...new Set(all.map((p) => p.stage))]
            const open = openSubject === s
            return (
              <div key={s} className="border-b border-slate-100 last:border-0">
                {/* 第一层：科目 */}
                <button
                  onClick={() => setOpenSubject(open ? null : s)}
                  className="w-full flex items-center gap-2 py-2.5 text-left"
                >
                  <span className={`text-sm flex-1 truncate ${s === subject ? 'text-indigo-700 font-medium' : 'text-slate-700'}`}>
                    {s}
                  </span>
                  <span className="text-[11px] text-slate-500 shrink-0">
                    {ok}/{all.length}
                  </span>
                  <span className={`text-[10px] text-slate-400 transition-transform ${open ? 'rotate-180' : ''}`}>
                    ▾
                  </span>
                </button>

                {open && (
                  <div className="pb-2 space-y-1.5">
                    {stages.map((stage) => {
                      const items = all.filter((p) => p.stage === stage)
                      const key = `${s}|${stage}`
                      const sOpen = !!openStages[key]
                      const sOk = items.filter((p) => p.status === 'completed').length
                      return (
                        <div key={stage} className="rounded-lg border border-slate-200 overflow-hidden">
                          {/* 第二层：阶段 */}
                          <button
                            onClick={() => setOpenStages((prev) => ({ ...prev, [key]: !sOpen }))}
                            className="w-full flex items-center gap-2 px-2 py-1.5 bg-slate-50 text-left"
                          >
                            <span className="text-[11px] text-slate-600 flex-1 truncate">{stage}</span>
                            <span className="text-[10px] text-slate-400 shrink-0">
                              {sOk}/{items.length}
                            </span>
                            <span className="text-[9px] text-slate-400 shrink-0">{sOpen ? '▲' : '▼'}</span>
                          </button>

                          {/* 第三层：课时 */}
                          {sOpen && (
                            <div className="p-1.5 space-y-0.5">
                              {items.map((p) => {
                                const isCur = p.code === code
                                const locked = p.status === 'locked'
                                return (
                                  <button
                                    key={p.code}
                                    disabled={locked}
                                    onClick={() => {
                                      void loadDetail(p.code)
                                      setNavOpen(false)
                                    }}
                                    className={`w-full flex items-center gap-1.5 px-2 py-1.5 rounded-md text-[11px] text-left transition-colors ${
                                      isCur
                                        ? 'bg-indigo-100 text-indigo-800 font-medium'
                                        : locked
                                          ? 'text-slate-300 cursor-not-allowed'
                                          : 'text-slate-600 active:bg-slate-100'
                                    }`}
                                  >
                                    <span className="shrink-0">
                                      {p.status === 'completed' ? '✓' : locked ? '🔒' : '○'}
                                    </span>
                                    <span className="flex-1 truncate">
                                      {p.order_no}. {p.title}
                                    </span>
                                  </button>
                                )
                              })}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </Drawer>
    </div>
  )
}
