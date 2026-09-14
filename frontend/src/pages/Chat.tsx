import { useCallback, useEffect, useRef, useState } from 'react'
import { App, Button, Input, Select } from 'antd'
import { motion } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import { api, getToken } from '../api/client'
import { useAuth } from '../store/auth'
import type { QuizItem } from '../types'

interface Msg {
  id: string
  role: 'user' | 'assistant'
  content: string
  reasoning?: string // 模型的思考过程
  thinkOpen?: boolean
  streaming?: boolean
  quiz?: QuizItem[]
  picks?: number[]
  submitted?: boolean
}

const QUICK_COMMANDS = ['举例子', '写代码', '画流程图', '考点总结', '学习路径']
const LETTERS = 'ABCDEFGH'

export default function Chat() {
  const { message } = App.useApp()
  const { refreshCharacter } = useAuth()
  const [mentors, setMentors] = useState<string[]>(['老架构师', '大厂面试官', '学霸学长'])
  const [mentor, setMentor] = useState('老架构师')
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState<number | null>(null)
  const [sending, setSending] = useState(false)
  const [summary, setSummary] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const seqRef = useRef(0)

  const nextId = () => `m${++seqRef.current}`

  useEffect(() => {
    api.get<string[]>('/api/chat/mentors').then(setMentors).catch(() => undefined)
    api
      .get<{ id: number; mentor: string }[]>('/api/chat/sessions')
      .then((sessions) => {
        if (sessions.length) {
          const s = sessions[0]
          setMentor(s.mentor)
          setSessionId(s.id)
          api
            .get<{ messages: { role: 'user' | 'assistant'; content: string }[] }>(`/api/chat/history/${s.id}`)
            .then((d) => setMsgs(d.messages.map((m) => ({ ...m, id: nextId() }))))
            .catch(() => undefined)
        }
      })
      .catch(() => undefined)
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [msgs.length, summary])

  /** 把流式事件写进对应的助手消息 */
  const applyEvent = useCallback((id: string, ev: Record<string, unknown>) => {
    const type = ev.type as string
    if (type === 'done') {
      setSessionId(ev.session_id as number)
      if (ev.summary) setSummary(ev.summary as string)
    }
    setMsgs((list) =>
      list.map((m) => {
        if (m.id !== id) return m
        if (type === 'reasoning') {
          return { ...m, reasoning: (m.reasoning || '') + (ev.text as string) }
        }
        if (type === 'reply') {
          // 正文开始输出后自动收起思考面板，把注意力让给答案
          return { ...m, content: m.content + (ev.text as string), thinkOpen: false }
        }
        if (type === 'done') {
          const quiz = (ev.quiz as QuizItem[]) || []
          return { ...m, streaming: false, quiz, picks: quiz.map(() => -1), submitted: false }
        }
        if (type === 'error') {
          return { ...m, streaming: false, content: m.content || `⚠️ ${ev.message}` }
        }
        return m
      }),
    )
  }, [])

  const send = useCallback(
    async (text?: string) => {
      const content = (text ?? input).trim()
      if (!content || sending) return
      setSending(true)
      const aiId = nextId()
      setMsgs((m) => [
        ...m,
        { id: nextId(), role: 'user', content },
        { id: aiId, role: 'assistant', content: '', reasoning: '', thinkOpen: true, streaming: true },
      ])
      setInput('')
      try {
        const resp = await fetch('/api/chat/stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${getToken() || ''}`,
          },
          body: JSON.stringify({ mentor, message: content, session_id: sessionId }),
        })
        if (!resp.ok || !resp.body) throw new Error(`请求失败 (${resp.status})`)
        const reader = resp.body.getReader()
        const decoder = new TextDecoder()
        let buf = ''
        for (;;) {
          const { done, value } = await reader.read()
          if (done) break
          buf += decoder.decode(value, { stream: true })
          const blocks = buf.split('\n\n')
          buf = blocks.pop() || ''
          for (const block of blocks) {
            const line = block.split('\n').find((l) => l.startsWith('data:'))
            if (!line) continue
            try {
              applyEvent(aiId, JSON.parse(line.slice(5).trim()))
            } catch {
              /* 半包，忽略 */
            }
          }
        }
        await refreshCharacter()
      } catch (e) {
        setMsgs((list) =>
          list.map((m) =>
            m.id === aiId
              ? { ...m, streaming: false, content: m.content || `⚠️ ${(e as Error).message}` }
              : m,
          ),
        )
      } finally {
        setSending(false)
      }
    },
    [input, sending, mentor, sessionId, refreshCharacter, applyEvent],
  )

  const pickOption = (msgIndex: number, quizIndex: number, optionIndex: number) => {
    setMsgs((list) =>
      list.map((m, i) => {
        if (i !== msgIndex || m.submitted) return m
        const picks = [...(m.picks || [])]
        picks[quizIndex] = optionIndex
        return { ...m, picks }
      }),
    )
  }

  const submitQuiz = (msgIndex: number) => {
    setMsgs((list) => list.map((m, i) => (i === msgIndex ? { ...m, submitted: true } : m)))
  }

  const toggleThink = (msgIndex: number) => {
    setMsgs((list) => list.map((m, i) => (i === msgIndex ? { ...m, thinkOpen: !m.thinkOpen } : m)))
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-indigo-200">💬 AI 导师</h1>
          <p className="text-slate-400 text-sm mt-1">随时召唤导师：概念讲解、代码答疑、学习路径、求职咨询</p>
        </div>
        <Select
          value={mentor}
          onChange={(v) => {
            setMentor(v)
            setSessionId(null)
            setMsgs([])
            setSummary('')
          }}
          options={mentors.map((m) => ({ value: m, label: m }))}
          style={{ width: 180 }}
        />
      </div>

      {/* 对话窗口 */}
      <div className="game-panel p-4 h-[56vh] overflow-y-auto flex flex-col gap-3">
        {msgs.length === 0 && (
          <div className="m-auto text-center text-slate-500">
            <div className="text-5xl mb-3 animate-float">🧙</div>
            <div className="mb-1">我是「{mentor}」，很高兴成为你的导师</div>
            <div className="text-xs text-slate-500">试试下面的快捷指令，或直接提问</div>
          </div>
        )}
        {msgs.map((m, i) => (
          <motion.div
            key={m.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
              m.role === 'user'
                ? 'self-end bg-indigo-500/25 border border-indigo-500/30 text-indigo-100'
                : 'self-start bg-white/5 border border-white/10 text-slate-200'
            }`}
          >
            {/* 深度思考过程 */}
            {m.role === 'assistant' && (m.reasoning || m.streaming) && (
              <div
                className={`mb-2 rounded-xl border text-xs ${
                  m.streaming && !m.content
                    ? 'border-amber-400/40 bg-amber-400/5'
                    : 'border-white/10 bg-white/[0.03]'
                }`}
              >
                <button
                  onClick={() => toggleThink(i)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-left"
                >
                  <span className={m.streaming && !m.content ? 'animate-pulse' : ''}>
                    {m.streaming && !m.content ? '🧠 深度思考中…' : '🧠 深度思考过程'}
                  </span>
                  <span className="text-slate-500">{m.reasoning ? `${m.reasoning.length} 字` : ''}</span>
                  <span className="ml-auto text-slate-500">{m.thinkOpen ? '收起 ▲' : '展开 ▼'}</span>
                </button>
                {m.thinkOpen && (
                  <div className="px-3 pb-2 max-h-48 overflow-y-auto whitespace-pre-wrap text-slate-400 leading-relaxed">
                    {m.reasoning || '（模型正在思考…）'}
                    {m.streaming && !m.content && <span className="animate-pulse">▍</span>}
                  </div>
                )}
              </div>
            )}

            {m.role === 'assistant' ? (
              <>
                <ReactMarkdown
                  components={{
                    pre: ({ children }) => (
                      <pre className="bg-[#12142e] p-2 rounded-lg overflow-x-auto text-xs my-1.5">
                        {children}
                      </pre>
                    ),
                    code: ({ children, className }) =>
                      className?.includes('language') ? (
                        <code className={className}>{children}</code>
                      ) : (
                        <code className="bg-[#12142e] px-1 py-0.5 rounded text-indigo-300 text-xs">
                          {children}
                        </code>
                      ),
                    strong: ({ children }) => <strong className="text-indigo-200">{children}</strong>,
                  }}
                >
                  {m.content}
                </ReactMarkdown>
                {m.streaming && m.content && <span className="animate-pulse text-indigo-300">▍</span>}
                {m.streaming && !m.content && !m.reasoning && (
                  <span className="text-slate-400">
                    导师正在思考<span className="animate-pulse">…</span>
                  </span>
                )}
              </>
            ) : (
              m.content
            )}

            {/* 配套练习题：点选项 → 提交 → 出解析 */}
            {m.role === 'assistant' && m.quiz && m.quiz.length > 0 && (
              <div className="mt-3 pt-3 border-t border-white/10 space-y-3">
                {m.quiz.map((q, qi) => {
                  const picked = m.picks?.[qi] ?? -1
                  const submitted = !!m.submitted
                  const right = picked === q.answer_index
                  return (
                    <div key={qi}>
                      <div className="text-xs text-indigo-200 mb-1.5">
                        <span className="mr-1.5 text-indigo-400">练习 {qi + 1}</span>
                        {q.stem}
                      </div>
                      <div className="grid gap-1.5">
                        {q.options.map((opt, oi) => {
                          let cls = 'border-indigo-500/20 text-slate-300 hover:border-indigo-400/60'
                          if (submitted) {
                            if (oi === q.answer_index) cls = 'border-emerald-400 bg-emerald-500/15 text-emerald-200'
                            else if (oi === picked) cls = 'border-rose-400 bg-rose-500/15 text-rose-200'
                            else cls = 'border-indigo-500/20 text-slate-500'
                          } else if (oi === picked) {
                            cls = 'border-indigo-400 bg-indigo-500/20 text-indigo-100'
                          }
                          return (
                            <button
                              key={oi}
                              disabled={submitted}
                              onClick={() => pickOption(i, qi, oi)}
                              className={`text-left px-3 py-2 rounded-xl border text-xs transition-all ${cls}`}
                            >
                              <span className="text-slate-500 mr-1">{LETTERS[oi]}.</span>
                              {opt}
                            </button>
                          )
                        })}
                      </div>
                      {submitted && (
                        <div className="mt-1.5 text-xs">
                          <span className={right ? 'text-emerald-300' : 'text-rose-300'}>
                            {right ? '✅ 回答正确' : `❌ 回答错误，正确答案是 ${LETTERS[q.answer_index]}`}
                          </span>
                          <div className="text-slate-300 mt-1 leading-relaxed">
                            <span className="text-indigo-300">解析：</span>
                            {q.explanation}
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
                {!m.submitted && (
                  <Button
                    size="small"
                    type="primary"
                    disabled={(m.picks || []).filter((p) => p >= 0).length < m.quiz.length}
                    onClick={() => submitQuiz(i)}
                  >
                    提交答案
                  </Button>
                )}
              </div>
            )}
          </motion.div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* 快捷指令 */}
      <div className="flex gap-2 flex-wrap">
        {QUICK_COMMANDS.map((c) => (
          <button
            key={c}
            onClick={() => send(c)}
            disabled={sending}
            className="px-3 py-1.5 rounded-full text-xs border border-indigo-500/30 text-indigo-300 hover:bg-indigo-500/15 transition-colors disabled:opacity-50"
          >
            {c}
          </button>
        ))}
      </div>

      {/* 输入区 */}
      <div className="flex gap-2">
        <Input.TextArea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="向导师提问，例如：讲讲 Python 的 GIL / 帮我规划 Python 后端学习路径"
          autoSize={{ minRows: 1, maxRows: 4 }}
          onPressEnter={(e) => {
            if (!e.shiftKey) {
              e.preventDefault()
              send()
            }
          }}
        />
        <Button type="primary" size="large" loading={sending} onClick={() => send()} className="glow-btn px-6">
          发送
        </Button>
      </div>

      {summary && (
        <div className="game-panel p-4 text-sm text-slate-300">
          <span className="text-indigo-300 font-medium">📝 本次对话知识点：</span>
          {summary}
        </div>
      )}
    </div>
  )
}
