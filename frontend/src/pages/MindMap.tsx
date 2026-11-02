import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { App, Input, Spin, Tooltip } from 'antd'
import { api } from '../api/client'
import type { MindMapSubject } from '../types'

/**
 * 面试知识地图：每个科目一棵向右生长的逻辑图。
 *
 * 为什么是「科目 → 考察维度 → 知识点」三级而不是照抄课程章节：
 * 课程的 stage 是教学顺序，面试官脑子里的结构是另一套。按课程生成出来的图
 * 只是目录换了个画法，学生看不出「这题会怎么问」。
 *
 * 布局是两趟遍历：先把叶子按顺序铺开（cursor 累加），再让父节点落在
 * 首末子节点的垂直中点上。这样父子连线不会交叉，也不用引入力导向。
 */

/** 三列的左边界。写死是为了 12 棵树纵向对齐，切科目时眼睛不用重新适应。 */
const COL_X = [0, 208, 440]
const ROOT_W = 152
const ROOT_H = 54
const BRANCH_W = 186
const BRANCH_H = 40
const LEAF_W = 264
const LEAF_MIN_H = 30
const V_GAP = 7
const GROUP_GAP = 17
const CANVAS_PAD = 36

const ROOT_FS = 15
const BRANCH_FS = 13
const LEAF_FS = 13
const LEAF_LH = 19

/** 每个一级分支一个色系，连线、边框、底色都取自这里 —— 靠颜色就能追踪归属。 */
const PALETTE = [
  { line: '#6366f1', bg: '#eef2ff', bd: '#c7d2fe', fg: '#4338ca' },
  { line: '#0ea5e9', bg: '#e0f2fe', bd: '#bae6fd', fg: '#0369a1' },
  { line: '#10b981', bg: '#d1fae5', bd: '#a7f3d0', fg: '#047857' },
  { line: '#f59e0b', bg: '#fef3c7', bd: '#fde68a', fg: '#b45309' },
  { line: '#ec4899', bg: '#fce7f3', bd: '#fbcfe8', fg: '#be185d' },
  { line: '#8b5cf6', bg: '#ede9fe', bd: '#ddd6fe', fg: '#6d28d9' },
  { line: '#14b8a6', bg: '#ccfbf1', bd: '#99f6e4', fg: '#0f766e' },
  { line: '#f97316', bg: '#ffedd5', bd: '#fed7aa', fg: '#c2410c' },
]

const HOT_COLOR: Record<number, string> = { 3: '#ef4444', 2: '#f59e0b', 1: '#cbd5e1' }

/** 中英混排宽度估算：汉字按全宽，英文数字按 0.56。只用来自适应叶子高度。 */
function textW(s: string, fs: number) {
  let w = 0
  for (const ch of s) {
    w += /[\u3000-\u9fff\uff00-\uffef]/.test(ch) ? fs : fs * 0.56
  }
  return w
}

function leafH(name: string) {
  const inner = LEAF_W - 30
  const lines = Math.max(1, Math.ceil(textW(name, LEAF_FS) / inner))
  return Math.max(LEAF_MIN_H, lines * LEAF_LH + 12)
}

interface MNode {
  id: string
  label: string
  depth: 0 | 1 | 2
  code?: string | null
  hot: number
  lesson: string
  status: string
  color: number
  /** 1 = 挂在根的右侧，-1 = 左侧。单列时全是 1。 */
  side: 1 | -1
  children: MNode[]
  collapsed: boolean
  w: number
  h: number
  x: number
  y: number
}

function buildTree(subject: MindMapSubject, collapsed: Set<string>): MNode {
  const root: MNode = {
    id: 'root', label: subject.subject, depth: 0, hot: 3, lesson: '', status: 'unlocked', color: 0, side: 1,
    children: [], collapsed: collapsed.has('root'),
    w: ROOT_W, h: ROOT_H, x: 0, y: 0,
  }
  subject.branches.forEach((b, bi) => {
    const bid = `b${bi}`
    const branch: MNode = {
      id: bid, label: b.name, depth: 1, hot: 3, lesson: '', status: 'unlocked', color: bi % PALETTE.length, side: 1,
      children: [], collapsed: collapsed.has(bid),
      w: BRANCH_W, h: BRANCH_H, x: 0, y: 0,
    }
    b.items.forEach((it, ii) => {
      branch.children.push({
        id: `${bid}-${ii}`, label: it.name, depth: 2, hot: it.hot,
        code: it.code ?? null, lesson: it.lesson_title || '',
        status: it.status || 'unlocked',
        color: bi % PALETTE.length, side: 1,
        children: [], collapsed: false,
        w: LEAF_W, h: leafH(it.name), x: 0, y: 0,
      })
    })
    root.children.push(branch)
  })
  return root
}

/** 双列时右侧各层的左边界；左侧镜像过去，所以不用再写一套。 */
const COL_X2 = [0, 124, 354]

/**
 * 铺位置，返回整幅图的高度。
 *
 * twoSided=true 时根节点居中、前半分支挂右、后半挂左 —— 这是横屏唯一的正解：
 * 树的高度才是瓶颈，单纯把画布 rotate 90° 只会更小（实测 0.185 → 0.103），
 * 必须让树自己变矮变宽，左右分挂能把高度直接砍一半。
 */
function placeTree(root: MNode, twoSided = false, tight = false): number {
  const groupGap = tight ? 9 : GROUP_GAP
  const vGap = tight ? 4 : V_GAP

  const colX = (n: MNode) => {
    if (!twoSided) return COL_X[n.depth]
    if (n.depth === 0) return -ROOT_W / 2
    const base = COL_X2[n.depth]
    return n.side > 0 ? base : -(base + n.w)
  }

  const walk = (n: MNode, side: 1 | -1, cursor: { v: number }) => {
    n.side = side
    n.x = colX(n)
    const kids = n.collapsed ? [] : n.children
    if (!kids.length) {
      n.y = cursor.v + n.h / 2
      cursor.v += n.h + (n.depth === 2 ? vGap : groupGap)
      return
    }
    kids.forEach((k) => walk(k, side, cursor))
    const top = kids[0].y - kids[0].h / 2
    const last = kids[kids.length - 1]
    n.y = (top + last.y + last.h / 2) / 2
  }

  if (!twoSided || root.collapsed) {
    const cursor = { v: 0 }
    walk(root, 1, cursor)
    return cursor.v
  }

  const mid = Math.ceil(root.children.length / 2)
  const right = root.children.slice(0, mid)
  const left = root.children.slice(mid)

  const cr = { v: 0 }
  right.forEach((b) => walk(b, 1, cr))
  const cl = { v: 0 }
  left.forEach((b) => walk(b, -1, cl))

  const maxH = Math.max(cr.v, cl.v)
  // 两侧各自居中，否则会出现一边顶到天花板、一边悬在中间
  const shift = (list: MNode[], dy: number) => {
    const rec = (n: MNode) => {
      n.y += dy
      if (!n.collapsed) n.children.forEach(rec)
    }
    list.forEach(rec)
  }
  shift(right, (maxH - cr.v) / 2)
  shift(left, (maxH - cl.v) / 2)

  root.side = 1
  root.x = -ROOT_W / 2
  root.y = maxH / 2
  return maxH
}

function collect(root: MNode) {
  const nodes: MNode[] = []
  const edges: Array<[MNode, MNode]> = []
  const walk = (n: MNode) => {
    nodes.push(n)
    if (!n.collapsed) {
      n.children.forEach((c) => {
        edges.push([n, c])
        walk(c)
      })
    }
  }
  walk(root)
  return { nodes, edges }
}

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v))

/**
 * 画布：布局、缩放、拖拽、节点渲染都在这里。
 * 主页面和「手机横屏」全屏层各用一个实例，互不干扰（各自持有缩放状态）。
 *
 * 布局方向由画布本身的高宽决定：内容比画布高 1.5 倍以上就自动改成左右双翼。
 * 手机横过来后可视区变成 804×390，双列能把 k 从 0.185 拉到 1.1。
 */
function GraphCanvas({
  subject, collapsed, matches, onNode, compact = false,
}: {
  subject: MindMapSubject
  collapsed: Set<string>
  matches: Set<string>
  onNode: (n: MNode) => void
  compact?: boolean
}) {
  const boxRef = useRef<HTMLDivElement>(null)
  const [view, setView] = useState({ k: 1, tx: 0, ty: 0 })
  const [box, setBox] = useState({ w: 0, h: 0 })
  const drag = useRef<{ x: number; y: number; tx: number; ty: number } | null>(null)
  const moved = useRef(false)
  const pending = useRef<MNode | null>(null)
  // 双指捏合：记住两根手指的起始距离与中心，移动时按比例改 k 并跟随中心平移
  const pts = useRef<Map<number, { x: number; y: number }>>(new Map())
  const pinch = useRef<
    { d: number; cx: number; cy: number; k: number; tx: number; ty: number } | null
  >(null)

  const graph = useMemo(() => {
    // 先按单列铺一遍量高度：只有「一屏塞不下」才值得分左右两翼。
    // 桌面折叠态本来就放得下，硬分列会让 k 从 1.09 掉到 0.86，反而更小。
    const one = buildTree(subject, collapsed)
    const oneH = placeTree(one, false, compact)
    const needTwo = box.h > 0 && oneH > box.h * 1.5 && one.children.length >= 4
    if (!needTwo) return { ...collect(one), two: false }
    const two = buildTree(subject, collapsed)
    placeTree(two, true, compact)
    return { ...collect(two), two: true }
  }, [subject, collapsed, box.h, compact])

  const { nodes, edges } = graph

  // 横屏全屏时画布本身就很挤，边距再按 36 留会把 k 吃掉两成
  const pad = compact ? 16 : CANVAS_PAD

  // 按「当前可见节点的真实包围盒」定中心，否则折叠到分支时整棵树会贴左、右侧空一大片
  const bounds = useMemo(() => {
    if (!nodes.length) return { minX: 0, minY: 0, maxX: COL_X[2] + LEAF_W, maxY: 1 }
    let minX = Infinity
    let minY = Infinity
    let maxX = -Infinity
    let maxY = -Infinity
    for (const n of nodes) {
      minX = Math.min(minX, n.x)
      minY = Math.min(minY, n.y - n.h / 2)
      maxX = Math.max(maxX, n.x + n.w)
      maxY = Math.max(maxY, n.y + n.h / 2)
    }
    return { minX, minY, maxX, maxY }
  }, [nodes])

  const viewW = bounds.maxX - bounds.minX + pad * 2
  const viewH = bounds.maxY - bounds.minY + pad * 2

  const fit = useCallback(() => {
    if (!box.w || !box.h) return
    // 下限放到 0.05：手机横屏时可视高度只有 ~390，Python 全展开要 k≈0.10 才装得下
    const k = clamp(Math.min((box.w - 12) / viewW, (box.h - 12) / viewH), 0.05, 1.6)
    setView({
      k,
      tx: (box.w - viewW * k) / 2 - (bounds.minX - pad) * k,
      ty: (box.h - viewH * k) / 2 - (bounds.minY - pad) * k,
    })
  }, [box.w, box.h, viewW, viewH, bounds, pad])

  useLayoutEffect(() => {
    const el = boxRef.current
    if (!el) return
    const sync = () => setBox({ w: el.clientWidth, h: el.clientHeight })
    sync()
    const ro = new ResizeObserver(sync)
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  // 折叠/展开/切科目都会换一批节点，换完就重新铺满
  useEffect(() => { fit() }, [fit, nodes])

  // React 的 onWheel 是 passive 的，preventDefault 会被忽略，只能手动绑
  useEffect(() => {
    const el = boxRef.current
    if (!el) return
    const onWheel = (e: WheelEvent) => {
      e.preventDefault()
      const rect = el.getBoundingClientRect()
      const mx = e.clientX - rect.left
      const my = e.clientY - rect.top
      setView((v) => {
        const k = clamp(v.k * Math.exp(-e.deltaY * 0.0016), 0.05, 3)
        const r = k / v.k
        return { k, tx: mx - (mx - v.tx) * r, ty: my - (my - v.ty) * r }
      })
    }
    el.addEventListener('wheel', onWheel, { passive: false })
    return () => el.removeEventListener('wheel', onWheel)
  }, [])

  return (
    <div
      ref={boxRef}
      data-canvas="1"
      className="relative w-full h-full rounded-2xl border border-slate-200 bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] [background-size:18px_18px] overflow-hidden touch-none select-none cursor-grab active:cursor-grabbing"
      onPointerDown={(e) => {
        e.currentTarget.setPointerCapture(e.pointerId)
        pts.current.set(e.pointerId, { x: e.clientX, y: e.clientY })
        if (pts.current.size >= 2) {
          // 第二根手指落下 → 进捏合，同时取消可能已经开始的单指拖拽/点击
          const [a, b] = [...pts.current.values()]
          pinch.current = {
            d: Math.hypot(a.x - b.x, a.y - b.y) || 1,
            cx: (a.x + b.x) / 2,
            cy: (a.y + b.y) / 2,
            k: view.k, tx: view.tx, ty: view.ty,
          }
          drag.current = null
          pending.current = null
          moved.current = true
          return
        }
        drag.current = { x: e.clientX, y: e.clientY, tx: view.tx, ty: view.ty }
        moved.current = false
      }}
      onPointerMove={(e) => {
        if (!pts.current.has(e.pointerId)) return
        pts.current.set(e.pointerId, { x: e.clientX, y: e.clientY })

        const p = pinch.current
        if (p && pts.current.size >= 2) {
          const [a, b] = [...pts.current.values()]
          const d = Math.hypot(a.x - b.x, a.y - b.y) || 1
          const cx = (a.x + b.x) / 2
          const cy = (a.y + b.y) / 2
          const k = clamp(p.k * (d / p.d), 0.05, 3)
          const r = k / p.k
          const rect = e.currentTarget.getBoundingClientRect()
          const mx = p.cx - rect.left
          const my = p.cy - rect.top
          // 以捏合中心为锚点缩放，再叠加两指中心的整体位移（边缩放边平移）
          setView({
            k,
            tx: mx - (mx - p.tx) * r + (cx - p.cx),
            ty: my - (my - p.ty) * r + (cy - p.cy),
          })
          return
        }

        const d = drag.current
        if (!d) return
        const dx = e.clientX - d.x
        const dy = e.clientY - d.y
        if (!moved.current && Math.abs(dx) + Math.abs(dy) > 5) moved.current = true
        if (!moved.current) return
        setView((v) => ({ ...v, tx: d.tx + dx, ty: d.ty + dy }))
      }}
      onPointerUp={(e) => {
        pts.current.delete(e.pointerId)
        if (pts.current.size < 2) pinch.current = null
        if (pts.current.size === 1) {
          // 松开一根后还剩一根：接着拖，不要跳
          const [a] = [...pts.current.values()]
          drag.current = { x: a.x, y: a.y, tx: view.tx, ty: view.ty }
          moved.current = true
          pending.current = null
          return
        }
        const n = pending.current
        pending.current = null
        drag.current = null
        // 拖拽超过阈值算平移，不算点击 —— 否则拖一下图就会误跳课程
        if (!moved.current && n) onNode(n)
      }}
      onPointerCancel={(e) => {
        pts.current.delete(e.pointerId)
        pinch.current = null
        drag.current = null
        pending.current = null
      }}
    >
      <svg width="100%" height="100%" className="block">
        <g
          transform={`translate(${view.tx},${view.ty}) scale(${view.k})`}
          style={{ transition: 'transform 240ms cubic-bezier(.4,0,.2,1)' }}
        >
          {edges.map(([p, c]) => {
            // 挂在左边的分支，连线要从父的左边缘连到子的右边缘
            const toLeft = c.side < 0
            const x1 = toLeft ? p.x : p.x + p.w
            const x2 = toLeft ? c.x + c.w : c.x
            const mx = (x1 + x2) / 2
            const col = PALETTE[c.color]
            return (
              <path
                key={`${p.id}->${c.id}`}
                d={`M${x1},${p.y} C${mx},${p.y} ${mx},${c.y} ${x2},${c.y}`}
                fill="none"
                stroke={col.line}
                strokeWidth={c.depth === 1 ? 2.2 : 1.4}
                strokeOpacity={c.depth === 1 ? 0.55 : 0.38}
                strokeLinecap="round"
              />
            )
          })}

          {nodes.map((n) => {
            const col = PALETTE[n.color]
            const isRoot = n.depth === 0
            const isBranch = n.depth === 1
            const isLeaf = n.depth === 2
            const noCourse = isLeaf && !n.code
            const hit = matches.has(n.id)
            const clickable = isBranch || (isLeaf && !!n.code)
            return (
              <foreignObject
                key={n.id}
                x={n.x}
                y={n.y - n.h / 2}
                width={n.w}
                height={n.h}
                style={{ overflow: 'visible' }}
              >
                <div
                  {...{ xmlns: 'http://www.w3.org/1999/xhtml' }}
                  data-mnode={n.id}
                  data-depth={n.depth}
                  data-code={n.code || undefined}
                  data-hit={hit ? '1' : undefined}
                  onPointerDown={() => { pending.current = n }}
                  title={isLeaf ? (n.lesson ? `对应课程：${n.lesson}` : '面试会问，站内暂无对应课程') : ''}
                  style={{
                    width: n.w,
                    height: n.h,
                    cursor: clickable ? 'pointer' : 'default',
                    ...(isBranch ? { background: col.bg, borderColor: col.bd } : {}),
                    ...(isLeaf && !noCourse ? { borderColor: '#e2e8f0' } : {}),
                  }}
                  className={[
                    'box-border flex items-center gap-1.5 px-2 relative overflow-hidden',
                    isRoot
                      ? 'rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-600 text-white font-bold shadow-lg justify-center'
                      : isBranch
                        ? 'rounded-xl border-2 font-semibold shadow-sm justify-between'
                        : 'rounded-lg border leading-[19px] text-slate-700 bg-white',
                    isLeaf && noCourse ? 'border-dashed bg-slate-50 !text-slate-500' : '',
                    hit ? 'ring-2 ring-amber-400 ring-offset-1' : '',
                    isLeaf && n.code ? 'hover:shadow-md hover:border-indigo-300' : '',
                  ].join(' ')}
                >
                  {isBranch && (
                    <span
                      className="absolute left-0 top-0 bottom-0 w-1 rounded-l-xl"
                      style={{ background: col.line, opacity: 0.85 }}
                    />
                  )}
                  {isLeaf && (
                    <span
                      className="shrink-0 rounded-full"
                      style={{
                        width: 6,
                        height: 6,
                        background: HOT_COLOR[n.hot] || HOT_COLOR[2],
                        boxShadow: n.hot === 3 ? '0 0 0 3px rgba(239,68,68,.14)' : undefined,
                      }}
                    />
                  )}
                  <span
                    className="min-w-0"
                    style={{
                      fontSize: isRoot ? ROOT_FS : isBranch ? BRANCH_FS : LEAF_FS,
                      wordBreak: 'break-word',
                      color: isRoot ? '#fff' : isBranch ? col.fg : undefined,
                    }}
                  >
                    {n.label}
                  </span>
                  {isBranch && (
                    <span className="shrink-0 text-[10px] font-normal opacity-55">
                      {n.collapsed ? `+${n.children.length}` : '−'}
                    </span>
                  )}
                  {noCourse && (
                    <span className="shrink-0 text-[9px] leading-none px-1 py-0.5 rounded bg-slate-200 text-slate-500">
                      待补
                    </span>
                  )}
                </div>
              </foreignObject>
            )
          })}
        </g>
      </svg>

      {/* 缩放控制 */}
      <div className="absolute right-2.5 bottom-2.5 flex flex-col gap-1">
        {[
          { t: '+', tip: '放大', fn: () => setView((v) => ({ ...v, k: clamp(v.k * 1.2, 0.05, 3) })) },
          { t: '−', tip: '缩小', fn: () => setView((v) => ({ ...v, k: clamp(v.k / 1.2, 0.05, 3) })) },
          {
            t: '1:1',
            tip: '原始大小',
            fn: () => setView({
              k: 1,
              tx: box.w / 2 - ((bounds.minX + bounds.maxX) / 2),
              ty: box.h / 2 - ((bounds.minY + bounds.maxY) / 2),
            }),
          },
          { t: '⤢', tip: '适应屏幕', fn: fit },
        ].map((b) => (
          <Tooltip key={b.t} title={b.tip}>
            <button
              onClick={b.fn}
              className="w-7 h-7 rounded-lg bg-white/95 border border-slate-200 text-slate-600 text-[11px] leading-none shadow-sm hover:border-indigo-300 hover:text-indigo-600"
            >
              {b.t}
            </button>
          </Tooltip>
        ))}
      </div>

      {/* 图例 */}
      <div className="absolute left-2.5 bottom-2.5 flex flex-wrap items-center gap-x-2.5 gap-y-1 text-[10.5px] text-slate-500 bg-white/85 backdrop-blur rounded-lg px-2 py-1 border border-slate-200 max-w-[70%]">
        {[
          { c: HOT_COLOR[3], t: '必问' },
          { c: HOT_COLOR[2], t: '常问' },
          { c: HOT_COLOR[1], t: '纵深' },
        ].map((l) => (
          <span key={l.t} className="inline-flex items-center gap-1">
            <i className="inline-block w-1.5 h-1.5 rounded-full" style={{ background: l.c }} />
            {l.t}
          </span>
        ))}
        {!compact && (
          <>
            <span className="text-slate-300">|</span>
            <span className="hidden sm:inline">点分支展开 · 点考点进入课程 · 滚轮缩放 · 拖拽平移</span>
            <span className="sm:hidden">点分支展开</span>
          </>
        )}
      </div>
    </div>
  )
}

export default function MindMap() {
  const navigate = useNavigate()
  const { message } = App.useApp()
  const [data, setData] = useState<MindMapSubject[]>([])
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState('')
  const [active, setActive] = useState(0)
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set())
  const [q, setQ] = useState('')

  // 手机横屏：进全屏层，让出导航和工具栏。真横过来后画布自动切左右双翼布局
  const [landscape, setLandscape] = useState(false)
  const [portrait, setPortrait] = useState(true)

  useEffect(() => {
    let alive = true
    api.get<MindMapSubject[]>('/api/learn/mindmaps')
      .then((d) => { if (alive) setData(d) })
      .catch((e) => { if (alive) setErr(e?.message || '加载失败') })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [])

  const subject = data[active]

  // 默认全部展开：进来先看全貌，要读细节再双指/滚轮放大
  useEffect(() => {
    if (!subject) return
    setCollapsed(new Set())
    setQ('')
  }, [subject])

  useEffect(() => {
    const mq = window.matchMedia('(orientation: portrait)')
    const sync = () => setPortrait(mq.matches)
    sync()
    mq.addEventListener('change', sync)
    return () => mq.removeEventListener('change', sync)
  }, [])

  useLayoutEffect(() => {
    if (!landscape) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setLandscape(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [landscape])

  // 搜索：只按数据算节点 id，不依赖布局结果（布局在画布内部按方向重算）
  const matches = useMemo(() => {
    const t = q.trim().toLowerCase()
    if (!t || !subject) return new Set<string>()
    const set = new Set<string>()
    subject.branches.forEach((b, bi) => {
      b.items.forEach((it, ii) => {
        if (it.name.toLowerCase().includes(t)) set.add(`b${bi}-${ii}`)
      })
    })
    return set
  }, [q, subject])

  useEffect(() => {
    const t = q.trim().toLowerCase()
    if (!t || !subject) return
    const need = new Set<string>()
    subject.branches.forEach((b, bi) => {
      if (b.items.some((it) => it.name.toLowerCase().includes(t))) need.add(`b${bi}`)
    })
    if (!need.size) return
    setCollapsed((prev) => {
      const next = new Set(prev)
      need.forEach((id) => next.delete(id))
      next.delete('root')
      return next.size === prev.size ? prev : next
    })
  }, [q, subject])

  const onNode = (n: MNode) => {
    if (n.depth === 2 && n.code) {
      // 锁着的课点进去，Learn 页会把选择退回第一课，学生看到「点了 A 打开 B」
      if (n.status === 'locked') {
        message.warning(`《${n.lesson}》还没解锁，先按顺序把前面的课学完`)
        return
      }
      // 项目里没有 /learn/:code 这条路由（只有 /learn 和 /learn/:code/practice），
      // 所以走「记住选中的课 + 回列表」：Learn 页会读这个 key 直接打开对应知识点。
      sessionStorage.setItem('ca_learn_code', n.code)
      setLandscape(false)
      navigate('/learn')
      return
    }
    if (!n.children.length) return
    setCollapsed((prev) => {
      const next = new Set(prev)
      if (next.has(n.id)) next.delete(n.id)
      else next.add(n.id)
      return next
    })
  }

  if (loading) {
    return (
      <div className="h-[calc(100dvh-140px)] md:h-[calc(100dvh-36px)] flex items-center justify-center">
        <Spin size="large" />
      </div>
    )
  }
  if (err || !subject) {
    return (
      <div className="h-[calc(100dvh-140px)] md:h-[calc(100dvh-36px)] flex items-center justify-center text-slate-400 text-sm">
        {err || '暂无知识地图'}
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100dvh-140px)] md:h-[calc(100dvh-36px)] gap-2">
      {/* 科目切换 */}
      <div className="flex gap-1.5 overflow-x-auto pb-0.5 shrink-0 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {data.map((s, i) => (
          <button
            key={s.subject}
            onClick={() => setActive(i)}
            className={`shrink-0 px-3 py-1.5 rounded-lg text-[13px] transition-colors ${
              i === active
                ? 'bg-indigo-600 text-white font-medium shadow-sm'
                : 'bg-white text-slate-600 border border-slate-200 hover:border-indigo-300 hover:text-indigo-600'
            }`}
          >
            {s.subject}
            <span className={`ml-1 text-[11px] ${i === active ? 'text-indigo-200' : 'text-slate-400'}`}>
              {s.node_total}
            </span>
          </button>
        ))}
      </div>

      {/* 这科在面试里怎么考 + 工具栏 */}
      <div className="flex flex-col md:flex-row md:items-start gap-2 shrink-0">
        <p className="flex-1 min-w-0 text-[12px] leading-relaxed text-slate-500 bg-white/70 border border-slate-200 rounded-lg px-3 py-2">
          {subject.intro}
          <span className="ml-1 text-slate-400">
            （{subject.node_total} 个考点，必问 {subject.hot_total}；覆盖 {subject.lesson_covered}/
            {subject.lesson_total} 课）
          </span>
        </p>
        <div className="flex items-center gap-1.5 shrink-0">
          <Input
            allowClear
            size="small"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="搜考点，如 索引"
            style={{ width: 148 }}
          />
          <button
            onClick={() => setCollapsed(new Set(subject.branches.map((_, i) => `b${i}`)))}
            className="px-2 py-1 rounded-md text-[12px] text-slate-600 border border-slate-200 bg-white hover:border-indigo-300"
          >
            折叠
          </button>
          <button
            onClick={() => setCollapsed(new Set())}
            className="px-2 py-1 rounded-md text-[12px] text-slate-600 border border-slate-200 bg-white hover:border-indigo-300"
          >
            展开全部
          </button>
          {/* 只有手机才需要：竖屏一屏放不下 85 个考点，转横屏能多看一倍 */}
          <button
            onClick={() => setLandscape(true)}
            className="md:hidden px-2 py-1 rounded-md text-[12px] text-white bg-indigo-600 hover:bg-indigo-700"
          >
            横屏看
          </button>
        </div>
      </div>

      {/* 画布 */}
      <div className="flex-1 min-h-0">
        <GraphCanvas
          subject={subject}
          collapsed={collapsed}
          matches={matches}
          onNode={onNode}
        />
      </div>

      {/* 手机横屏层 */}
      {landscape && (
        <div className="fixed inset-0 z-[70] bg-white flex flex-col">
          <div className="flex items-center gap-2 px-3 h-10 border-b border-slate-200 shrink-0">
            <span className="text-[13px] font-semibold text-indigo-700">{subject.subject}</span>
            <span className="text-[11px] text-slate-400">{subject.node_total} 个考点</span>
            {portrait && (
              <span className="text-[11px] text-amber-600">把手机横过来，分支会分成左右两翼</span>
            )}
            <button
              data-exit="1"
              onClick={() => setLandscape(false)}
              className="ml-auto px-2.5 py-1 rounded-md text-[12px] text-slate-600 border border-slate-300 bg-white"
            >
              退出
            </button>
          </div>
          <div data-stage="1" className="flex-1 relative overflow-hidden bg-white p-1.5">
            <GraphCanvas
              subject={subject}
              collapsed={collapsed}
              matches={matches}
              onNode={onNode}
              compact
            />
          </div>
        </div>
      )}
    </div>
  )
}
