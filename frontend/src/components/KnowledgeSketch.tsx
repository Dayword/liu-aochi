import { useEffect, useMemo, useRef, useState } from 'react'
import type { LessonSketch, SketchKind, SketchNode } from '../types'

/**
 * 手绘风知识图。
 *
 * 为什么用 SVG 画而不是贴图：
 * - 图里的每个节点都对应真实的课程 code，点一下就能跳到那一课；
 * - 文字永远是矢量渲染，手机上不会糊；
 * - 改课程内容只要改数据，不用重画 135 张图。
 *
 * 「手绘感」靠三件事堆出来，不靠字体：
 * 1. 连线是带一点弓形的二次贝塞尔，不是直线；
 * 2. 节点框描两遍（第二遍偏移 0.7px、半透明），像笔描过两下；
 * 3. 每个节点的旋转角、抖动幅度都由 id 哈希出来的伪随机数决定 ——
 *    同一张图每次渲染都一样，不会一刷新就「抖」一下。
 *
 * 布局是「两圈八方位」：本课知识点在内圈（实线），前后课/跨科目在外圈（虚线）。
 * 方位由数据里的 zone 指定，渲染器只负责算坐标，不做自动布局 ——
 * 自动布局在这种小画布上很容易把两个球怼到一起。
 */

const ZONE_ANGLE: Record<string, number> = {
  t: -90,
  tr: -45,
  r: 0,
  br: 45,
  b: 90,
  bl: 135,
  l: 180,
  tl: -135,
}

// 字号随画布宽度走：手机上画布只有 350，12.5px 刚好；桌面端 700 宽还 12.5px 就偏小
const fsFor = (w: number) => (w >= 600 ? 14 : 12.5)
const centerFsFor = (w: number) => (w >= 600 ? 16.5 : 15)
const nodeHFor = (w: number) => (w >= 600 ? 30 : 27)

const TONE: Record<SketchKind, { line: string; fill: string; text: string }> = {
  core: { line: '#818cf8', fill: '#eef2ff', text: '#3730a3' },
  prev: { line: '#94a3b8', fill: '#f8fafc', text: '#475569' },
  next: { line: '#34d399', fill: '#ecfdf5', text: '#047857' },
  side: { line: '#fbbf24', fill: '#fffbeb', text: '#b45309' },
}

/** 和 backend/learn_sketch_check.py 同一套宽度估算：汉字 1，英文 0.55。 */
function effWidth(s: string): number {
  let n = 0
  for (const ch of s) n += ch.codePointAt(0)! > 0x2e80 ? 1 : 0.55
  return n
}

/** 由字符串种子生成的确定性伪随机（mulberry32），保证每次渲染一模一样。 */
function rng(seed: string): () => number {
  let h = 2166136261
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  let a = h >>> 0
  return () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = a
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

interface Box {
  id: string
  label: string
  kind: SketchKind
  code?: string
  w: number
  h: number
  cx: number
  cy: number
  rot: number
}

interface EdgeShape {
  key: string
  d: string
  ax: number
  ay: number
  ux: number
  uy: number
  label: string
  lx: number
  ly: number
  dashed: boolean
  tone: SketchKind
}

/** 求线段与矩形边框的交点，让连线正好停在框边上，不插进文字里。 */
function edgePoint(b: Box, tx: number, ty: number): [number, number] {
  const dx = tx - b.cx
  const dy = ty - b.cy
  if (dx === 0 && dy === 0) return [b.cx, b.cy]
  const hw = b.w / 2 + 2
  const hh = b.h / 2 + 2
  const sx = dx === 0 ? Infinity : hw / Math.abs(dx)
  const sy = dy === 0 ? Infinity : hh / Math.abs(dy)
  const s = Math.min(sx, sy)
  return [b.cx + dx * s, b.cy + dy * s]
}

export default function KnowledgeSketch({
  sketch,
  onOpen,
}: {
  sketch: LessonSketch
  onOpen?: (code: string) => void
}) {
  const wrap = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(0)

  useEffect(() => {
    const el = wrap.current
    if (!el) return
    const sync = () => setWidth(el.clientWidth)
    sync()
    const ro = new ResizeObserver(sync)
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const layout = useMemo(() => {
    const W = Math.max(300, Math.min(width || 360, 720))
    // 手机上给纵向留够空间，宽屏则压扁一点，避免一张图占满一屏
    const H = W < 430 ? 372 : Math.max(330, Math.min(W * 0.6, 430))
    const cx = W / 2
    const cy = H / 2
    const fs = fsFor(W)
    const centerFs = centerFsFor(W)
    const nodeH = nodeHFor(W)
    const labFs = fs * 0.74

    const boxes: Box[] = sketch.nodes.map((n) => {
      const w = effWidth(n.label) * fs + 22
      const r = rng(n.id)
      return {
        id: n.id,
        label: n.label,
        kind: n.kind,
        code: n.code,
        w,
        h: nodeH,
        cx: 0,
        cy: 0,
        rot: (r() - 0.5) * 2.4,
      }
    })

    const maxHalfW = Math.max(48, ...boxes.map((b) => b.w / 2)) + 4
    const rx = Math.max(40, cx - maxHalfW)
    const ry = Math.max(34, cy - nodeH / 2 - 8)

    for (const b of boxes) {
      const ang = ((ZONE_ANGLE[sketch.nodes.find((n) => n.id === b.id)!.zone] ?? 0) * Math.PI) / 180
      const k = b.kind === 'core' ? 0.56 : 1
      b.cx = cx + Math.cos(ang) * rx * k
      b.cy = cy + Math.sin(ang) * ry * k
    }

    // 去重叠 + 拉回画布：两件事必须放在同一个循环里。
    // 先推散再 clamp 的话，clamp 会把刚推开的两个框又挤回去（手机上很常见）。
    const pad = 6
    const clamp = () => {
      for (const b of boxes) {
        b.cx = Math.max(pad + b.w / 2, Math.min(W - pad - b.w / 2, b.cx))
        b.cy = Math.max(pad + b.h / 2, Math.min(H - pad - b.h / 2, b.cy))
      }
    }
    clamp()
    for (let iter = 0; iter < 12; iter++) {
      let moved = false
      for (let i = 0; i < boxes.length; i++) {
        for (let j = i + 1; j < boxes.length; j++) {
          const a = boxes[i]
          const b = boxes[j]
          const ox = (a.w + b.w) / 2 + 6 - Math.abs(a.cx - b.cx)
          const oy = (a.h + b.h) / 2 + 4 - Math.abs(a.cy - b.cy)
          if (ox <= 0 || oy <= 0) continue
          moved = true
          const push = Math.min(ox, oy) / 2 + 1
          const dx = a.cx === b.cx ? (i % 2 ? 1 : -1) : Math.sign(a.cx - b.cx)
          const dy = a.cy === b.cy ? (j % 2 ? 1 : -1) : Math.sign(a.cy - b.cy)
          if (ox < oy) {
            a.cx += dx * push
            b.cx -= dx * push
          } else {
            a.cy += dy * push
            b.cy -= dy * push
          }
        }
      }
      clamp()
      if (!moved) break
    }

    // 中心节点最后算：它的宽高由它自己的字决定
    const cw = Math.max(76, effWidth(sketch.center) * centerFs + 40)
    const ch = 44
    const center: Box = {
      id: 'center',
      label: sketch.center,
      kind: 'core',
      w: cw,
      h: ch,
      cx,
      cy,
      rot: -0.8,
    }

    // 整体居中：章节方位是手写的，上边只挂了内圈节点、下边挂了外圈节点时，
    // 视觉重心会偏，画布上方留一大片白。按实际占地把整组往下/往上挪一点。
    const all = [...boxes, center]
    const bounds = () => ({
      minY: Math.min(...all.map((b) => b.cy - b.h / 2)),
      maxY: Math.max(...all.map((b) => b.cy + b.h / 2)),
    })
    let bb = bounds()
    const shift = (H / 2 - (bb.minY + bb.maxY) / 2) * 0.8
    if (Math.abs(shift) > 6) {
      for (const b of all) b.cy += shift
      clamp()
      bb = bounds()
    }

    // 按实际内容裁高度：这一课要是没有上下方向的外圈节点，画布会空掉一半。
    const padY = 14
    const fitH = Math.max(240, Math.round(bb.maxY - bb.minY + padY * 2))
    for (const b of all) b.cy += padY - bb.minY

    const byId = new Map<string, Box>(boxes.map((b) => [b.id, b]))
    byId.set('center', center)
    const allBoxes = [...boxes, center]

    /** 二次贝塞尔上 t 处的点，再沿法线推开 off，让文字落在线的旁边而不是压着线。 */
    const pointAt = (t: number, x1: number, y1: number, qx: number, qy: number,
                     x2: number, y2: number, off: number) => {
      const u = 1 - t
      const px = u * u * x1 + 2 * u * t * qx + t * t * x2
      const py = u * u * y1 + 2 * u * t * qy + t * t * y2
      const dx = 2 * u * (qx - x1) + 2 * t * (x2 - qx)
      const dy = 2 * u * (qy - y1) + 2 * t * (y2 - qy)
      const l = Math.hypot(dx, dy) || 1
      return { x: px - (dy / l) * off, y: py + (dx / l) * off }
    }

    const hits = (x: number, y: number, w: number, h: number) =>
      allBoxes.some(
        (b) =>
          Math.abs(x - b.cx) < b.w / 2 + w / 2 + 3 &&
          Math.abs(y - b.cy) < b.h / 2 + h / 2 + 2,
      )

    // 已经放下的标签占位，后放的避让前面的 —— 否则「不合规就报错」和「全大写」会叠在一起
    const placedLabels: { x: number; y: number; w: number; h: number }[] = []
    const hitsLabel = (x: number, y: number, w: number, h: number) =>
      placedLabels.some(
        (p) => Math.abs(x - p.x) < (p.w + w) / 2 + 4 && Math.abs(y - p.y) < (p.h + h) / 2 + 3,
      )

    const edges: EdgeShape[] = []
    ;(sketch.edges || []).forEach((e, i) => {
      const A = byId.get(e.a)
      const B = byId.get(e.b)
      if (!A || !B) return
      const [x1, y1] = edgePoint(A, B.cx, B.cy)
      const [x2, y2] = edgePoint(B, A.cx, A.cy)
      // 弓形方向交替，看起来像随手画的，不是用尺子比着画的
      const bow = (i % 2 === 0 ? 1 : -1) * (5 + (i % 3) * 3)
      const mx = (x1 + x2) / 2
      const my = (y1 + y2) / 2
      const nx = -(y2 - y1)
      const ny = x2 - x1
      const len = Math.hypot(nx, ny) || 1
      const qx = mx + (nx / len) * bow
      const qy = my + (ny / len) * bow
      // 箭头方向取终点处的切线
      const tx = x2 - qx
      const ty = y2 - qy
      const tl = Math.hypot(tx, ty) || 1

      // 关系词只在够长、且挪几个位置都不压节点时才画 ——
      // 小画布上五条边各挂一个标签，必然糊成一团。
      let label = ''
      let lx = 0
      let ly = 0
      const text = (e.label || '').trim()
      const straight = Math.hypot(x2 - x1, y2 - y1)
      // 关系词能不能显示，交给下面两个碰撞检测决定；
      // 只有短到肉眼都分不清方向的边才直接放弃（阈值 40px）。
      if (text && straight > 40) {
        const w = effWidth(text) * labFs
        for (const t of [0.46 + (i % 3) * 0.07, 0.34, 0.64, 0.25, 0.75]) {
          const p = pointAt(t, x1, y1, qx, qy, x2, y2, 9)
          if (!hits(p.x, p.y, w, 10) && !hitsLabel(p.x, p.y, w, 10)) {
            label = text
            lx = p.x
            ly = p.y
            placedLabels.push({ x: p.x, y: p.y, w, h: 10 })
            break
          }
        }
      }

      edges.push({
        key: `${e.a}-${e.b}-${i}`,
        d: `M ${x1.toFixed(1)} ${y1.toFixed(1)} Q ${qx.toFixed(1)} ${qy.toFixed(1)} ${x2.toFixed(1)} ${y2.toFixed(1)}`,
        ax: x2,
        ay: y2,
        ux: tx / tl,
        uy: ty / tl,
        label,
        lx,
        ly,
        dashed: B.kind !== 'core',
        tone: B.kind,
      })
    })

    return { W, H: fitH, boxes, center, edges, fs, centerFs, labFs }
  }, [sketch, width])

  return (
    <div className="mt-2.5">
      <div className="mb-1 flex items-center gap-1.5 px-0.5">
        <span className="text-[11.5px] font-medium text-slate-600">🗺 这节课在知识地图里的位置</span>
        <span className="ml-auto text-[10px] text-slate-400">点虚线框可以跳过去</span>
      </div>

      <div
        ref={wrap}
        className="relative mx-auto overflow-hidden rounded-xl border border-indigo-100 bg-[#fdfdff]"
        // 画布最宽 720：再宽下去 SVG 会等比缩放，节点反而变小、四周留白变大
        style={{ maxWidth: 720, minHeight: width ? undefined : 260 }}
      >
        {width > 0 && (
          <svg
            width="100%"
            height={layout.H}
            viewBox={`0 0 ${layout.W} ${layout.H}`}
            role="img"
            aria-label={`${sketch.center}的知识关系图`}
          >
            <defs>
              <pattern id="ks-dots" width="18" height="18" patternUnits="userSpaceOnUse">
                <circle cx="1.2" cy="1.2" r="1" fill="#e6eaf5" />
              </pattern>
            </defs>
            <rect width={layout.W} height={layout.H} fill="url(#ks-dots)" opacity="0.75" />

            {/* 连线 */}
            {layout.edges.map((e) => {
              const tone = TONE[e.tone]
              return (
                <g key={e.key}>
                  <path
                    d={e.d}
                    fill="none"
                    stroke={tone.line}
                    strokeWidth={1.4}
                    strokeLinecap="round"
                    strokeDasharray={e.dashed ? '5 4' : undefined}
                    opacity={0.85}
                  />
                  <path
                    d={`M ${e.ax - e.ux * 8 - e.uy * 3.6} ${e.ay - e.uy * 8 + e.ux * 3.6} L ${e.ax} ${e.ay} L ${e.ax - e.ux * 8 + e.uy * 3.6} ${e.ay - e.uy * 8 - e.ux * 3.6}`}
                    fill="none"
                    stroke={tone.line}
                    strokeWidth={1.3}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    opacity={0.85}
                  />
                  {e.label && (
                    <text
                      x={e.lx}
                      y={e.ly}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fontSize={layout.labFs}
                      fill="#64748b"
                      stroke="#fdfdff"
                      strokeWidth={3.4}
                      paintOrder="stroke"
                      style={{ fontFamily: 'var(--sketch-font)' }}
                    >
                      {e.label}
                    </text>
                  )}
                </g>
              )
            })}

            {/* 外圈节点 */}
            {layout.boxes.map((b) => {
              const tone = TONE[b.kind]
              const clickable = !!b.code && !!onOpen
              return (
                <g
                  key={b.id}
                  transform={`translate(${b.cx} ${b.cy}) rotate(${b.rot})`}
                  style={{ cursor: clickable ? 'pointer' : 'default' }}
                  onClick={clickable ? () => onOpen!(b.code!) : undefined}
                  role={clickable ? 'button' : undefined}
                  data-sketch-node={b.id}
                >
                  <rect
                    x={-b.w / 2}
                    y={-b.h / 2}
                    width={b.w}
                    height={b.h}
                    rx={8}
                    fill={tone.fill}
                    stroke="none"
                    opacity={0.9}
                  />
                  <rect
                    x={-b.w / 2}
                    y={-b.h / 2}
                    width={b.w}
                    height={b.h}
                    rx={8}
                    fill="none"
                    stroke={tone.line}
                    strokeWidth={1.3}
                    strokeDasharray={b.kind === 'core' ? undefined : '5 3.5'}
                  />
                  <rect
                    x={-b.w / 2 + 0.7}
                    y={-b.h / 2 + 0.7}
                    width={b.w}
                    height={b.h}
                    rx={8}
                    fill="none"
                    stroke={tone.line}
                    strokeWidth={0.8}
                    strokeDasharray={b.kind === 'core' ? undefined : '5 3.5'}
                    opacity={0.35}
                  />
                  <text
                    x={0}
                    y={0.5}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fontSize={layout.fs}
                    fontWeight={500}
                    fill={tone.text}
                    style={{ fontFamily: 'var(--sketch-font)' }}
                  >
                    {b.label}
                  </text>
                  {clickable && (
                    // 可点的节点不再额外画「›」或「点击查看」——
                    // 27px 高的框里塞不下第二行字，图例里已经写了「点虚线框可以跳过去」。
                    // 这里只用下划线暗示它是链接。
                    <line
                      x1={(-effWidth(b.label) * layout.fs) / 2}
                      y1={b.h / 2 - 6.5}
                      x2={(effWidth(b.label) * layout.fs) / 2}
                      y2={b.h / 2 - 6.5}
                      stroke={tone.line}
                      strokeWidth={0.7}
                      opacity={0.5}
                    />
                  )}
                </g>
              )
            })}

            {/* 中心节点：画得比别的胖一点、描两圈，视觉上压住整张图 */}
            <g transform={`translate(${layout.center.cx} ${layout.center.cy}) rotate(${layout.center.rot})`}>
              <ellipse
                rx={layout.center.w / 2}
                ry={layout.center.h / 2 + 2}
                fill="#e0e7ff"
                stroke="none"
                opacity={0.55}
              />
              <ellipse
                rx={layout.center.w / 2}
                ry={layout.center.h / 2}
                fill="#ffffff"
                stroke="#4f46e5"
                strokeWidth={1.7}
              />
              <ellipse
                rx={layout.center.w / 2 - 1.2}
                ry={layout.center.h / 2 - 1.2}
                fill="none"
                stroke="#4f46e5"
                strokeWidth={0.8}
                opacity={0.3}
              />
              <text
                x={0}
                y={0.5}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize={layout.centerFs}
                fontWeight={700}
                fill="#312e81"
                style={{ fontFamily: 'var(--sketch-font)' }}
              >
                {layout.center.label}
              </text>
            </g>
          </svg>
        )}
      </div>

      <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-0.5 px-0.5 text-[10px] text-slate-400">
        <span>—— 本课知识点</span>
        <span>- - 前后课程 / 跨科目</span>
        <span className="text-emerald-500">绿 = 下一课</span>
        <span className="text-amber-500">黄 = 旁支</span>
      </div>
    </div>
  )
}
