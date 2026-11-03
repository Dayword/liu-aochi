import { themeOf } from '../levelTheme'

/**
 * 品牌标：行星 + 轨道。
 *
 * 为什么不用 🌌：emoji 在不同系统上字形完全不一样（Windows 是彩色圆盘、
 * Android 是紫色漩涡），品牌标不能在别人机器上换一张脸。矢量标只有一份形状，
 * 而且能和首页封面的「星系」意象对上。
 *
 * 顺带一个好处：入场动画里可以把轨道当描边来画（strokeDashoffset），
 * 让标志自己「长」出来，而 emoji 做不到这个。
 */
export default function BrandMark({
  size = 32,
  className = '',
  level,
  tone = 'light',
}: {
  size?: number
  className?: string
  /** 传入等级就跟随该级封面配色；不传用默认靛蓝 */
  level?: number
  /** light = 深色背景上用（白线条），dark = 浅色背景上用（靛蓝线条） */
  tone?: 'light' | 'dark'
}) {
  const theme = level ? themeOf(level) : null
  const main = tone === 'light' ? '#ffffff' : theme?.accent ?? '#4f46e5'
  const sub =
    tone === 'light'
      ? theme?.glow[0] ?? 'rgba(255,255,255,0.72)'
      : theme
        ? '#818cf8'
        : '#818cf8'

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 34 34"
      fill="none"
      aria-hidden="true"
      className={className}
    >
      <circle cx="17" cy="17" r="7.5" stroke={main} strokeWidth="2.3" />
      <ellipse
        cx="17"
        cy="17"
        rx="14"
        ry="5"
        stroke={sub}
        strokeWidth="1.5"
        opacity="0.9"
        transform="rotate(-22 17 17)"
      />
      <circle cx="28.6" cy="9.4" r="1.8" fill={main} />
      <circle cx="5.4" cy="23.8" r="1.35" fill={sub} />
    </svg>
  )
}
