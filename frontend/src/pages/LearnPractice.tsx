import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { App, Button, Spin } from 'antd'
import { api } from '../api/client'
import CodeEditor from '../components/CodeEditor'
import Md from '../components/Md'
import SplitPane from '../components/SplitPane'
import type { LearnCheckResult, LearnPointDetail } from '../types'

/** 返回课程页时用它定位到刚练的那一课（否则会被「第一门没学完的课」抢走焦点） */
export const LEARN_CODE_KEY = 'ca_learn_code'

/**
 * 动手任务页：把「题目 + 写代码 + 运行判定」放在同一个页面里。
 *
 * 之前这三块分散在课程的左右两栏：题目在左栏底部、编辑器在右栏，
 * 手机上要来回滚，还会被讲解文字挤到看不见。
 * 现在题目固定在上方（可折叠），下面是编辑器 + 结果，中间可拖拽分配比例。
 */
export default function LearnPractice() {
  const { code = '' } = useParams<{ code: string }>()
  const navigate = useNavigate()
  const { message } = App.useApp()

  const [detail, setDetail] = useState<LearnPointDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [userCode, setUserCode] = useState('')
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<LearnCheckResult | null>(null)
  const [hint, setHint] = useState('')
  const [hintLoading, setHintLoading] = useState(false)
  const [taskOpen, setTaskOpen] = useState(true)
  const [setupOpen, setSetupOpen] = useState(false)
  const alive = useRef(true)

  useEffect(() => {
    alive.current = true
    return () => {
      alive.current = false
    }
  }, [])

  const load = useCallback(
    async (target: string) => {
      setLoading(true)
      try {
        const d = await api.get<LearnPointDetail>(`/api/learn/points/${target}`)
        if (!alive.current) return
        setDetail(d)
        setUserCode(d.last_code || d.starter)
      } catch (e) {
        // 锁住的课会返回 403（正常拦截），直接退回课程页别让人卡在空白页
        message.error((e as Error).message)
        navigate('/learn', { replace: true })
      } finally {
        if (alive.current) setLoading(false)
      }
    },
    [message, navigate],
  )

  useEffect(() => {
    if (code) {
      sessionStorage.setItem(LEARN_CODE_KEY, code)
      void load(code)
    }
  }, [code, load])

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
    } catch (e) {
      if (alive.current) message.error((e as Error).message)
    } finally {
      if (alive.current) setRunning(false)
    }
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

  const back = () => navigate('/learn')

  const gotoNext = (next: string | null) => {
    if (!next) return back()
    sessionStorage.setItem(LEARN_CODE_KEY, next)
    navigate(`/learn/${next}/practice`, { replace: true })
    void load(next)
  }

  if (loading) {
    return (
      <div className="h-[100dvh] flex flex-col items-center justify-center gap-3 text-slate-500">
        <Spin />
        <span className="text-xs">正在加载题目…</span>
      </div>
    )
  }

  if (!detail) return null

  const isSql = detail.runner === 'sql'

  return (
    <div className="h-[100dvh] flex flex-col bg-[#f6f7fb]">
      {/* 顶部工具条 */}
      <header className="shrink-0 flex items-center gap-2 px-2 h-12 bg-white/95 backdrop-blur border-b border-indigo-100">
        <button
          onClick={back}
          aria-label="返回课程"
          className="shrink-0 w-9 h-9 rounded-lg text-slate-500 active:bg-slate-100 text-lg"
        >
          ←
        </button>
        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium text-indigo-700 truncate leading-tight">
            {isSql ? '⌨️ 动手任务 · SQL' : '✍️ 动手任务'}
          </div>
          <div className="text-[10px] text-slate-500 truncate leading-tight">
            {detail.subject} · 第 {detail.order_no} 课 · {detail.title}
          </div>
        </div>
        <Button
          size="small"
          type="primary"
          loading={running}
          disabled={!userCode.trim()}
          onClick={run}
          className="shrink-0"
        >
          ▶ 运行判定
        </Button>
      </header>

      {/* ===== 题目区：动手任务 + 给定代码，放在编辑器上方 ===== */}
      <div className="shrink-0 max-h-[34vh] overflow-y-auto border-b border-slate-200 bg-white">
        <button
          onClick={() => setTaskOpen((v) => !v)}
          className="w-full flex items-center gap-2 px-3 py-2 text-left"
        >
          <span className="text-xs font-medium text-amber-700">📋 题目要求</span>
          <span className="text-[10px] text-slate-400">{taskOpen ? '收起 ▲' : '展开 ▼'}</span>
        </button>

        {taskOpen && (
          <div className="px-3 pb-3 space-y-2">
            <div className="rounded-xl border border-amber-300 bg-amber-50 p-2.5 text-[13px] text-slate-700">
              {detail.task ? <Md>{detail.task}</Md> : <span className="text-slate-500">本课没有文字题目，按讲解要求写即可。</span>}
            </div>

            {detail.setup && (
              <div>
                <button
                  onClick={() => setSetupOpen((v) => !v)}
                  className="text-[11px] text-slate-500 mb-1"
                >
                  {isSql ? '题目已给好的表结构与数据' : '题目已给好的代码'}（不用改）{setupOpen ? ' ▲' : ' ▼'}
                </button>
                {setupOpen && (
                  <pre className="bg-[#f4f6fa] border border-slate-200 rounded-lg p-2 text-[11px] text-slate-500 font-mono overflow-x-auto">
                    <code>{detail.setup}</code>
                  </pre>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ===== 编辑区 + 结果区（中间可拖拽） ===== */}
      <div className="flex-1 min-h-0 p-2">
        <SplitPane
          storageKey="ca_practice_ratio"
          initial={0.55}
          snaps={[0.4, 0.55, 0.75]}
          top={
            <div className="flex-1 min-h-0 flex flex-col gap-1.5">
              <CodeEditor
                value={userCode}
                onChange={setUserCode}
                placeholder={
                  isSql
                    ? '在这里写你的 SQL…（语句结尾记得加分号 ;）'
                    : '在这里写你的代码…（回车会自动缩进，Tab 缩进 4 格）'
                }
              />
              <div className="shrink-0 flex gap-2">
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
            </div>
          }
          bottom={
            <div className="flex-1 min-h-0 overflow-auto rounded-xl border border-slate-200 bg-white p-2.5 pb-4 text-xs space-y-2">
              {hint && (
                <div className="rounded-lg border border-sky-300 bg-sky-50 p-2.5 text-sky-800 leading-relaxed">
                  <span className="text-sky-700">💡 提示：</span>
                  {hint}
                </div>
              )}

              {!result && !hint && (
                <div className="h-full flex items-center justify-center text-center px-4 text-slate-400">
                  写完点右上角「运行判定」· 结果和报错会显示在这里
                </div>
              )}

              {result && (
                <div
                  className={`rounded-lg border p-2.5 space-y-2 ${
                    result.passed ? 'border-emerald-300 bg-emerald-50' : 'border-rose-300 bg-rose-50'
                  }`}
                >
                  <div className={result.passed ? 'text-emerald-700' : 'text-rose-700'}>
                    {result.passed
                      ? isSql
                        ? '✅ 结果完全正确 —— 这个知识点你掌握了！'
                        : `✅ 判定通过（${result.solved}/${result.total} 组用例全对）—— 这个知识点你掌握了！`
                      : `❌ 还没通过${
                          isSql || !result.total ? '' : `（通过 ${result.solved}/${result.total} 组）`
                        }`}
                  </div>

                  {!result.passed && result.reason && (
                    <div className="text-rose-800 whitespace-pre-wrap leading-relaxed">{result.reason}</div>
                  )}

                  {result.output && (
                    <div>
                      <div className="text-slate-500 mb-1">你的输出：</div>
                      <pre className="bg-white/70 rounded p-2 text-slate-700 font-mono whitespace-pre-wrap">
                        {result.output}
                      </pre>
                    </div>
                  )}

                  {result.error && (
                    <div>
                      <div className="text-slate-500 mb-1">报错信息：</div>
                      <pre className="bg-white/70 rounded p-2 text-rose-600 font-mono whitespace-pre-wrap max-h-40 overflow-auto">
                        {result.error}
                      </pre>
                    </div>
                  )}

                  {result.passed && !result.lesson_completed && (
                    <div className="text-amber-700">
                      {isSql ? 'SQL 这关过了' : '代码这关过了'} 👍 不过这课还有练习题要答，答完才解锁下一个。
                      <Button size="small" type="primary" className="mt-1.5" onClick={back}>
                        去做练习题
                      </Button>
                    </div>
                  )}

                  {result.lesson_completed && (
                    <Button type="primary" block onClick={() => gotoNext(result.next_code)}>
                      {result.next_code ? '进入下一个知识点 →' : '本科目学完了，回课程页'}
                    </Button>
                  )}
                </div>
              )}
            </div>
          }
        />
      </div>
    </div>
  )
}
