import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { App, Button, Progress } from 'antd'
import { motion } from 'framer-motion'
import { api } from '../api/client'
import FavStar from '../components/FavStar'
import { useFavorites } from '../store/favorites'
import type { GameCard, GameStart, GameSubmitResult } from '../types'

/**
 * 知识小游戏：四种玩法共用一个壳。
 *
 * 共同约定：
 * - 顶部信息条：关卡名 / 玩法名 / 计时 / 进度
 * - 每种玩法自己算「可提交的数据」，通过 report(data) 交给壳存进 ref；
 *   时间到了由壳直接用最新数据提交，所以即使没做完也能算分（不会白玩）。
 * - 结算弹窗统一在这里渲染，玩法的对错反馈各管各的。
 *
 * 为什么配对关系在前端：连线和网格要「点下去立刻知道对错」，没有映射就没法即时反馈；
 * 判分仍以服务端复核为准（见 routers/games.py）。
 */

type Phase = 'loading' | 'play' | 'done'

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

/** 把 token 归到同一个 pair 上：左 token 直接取右值，右 token 反查左 key */
function pairIdOf(token: string, keys: Record<string, string>): string {
  if (keys[token]) return keys[token]
  const hit = Object.keys(keys).find((k) => keys[k] === token)
  return hit ?? token
}

function Stars({ n, size = 18 }: { n: number; size?: number }) {
  return (
    <span className="tracking-tight" style={{ fontSize: size }}>
      {[0, 1, 2].map((i) => (
        <span key={i} className={i < n ? 'text-amber-400' : 'text-slate-300'}>
          ★
        </span>
      ))}
    </span>
  )
}

/* ------------------------------------------------------------------ 连连看 */
function MatchBoard({
  left,
  right,
  keys,
  onReport,
  onDone,
  frozen,
}: {
  left: GameCard[]
  right: GameCard[]
  keys: Record<string, string>
  onReport: (d: unknown) => void
  onDone: () => void
  frozen: boolean
}) {
  const [pickL, setPickL] = useState<string | null>(null)
  const [pickR, setPickR] = useState<string | null>(null)
  const [matched, setMatched] = useState<Set<string>>(new Set())
  const [shake, setShake] = useState<string | null>(null)
  const doneRef = useRef(false)

  const pairs = useRef<{ l: string; r: string }[]>([])

  const settle = (l: string, r: string) => {
    const ok = keys[l] === r
    if (ok) {
      const next = new Set(matched).add(l).add(r)
      setMatched(next)
      pairs.current.push({ l, r })
      onReport({ pairs: pairs.current })
      if (next.size >= left.length + right.length && !doneRef.current) {
        doneRef.current = true
        void sleep(320).then(onDone)
      }
    } else {
      setShake(l)
      void sleep(360).then(() => setShake(null))
    }
    setPickL(null)
    setPickR(null)
  }

  const clickL = (k: string) => {
    if (frozen || matched.has(k)) return
    setPickL(k)
    if (pickR) settle(k, pickR)
  }
  const clickR = (k: string) => {
    if (frozen || matched.has(k)) return
    setPickR(k)
    if (pickL) settle(pickL, k)
  }

  return (
    <div className="grid grid-cols-2 gap-2.5">
      <div className="space-y-2">
        <div className="text-[11px] text-slate-400">术语</div>
        {left.map((c) => {
          const gone = matched.has(c.k)
          return (
            <button
              key={c.k}
              data-card={c.k}
              onClick={() => clickL(c.k)}
              className={`w-full rounded-xl border px-2.5 py-2.5 text-[13px] leading-snug text-left transition-all ${
                gone
                  ? 'border-emerald-200 bg-emerald-50 text-emerald-600 opacity-60'
                  : pickL === c.k
                    ? 'border-indigo-500 bg-indigo-50 text-indigo-800 ring-2 ring-indigo-200'
                    : 'border-slate-200 bg-white text-slate-700 active:bg-slate-50'
              } ${shake === c.k ? 'animate-bounce border-rose-400' : ''}`}
            >
              {c.text}
              {gone && <span className="ml-1">✓</span>}
            </button>
          )
        })}
      </div>
      <div className="space-y-2">
        <div className="text-[11px] text-slate-400">释义</div>
        {right.map((c) => {
          const gone = matched.has(c.k)
          return (
            <button
              key={c.k}
              data-card={c.k}
              onClick={() => clickR(c.k)}
              className={`w-full rounded-xl border px-2.5 py-2.5 text-[12px] leading-snug text-left transition-all ${
                gone
                  ? 'border-emerald-200 bg-emerald-50 text-emerald-600 opacity-60'
                  : pickR === c.k
                    ? 'border-indigo-500 bg-indigo-50 text-indigo-800 ring-2 ring-indigo-200'
                    : 'border-slate-200 bg-white text-slate-600 active:bg-slate-50'
              } ${shake === c.k ? 'animate-bounce border-rose-400' : ''}`}
            >
              {c.text}
              {gone && <span className="ml-1">✓</span>}
            </button>
          )
        })}
      </div>
    </div>
  )
}

/* -------------------------------------------------------------- 网格消除 */
function GridBoard({
  cards,
  keys,
  onReport,
  onDone,
  frozen,
}: {
  cards: GameCard[]
  keys: Record<string, string>
  onReport: (d: unknown) => void
  onDone: () => void
  frozen: boolean
}) {
  // 手机窄屏用 3 列，卡片宽一点、长释义不用在 85px 里挤成四行
  const [nCols] = useState(() =>
    typeof window !== 'undefined' && window.innerWidth < 430 ? 3 : 4,
  )
  // 纵向排布：消除后同列上方格子自动下落（用 flex 列天然实现）
  const [cols, setCols] = useState<GameCard[][]>(() => {
    const c: GameCard[][] = Array.from({ length: nCols }, () => [])
    cards.forEach((card, i) => c[i % nCols].push(card))
    return c
  })
  const [picked, setPicked] = useState<string[]>([])
  const [shake, setShake] = useState<string | null>(null)
  const pairs = useRef<{ l: string; r: string }[]>([])
  const doneRef = useRef(false)
  const totalPairs = cards.length / 2

  const click = (card: GameCard) => {
    if (frozen) return
    if (picked.includes(card.k)) {
      setPicked(picked.filter((k) => k !== card.k))
      return
    }
    const next = [...picked, card.k]
    setPicked(next)
    if (next.length < 2) return

    const [a, b] = next
    if (a !== b && pairIdOf(a, keys) === pairIdOf(b, keys)) {
      const l = keys[a] ? a : b
      const r = keys[a] ? b : a
      pairs.current.push({ l, r })
      onReport({ pairs: pairs.current })
      const rest = cols.map((col) => col.filter((c) => c.k !== a && c.k !== b))
      setCols(rest)
      setPicked([])
      const left = rest.reduce((acc, col) => acc + col.length, 0)
      if (left === 0 && !doneRef.current) {
        doneRef.current = true
        void sleep(320).then(onDone)
      }
    } else {
      setShake(b)
      void sleep(360).then(() => {
        setShake(null)
        setPicked([])
      })
    }
  }

  const matchedCount = (totalPairs * 2 - cols.reduce((a, c) => a + c.length, 0)) / 2

  return (
    <div>
      <div className="mb-2 text-[11px] text-slate-400">
        已消除 {matchedCount}/{totalPairs} 对
      </div>
      <div
        className="grid gap-1.5"
        style={{ gridTemplateColumns: `repeat(${nCols}, minmax(0, 1fr))` }}
      >
        {cols.map((col, ci) => (
          <div key={ci} className="flex flex-col gap-1.5">
            {col.map((c) => (
              <button
                key={c.k}
                data-card={c.k}
                onClick={() => click(c)}
                className={`rounded-lg border px-1 py-2 text-[11px] leading-snug transition-all ${
                  picked.includes(c.k)
                    ? 'border-indigo-500 bg-indigo-50 text-indigo-800 ring-2 ring-indigo-200'
                    : 'border-slate-200 bg-white text-slate-600 active:bg-slate-50'
                } ${shake === c.k ? 'animate-bounce border-rose-400' : ''}`}
                style={{ minHeight: 52 }}
              >
                {c.text}
              </button>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ 排序 */
function OrderBoard({
  steps,
  onReport,
  frozen,
}: {
  steps: GameCard[]
  onReport: (d: unknown) => void
  frozen: boolean
}) {
  const [list, setList] = useState<GameCard[]>(steps)

  const move = (i: number, dir: -1 | 1) => {
    if (frozen) return
    const j = i + dir
    if (j < 0 || j >= list.length) return
    const next = list.slice()
    ;[next[i], next[j]] = [next[j], next[i]]
    setList(next)
    onReport({ steps: next.map((s) => s.k) })
  }

  useEffect(() => {
    onReport({ steps: list.map((s) => s.k) })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="space-y-2">
      {list.map((s, i) => (
        <div
          key={s.k}
          className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-2.5 py-2"
        >
          <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-[11px] font-medium text-indigo-700">
            {i + 1}
          </span>
          <span className="min-w-0 flex-1 text-[12.5px] leading-snug text-slate-700">
            {s.text}
          </span>
          <span className="flex shrink-0 flex-col gap-0.5">
            <button
              onClick={() => move(i, -1)}
              disabled={i === 0 || frozen}
              className="rounded border border-slate-200 px-1.5 text-[10px] leading-4 text-slate-500 disabled:opacity-30"
            >
              ▲
            </button>
            <button
              onClick={() => move(i, 1)}
              disabled={i === list.length - 1 || frozen}
              className="rounded border border-slate-200 px-1.5 text-[10px] leading-4 text-slate-500 disabled:opacity-30"
            >
              ▼
            </button>
          </span>
        </div>
      ))}
    </div>
  )
}

/* ------------------------------------------------------------------ 竞速 */
function SpeedBoard({
  questions,
  onReport,
  onDone,
  frozen,
  favIds,
  toggleFav,
}: {
  questions: NonNullable<GameStart['payload']['questions']>
  onReport: (d: unknown) => void
  onDone: () => void
  frozen: boolean
  favIds: Set<number>
  toggleFav: (qid: number) => Promise<unknown>
}) {
  const [idx, setIdx] = useState(0)
  const [picked, setPicked] = useState<number | null>(null)
  const picks = useRef<{ qid: number; picked: number }[]>([])

  const q = questions[idx]
  if (!q) return <div className="py-10 text-center text-slate-400">题目已答完</div>
  const answered = picked !== null

  const choose = (i: number) => {
    if (answered || frozen) return
    setPicked(i)
    picks.current = [...picks.current, { qid: q.qid, picked: i }]
    onReport({ picks: picks.current })
  }

  const next = () => {
    if (idx + 1 >= questions.length) {
      onDone()
      return
    }
    setIdx(idx + 1)
    setPicked(null)
  }

  return (
    <div>
      <div className="mb-2 flex items-start gap-1">
        <div className="min-w-0 flex-1 text-[15px] leading-relaxed text-slate-800">
          <span className="mr-1 text-[11px] text-slate-400">
            {idx + 1}/{questions.length}
          </span>
          {q.stem}
        </div>
        <FavStar qid={q.qid} favored={favIds.has(q.qid)} onToggle={toggleFav} />
      </div>
      <div className="grid gap-2">
        {q.options.map((opt, i) => {
          let cls = 'border-slate-200 bg-white text-slate-700 active:bg-slate-50'
          if (answered) {
            if (i === q.correct_index) cls = 'border-emerald-400 bg-emerald-50 text-emerald-700'
            else if (i === picked) cls = 'border-rose-400 bg-rose-50 text-rose-700'
            else cls = 'border-slate-200 bg-white text-slate-400'
          }
          return (
            <button
              key={i}
              disabled={answered}
              onClick={() => choose(i)}
              className={`rounded-xl border px-3 py-2.5 text-left text-[13px] leading-snug transition-all ${cls}`}
            >
              <span className="mr-1.5 text-slate-400">{'ABCD'[i]}.</span>
              {opt}
            </button>
          )
        })}
      </div>
      {answered && (
        <div className="mt-3 rounded-xl border border-indigo-100 bg-indigo-50/60 p-2.5">
          <div
            className={`text-[12px] font-medium ${
              picked === q.correct_index ? 'text-emerald-600' : 'text-rose-600'
            }`}
          >
            {picked === q.correct_index
              ? '✅ 答对了'
              : `❌ 答错了，正确答案是 ${'ABCD'[q.correct_index]}`}
          </div>
          {q.explanation && (
            <div className="mt-1 text-[12px] leading-relaxed text-slate-600">
              {q.explanation}
            </div>
          )}
          <Button type="primary" size="small" className="mt-2" onClick={next}>
            {idx + 1 >= questions.length ? '看结果' : '下一题'}
          </Button>
        </div>
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ 主体 */
export default function Game() {
  const { levelCode = '' } = useParams()
  const navigate = useNavigate()
  const { message } = App.useApp()
  const { ids: favIds, toggle: toggleFav } = useFavorites()

  const [phase, setPhase] = useState<Phase>('loading')
  const [game, setGame] = useState<GameStart | null>(null)
  const [left, setLeft] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<GameSubmitResult | null>(null)

  const dataRef = useRef<unknown>({})
  const submitted = useRef(false)
  const startedAt = useRef(Date.now())

  const begin = useCallback(async () => {
    setPhase('loading')
    setResult(null)
    setSubmitting(false)
    submitted.current = false
    dataRef.current = {}
    startedAt.current = Date.now()
    try {
      const g = await api.post<GameStart>('/api/games/start', { level_code: levelCode })
      setGame(g)
      setLeft(g.time_limit)
      setPhase('play')
    } catch (e) {
      message.error((e as Error).message)
      navigate('/levels')
    }
  }, [levelCode, message, navigate])

  useEffect(() => {
    void begin()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [levelCode])

  const submit = useCallback(async () => {
    if (!game || submitted.current) return
    submitted.current = true
    setSubmitting(true)
    try {
      const elapsed = Math.round((Date.now() - startedAt.current) / 1000)
      const r = await api.post<GameSubmitResult>('/api/games/submit', {
        round_id: game.round_id,
        data: dataRef.current,
        elapsed,
      })
      setResult(r)
      setPhase('done')
    } catch (e) {
      message.error((e as Error).message)
      submitted.current = false
    } finally {
      setSubmitting(false)
    }
  }, [game, message])

  // 倒计时：归零自动交卷，别让人卡在那儿
  useEffect(() => {
    if (phase !== 'play') return
    const id = window.setInterval(() => {
      setLeft((s) => {
        if (s <= 1) {
          window.clearInterval(id)
          void submit()
          return 0
        }
        return s - 1
      })
    }, 1000)
    return () => window.clearInterval(id)
  }, [phase, submit])

  // 网格消除要把术语和释义交错混排：各自扎堆就变成左半屏术语、右半屏释义了。
  // ⚠️ 这个 useMemo 必须放在「加载中」的提前 return 之前 —— 放在后面会让
  // hooks 调用顺序随渲染变化，React 会直接报 "Rendered more hooks"。
  const gridCards = useMemo<GameCard[]>(() => {
    if (!game || game.mode !== 'grid') return []
    const l = game.payload.left || []
    const r = game.payload.right || []
    const all: GameCard[] = []
    for (let i = 0; i < Math.max(l.length, r.length); i += 1) {
      if (l[i]) all.push(l[i])
      if (r[i]) all.push(r[i])
    }
    return all
  }, [game])

  if (phase === 'loading' || !game) {
    return <div className="game-panel p-10 text-center text-slate-500">正在出题…</div>
  }

  const total = game.time_limit || 1
  const timePct = Math.max(0, Math.round((left / total) * 100))
  const mode = game.mode

  return (
    <div className="space-y-3">
      {/* 顶部信息条 */}
      <div className="game-panel p-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/levels')}
            className="shrink-0 text-[12px] text-slate-500 active:text-indigo-600"
          >
            ← 地图
          </button>
          <div className="min-w-0 flex-1">
            <div className="truncate text-[14px] font-semibold text-indigo-700">
              {game.mode_name} · {game.name}
            </div>
            <div className="truncate text-[11px] text-slate-400">{game.rule}</div>
          </div>
          <div className="shrink-0 text-right">
            <div
              className={`text-[15px] font-bold tabular-nums ${
                left <= 10 ? 'text-rose-600' : 'text-indigo-600'
              }`}
            >
              {left}s
            </div>
            <div className="text-[10px] text-slate-400">{game.subject}</div>
          </div>
        </div>
        <Progress
          percent={timePct}
          showInfo={false}
          size="small"
          strokeColor={left <= 10 ? '#f43f5e' : '#6366f1'}
          trailColor="#e2e8f0"
          className="mt-1"
        />
      </div>

      {/* 玩法主体 */}
      <div className="game-panel p-3">
        {mode === 'match' && (
          <>
            <div className="mb-2 text-[11px] text-slate-400">
              先点左边的术语，再点右边对应的释义；配错会抖一下但不扣分
            </div>
            <MatchBoard
              left={game.payload.left || []}
              right={game.payload.right || []}
              keys={game.payload.key || {}}
              onReport={(d) => (dataRef.current = d)}
              onDone={() => void submit()}
              frozen={submitting}
            />
          </>
        )}

        {mode === 'grid' && (
          <>
            <div className="mb-2 text-[11px] text-slate-400">
              点两个能配成一对的格子（术语 + 释义），配对成功即消除
            </div>
            <GridBoard
              cards={gridCards}
              keys={game.payload.key || {}}
              onReport={(d) => (dataRef.current = d)}
              onDone={() => void submit()}
              frozen={submitting}
            />
          </>
        )}

        {mode === 'order' && (
          <>
            <div className="mb-2 rounded-lg bg-indigo-50/70 px-2.5 py-1.5 text-[12px] text-indigo-800">
              {game.payload.title}
            </div>
            <OrderBoard
              steps={game.payload.steps || []}
              onReport={(d) => (dataRef.current = d)}
              frozen={submitting}
            />
            <Button
              type="primary"
              block
              className="mt-3"
              loading={submitting}
              onClick={() => void submit()}
            >
              提交顺序
            </Button>
          </>
        )}

        {mode === 'speed' && (
          <SpeedBoard
            questions={game.payload.questions || []}
            onReport={(d) => (dataRef.current = d)}
            onDone={() => void submit()}
            frozen={submitting}
            favIds={favIds}
            toggleFav={toggleFav}
          />
        )}
      </div>

      {/* 结算 */}
      {phase === 'done' && result && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            className="game-panel w-full max-w-md p-5 text-center"
          >
            <div className="text-4xl">{result.stars > 0 ? '🎉' : '😵'}</div>
            <div className="mt-1 text-lg font-bold text-indigo-800">
              {result.stars > 0 ? '通关！' : '没到 60%，再来一次'}
            </div>
            <div className="mt-1">
              <Stars n={result.stars} size={26} />
            </div>
            <div className="mt-2 text-[13px] text-slate-600">
              答对 {result.correct}/{result.total} · 正确率 {result.accuracy}%
            </div>
            {result.unlocked_next && (
              <div className="mt-1 text-[12px] text-emerald-600">🔓 已解锁下一关</div>
            )}
            {/* 排序题给逐条对错，方便复盘顺序 */}
            {mode === 'order' && result.detail.length > 0 && (
              <div className="mt-3 space-y-1 text-left">
                {result.detail.map((d, i) => (
                  <div key={d.key} className="flex items-center gap-1.5 text-[12px]">
                    <span className={d.correct ? 'text-emerald-600' : 'text-rose-500'}>
                      {d.correct ? '✓' : '✗'} 第 {i + 1} 步
                    </span>
                  </div>
                ))}
              </div>
            )}
            <div className="mt-4 flex gap-2">
              <Button block onClick={() => navigate('/levels')}>
                返回地图
              </Button>
              <Button block type="primary" onClick={() => void begin()}>
                再来一局
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}
