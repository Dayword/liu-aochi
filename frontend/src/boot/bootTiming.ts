/**
 * 入场动画的时间令牌。
 *
 * 曲线只有三条，全部来自「进场用 ease-out 家族」这条硬规则：
 *   ENTER  强调式 ease-out，落定用（描边收笔、光带扫过）
 *   SOFT   标准 ease-out，位移/淡入用
 *   INOUT  进出对称，场景推进用
 *
 * 时长单独列出，不散在代码里 —— 想调快调慢只改这张表，不用翻实现。
 * 数值单位都是毫秒，且是「从画面出现算起」的绝对时间点。
 */
export const BOOT_EASE = {
  ENTER: 'cubic-bezier(0.23, 1, 0.32, 1)',
  SOFT: 'cubic-bezier(0.22, 1, 0.36, 1)',
  /** 擦除/位移用：比 ENTER 平缓，前段不会「一下就到 96%」 */
  WIPE: 'cubic-bezier(0.33, 1, 0.68, 1)',
  INOUT: 'cubic-bezier(0.77, 0, 0.175, 1)',
} as const

export interface BootTiming {
  /** 整段时长（含入场波次） */
  total: number
  /** 底色与点缀淡入 */
  bgIn: number
  /** 轨道自己画出来 */
  orbit: number
  orbitDur: number
  /** 行星圆画出来 */
  planet: number
  planetDur: number
  /** 两颗小星点弹出 */
  dots: number
  dotsDur: number
  /** 字标从左擦出 */
  word: number
  wordDur: number
  /** 字距收拢（营造「落定」感） */
  track: number
  trackDur: number
  /** 轨道向外扩散一次 */
  pulse: number
  pulseDur: number
  /** 场景推进淡出 */
  out: number
  outDur: number
  /** UI 环环入场起点 */
  wave: number
  /** 露出界面后多久算结束 */
  end: number
  /** 等页面就绪的上限（超过就直接揭幕，绝不压着黑幕） */
  readyTimeout: number
}

export const BOOT_TIMING: Record<'desktop' | 'mobile', BootTiming> = {
  desktop: {
    total: 3060,
    bgIn: 0,
    orbit: 180,
    orbitDur: 700,
    planet: 500,
    planetDur: 620,
    dots: 1120,
    dotsDur: 200,
    word: 1000,
    wordDur: 760,
    track: 1080,
    trackDur: 900,
    pulse: 1700,
    pulseDur: 900,
    out: 2400,
    outDur: 460,
    wave: 2380,
    end: 3040,
    readyTimeout: 1200,
  },
  mobile: {
    total: 2420,
    bgIn: 0,
    orbit: 140,
    orbitDur: 560,
    planet: 380,
    planetDur: 480,
    dots: 800,
    dotsDur: 170,
    word: 700,
    wordDur: 600,
    track: 780,
    trackDur: 720,
    pulse: 1280,
    pulseDur: 700,
    out: 1800,
    outDur: 400,
    wave: 1780,
    end: 2400,
    readyTimeout: 1000,
  },
}

/** 星点位置（百分比，贴边分布，避开中心字标）。 */
export const BOOT_STARS: [number, number, number][] = [
  [8, 16, 1.4],
  [22, 34, 1],
  [78, 12, 1.2],
  [90, 30, 1],
  [12, 76, 1.1],
  [30, 88, 1.3],
  [70, 84, 1],
  [88, 68, 1.5],
  [50, 10, 0.9],
  [64, 42, 0.8],
]
