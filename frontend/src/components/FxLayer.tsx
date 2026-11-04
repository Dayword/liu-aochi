import { useEffect, useRef } from 'react'
import { useSettings } from '../theme/ThemeProvider'
import { onBus } from '../lib/bus'
import { streak } from '../lib/activity'

/**
 * 特效层：一张固定的 canvas，盖在页面最上面但不吃事件。
 *
 * 为什么用 canvas 而不是 DOM 元素：一次答对要撒 24 颗星星，用 div 就是
 * 24 次重排 + 24 个动画，手机上肉眼可见地掉帧。canvas 只在有粒子时才
 * 启动 rAF，空闲时完全不占 CPU。
 */
interface P {
  x: number
  y: number
  vx: number
  vy: number
  life: number
  max: number
  size: number
  color: string
  rot: number
  vr: number
  kind: 'star' | 'confetti' | 'text'
  text?: string
  gravity: number
}

const STAR = 'var(--t-brand)'

function starPath(ctx: CanvasRenderingContext2D, r: number) {
  ctx.beginPath()
  for (let i = 0; i < 8; i++) {
    const a = (Math.PI / 4) * i
    const rr = i % 2 === 0 ? r : r * 0.38
    const x = Math.cos(a) * rr
    const y = Math.sin(a) * rr
    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  }
  ctx.closePath()
}

export default function FxLayer() {
  const { settings, theme } = useSettings()
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const parts = useRef<P[]>([])
  const raf = useRef<number>(0)
  const pointer = useRef({ x: 0, y: 0 })

  // 记住最后一次指针位置：星星从「你刚点的地方」炸开，而不是屏幕中央
  useEffect(() => {
    const onDown = (e: PointerEvent) => {
      pointer.current = { x: e.clientX, y: e.clientY }
    }
    window.addEventListener('pointerdown', onDown, { passive: true })
    return () => window.removeEventListener('pointerdown', onDown)
  }, [])

  useEffect(() => {
    if (!settings.effects) return
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      canvas.width = Math.floor(window.innerWidth * dpr)
      canvas.height = Math.floor(window.innerHeight * dpr)
      canvas.style.width = `${window.innerWidth}px`
      canvas.style.height = `${window.innerHeight}px`
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    }
    resize()
    window.addEventListener('resize', resize)

    const brand = getComputedStyle(document.documentElement).getPropertyValue('--t-brand').trim() || STAR
    const accent = getComputedStyle(document.documentElement).getPropertyValue('--t-accent').trim() || '#f59e0b'
    const palette = [brand, accent, '#f472b6', '#38bdf8', '#a3e635']

    const tick = () => {
      const { innerWidth: W, innerHeight: H } = window
      ctx.clearRect(0, 0, W, H)
      const list = parts.current
      for (let i = list.length - 1; i >= 0; i--) {
        const p = list[i]
        p.life -= 1
        if (p.life <= 0) {
          list.splice(i, 1)
          continue
        }
        p.vy += p.gravity
        p.vx *= 0.985
        p.x += p.vx
        p.y += p.vy
        p.rot += p.vr
        const alpha = Math.max(0, Math.min(1, p.life / (p.max * 0.7)))
        ctx.save()
        ctx.globalAlpha = alpha
        ctx.translate(p.x, p.y)
        if (p.kind === 'text') {
          ctx.font = `700 ${p.size}px 'Segoe UI','PingFang SC',sans-serif`
          ctx.fillStyle = p.color
          ctx.textAlign = 'center'
          ctx.fillText(p.text || '', 0, 0)
        } else if (p.kind === 'star') {
          ctx.rotate(p.rot)
          ctx.fillStyle = p.color
          starPath(ctx, p.size)
          ctx.fill()
        } else {
          ctx.rotate(p.rot)
          ctx.fillStyle = p.color
          ctx.fillRect(-p.size / 2, -p.size / 4, p.size, p.size / 2)
        }
        ctx.restore()
      }
      if (list.length) raf.current = requestAnimationFrame(tick)
      else raf.current = 0
    }

    const kick = () => {
      if (!raf.current) raf.current = requestAnimationFrame(tick)
    }

    const burst = (x: number, y: number, n: number, spread = 5) => {
      for (let i = 0; i < n; i++) {
        const a = Math.random() * Math.PI * 2
        const sp = spread + Math.random() * spread
        parts.current.push({
          x,
          y,
          vx: Math.cos(a) * sp,
          vy: Math.sin(a) * sp - 2,
          life: 46 + Math.random() * 26,
          max: 72,
          size: 3 + Math.random() * 3.5,
          color: palette[(Math.random() * palette.length) | 0],
          rot: Math.random() * Math.PI,
          vr: (Math.random() - 0.5) * 0.3,
          kind: Math.random() > 0.45 ? 'star' : 'confetti',
          gravity: 0.12,
        })
      }
      kick()
    }

    const confetti = () => {
      const W = window.innerWidth
      for (let i = 0; i < 90; i++) {
        parts.current.push({
          x: Math.random() * W,
          y: -20 - Math.random() * 120,
          vx: (Math.random() - 0.5) * 2.4,
          vy: 1.6 + Math.random() * 2.6,
          life: 130 + Math.random() * 70,
          max: 200,
          size: 6 + Math.random() * 7,
          color: palette[(Math.random() * palette.length) | 0],
          rot: Math.random() * Math.PI,
          vr: (Math.random() - 0.5) * 0.35,
          kind: 'confetti',
          gravity: 0.03,
        })
      }
      kick()
    }

    const off = onBus((e) => {
      if (e.type === 'answer') {
        if (e.correct) {
          const { x, y } = pointer.current
          const px = x || window.innerWidth / 2
          const py = y || window.innerHeight * 0.6
          burst(px, py, 22)
          const n = streak()
          // 连击到 3 才值得报出来，1 连击天天见会烦
          if (n >= 3 && n % 3 === 0) {
            parts.current.push({
              x: px,
              y: py - 34,
              vx: 0,
              vy: -1.15,
              life: 60,
              max: 60,
              size: 20,
              color: accent,
              rot: 0,
              vr: 0,
              kind: 'text',
              text: `${n} 连击`,
              gravity: 0,
            })
            kick()
          }
        }
      } else if (e.type === 'levelup' || e.type === 'clear') {
        confetti()
      }
    })

    return () => {
      off()
      window.removeEventListener('resize', resize)
      if (raf.current) cancelAnimationFrame(raf.current)
      raf.current = 0
      parts.current = []
      ctx.clearRect(0, 0, window.innerWidth, window.innerHeight)
    }
    // theme 变了要重新取一次品牌色
  }, [settings.effects, theme.id])

  if (!settings.effects) return null

  return (
    <canvas
      ref={canvasRef}
      aria-hidden
      className="fx-layer pointer-events-none fixed inset-0 z-[60]"
    />
  )
}
