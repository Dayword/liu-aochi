import { idleDays, recentAccuracy, todayStat } from '../lib/activity'

/**
 * 小机器人的台词。
 *
 * 全部是本地拼出来的，不调模型：点它要立刻有反应，
 * 一次网络往返换一句「今天学了 3 题」不值得。
 */
export type Mood = 'idle' | 'happy' | 'worried' | 'sleep' | 'focus'

export interface LineCtx {
  mood: Mood
  level: number
  levelTitle: string
  personaName?: string
  learnTotal: number
  learnDone: number
  wrongOpen: number
  focusMinutes: number
}

const pick = <T,>(arr: T[]): T => arr[(Math.random() * arr.length) | 0]

const HOUR = new Date().getHours()
const greeting = () => {
  if (HOUR < 6) return '这个点还醒着？'
  if (HOUR < 11) return '早上好'
  if (HOUR < 14) return '中午了，先吃口饭'
  if (HOUR < 18) return '下午好'
  if (HOUR < 23) return '晚上好'
  return '夜深了，别熬太狠'
}

export function buildLine(c: LineCtx): string {
  const t = todayStat()
  if (c.mood === 'sleep') {
    return pick([
      `我已经 ${idleDays() ?? 0} 天没被点开了，灰尘都能写字了`,
      '喂……我还在的，学一课把我叫醒？',
      '再不来我就要长蘑菇了',
    ])
  }
  if (c.mood === 'focus') {
    return pick(['耳机戴好了，这 25 分钟我陪你', '专注中，别摸手机', '有人陪你熬，时间过得快一点'])
  }
  if (c.mood === 'worried') {
    return pick([
      '最近几题不太顺，要不要从错题本看看？',
      `错题本还压着 ${c.wrongOpen} 道没看解析，先解决它们？`,
      '正确率掉下来了，慢一点没关系',
    ])
  }
  if (c.mood === 'happy') {
    return pick([
      `连对这么多，你现在是 ${c.levelTitle}`,
      '这个状态很适合啃硬骨头，继续',
      `今天第 ${t.answers} 题，手感在线`,
    ])
  }
  if (c.learnDone >= c.learnTotal && c.learnTotal > 0) {
    return pick(['主线全清了，现在可以随便翻翻面试题', '全部学完了，剩下的就是重复和面试'])
  }
  if (t.answers === 0) {
    return pick([
      `${greeting()}。今天还一题没答`,
      `主线 ${c.learnDone}/${c.learnTotal}，还差 ${c.learnTotal - c.learnDone} 课`,
      '点我一下不如点开一课',
    ])
  }
  return pick([
    `今天答了 ${t.answers} 题，对了 ${t.correct} 题`,
    `主线 ${c.learnDone}/${c.learnTotal}，按这个速度还行`,
    c.focusMinutes > 0 ? `今天专注了 ${c.focusMinutes} 分钟` : '今天还没开番茄钟',
  ])
}

/** 彩蛋模式下多出来的奇怪台词，只在 easter 打开时混进去 */
export const RARE_LINES = [
  '我曾经也是一台服务器，直到被折价回收',
  '别问我第 42 课在哪，我只负责可爱',
  '如果你看到这条，说明你真的点了很多下',
  'BFS 会找到最短路径，但找不到女朋友',
]

export function accuracyText(): string {
  const a = recentAccuracy()
  if (a === null) return '还没有答题记录'
  return `最近 10 题正确率 ${Math.round(a * 100)}%`
}
