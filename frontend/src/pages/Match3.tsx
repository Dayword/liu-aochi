import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { App, Button, Progress } from 'antd'
import { api } from '../api/client'
import { useAuth } from '../store/auth'
import type {
  Match3AnswerResult,
  Match3CompleteResult,
  Match3Question,
  Match3Start,
} from '../types'
import {
  type Board,
  collapse,
  createBoard,
  hasValidMove,
  isAdjacent,
  resolveOnce,
  shuffleBoard,
  trySwap,
} from '../game/match3'
import { MAX_LIVES, formatCountdown, useLives } from '../game/lives'

const GEMS = [
  { color: '#ef4444', emoji: '🍎' },
  { color: '#3b82f6', emoji: '💧' },
  { color: '#22c55e', emoji: '🍀' },
  { color: '#eab308', emoji: '⭐' },
  { color: '#a855f7', emoji: '🔮' },
  { color: '#f97316', emoji: '🔥' },
]
const SPECIAL_BADGE: Record<string, string> = { 'line-h': '↔', 'line-v': '↕', bird: '🌈' }
const BONUS_MOVES = 5
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))
const cellKey = (r: number, c: number) => `${r},${c}`

type Phase = 'loading' | 'play' | 'quiz' | 'won' | 'failed' | 'nolife'

export default function Match3() {
  const { levelCode = '' } = useParams()
  const navigate = useNavigate()
  const { message } = App.useApp()
  const { refreshCharacter } = useAuth()
  const { lives, nextInMs, consume } = useLives()

  const [phase, setPhase] = useState<Phase>('loading')
  const [config, setConfig] = useState<Match3Start | null>(null)
  const [board, setBoard] = useState<Board>([])
  const [score, setScore] = useState(0)
  const [movesLeft, setMovesLeft] = useState(0)
  const [selected, setSelected] = useState<[number, number] | null>(null)
  const [clearing, setClearing] = useState<Set<string>>(new Set())
  const [shake, setShake] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [combo, setCombo] = useState(0)

  const [question, setQuestion] = useState<Match3Question | null>(null)
  const [questionLoading, setQuestionLoading] = useState(false)
  const [picked, setPicked] = useState(-1)
  const [answerResult, setAnswerResult] = useState<Match3AnswerResult | null>(null)
  const [result, setResult] = useState<Match3CompleteResult | null>(null)

  const scoreRef = useRef(0)
  const qCache = useRef<Match3Question | null>(null)
  const qFetching = useRef(false)
  const alive = useRef(true)

  useEffect(() => {
    alive.current = true
    return () => {
      alive.current = false
    }
  }, [])

  const addScore = (n: number) => {
    scoreRef.current += n
    setScore(scoreRef.current)
  }

  /** 提前备好一道题：失败时立刻就能答，不用干等模型 */
  const prefetchQuestion = useCallback(
    async (code: string) => {
      if (qCache.current || qFetching.current) return
      qFetching.current = true
      try {
        qCache.current = await api.get<Match3Question>(
          `/api/games/match3/question?level_code=${code}`,
        )
      } catch {
        /* 失败就等用时再拉一次 */
      } finally {
        qFetching.current = false
      }
    },
    [],
  )

  /**
   * 取一道题：优先用预取好的；预取还没回来时最多等 6 秒，
   * 超时就用题库快速兜底 —— 不能让玩家盯着加载动画等模型思考 30 秒。
   * （AI 那道仍会在后台完成并缓存，留给下一次用。）
   */
  const takeQuestion = async (code: string): Promise<Match3Question | null> => {
    void prefetchQuestion(code)
    for (let i = 0; i < 12; i++) {
      if (qCache.current) {
        const q = qCache.current
        qCache.current = null
        void prefetchQuestion(code)
        return q
      }
      await sleep(500)
      if (!alive.current) return null
    }
    try {
      return await api.get<Match3Question>(
        `/api/games/match3/question?level_code=${code}&fast=1`,
      )
    } catch {
      return null
    }
  }

  const startLevel = useCallback(
    async (cfg: Match3Start) => {
      scoreRef.current = 0
      setScore(0)
      setBoard(createBoard(cfg.rows, cfg.cols, cfg.gem_types))
      setMovesLeft(cfg.moves)
      setSelected(null)
      setClearing(new Set())
      setCombo(0)
      setQuestion(null)
      setAnswerResult(null)
      setPicked(-1)
      setResult(null)
      setBusy(false)
      setPhase('play')
      void prefetchQuestion(cfg.level_code)
    },
    [prefetchQuestion],
  )

  useEffect(() => {
    if (!levelCode) return
    setPhase('loading')
    api
      .post<Match3Start>('/api/games/match3/start', { level_code: levelCode })
      .then((cfg) => {
        if (!alive.current) return
        setConfig(cfg)
        if (lives <= 0) {
          setPhase('nolife')
          return
        }
        void startLevel(cfg)
      })
      .catch((e) => {
        if (alive.current) message.error((e as Error).message)
      })
    // lives 只在首次进入时用于判断，后续变化不应重新拉关
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [levelCode])

  // ---------------------------------------------------------------- 游戏流程

  const settle = useCallback(
    async (finalScore: number) => {
      if (!config) return
      try {
        const res = await api.post<Match3CompleteResult>('/api/games/match3/complete', {
          level_code: config.level_code,
          score: finalScore,
          moves_used: config.moves,
        })
        if (!alive.current) return
        setResult(res)
        void refreshCharacter()
        if (res.completed) {
          setPhase('won')
        } else {
          setPhase('quiz')
          setQuestionLoading(true)
          const q = await takeQuestion(config.level_code)
          if (!alive.current) return
          setQuestion(q)
          setQuestionLoading(false)
        }
      } catch (e) {
        if (alive.current) message.error((e as Error).message)
      }
    },
    [config, refreshCharacter, prefetchQuestion, message],
  )

  /** 反复消除直到没有新的消除为止，同时逐步播放动画 */
  const runCascade = useCallback(
    async (from: Board) => {
      if (!config) return
      let cur = from
      let steps = 0
      for (;;) {
        const res = resolveOnce(cur)
        if (!res) break
        steps++
        setCombo(steps)
        setClearing(new Set(res.clearedCells.map(([r, c]) => cellKey(r, c))))
        await sleep(230)
        if (!alive.current) return
        addScore(res.cleared * 10 * steps) // 连击倍率是这类游戏的主要爽点
        cur = collapse(res.board, config.gem_types)
        setClearing(new Set())
        setBoard(cur)
        await sleep(190)
        if (!alive.current) return
      }
      setCombo(0)
      if (!hasValidMove(cur)) {
        setBoard(shuffleBoard(cur))
        message.info('没有可消除的组合了，已自动重排')
      }
      const left = movesLeft - 1
      setMovesLeft(left)
      if (left <= 0) await settle(scoreRef.current)
    },
    // movesLeft 每次都是最新值，由调用时闭包捕获
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [config, movesLeft, settle, message],
  )

  const attemptSwap = useCallback(
    async (a: [number, number], b: [number, number]) => {
      setBusy(true)
      const swapped = trySwap(board, a, b)
      if (!swapped) {
        setShake(cellKey(b[0], b[1]))
        await sleep(320)
        setShake(null)
        if (alive.current) setBusy(false)
        return
      }
      setBoard(swapped)
      await sleep(170)
      if (!alive.current) return
      await runCascade(swapped)
      if (alive.current) setBusy(false)
    },
    [board, runCascade],
  )

  const onCellClick = (r: number, c: number) => {
    if (busy || phase !== 'play') return
    if (!selected) {
      setSelected([r, c])
      return
    }
    if (selected[0] === r && selected[1] === c) {
      setSelected(null)
      return
    }
    if (!isAdjacent(selected, [r, c])) {
      setSelected([r, c])
      return
    }
    const from = selected
    setSelected(null)
    void attemptSwap(from, [r, c])
  }

  const submitAnswer = async () => {
    if (!question || picked < 0) return
    try {
      const res = await api.post<Match3AnswerResult>('/api/games/match3/answer', {
        question_id: question.question_id,
        answer_index: picked,
      })
      if (!alive.current) return
      setAnswerResult(res)
      if (res.correct) {
        message.success(`答对了！奖励 ${BONUS_MOVES} 步继续挑战`)
        await sleep(1800)
        if (!alive.current) return
        setMovesLeft((m) => m + BONUS_MOVES)
        setQuestion(null)
        setAnswerResult(null)
        setPicked(-1)
        setPhase('play')
      } else {
        consume() // 答错扣一颗生命
      }
    } catch (e) {
      if (alive.current) message.error((e as Error).message)
    }
  }

  const retryAfterWrong = () => {
    if (lives <= 0) return
    if (config) void startLevel(config)
  }

  // ---------------------------------------------------------------- 渲染

  if (phase === 'loading') {
    return (
      <div className="game-panel p-10 text-center text-slate-500">关卡加载中…</div>
    )
  }

  if (phase === 'nolife') {
    return (
      <div className="game-panel p-10 text-center space-y-4">
        <div className="text-5xl">💔</div>
        <div className="text-lg text-slate-700">生命值用完了</div>
        <p className="text-slate-500 text-sm">
          每 1 分钟恢复 1 颗，下一颗还有{' '}
          <span className="text-amber-600 font-mono">{formatCountdown(nextInMs)}</span>
        </p>
        <div className="flex gap-2 justify-center">
          <Button onClick={() => navigate('/levels')}>返回地图</Button>
          <Button type="primary" onClick={() => lives > 0 && config && startLevel(config)}>
            刷新状态
          </Button>
        </div>
      </div>
    )
  }

  const pct = config ? Math.min(100, Math.round((score / config.target_score) * 100)) : 0
  const reached = config ? score >= config.target_score : false

  return (
    <div className="space-y-4">
      {/* 顶部信息条 */}
      <div className="game-panel p-4 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-indigo-700">🍬 {config?.name}</h1>
          <p className="text-slate-500 text-xs mt-0.5">
            {config?.subject} · 消消乐闯关
            {reached && <span className="ml-2 text-emerald-600">✓ 已达标，继续冲高分</span>}
          </p>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <div className="text-center">
            <div className="text-slate-500 text-[11px]">剩余步数</div>
            <div className={`text-xl font-bold ${movesLeft <= 5 ? 'text-rose-600' : 'text-indigo-700'}`}>
              {movesLeft}
            </div>
          </div>
          <div className="text-center">
            <div className="text-slate-500 text-[11px]">得分 / 目标</div>
            <div className="text-xl font-bold text-amber-600">
              {score}
              <span className="text-slate-500 text-sm"> / {config?.target_score}</span>
            </div>
          </div>
          <div className="text-center">
            <div className="text-slate-500 text-[11px]">生命值</div>
            <div className="text-lg">
              {'❤️'.repeat(Math.min(lives, MAX_LIVES))}
              <span className="text-slate-400">
                {'🖤'.repeat(Math.max(0, MAX_LIVES - lives))}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-4 items-start">
        {/* 棋盘 */}
        <div className="game-panel p-3">
          <div
            data-board="1"
            className="grid gap-1.5"
            style={{
              gridTemplateColumns: `repeat(${config?.cols ?? 8}, minmax(0, 1fr))`,
              width: 'min(88vw, 440px)',
            }}
          >
            {board.map((row, r) =>
              row.map((cell, c) => {
                const k = cellKey(r, c)
                const isSel = selected?.[0] === r && selected?.[1] === c
                const isClearing = clearing.has(k)
                const isShake = shake === k
                const gem = cell ? GEMS[cell.type % GEMS.length] : null
                return (
                  <button
                    key={cell?.id ?? k}
                    data-cell={`${r},${c}`}
                    data-gem={gem?.emoji ?? ''}
                    onClick={() => onCellClick(r, c)}
                    disabled={busy || phase !== 'play'}
                    className={`relative aspect-square rounded-xl flex items-center justify-center text-2xl
                      transition-all duration-200 select-none
                      ${isClearing ? 'scale-0 opacity-0' : 'scale-100 opacity-100'}
                      ${isSel ? 'ring-2 ring-indigo-500 z-10' : ''}
                      ${isShake ? 'animate-bounce' : ''}`}
                    style={{
                      background: gem
                        ? `linear-gradient(145deg, ${gem.color}dd, ${gem.color}66)`
                        : '#ffffff',
                      boxShadow: isSel ? `0 0 0 2px ${gem?.color}` : undefined,
                    }}
                  >
                    <span>{gem?.emoji}</span>
                    {cell && cell.special !== 'none' && (
                      <span className="absolute -top-1 -right-1 text-[10px] bg-black/60 rounded px-1">
                        {SPECIAL_BADGE[cell.special]}
                      </span>
                    )}
                  </button>
                )
              }),
            )}
          </div>
          <div className="mt-3">
            <Progress
              percent={pct}
              size="small"
              strokeColor={reached ? '#34d399' : '#d97706'}
              trailColor="#e2e8f0"
              format={() => (reached ? '已达标' : `${pct}%`)}
            />
          </div>
        </div>

        {/* 侧边说明 */}
        <div className="game-panel p-4 text-sm text-slate-600 space-y-3 w-full lg:w-72">
          <div className="font-medium text-indigo-700">玩法</div>
          <ul className="list-disc pl-4 space-y-1 text-xs text-slate-500">
            <li>点击相邻两颗宝石交换，凑齐 3 颗同色即可消除</li>
            <li>4 连生成 <span className="text-indigo-600">直线宝石 ↔↕</span>，消除整行或整列</li>
            <li>5 连生成 <span className="text-indigo-600">魔力鸟 🌈</span>，清空全场同色</li>
            <li>连续消除有连击加成，分数翻倍</li>
          </ul>
          <div className="border-t border-slate-200 pt-3 text-xs text-slate-500 space-y-1">
            <div>步数用尽仍未达标 → 触发知识问答</div>
            <div>
              答对 <span className="text-emerald-600">奖励 {BONUS_MOVES} 步</span>
            </div>
            <div>
              答错 <span className="text-rose-600">扣 1 颗生命值</span>
            </div>
            <div>生命值上限 {MAX_LIVES} 颗，每 1 分钟恢复 1 颗</div>
          </div>
          <Button block onClick={() => navigate('/levels')}>
            返回地图
          </Button>
        </div>
      </div>

      {/* 连击提示 */}
      {combo > 1 && (
        <div className="fixed left-1/2 top-1/3 -translate-x-1/2 text-4xl font-black text-amber-600 drop-shadow-lg pointer-events-none">
          {combo} 连击！
        </div>
      )}

      {/* 失败答题弹窗 */}
      {phase === 'quiz' && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="game-panel p-6 w-full max-w-lg space-y-4">
            <div className="text-center">
              <div className="text-4xl">😵</div>
              <div className="text-lg font-bold text-rose-700 mt-1">步数用尽，未达目标</div>
              <p className="text-slate-500 text-xs">
                得分 {score} / {config?.target_score} —— 答对下面这题就能获得 {BONUS_MOVES} 步继续挑战
              </p>
            </div>

            {questionLoading || !question ? (
              <div className="py-8 text-center text-slate-500 text-sm">
                正在生成题目<span className="animate-pulse">…</span>
              </div>
            ) : (
              <>
                <div className="text-sm text-slate-800">{question.stem}</div>
                <div className="grid gap-2">
                  {question.options.map((opt, i) => {
                    let cls = 'border-indigo-200 text-slate-600 hover:border-indigo-400/60'
                    if (answerResult) {
                      if (i === answerResult.correct_index)
                        cls = 'border-emerald-500 bg-emerald-50 text-emerald-700'
                      else if (i === picked) cls = 'border-rose-400 bg-rose-50 text-rose-700'
                      else cls = 'border-indigo-200 text-slate-500'
                    } else if (i === picked) {
                      cls = 'border-indigo-400 bg-indigo-100 text-indigo-800'
                    }
                    return (
                      <button
                        key={i}
                        disabled={!!answerResult}
                        onClick={() => setPicked(i)}
                        className={`text-left px-3 py-2 rounded-xl border text-sm transition-all ${cls}`}
                      >
                        <span className="text-slate-500 mr-1.5">
                          {'ABCD'[i]}.
                        </span>
                        {opt}
                      </button>
                    )
                  })}
                </div>

                {answerResult && (
                  <div className="text-xs">
                    <span className={answerResult.correct ? 'text-emerald-600' : 'text-rose-600'}>
                      {answerResult.correct
                        ? '✅ 回答正确'
                        : `❌ 回答错误，正确答案是 ${'ABCD'[answerResult.correct_index]}`}
                    </span>
                    <div className="text-slate-600 mt-1 leading-relaxed">
                      <span className="text-indigo-600">解析：</span>
                      {answerResult.explanation}
                    </div>
                  </div>
                )}

                {!answerResult ? (
                  <Button block type="primary" disabled={picked < 0} onClick={submitAnswer}>
                    提交答案
                  </Button>
                ) : (
                  <div className="space-y-2">
                    {answerResult.correct ? null : lives > 0 ? (
                      <>
                        <div className="text-center text-xs text-rose-600">
                          已扣 1 颗生命值，剩余 {lives} 颗
                        </div>
                        <Button block type="primary" onClick={retryAfterWrong}>
                          重新挑战本关
                        </Button>
                      </>
                    ) : (
                      <div className="text-center text-xs text-rose-600">
                        生命值已耗尽，下一颗还需 {formatCountdown(nextInMs)}
                      </div>
                    )}
                    <Button block onClick={() => navigate('/levels')}>
                      返回地图
                    </Button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {/* 通关弹窗 */}
      {phase === 'won' && result && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="game-panel p-6 w-full max-w-md text-center space-y-3">
            <div className="text-5xl">🎉</div>
            <div className="text-xl font-bold text-emerald-700">闯关成功！</div>
            <p className="text-slate-600 text-sm">
              最终得分 <span className="text-amber-600 font-bold">{score}</span> / 目标{' '}
              {config?.target_score}
            </p>
            <div className="flex justify-center gap-4 text-sm text-slate-700">
              <span>⚡ +{result.exp_gained} EXP</span>
              <span>🪙 +{result.coins_gained}</span>
            </div>
            {result.unlocked_next && (
              <div className="text-xs text-indigo-600">🔓 已解锁新关卡</div>
            )}
            <div className="flex gap-2 pt-2">
              <Button block onClick={() => navigate('/levels')}>
                返回地图
              </Button>
              <Button block type="primary" onClick={() => config && startLevel(config)}>
                再玩一次
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
