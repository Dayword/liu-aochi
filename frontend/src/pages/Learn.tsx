import { useCallback, useEffect, useRef, useState } from 'react'
import { App, Button, Input, Spin } from 'antd'
import ReactMarkdown from 'react-markdown'
import { api } from '../api/client'
import type {
  LearnCheckResult,
  LearnPointBrief,
  LearnPointDetail,
  LearnQuizItem,
  LearnQuizResult,
} from '../types'

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
            <code className="bg-indigo-50 text-indigo-700 px-1 py-0.5 rounded text-[0.9em]">
              {children}
            </code>
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

      {/* 作答区 */}
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

      {/* 判分结果 */}
      {result && (
        <div className="text-xs space-y-1.5 pt-1 border-t border-slate-200">
          {objective ? (
            <div className={result.correct ? 'text-emerald-600' : 'text-rose-600'}>
              {result.correct ? '✅ 回答正确' : `❌ 回答错误，正确答案是「${result.correct_answer}」`}
            </div>
          ) : (
            <div className="text-sky-200">
              {result.coverage !== null && (
                <span>
                  要点覆盖 {Math.round((result.coverage || 0) * 100)}%
                  {result.missing.length > 0 && (
                    <span className="text-amber-700 ml-2">
                      还可以补充：{result.missing.join('、')}
                    </span>
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
  const [points, setPoints] = useState<LearnPointBrief[]>([])
  const [subject, setSubject] = useState<string>('')
  const [code, setCode] = useState<string>('')
  const [detail, setDetail] = useState<LearnPointDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [userCode, setUserCode] = useState('')
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<LearnCheckResult | null>(null)
  const [hint, setHint] = useState('')
  const [hintLoading, setHintLoading] = useState(false)
  // 习题：当前作答 / 判分结果 / 正在提交哪一题
  const [answers, setAnswers] = useState<Record<number, string | number>>({})
  const [quizResults, setQuizResults] = useState<Record<number, LearnQuizResult>>({})
  const [submitting, setSubmitting] = useState<number | null>(null)
  const [completed, setCompleted] = useState(false)
  const alive = useRef(true)
  const taRef = useRef<HTMLTextAreaElement>(null)
  const gutterRef = useRef<HTMLPreElement>(null)

  /**
   * 自动缩进：新手最容易死在缩进上（Python 全靠缩进分块）。
   * 回车继承上一行缩进，上一行以 `:` 结尾再多缩进一级；Tab 插入 4 个空格。
   */
  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    const ta = e.currentTarget
    if (e.key === 'Tab') {
      e.preventDefault()
      const s = ta.selectionStart
      const end = ta.selectionEnd
      const next = userCode.slice(0, s) + '    ' + userCode.slice(end)
      setUserCode(next)
      requestAnimationFrame(() => {
        ta.selectionStart = ta.selectionEnd = s + 4
      })
      return
    }
    if (e.key === 'Enter') {
      e.preventDefault()
      const s = ta.selectionStart
      const end = ta.selectionEnd
      const lineStart = userCode.lastIndexOf('\n', s - 1) + 1
      const line = userCode.slice(lineStart, s)
      const indent = (line.match(/^[ \t]*/) || [''])[0]
      const extra = line.trimEnd().endsWith(':') ? '    ' : ''
      const insert = '\n' + indent + extra
      const next = userCode.slice(0, s) + insert + userCode.slice(end)
      setUserCode(next)
      const pos = s + insert.length
      requestAnimationFrame(() => {
        ta.selectionStart = ta.selectionEnd = pos
        if (gutterRef.current) gutterRef.current.scrollTop = ta.scrollTop
      })
    }
  }

  useEffect(() => {
    alive.current = true
    return () => {
      alive.current = false
    }
  }, [])

  const loadDetail = useCallback(
    async (target: string) => {
      setLoading(true)
      setCode(target)
      setResult(null)
      setHint('')
      try {
        const d = await api.get<LearnPointDetail>(`/api/learn/points/${target}`)
        if (!alive.current) return
        setDetail(d)
        setUserCode(d.last_code || d.starter)
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
        // 默认停在第一个还没掌握的知识点（科目之间互不阻塞）；全学完了就停在最后一个
        const cur = list.find((p) => p.status !== 'completed') || list[list.length - 1]
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

  /** 切科目时自动跳到该科目第一个还没掌握的知识点 */
  const pickSubject = (s: string) => {
    if (s === subject) return
    setSubject(s)
    const list = points.filter((p) => p.subject === s)
    const cur = list.find((p) => p.status !== 'completed') || list[0]
    if (cur) void loadDetail(cur.code)
  }

  const refreshPoints = async () => {
    const list = await api.get<LearnPointBrief[]>('/api/learn/points')
    if (alive.current) setPoints(list)
  }

  const run = async () => {
    if (!detail) return
    setRunning(true)
    setHint('')
    try {
      const r = await api.post<LearnCheckResult>('/api/learn/check', {
        code: detail.code,
        user_code: userCode,
      })
      if (!alive.current) return
      setResult(r)
      setCompleted(r.lesson_completed)
      if (r.passed) await refreshPoints()
    } catch (e) {
      if (alive.current) message.error((e as Error).message)
    } finally {
      if (alive.current) setRunning(false)
    }
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
      const r = await api.post<{ hint: string }>('/api/learn/hint', {
        code: detail.code,
        user_code: userCode,
        reason: result?.reason || '',
      })
      if (alive.current) setHint(r.hint)
    } catch (e) {
      if (alive.current) message.error((e as Error).message)
    } finally {
      if (alive.current) setHintLoading(false)
    }
  }

  const subjects = [...new Set(points.map((p) => p.subject))]
  const subjectPoints = points.filter((p) => p.subject === subject)
  const done = subjectPoints.filter((p) => p.status === 'completed').length

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-indigo-700">📘 引导式学习</h1>
        <p className="text-slate-500 text-sm mt-1">
          八个科目独立解锁，互不阻塞。先看懂，再自己动手写 —— 写完点「运行判定」，
          通过就解锁同一科目的下一课。
        </p>
      </div>

      {/* 科目切换 */}
      <div className="flex gap-1.5 flex-wrap">
        {subjects.map((s) => {
          const all = points.filter((p) => p.subject === s)
          const ok = all.filter((p) => p.status === 'completed').length
          const active = s === subject
          return (
            <button
              key={s}
              onClick={() => pickSubject(s)}
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

      {/* 进度：当前科目的知识点列表 */}
      <div className="game-panel p-3">
        <div className="flex items-center gap-2 flex-wrap mb-2">
          <span className="text-xs text-slate-500">
            {subject} 进度 {done}/{subjectPoints.length}
          </span>
          <span className="text-[11px] text-slate-500">
            （本科目内按顺序解锁：上一课判定通过才会亮起下一课）
          </span>
        </div>
        {/* 按科目内的分组展示，一科 8~10 课才找得到 */}
        {[...new Set(subjectPoints.map((p) => p.stage))].map((stage) => (
          <div key={stage} className="flex items-start gap-2 flex-wrap mb-1.5">
            <span className="text-[10px] text-slate-500 w-[112px] shrink-0 pt-1.5 text-right">
              {stage}
            </span>
            <div className="flex items-center gap-1.5 flex-wrap flex-1">
              {subjectPoints
                .filter((p) => p.stage === stage)
                .map((p) => {
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
                      className={`px-2 py-1 rounded-lg border text-[11px] transition-all ${cls}`}
                      title={p.summary}
                    >
                      {p.status === 'completed' ? '✓ ' : p.status === 'locked' ? '🔒 ' : ''}
                      {p.order_no}. {p.title}
                    </button>
                  )
                })}
            </div>
          </div>
        ))}
      </div>

      {loading && (
        <div className="game-panel p-10 text-center">
          <Spin />
        </div>
      )}

      {!loading && detail && (
        <div
          className={`grid gap-4 items-start ${
            detail.has_task ? 'lg:grid-cols-[minmax(0,1fr)_minmax(0,420px)]' : ''
          }`}
        >
          {/* 左侧：讲解 */}
          <div className="game-panel p-5">
            <div className="flex items-baseline gap-2 flex-wrap">
              <h2 className="text-lg font-bold text-indigo-700">
                {detail.subject} · 第 {detail.order_no} 课 · {detail.title}
              </h2>
              {detail.status === 'completed' && (
                <span className="text-xs text-emerald-600">✓ 已掌握</span>
              )}
            </div>
            <p className="text-slate-500 text-xs mt-1">{detail.summary}</p>

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

            {detail.task && (
              <Section icon="✍️" title="动手任务">
                <div className="rounded-xl border border-amber-300 bg-amber-50 p-3">
                  <Md>{detail.task}</Md>
                </div>
              </Section>
            )}

            {detail.quizzes.length > 0 && (
              <Section
                icon="🧩"
                title={`练习题（${
                  detail.quizzes.filter(
                    (q) => q.type === 'choice' || q.type === 'judge' || q.type === 'blank',
                  ).length
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
                  <Button size="small" type="primary" onClick={() => void loadDetail(detail.next_code as string)}>
                    进入下一个知识点 →
                  </Button>
                ) : (
                  <span className="text-emerald-700/80">本科目已是最后一课</span>
                )}
              </div>
            )}
          </div>

          {/* 右侧：写代码 + 运行判定（没有动手题的知识点则不显示这一栏） */}
          {detail.has_task && (
          <div className="game-panel p-4 lg:sticky lg:top-4 space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-emerald-700">
                {detail.runner === 'sql' ? '⌨️ 自己写 SQL' : '⌨️ 自己写'}
              </span>
              <span className="text-[10px] text-slate-500">
                {detail.runner === 'sql' ? 'SQLite · 只读查询' : 'Python · 5s 超时'}
              </span>
              <Button
                size="small"
                type="primary"
                className="ml-auto"
                loading={running}
                onClick={run}
                disabled={!userCode.trim()}
              >
                ▶ 运行判定
              </Button>
            </div>

            {detail.setup && (
              <div>
                <div className="text-[11px] text-slate-500 mb-1">
                  {detail.runner === 'sql'
                    ? '题目已给好的表结构与数据（不用改，查询时直接用）'
                    : '题目已给好的代码（不用改）'}
                </div>
                <pre className="bg-[#f4f6fa] border border-slate-200 rounded-lg p-2 text-xs text-slate-500 font-mono">
                  <code>{detail.setup}</code>
                </pre>
              </div>
            )}

            <div className="flex rounded-lg border border-indigo-300 bg-[#f4f6fa] focus-within:border-indigo-400 overflow-hidden">
              {/* 行号：报错信息里的「第几行」能直接对上 */}
              <pre
                ref={gutterRef}
                aria-hidden
                className="select-none shrink-0 text-right pl-2 pr-1.5 py-3 bg-slate-100 text-[13px] leading-[22px] font-mono text-slate-400 overflow-hidden"
              >
                {userCode.split('\n').map((_, i) => i + 1).join('\n')}
              </pre>
              <textarea
                ref={taRef}
                value={userCode}
                onChange={(e) => setUserCode(e.target.value)}
                onKeyDown={onKeyDown}
                onScroll={(e) => {
                  if (gutterRef.current) gutterRef.current.scrollTop = e.currentTarget.scrollTop
                }}
                spellCheck={false}
                rows={11}
                className="flex-1 min-w-0 bg-transparent px-2 py-3 text-[13px] leading-[22px] font-mono text-slate-800 outline-none resize-none"
                placeholder={
                  detail.runner === 'sql'
                    ? '在这里写你的 SQL…（语句结尾记得加分号 ;）'
                    : '在这里写你的代码…（回车会自动缩进，Tab 缩进 4 格）'
                }
              />
            </div>

            <div className="flex gap-2">
              <Button size="small" loading={hintLoading} onClick={askHint} className="flex-1">
                💡 我卡住了
              </Button>
              <Button
                size="small"
                className="flex-1"
                onClick={() => setUserCode(detail.starter)}
                disabled={!detail.starter}
              >
                ↺ 回到初始
              </Button>
            </div>

            {hint && (
              <div className="rounded-lg border border-sky-300 bg-sky-50 p-3 text-xs text-sky-800 leading-relaxed">
                <span className="text-sky-700">💡 提示：</span>
                {hint}
              </div>
            )}

            {/* 判定结果 */}
            {result && (
              <div
                className={`rounded-lg border p-3 text-xs space-y-2 ${
                  result.passed
                    ? 'border-emerald-300 bg-emerald-50'
                    : 'border-rose-300 bg-rose-50'
                }`}
              >
                <div className={result.passed ? 'text-emerald-700' : 'text-rose-700'}>
                  {result.passed
                    ? detail.runner === 'sql'
                      ? '✅ 结果完全正确 —— 这个知识点你掌握了！'
                      : `✅ 判定通过（${result.solved}/${result.total} 组用例全对）—— 这个知识点你掌握了！`
                    : `❌ 还没通过${
                        detail.runner === 'sql' || !result.total
                          ? ''
                          : `（通过 ${result.solved}/${result.total} 组）`
                      }`}
                </div>

                {!result.passed && result.reason && (
                  <div className="text-rose-800 whitespace-pre-wrap leading-relaxed">
                    {result.reason}
                  </div>
                )}

                {result.output && (
                  <div>
                    <div className="text-slate-500 mb-1">你的输出：</div>
                    <pre className="bg-[#f4f6fa] rounded p-2 text-slate-700 font-mono whitespace-pre-wrap">
                      {result.output}
                    </pre>
                  </div>
                )}

                {result.error && (
                  <div>
                    <div className="text-slate-500 mb-1">报错信息：</div>
                    <pre className="bg-[#f4f6fa] rounded p-2 text-rose-600 font-mono whitespace-pre-wrap max-h-40 overflow-auto">
                      {result.error}
                    </pre>
                  </div>
                )}

                {result.passed && !result.lesson_completed && (
                  <div className="text-amber-700 text-center">
                    {detail.runner === 'sql' ? 'SQL 这关过了' : '代码这关过了'} 👍
                    不过这课还有练习题要答，答完就解锁下一个。
                  </div>
                )}
                {result.lesson_completed && result.next_code && (
                  <Button
                    type="primary"
                    block
                    onClick={() => void loadDetail(result.next_code as string)}
                  >
                    进入下一个知识点 →
                  </Button>
                )}
                {result.lesson_completed && !result.next_code && (
                  <div className="text-emerald-700 text-center">
                    🎉 {detail.subject} 这个科目学完了，去换个科目挑战吧。
                  </div>
                )}
              </div>
            )}
          </div>
          )}
        </div>
      )}
    </div>
  )
}
