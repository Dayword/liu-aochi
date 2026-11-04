/**
 * 内置壁纸：全部是纯 CSS 渐变 / 重复渐变，没有图片文件。
 *
 * 为什么不用图：一张 1600px 的星空 JPEG 压缩后也有 200KB+，而这里
 * 六张加起来是 0 字节请求，且在任意分辨率下都不糊。
 * 自定义图片另走 IndexedDB（见 lib/idb.ts），不上传服务器。
 */
export interface Wallpaper {
  id: string
  name: string
  /** 直接塞进 background-image 的值 */
  css: string
  /** 缩略图预览（卡片里用，尺寸小所以单独写一份） */
  thumb: string
  /** 亮 / 暗：决定遮罩用不用反色描边 */
  tone: 'light' | 'dark'
}

const stars = (dots: string, size: string) =>
  `radial-gradient(circle at 12% 18%, ${dots} 1.2px, transparent 1.4px),
   radial-gradient(circle at 68% 8%, ${dots} 1px, transparent 1.2px),
   radial-gradient(circle at 38% 62%, ${dots} 1.5px, transparent 1.7px),
   radial-gradient(circle at 86% 44%, ${dots} 1.1px, transparent 1.3px),
   radial-gradient(circle at 22% 78%, ${dots} 1px, transparent 1.2px),
   radial-gradient(circle at 92% 82%, ${dots} 1.3px, transparent 1.5px),
   ${size}`

export const WALLPAPERS: Wallpaper[] = [
  {
    id: 'none',
    name: '无',
    css: 'none',
    thumb: 'none',
    tone: 'light',
  },
  {
    id: 'aurora',
    name: '极光',
    css: `radial-gradient(ellipse 70% 55% at 15% 0%, rgba(16,185,129,0.30), transparent 65%),
          radial-gradient(ellipse 60% 50% at 90% 12%, rgba(59,130,246,0.26), transparent 62%),
          radial-gradient(ellipse 80% 50% at 60% 100%, rgba(139,92,246,0.22), transparent 68%)`,
    thumb: 'linear-gradient(135deg,#0f766e,#0ea5e9 55%,#7c3aed)',
    tone: 'dark',
  },
  {
    id: 'dusk',
    name: '暮色',
    css: `radial-gradient(ellipse 75% 55% at 85% 0%, rgba(244,114,182,0.28), transparent 62%),
          radial-gradient(ellipse 70% 50% at 10% 20%, rgba(251,146,60,0.26), transparent 60%),
          radial-gradient(ellipse 90% 60% at 50% 110%, rgba(99,102,241,0.24), transparent 70%)`,
    thumb: 'linear-gradient(135deg,#fb923c,#f472b6 55%,#6366f1)',
    tone: 'dark',
  },
  {
    id: 'starfield',
    name: '星野',
    css: stars('rgba(255,255,255,0.55)', `
      radial-gradient(ellipse 80% 60% at 20% 0%, rgba(56,189,248,0.18), transparent 60%),
      radial-gradient(ellipse 70% 60% at 90% 30%, rgba(168,85,247,0.20), transparent 62%),
      linear-gradient(180deg, #0b1020 0%, #0d1424 55%, #131a2e 100%)`),
    thumb: 'linear-gradient(160deg,#0b1020,#1e293b)',
    tone: 'dark',
  },
  {
    id: 'ocean',
    name: '海面',
    css: `repeating-linear-gradient(180deg, rgba(14,165,233,0.10) 0 2px, transparent 2px 26px),
          radial-gradient(ellipse 90% 60% at 50% -10%, rgba(56,189,248,0.28), transparent 62%),
          linear-gradient(180deg, rgba(8,145,178,0.16), transparent 70%)`,
    thumb: 'linear-gradient(180deg,#38bdf8,#0369a1)',
    tone: 'dark',
  },
  {
    id: 'paper',
    name: '纸感',
    css: `repeating-linear-gradient(0deg, rgba(120,113,108,0.055) 0 1px, transparent 1px 3px),
          radial-gradient(ellipse 70% 50% at 20% 0%, rgba(251,191,36,0.14), transparent 62%)`,
    thumb: 'linear-gradient(135deg,#fdf6e3,#e7e0cf)',
    tone: 'light',
  },
  {
    id: 'sakura',
    name: '樱',
    css: `radial-gradient(ellipse 60% 45% at 15% 8%, rgba(244,114,182,0.26), transparent 62%),
          radial-gradient(ellipse 55% 40% at 88% 22%, rgba(251,113,133,0.20), transparent 60%),
          radial-gradient(ellipse 70% 45% at 50% 105%, rgba(196,181,253,0.22), transparent 65%)`,
    thumb: 'linear-gradient(135deg,#fbcfe8,#f9a8d4 50%,#c4b5fd)',
    tone: 'light',
  },
  {
    id: 'custom',
    name: '自定义',
    css: 'none',
    thumb: '',
    tone: 'dark',
  },
]

export const WALL_BY_ID: Record<string, Wallpaper> = Object.fromEntries(
  WALLPAPERS.map((w) => [w.id, w]),
)

/** 自定义图在所有主题下都压一层底色，避免深色主题里白图刺眼 */
export function customWallCss(url: string): string {
  return `linear-gradient(color-mix(in srgb, var(--t-bg) 72%, transparent), color-mix(in srgb, var(--t-bg) 82%, transparent)), url("${url}")`
}

/** 内置壁纸也压一层，保证卡片上的文字对比度（纸感、樱这类浅壁纸尤其需要） */
export function wallCss(id: string, customUrl?: string | null): string {
  if (!id || id === 'none') return 'none'
  if (id === 'custom') return customUrl ? customWallCss(customUrl) : 'none'
  const w = WALL_BY_ID[id]
  if (!w || w.css === 'none') return 'none'
  // 深色壁纸压得轻一点：压到 46% 时星空会变成一片灰，看不出是壁纸。
  // 可读性由卡片本身保证（面板全是不透明的），背景只需要不刺眼。
  const alpha = w.tone === 'light' ? 62 : 22
  return `linear-gradient(color-mix(in srgb, var(--t-bg) ${alpha}%, transparent), color-mix(in srgb, var(--t-bg) ${alpha + 12}%, transparent)), ${w.css}`
}
