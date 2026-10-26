import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * 可拖拽的上下分屏（对应「拖动分屏比例」这个交互）：
 * 中间一条把手，拖动时上下两区同步变高，松手自动吸附到最近的预设比例。
 *
 * 为什么需要吸附：手机上手指一抖就会停在一个「上面 43%、下面 57%」的尴尬比例，
 * 每次都得微调。吸附到 30 / 50 / 70 三档，拖完就落在能用的位置上。
 * 双击把手回到初始比例，避免拖坏了没法复位。
 */
export default function SplitPane({
  top,
  bottom,
  initial = 0.55,
  min = 0.18,
  max = 0.86,
  snaps = [0.3, 0.5, 0.7],
  storageKey,
  className = '',
}: {
  top: React.ReactNode
  bottom: React.ReactNode
  /** 上半区初始占比 0~1 */
  initial?: number
  min?: number
  max?: number
  /** 松手时吸附到这些比例里最近的一个 */
  snaps?: number[]
  /** 传了就记忆用户拖过的比例 */
  storageKey?: string
  className?: string
}) {
  const [ratio, setRatio] = useState(() => {
    if (storageKey) {
      const saved = Number(localStorage.getItem(storageKey))
      if (saved >= min && saved <= max) return saved
    }
    return initial
  })
  const [dragging, setDragging] = useState(false)
  const boxRef = useRef<HTMLDivElement>(null)

  /** 指针位置 → 上半区占比 */
  const ratioFromY = useCallback(
    (clientY: number) => {
      const el = boxRef.current
      if (!el) return ratio
      const rect = el.getBoundingClientRect()
      if (rect.height < 40) return ratio
      const r = (clientY - rect.top) / rect.height
      return Math.min(max, Math.max(min, r))
    },
    [max, min, ratio],
  )

  const onPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.currentTarget.setPointerCapture(e.pointerId)
    setDragging(true)
  }

  const onPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!dragging) return
    setRatio(ratioFromY(e.clientY))
  }

  const onPointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!dragging) return
    setDragging(false)
    const raw = ratioFromY(e.clientY)
    const snapped = snaps.reduce((a, b) => (Math.abs(b - raw) < Math.abs(a - raw) ? b : a), snaps[0])
    // 手指离吸附点太远时保留原位，硬吸会让人以为「拖不动」
    const final = Math.abs(snapped - raw) < 0.12 ? snapped : raw
    setRatio(final)
    if (storageKey) localStorage.setItem(storageKey, String(final))
  }

  // 拖动期间锁住页面滚动，否则手机上会边拖边滚整个页面
  useEffect(() => {
    if (!dragging) return
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = prev
    }
  }, [dragging])

  return (
    // h-full 不能少：父级是普通 block（不是 flex）时，没有高度的子元素
    // 会让 `flex: 0 0 X%` 按 auto 计算 → 上半区塌成内容高度、下半区剩一大片空白
    <div ref={boxRef} className={`flex h-full min-h-0 flex-col ${className}`}>
      <div className="min-h-0 overflow-hidden flex flex-col" style={{ flex: `0 0 ${ratio * 100}%` }}>
        {top}
      </div>

      {/* 把手：移动端给足热区（24px），细高但手指好按 */}
      <div
        role="separator"
        aria-orientation="horizontal"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        onDoubleClick={() => {
          setRatio(initial)
          if (storageKey) localStorage.setItem(storageKey, String(initial))
        }}
        className={`shrink-0 h-6 my-0.5 flex items-center justify-center touch-none select-none cursor-row-resize ${
          dragging ? 'text-indigo-500' : 'text-slate-300'
        }`}
      >
        <div className="h-1 w-12 rounded-full bg-current opacity-70" />
      </div>

      <div className="min-h-0 flex-1 flex flex-col overflow-hidden">{bottom}</div>
    </div>
  )
}
