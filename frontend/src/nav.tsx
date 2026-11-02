import type { ReactNode } from 'react'
import {
  ApartmentOutlined,
  BookOutlined,
  BugOutlined,
  CommentOutlined,
  CrownOutlined,
  EnvironmentOutlined,
  FormOutlined,
  HomeOutlined,
  ReadOutlined,
  StarOutlined,
  TrophyOutlined,
  UserOutlined,
} from '@ant-design/icons'

/**
 * 全站入口的**唯一清单**。
 *
 * 桌面左侧栏、手机抽屉、首页「全部功能」宫格三处都读这一份，
 * 避免出现「加了页面但某个入口没跟上」——这次知识地图找不到入口就是这个原因：
 * 页面和路由都写好了，但手机端底部只有 4 个 Tab，抽屉里又没有它。
 *
 * 加新页面时只改这里，三个入口自动同步。
 */
export interface NavEntry {
  to: string
  label: string
  icon: ReactNode
  emoji: string
  desc: string
  /** 图标底色（Tailwind 渐变类，写在源码里才能被 JIT 扫到） */
  tone: string
}

export interface NavGroup {
  title: string
  items: NavEntry[]
}

export const NAV_GROUPS: NavGroup[] = [
  {
    title: '',
    items: [
      {
        to: '/',
        label: '首页',
        icon: <HomeOutlined />,
        emoji: '🏠',
        desc: '入口大厅',
        tone: 'from-slate-500 to-slate-600',
      },
    ],
  },
  {
    title: '学习',
    items: [
      {
        to: '/learn',
        label: '引导式学习',
        icon: <BookOutlined />,
        emoji: '📚',
        desc: '12 科目 · 135 课时',
        tone: 'from-indigo-500 to-violet-500',
      },
      {
        to: '/mindmap',
        label: '思维导图',
        icon: <ApartmentOutlined />,
        emoji: '🧠',
        desc: '12 棵知识点树 · 357 个知识点',
        tone: 'from-violet-500 to-purple-500',
      },
      {
        to: '/questions',
        label: '面试考题',
        icon: <ReadOutlined />,
        emoji: '📝',
        desc: '357 题 · 带标准答案',
        tone: 'from-cyan-500 to-teal-500',
      },
      {
        to: '/levels',
        label: '关卡地图',
        icon: <EnvironmentOutlined />,
        emoji: '🗺️',
        desc: '4 种知识小游戏',
        tone: 'from-emerald-500 to-teal-500',
      },
      {
        to: '/leaderboard',
        label: '排行榜',
        icon: <TrophyOutlined />,
        emoji: '🏆',
        desc: '年级班级榜',
        tone: 'from-sky-500 to-blue-500',
      },
    ],
  },
  {
    title: '陪练',
    items: [
      {
        to: '/chat',
        label: 'AI 导师',
        icon: <CommentOutlined />,
        emoji: '💬',
        desc: '随时提问 · 流式回答',
        tone: 'from-fuchsia-500 to-rose-500',
      },
      {
        to: '/interview',
        label: '面试闯关',
        icon: <CrownOutlined />,
        emoji: '🎤',
        desc: '9 分类 × 8 题',
        tone: 'from-amber-500 to-orange-500',
      },
      {
        to: '/bugs',
        label: 'Bug 猎人',
        icon: <BugOutlined />,
        emoji: '🐛',
        desc: '限时读码找 Bug',
        tone: 'from-rose-500 to-pink-500',
      },
    ],
  },
  {
    title: '我的',
    items: [
      {
        to: '/wrong',
        label: '错题本',
        icon: <FormOutlined />,
        emoji: '📕',
        desc: '答错自动收录',
        tone: 'from-orange-500 to-red-500',
      },
      {
        to: '/favorites',
        label: '我的收藏',
        icon: <StarOutlined />,
        emoji: '⭐',
        desc: '收藏过的题目',
        tone: 'from-amber-400 to-yellow-500',
      },
      {
        to: '/profile',
        label: '个人中心',
        icon: <UserOutlined />,
        emoji: '👤',
        desc: '进度 · 成就 · 资料',
        tone: 'from-slate-500 to-gray-600',
      },
    ],
  },
]

/** 扁平化，顺序即导航顺序。抽屉和首页宫格都按它渲染。 */
export const ALL_ENTRIES: NavEntry[] = NAV_GROUPS.flatMap((g) => g.items)

/**
 * 手机底部四 Tab 只留高频的四个，其余进抽屉。
 * 「引导式学习」吃掉 /mindmap 的高亮不合适（地图是独立功能），
 * 所以 /mindmap 现在不在任何 Tab 里高亮——靠抽屉进入，符合它的次要定位。
 */
export const TAB_PATHS = ['/', '/learn', '/chat', '/profile']
