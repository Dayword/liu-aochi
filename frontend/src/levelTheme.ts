/**
 * 等级视觉主题：13 级，一级一套「称号 + 图标 + 首页封面」。
 *
 * 为什么单开一个文件：称号不只出现在首页海报上，个人中心、排行榜、
 * 升级弹窗都要用同一套配色。散在各页面里写死颜色，改一次要改五处。
 *
 * 配色原则：三档渐变都压得够深（最亮一档也保证白字对比度 > 4.5），
 * 因为海报上压着姓名和等级，底色一浅字就糊了。accent 是唯一的高亮色，
 * 只给经验环和经验条用，不超过一个色相，避免封面变成调色盘。
 */
export type Motif =
  | 'rubble' | 'clearing' | 'rail' | 'bridge' | 'lamp' | 'night' | 'web'
  | 'compass' | 'crack' | 'build' | 'lanterns' | 'constellation' | 'cosmos'

/** 底纹。13 张封面各配一种，避免「同一张底图只换色」的廉价感。 */
export type Texture = 'grid' | 'dots' | 'stripes' | 'weave' | 'scan' | 'none'

export interface LevelTheme {
  level: number
  title: string
  icon: string
  /** 背景渐变三停（左 → 中 → 右） */
  sky: [string, string, string]
  /** 两处光斑 */
  glow: [string, string]
  /** 经验环 / 经验条强调色 */
  accent: string
  /** 封面装饰图层 */
  motif: Motif
  /** 封面底纹 */
  texture: Texture
  /** 一句「这一级在干什么」，升级弹窗与个人中心用 */
  note: string
}

export const LEVEL_THEMES: LevelTheme[] = [
  {
    level: 1, title: '拾荒者', icon: '🪨', motif: 'rubble',
    texture: 'none',
    sky: ['#52525b', '#71717a', '#27272a'],
    glow: ['#a1a1aa', '#71717a'], accent: '#d4d4d8',
    note: '在语法废墟里捡碎片，先攒够能跑起来的零件',
  },
  {
    level: 2, title: '拓荒者', icon: '🪓', motif: 'clearing',
    texture: 'stripes',
    sky: ['#4d7c0f', '#65a30d', '#243b06'],
    glow: ['#bef264', '#84cc16'], accent: '#bef264',
    note: '砍掉第一片荒地：变量、循环、函数能连起来写了',
  },
  {
    level: 3, title: '筑路者', icon: '🛤️', motif: 'rail',
    texture: 'scan',
    sky: ['#92400e', '#b45309', '#292524'],
    glow: ['#fcd34d', '#f59e0b'], accent: '#fcd34d',
    note: '把零散知识铺成路：数据库、网络开始接上主线',
  },
  {
    level: 4, title: '架桥者', icon: '🌉', motif: 'bridge',
    texture: 'grid',
    sky: ['#075985', '#0284c7', '#082f49'],
    glow: ['#7dd3fc', '#38bdf8'], accent: '#7dd3fc',
    note: '能在两个世界之间搭桥：代码调得动数据库和接口了',
  },
  {
    level: 5, title: '点灯人', icon: '🕯️', motif: 'lamp',
    texture: 'dots',
    sky: ['#9a3412', '#ea580c', '#431407'],
    glow: ['#fdba74', '#fb923c'], accent: '#fdba74',
    note: '第一次给别人讲明白一个概念，灯亮了一小片',
  },
  {
    level: 6, title: '守夜人', icon: '🌙', motif: 'night',
    texture: 'none',
    sky: ['#312e81', '#4338ca', '#0f172a'],
    glow: ['#c7d2fe', '#818cf8'], accent: '#c7d2fe',
    note: '线上出问题时能扛住，看得懂日志也敢改代码',
  },
  {
    level: 7, title: '织网者', icon: '🕸️', motif: 'web',
    texture: 'weave',
    sky: ['#115e59', '#0d9488', '#042f2e'],
    glow: ['#5eead4', '#2dd4bf'], accent: '#5eead4',
    note: '服务之间开始连成网：缓存、消息、检索各就各位',
  },
  {
    level: 8, title: '引航员', icon: '🧭', motif: 'compass',
    texture: 'grid',
    sky: ['#155e75', '#0891b2', '#083344'],
    glow: ['#67e8f9', '#22d3ee'], accent: '#67e8f9',
    note: '能定方向：技术选型、拆任务、带一个模块往前走',
  },
  {
    level: 9, title: '破壁人', icon: '🔨', motif: 'crack',
    texture: 'none',
    sky: ['#991b1b', '#dc2626', '#450a0a'],
    glow: ['#fca5a5', '#f87171'], accent: '#fca5a5',
    note: '专挑硬骨头：性能、并发、RAG 效果，一层层砸开',
  },
  {
    level: 10, title: '造境者', icon: '🏗️', motif: 'build',
    texture: 'grid',
    sky: ['#5b21b6', '#7c3aed', '#2e1065'],
    glow: ['#c4b5fd', '#a78bfa'], accent: '#c4b5fd',
    note: '不再只解题，开始自己造一个能跑起来的系统',
  },
  {
    level: 11, title: '掌灯使', icon: '🏮', motif: 'lanterns',
    texture: 'stripes',
    sky: ['#a16207', '#ca8a04', '#422006'],
    glow: ['#fde047', '#facc15'], accent: '#fde047',
    note: '手里这盏灯能照亮别人：写文档、做分享、带新人',
  },
  {
    level: 12, title: '观星者', icon: '🔭', motif: 'constellation',
    texture: 'dots',
    sky: ['#1e3a8a', '#2563eb', '#020617'],
    glow: ['#93c5fd', '#60a5fa'], accent: '#93c5fd',
    note: '看得见全局：系统怎么长、瓶颈在哪、明年该补什么',
  },
  {
    level: 13, title: '开天者', icon: '🌌', motif: 'cosmos',
    texture: 'none',
    sky: ['#6b21a8', '#a21caf', '#0e7490'],
    glow: ['#f0abfc', '#e879f9'], accent: '#f0abfc',
    note: '135 课全部通关，从语法废土一路走到自己开天',
  },
]

export const MAX_LEVEL = LEVEL_THEMES.length

/** 越界一律夹到 1~13，避免脏数据把首页渲染成空白。 */
export function themeOf(level: number): LevelTheme {
  const i = Math.min(Math.max(Math.round(level) || 1, 1), MAX_LEVEL)
  return LEVEL_THEMES[i - 1]
}
