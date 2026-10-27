import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { App, Button, Modal, Progress } from 'antd'
import { api } from '../api/client'
import type { LevelItem, Scene } from '../types'

/**
 * 关卡地图：一条横版长卷，从左往右依次是 9 个章节。
 *
 * 布局是算出来的，不是切图：
 * - 每个关卡一个节点，x 按序号等距排开，y 用正弦波上下起伏，看起来才像山道；
 * - 章节之间插一条虚线 + 章节牌，滑到哪儿都知道自己在第几章；
 * - 连线逐段上色：上一关通关了就是绿色实线，否则灰虚线。
 *
 * 手机上横向滑动，进入时自动滚到「当前关」附近，省得同学们自己找。
 */

const NODE = 122 // 相邻节点的水平间距
const PAD = 76 // 左右留白
const HEIGHT = 320 // 卷轴高度
const BASE_Y = 150 // 波浪基线
const AMP = 62 // 起伏幅度

const MODE_ICON: Record<string, string> = {
  match: '🧩',
  grid: '🧱',
  order: '🔢',
  speed: '⚡',
}

const DIFF_COLORS = ['#34d399', '#a3e635', '#d97706', '#ea580c', '#dc2626']
const DIFF_LABELS = ['L1', 'L2', 'L3', 'L4', 'L5']

export default function LevelMap() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const [levels, setLevels] = useState<LevelItem[]>([])
  const [scenes, setScenes] = useState<Scene[]>([])
  const [refreshing, setRefreshing] = useState(false)
  const [picked, setPicked] = useState<LevelItem | null>(null)
  const scroller = useRef<HTMLDivElement>(null)
  const scrolled = useRef(false)

  const loadMap = useCallback(async () => {
    const d = await api.get<{ scenes: Scene[]; levels: LevelItem[] }>('/api/levels/map')
    setScenes(d.scenes)
    setLevels(d.levels)
  }, [])

  useEffect(() => {
    loadMap().catch((e) => message.error((e as Error).message))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadMap])

  // 节点坐标：x 等距，y 用正弦波起伏
  const nodes = useMemo(
    () =>
      levels.map((lv, i) => ({
        lv,
        x: PAD + i * NODE,
        y: BASE_Y + Math.sin(i * 0.95) * AMP,
      })),
    [levels],
  )

  const width = PAD * 2 + Math.max(0, levels.length - 1) * NODE
  const currentIdx = nodes.findIndex((n) => n.lv.status === 'unlocked')
  const doneCount = levels.filter((l) => l.completed).length
  const starCount = levels.reduce((a, l) => a + (l.best_score || 0), 0)

  // 进页面自动滚到当前关：手机上手动滑到第 12 关太费劲
  useEffect(() => {
    if (scrolled.current || !nodes.length || currentIdx < 0 || !scroller.current) return
    scrolled.current = true
    const box = scroller.current
    box.scrollLeft = Math.max(0, nodes[currentIdx].x - box.clientWidth / 2)
  }, [nodes, currentIdx])

  const locate = () => {
    if (!scroller.current) return
    const idx = currentIdx >= 0 ? currentIdx : nodes.length - 1
    if (idx < 0) return
    scroller.current.scrollTo({
      left: Math.max(0, nodes[idx].x - scroller.current.clientWidth / 2),
      behavior: 'smooth',
    })
  }

  // 点章节卡片：把卷轴滑到这一章的第一个节点
  const jumpScene = (si: number) => {
    if (!scroller.current) return
    const name = scenes[si]?.name
    const idx = nodes.findIndex((n) => n.lv.scene === name)
    if (idx < 0) return
    scroller.current.scrollTo({
      left: Math.max(0, nodes[idx].x - 40),
      behavior: 'smooth',
    })
  }

  const refresh = async () => {
    setRefreshing(true)
    try {
      await loadMap()
      message.success('已刷新')
    } catch (e) {
      message.error((e as Error).message)
    } finally {
      setRefreshing(false)
    }
  }

  // 章节分段：每个场景第一个节点的下标
  const chapters = useMemo(() => {
    const out: { scene: Scene; start: number; end: number }[] = []
    let idx = 0
    for (const s of scenes) {
      out.push({ scene: s, start: idx, end: idx + s.level_count - 1 })
      idx += s.level_count
    }
    return out
  }, [scenes])

  const openNode = (lv: LevelItem) => {
    if (lv.status === 'locked') {
      message.info('先通关前面的关卡才会解锁这里')
      return
    }
    setPicked(lv)
  }

  return (
    <div className="space-y-3">
      {/* 顶部进度 */}
      <div className="game-panel p-3">
        <div className="flex items-start gap-2">
          <div className="min-w-0 flex-1">
            <h1 className="text-[17px] font-bold text-indigo-700">🗺️ 冒险大陆</h1>
            <p className="mt-0.5 text-[11px] text-slate-500">
              从新手村一路向东，9 个章节 · {levels.length} 关 · 每关一个小游戏
            </p>
          </div>
          <div className="shrink-0 text-right">
            <div className="text-[13px] font-semibold text-emerald-600">
              {doneCount}
              <span className="text-[11px] font-normal text-slate-400">/{levels.length} 关</span>
            </div>
            <div className="text-[11px] text-amber-500">
              ★ {starCount}
              <span className="text-slate-300">/{levels.length * 3}</span>
            </div>
          </div>
        </div>
        <Progress
          percent={levels.length ? Math.round((doneCount / levels.length) * 100) : 0}
          size="small"
          showInfo={false}
          strokeColor={{ from: '#34d399', to: '#6366f1' }}
          trailColor="#e2e8f0"
          className="mt-2"
        />
      </div>

      {/* 横版卷轴 */}
      <div className="game-panel overflow-hidden p-0">
        <div className="flex items-center gap-2 border-b border-indigo-100 bg-indigo-50/50 px-3 py-1.5">
          <span className="text-[11px] text-slate-500">← 左右滑动浏览整张地图 →</span>
          <button
            onClick={locate}
            className="ml-auto shrink-0 rounded-full bg-white px-2 py-0.5 text-[11px] text-indigo-600 shadow-sm active:bg-indigo-50"
          >
            定位当前关
          </button>
        </div>

        <div ref={scroller} className="overflow-x-auto overflow-y-hidden">
          <div
            className="relative"
            style={{ width: Math.max(width, 320), height: HEIGHT }}
            data-map="1"
          >
            {/* 章节色带 + 章节牌 */}
            {chapters.map((c, ci) => {
              const x0 = PAD + c.start * NODE - NODE / 2
              const w = (c.end - c.start) * NODE + NODE
              const hue = ['#eef2ff', '#ecfdf5', '#fff7ed', '#f5f3ff', '#f0f9ff', '#fdf2f8', '#f8fafc', '#fefce8', '#f7fee7'][ci % 9]
              return (
                <div key={c.scene.name}>
                  <div
                    className="absolute top-0 bottom-0"
                    style={{ left: Math.max(0, x0), width: w, background: hue, opacity: 0.85 }}
                  />
                  <div
                    className="absolute top-2 whitespace-nowrap text-[10px] font-medium text-slate-400"
                    style={{ left: Math.max(6, x0 + 8) }}
                  >
                    {c.scene.icon} {c.scene.name} · {c.scene.completed_count}/{c.scene.level_count}
                  </div>
                </div>
              )
            })}

            {/* 连线：逐段判断上一关是否通关 */}
            <svg className="absolute inset-0" width={Math.max(width, 320)} height={HEIGHT}>
              {nodes.map((n, i) => {
                if (i === 0) return null
                const prev = nodes[i - 1]
                const passed = prev.lv.completed
                return (
                  <line
                    key={`l-${n.lv.code}`}
                    x1={prev.x}
                    y1={prev.y}
                    x2={n.x}
                    y2={n.y}
                    stroke={passed ? '#34d399' : '#cbd5e1'}
                    strokeWidth={passed ? 5 : 3}
                    strokeDasharray={passed ? undefined : '6 6'}
                    strokeLinecap="round"
                  />
                )
              })}
            </svg>

            {/* 节点 */}
            {nodes.map((n, i) => {
              const lv = n.lv
              const locked = lv.status === 'locked'
              const isCurrent = i === currentIdx
              return (
                <button
                  key={lv.code}
                  data-level={lv.code}
                  data-status={lv.status}
                  onClick={() => openNode(lv)}
                  className="absolute -translate-x-1/2 -translate-y-1/2"
                  style={{ left: n.x, top: n.y }}
                >
                  <span className="relative flex flex-col items-center">
                    {isCurrent && (
                      <span className="absolute -inset-2 animate-ping rounded-full bg-indigo-300/40" />
                    )}
                    <span
                      className={`relative flex h-14 w-14 items-center justify-center rounded-full border-2 text-2xl shadow-sm transition-transform active:scale-95 ${
                        locked
                          ? 'border-slate-200 bg-slate-100 opacity-70'
                          : lv.completed
                            ? 'border-emerald-400 bg-white'
                            : 'border-indigo-400 bg-white'
                      } ${isCurrent ? 'ring-4 ring-indigo-200' : ''}`}
                    >
                      {locked ? '🔒' : lv.icon}
                      {!locked && (
                        <span className="absolute -right-1 -top-1 rounded-full bg-white px-0.5 text-[9px] leading-4 shadow">
                          {MODE_ICON[lv.mode] || '🎮'}
                        </span>
                      )}
                    </span>
                    <span className="mt-1 w-20 truncate text-center text-[10px] text-slate-600">
                      {lv.name}
                    </span>
                    <span className="text-[9px] leading-none tracking-tighter">
                      {[0, 1, 2].map((s) => (
                        <span
                          key={s}
                          className={s < (lv.best_score || 0) ? 'text-amber-400' : 'text-slate-200'}
                        >
                          ★
                        </span>
                      ))}
                    </span>
                  </span>
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* 图例 */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 px-1 text-[10px] text-slate-400">
        <span>🧩 连连看</span>
        <span>🧱 网格消除</span>
        <span>🔢 排序</span>
        <span>⚡ 竞速</span>
        <span className="ml-auto">难度</span>
        {DIFF_LABELS.map((l, i) => (
          <span key={l} style={{ color: DIFF_COLORS[i] }}>
            {l}
          </span>
        ))}
        <Button size="small" loading={refreshing} onClick={refresh} className="ml-1">
          刷新
        </Button>
      </div>

      {/* 章节进度：9 个章节各走多少，点一下把地图滑到那一章 */}
      {scenes.length > 0 && (
        <div className="mt-1">
          <div className="mb-1.5 flex items-center px-1">
            <span className="text-[12px] font-medium text-slate-600">章节进度</span>
            <span className="ml-auto text-[11px] text-slate-400">点章节可跳到对应位置</span>
          </div>
          <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-3 lg:grid-cols-5">
            {scenes.map((s, si) => {
              const pct = s.level_count
                ? Math.round((s.completed_count / s.level_count) * 100)
                : 0
              const full = s.level_count > 0 && s.completed_count >= s.level_count
              return (
                <button
                  key={s.name}
                  onClick={() => jumpScene(si)}
                  data-scene={s.name}
                  className={`rounded-xl border px-2 py-1.5 text-left transition-colors active:bg-indigo-50 ${
                    full
                      ? 'border-emerald-200 bg-emerald-50/70'
                      : s.completed_count > 0
                        ? 'border-indigo-200 bg-indigo-50/60'
                        : 'border-slate-100 bg-white'
                  }`}
                >
                  <div className="flex items-center gap-1">
                    <span className="text-[13px]">{s.icon}</span>
                    <span className="truncate text-[11.5px] font-medium text-slate-700">
                      {s.name}
                    </span>
                  </div>
                  <div className="mt-0.5 flex items-center gap-1 text-[10px] text-slate-400">
                    <span>
                      {s.completed_count}/{s.level_count} 关
                    </span>
                    <span className="ml-auto text-amber-500">★{s.stars || 0}</span>
                  </div>
                  <div className="mt-1 h-1 overflow-hidden rounded-full bg-slate-200/70">
                    <div
                      className={`h-full rounded-full ${
                        full ? 'bg-emerald-400' : 'bg-indigo-400'
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {levels.length === 0 && (
        <div className="game-panel p-10 text-center text-slate-500">关卡加载中…</div>
      )}

      {/* 关卡详情：先选玩法再进 */}
      <Modal
        open={!!picked}
        onCancel={() => setPicked(null)}
        footer={null}
        width={380}
        title={picked ? `${picked.icon} ${picked.name}` : ''}
      >
        {picked && (
          <div className="space-y-3 pt-1">
            <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-slate-500">
                {picked.scene}
              </span>
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-slate-500">
                {picked.subject}
              </span>
              <span
                className="rounded-full px-2 py-0.5"
                style={{
                  background: `${DIFF_COLORS[picked.difficulty - 1]}22`,
                  color: DIFF_COLORS[picked.difficulty - 1],
                }}
              >
                {DIFF_LABELS[picked.difficulty - 1]}
              </span>
            </div>
            <div className="text-[12.5px] leading-relaxed text-slate-600">
              {picked.description}
            </div>
            <div className="flex items-center justify-between rounded-xl bg-amber-50 px-3 py-2">
              <span className="text-[12px] text-amber-700">
                {MODE_ICON[picked.mode]} {picked.mode_name}
              </span>
              <span className="text-[14px] leading-none tracking-tight">
                {[0, 1, 2].map((s) => (
                  <span
                    key={s}
                    className={s < (picked.best_score || 0) ? 'text-amber-400' : 'text-amber-200'}
                  >
                    ★
                  </span>
                ))}
              </span>
            </div>
            <div className="flex gap-2">
              <Button
                block
                onClick={() => {
                  const code = picked.code
                  setPicked(null)
                  navigate(`/quest/${code}`)
                }}
              >
                刷题模式
              </Button>
              <Button
                block
                type="primary"
                className="glow-btn"
                onClick={() => {
                  const code = picked.code
                  setPicked(null)
                  navigate(`/game/${code}`)
                }}
              >
                开始挑战
              </Button>
            </div>
            <div className="text-center text-[10px] leading-relaxed text-slate-400">
              「刷题模式」是 10 道题的答题闯关，可以用来熟悉这关的知识点
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
