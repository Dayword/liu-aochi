import { useEffect, useState } from 'react'
import { App, Button, Input, Progress, Select } from 'antd'
import { motion } from 'framer-motion'
import { api } from '../api/client'
import { useAuth } from '../store/auth'
import type { ClassInfo, InterviewAnswer, InterviewReport, InterviewStart } from '../types'

const ROUND_NAMES: Record<number, string> = { 1: '一面·基础面', 2: '二面·深度面', 3: '三面·主管面', 4: 'HR面' }
const DIMS = ['技术准确性', '逻辑清晰度', '表达流畅度', 'STAR法则']
const COMPANIES = ['字节跳动', '腾讯', '阿里巴巴', '美团', '百度', '京东']

interface Msg {
  role: 'interviewer' | 'candidate' | 'system'
  content: string
}

export default function Interview() {
  const { message } = App.useApp()
  const { refreshCharacter, character } = useAuth()
  const [classes, setClasses] = useState<ClassInfo[]>([])
  const [classKey, setClassKey] = useState('backend')
  const [company, setCompany] = useState('字节跳动')
  const [difficulty, setDifficulty] = useState(2)
  const [session, setSession] = useState<InterviewStart | null>(null)
  const [answer, setAnswer] = useState('')
  const [sending, setSending] = useState(false)
  const [roundResult, setRoundResult] = useState<InterviewAnswer | null>(null)
  const [report, setReport] = useState<InterviewReport | null>(null)
  const [history, setHistory] = useState<Msg[]>([])

  useEffect(() => {
    api
      .get<ClassInfo[]>('/api/user/classes')
      .then((c) => {
        setClasses(c)
        if (c.length) setClassKey(c[1]?.key || c[0].key)
      })
      .catch((e) => message.error((e as Error).message))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const start = async () => {
    setSending(true)
    try {
      const r = await api.post<InterviewStart>('/api/interview/start', {
        class_key: classKey,
        company,
        difficulty,
      })
      setSession(r)
      setHistory([{ role: 'interviewer', content: r.question }])
      setAnswer('')
      setReport(null)
      setRoundResult(null)
    } catch (e) {
      message.error((e as Error).message)
    } finally {
      setSending(false)
    }
  }

  const submit = async () => {
    if (!session) return
    const text = answer.trim()
    if (!text) {
      message.warning('请先作答')
      return
    }
    setSending(true)
    try {
      const r = await api.post<InterviewAnswer>('/api/interview/answer', {
        session_id: session.session_id,
        answer: text,
      })
      setAnswer('')
      // 用户回答先落到对话流里，保证复盘时看得到
      setHistory((h) => [...h, { role: 'candidate', content: text }])
      if (r.interview_finished) {
        setReport(r.report)
        await refreshCharacter()
      } else {
        setRoundResult(r)
      }
    } catch (e) {
      message.error((e as Error).message)
    } finally {
      setSending(false)
    }
  }

  const continueRound = () => {
    if (!roundResult || !session) return
    const { round_finished, round_no, next_question } = roundResult
    if (round_finished) {
      const nextRound = round_no + 1
      setSession({ ...session, round_no: nextRound })
      setHistory((h) => [
        ...h,
        { role: 'system', content: `—— 进入${ROUND_NAMES[nextRound] ?? '下一轮'} ——` },
      ])
    }
    if (next_question) {
      setHistory((h) => [...h, { role: 'interviewer', content: next_question }])
    }
    setRoundResult(null)
  }

  // ---------- 报告 ----------
  if (report) {
    const dims = report.dimensions || {}
    return (
      <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="game-panel p-8 max-w-3xl mx-auto">
        <div className="text-center mb-6">
          <div className="text-6xl mb-2">{report.grade === 'S' || report.grade === 'A' ? '🏆' : report.grade === 'B' ? '💪' : '📚'}</div>
          <h1 className="text-2xl font-bold text-indigo-200">面试报告</h1>
          <div className="mt-2 inline-block px-4 py-1 rounded-full bg-amber-500/20 text-amber-300 font-bold text-lg">
            {report.offer === '虚拟 Offer' ? '🎉 虚拟 Offer！' : '继续修炼，再战一轮'}
          </div>
          <div className="text-slate-400 text-sm mt-1">
            综合评分 <span className="text-indigo-300 font-bold text-xl">{report.overall}</span> 分 · 评级{' '}
            <span className="text-amber-300 font-bold">{report.grade}</span>
          </div>
        </div>

        <div className="grid gap-3 mb-6">
          {DIMS.map((d) => (
            <div key={d} className="flex items-center gap-3">
              <span className="w-24 text-sm text-slate-300">{d}</span>
              <Progress
                percent={dims[d] || 0}
                strokeColor={dims[d] >= 75 ? '#34d399' : dims[d] >= 60 ? '#fbbf24' : '#f87171'}
                trailColor="#2a2d52"
              />
              <span className="w-8 text-right text-sm text-slate-400">{dims[d] || 0}</span>
            </div>
          ))}
        </div>

        <div className="p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-sm text-slate-300 leading-relaxed">
          <span className="text-emerald-400">✅ 优势：</span>
          {report.strong_point}
          <br />
          <span className="text-rose-400">⚠️ 短板：</span>
          {report.weak_point}
          <br />
          <span className="text-indigo-300">💡 建议：</span>
          {report.advice}
        </div>

        <div className="flex gap-3 mt-6 justify-center">
          <Button onClick={() => setReport(null)}>返回面试大厅</Button>
          <Button
            type="primary"
            onClick={() => {
              setReport(null)
              setSession(null)
              setHistory([])
            }}
            className="glow-btn"
          >
            再战一场
          </Button>
        </div>
      </motion.div>
    )
  }

  // ---------- 大厅 / 进行中 ----------
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-indigo-200">🎤 面试闯关</h1>
        <p className="text-slate-400 text-sm mt-1">模拟真实面试全流程：一面基础面 → 二面深度面 → 三面主管面 → HR面</p>
      </div>

      {!session ? (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="game-panel p-6 max-w-2xl">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
            <div>
              <div className="text-xs text-slate-400 mb-2">目标岗位方向</div>
              <Select
                value={classKey}
                onChange={setClassKey}
                style={{ width: '100%' }}
                options={classes.map((c) => ({ value: c.key, label: `${c.emoji} ${c.name}` }))}
              />
            </div>
            <div>
              <div className="text-xs text-slate-400 mb-2">目标公司</div>
              <Select value={company} onChange={setCompany} style={{ width: '100%' }} options={COMPANIES.map((c) => ({ value: c, label: c }))} />
            </div>
            <div>
              <div className="text-xs text-slate-400 mb-2">难度等级</div>
              <Select
                value={difficulty}
                onChange={setDifficulty}
                style={{ width: '100%' }}
                options={[
                  { value: 1, label: '⭐ 轻松' },
                  { value: 2, label: '⭐⭐ 标准' },
                  { value: 3, label: '⭐⭐⭐ 大厂' },
                ]}
              />
            </div>
          </div>
          <Button type="primary" size="large" block loading={sending} onClick={start} className="glow-btn">
            开始模拟面试
          </Button>
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-2 text-center text-[11px] text-slate-400">
            <div className="p-2 bg-white/5 rounded-lg">🎯 岗位题库匹配</div>
            <div className="p-2 bg-white/5 rounded-lg">🔍 动态追问机制</div>
            <div className="p-2 bg-white/5 rounded-lg">📊 四维实时评分</div>
            <div className="p-2 bg-white/5 rounded-lg">📜 完整面试报告</div>
          </div>
        </motion.div>
      ) : (
        <div className="game-panel p-6">
          <div className="flex items-center gap-3 mb-5 flex-wrap">
            <span className="text-3xl">👔</span>
            <div>
              <div className="font-medium text-slate-100">
                {session.interviewer_name} · {company}
              </div>
              <div className="text-xs text-slate-400">
                {ROUND_NAMES[session.round_no]}（第 {session.round_no}/4 轮）· {character?.class_name}
              </div>
            </div>
            <div className="ml-auto flex gap-1">
              {[1, 2, 3, 4].map((r) => (
                <span
                  key={r}
                  className={`w-8 h-2 rounded-full ${r <= session.round_no ? 'bg-indigo-400' : 'bg-slate-700'}`}
                />
              ))}
            </div>
          </div>

          {/* 对话流 */}
          <div className="h-[40vh] overflow-y-auto space-y-3 mb-4 pr-1">
            {history.map((m, i) => {
              if (m.role === 'system') {
                return (
                  <div key={i} className="text-center text-xs text-amber-300 py-1">
                    {m.content}
                  </div>
                )
              }
              if (m.role === 'candidate') {
                return (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="max-w-[85%] ml-auto bg-indigo-500/20 border border-indigo-500/30 rounded-2xl px-4 py-3 text-sm text-indigo-100 whitespace-pre-wrap"
                  >
                    <div className="text-[10px] text-indigo-300/70 mb-1 text-right">我</div>
                    {m.content}
                  </motion.div>
                )
              }
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="max-w-[85%] bg-white/5 border border-white/10 rounded-2xl px-4 py-3 text-sm text-slate-200 whitespace-pre-wrap"
                >
                  <div className="text-[10px] text-slate-500 mb-1">面试官</div>
                  {m.content}
                </motion.div>
              )
            })}
            {roundResult && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 rounded-2xl border border-indigo-500/30 bg-indigo-500/10"
              >
                <div className="font-medium text-indigo-200 mb-2">
                  {roundResult.round_finished ? `📊 ${ROUND_NAMES[roundResult.round_no]} 评分` : '📊 本题评分'}
                </div>
                {roundResult.round_scores && Object.keys(roundResult.round_scores).length > 0 ? (
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-center">
                    {Object.entries(roundResult.round_scores)
                      .filter(([k]) => k !== '点评' && k !== '建议')
                      .map(([k, v]) => (
                        <div key={k} className="p-2 bg-white/5 rounded-lg">
                          <div className="text-lg font-bold text-indigo-300">{v}</div>
                          <div className="text-[10px] text-slate-400">{k}</div>
                        </div>
                      ))}
                  </div>
                ) : null}
                {roundResult.round_scores?.点评 && (
                  <div className="text-xs text-slate-300 mt-2">{roundResult.round_scores.点评}</div>
                )}
                {roundResult.round_scores?.建议 && (
                  <div className="text-xs text-purple-300 mt-1">💡 {roundResult.round_scores.建议}</div>
                )}
                <Button type="primary" className="mt-3" onClick={continueRound}>
                  {roundResult.round_finished ? `进入 ${ROUND_NAMES[roundResult.round_no + 1] ?? '下一轮'} →` : '下一题 →'}
                </Button>
              </motion.div>
            )}
          </div>

          {/* 作答区 */}
          {!roundResult && (
            <div className="flex gap-2">
              <Input.TextArea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                rows={4}
                placeholder="组织你的回答：结论先行 → 术语支撑 → 例子佐证（试试 STAR 法则）"
              />
              <Button type="primary" loading={sending} onClick={submit} className="px-6 self-stretch glow-btn">
                提交回答
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
