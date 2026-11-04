/**
 * 全站主题表 —— **唯一数据源**。
 *
 * 一套主题 = 一组语义 token，切换时只改 `html` 上的 CSS 变量，
 * 页面里不用感知主题（详见 theme.css 的中性色映射）。
 * 加一套新主题 = 在 THEMES 里加一个对象 + 在 Settings 的预览网格里自动出现。
 *
 * 取值原则：
 * 1. **深浅各 5 套，色相分散**（米/绿/粉/报纸/蓝/灰/黑/霓虹/青），
 *    避免"10 套都是换个色相的紫"这种假多样。
 * 2. 深色不是简单反色：底色压得够深（L < 12%），面板比底色亮一级，
 *    这样层次靠"面板比底亮"建立，而不是靠阴影——深色下阴影几乎看不见。
 * 3. 正文色对比度全部 ≥ 7:1（AAA），次要文字 ≥ 4.5:1。
 *    学生长时间看屏幕，灰字太白/太黑都难受。
 * 4. `swatch` 是选择卡片上的三色预览（底 / 品牌 / 强调），
 *    必须和真实运行时一致，否则选了发现"和预览不一样"。
 */
export type ThemeMode = 'light' | 'dark'

export interface ThemeVars {
  /** 页面底色 */
  bg: string
  /** 卡片 / 侧栏 / 弹窗 */
  panel: string
  /** 次级面板：表头、hover 底、输入框底 */
  panelAlt: string
  /** 主文字 */
  ink: string
  /** 次要文字 */
  ink2: string
  /** 三级文字：占位符、辅助说明 */
  ink3: string
  /** 描边 */
  line: string
  /** 带品牌色调的描边（选中卡片、分隔线） */
  lineBrand: string
  /** 品牌主色 */
  brand: string
  /** 品牌深色（标题、链接） */
  brandDark: string
  /** 品牌淡底（选中态背景） */
  brandSoft: string
  /** 压在品牌色上的文字 */
  onBrand: string
  /** 点缀色：等级、金币、强调 */
  accent: string
  /** 背景两处光斑 */
  glow1: string
  glow2: string
}

export interface ThemeDef {
  id: string
  name: string
  /** 一句话气质描述，选择卡片上用 */
  desc: string
  mode: ThemeMode
  /** 预览卡三色：底 / 品牌 / 强调 */
  swatch: [string, string, string]
  /** 复古报这类主题换成衬线正文 */
  serif?: boolean
  vars: ThemeVars
}

export const THEMES: ThemeDef[] = [
  // ======================= 浅色 5 套 =======================
  {
    id: 'daylight',
    name: '极简白',
    desc: '默认。干净通透，长时间看最不累',
    mode: 'light',
    swatch: ['#f6f7fb', '#6366f1', '#d97706'],
    vars: {
      bg: '#f6f7fb',
      panel: '#ffffff',
      panelAlt: '#f1f3f9',
      ink: '#1f2430',
      ink2: '#64748b',
      ink3: '#94a3b8',
      line: '#e2e8f0',
      lineBrand: '#c7d2fe',
      brand: '#6366f1',
      brandDark: '#4f46e5',
      brandSoft: '#eef2ff',
      onBrand: '#ffffff',
      accent: '#d97706',
      glow1: 'rgba(99,102,241,0.07)',
      glow2: 'rgba(251,191,36,0.06)',
    },
  },
  {
    id: 'parchment',
    name: '暖阳米',
    desc: '米黄纸感，夜里不刺眼',
    mode: 'light',
    swatch: ['#faf6ee', '#b45309', '#0f766e'],
    vars: {
      bg: '#faf6ee',
      panel: '#fffdf8',
      panelAlt: '#f5efe2',
      ink: '#3b2f21',
      ink2: '#7c6a52',
      ink3: '#a89880',
      line: '#e6dcc8',
      lineBrand: '#e8d5ae',
      brand: '#b45309',
      brandDark: '#92400e',
      brandSoft: '#fdf1de',
      onBrand: '#fff8ec',
      accent: '#0f766e',
      glow1: 'rgba(180,83,9,0.06)',
      glow2: 'rgba(15,118,110,0.05)',
    },
  },
  {
    id: 'forest',
    name: '森林绿',
    desc: '低饱和绿，像在草稿纸背面写代码',
    mode: 'light',
    swatch: ['#f1f7f1', '#15803d', '#ca8a04'],
    vars: {
      bg: '#f1f7f1',
      panel: '#ffffff',
      panelAlt: '#e8f2e8',
      ink: '#1c2b21',
      ink2: '#55705e',
      ink3: '#86a08d',
      line: '#d5e6d8',
      lineBrand: '#bbdcc2',
      brand: '#15803d',
      brandDark: '#166534',
      brandSoft: '#e7f6ea',
      onBrand: '#ffffff',
      accent: '#ca8a04',
      glow1: 'rgba(21,128,61,0.07)',
      glow2: 'rgba(202,138,4,0.05)',
    },
  },
  {
    id: 'sakura',
    name: '樱花粉',
    desc: '淡粉不腻，界面显得轻',
    mode: 'light',
    swatch: ['#fdf2f6', '#db2777', '#7c3aed'],
    vars: {
      bg: '#fdf2f6',
      panel: '#ffffff',
      panelAlt: '#fce9f0',
      ink: '#3a1f2b',
      ink2: '#8a5f70',
      ink3: '#b78c9c',
      line: '#f5dbe5',
      lineBrand: '#f0c4d6',
      brand: '#db2777',
      brandDark: '#be185d',
      brandSoft: '#fde8f1',
      onBrand: '#ffffff',
      accent: '#7c3aed',
      glow1: 'rgba(219,39,119,0.06)',
      glow2: 'rgba(124,58,237,0.05)',
    },
  },
  {
    id: 'newsprint',
    name: '复古报',
    desc: '米白油墨 + 衬线字，像旧杂志',
    mode: 'light',
    serif: true,
    swatch: ['#f4f1e8', '#1f2937', '#92400e'],
    vars: {
      bg: '#f4f1e8',
      panel: '#fbf9f2',
      panelAlt: '#efeade',
      ink: '#1f2937',
      ink2: '#5b6472',
      ink3: '#8b93a1',
      line: '#ddd6c4',
      lineBrand: '#cfc6b1',
      brand: '#1f2937',
      brandDark: '#111827',
      brandSoft: '#e8e4d6',
      onBrand: '#f9f7ef',
      accent: '#92400e',
      glow1: 'rgba(31,41,55,0.05)',
      glow2: 'rgba(146,64,14,0.04)',
    },
  },

  // ======================= 深色 5 套 =======================
  {
    id: 'midnight',
    name: '午夜蓝',
    desc: '深蓝底 + 靛紫主色，最像码境',
    mode: 'dark',
    swatch: ['#0f172a', '#6366f1', '#fbbf24'],
    vars: {
      bg: '#0f172a',
      panel: '#1a2338',
      panelAlt: '#141d31',
      ink: '#e6ecf7',
      ink2: '#9fb0cc',
      ink3: '#6b7d9c',
      line: '#2a3752',
      lineBrand: '#3b4b73',
      brand: '#6366f1',
      brandDark: '#a5b4fc',
      brandSoft: '#23304d',
      onBrand: '#ffffff',
      accent: '#fbbf24',
      glow1: 'rgba(99,102,241,0.14)',
      glow2: 'rgba(56,189,248,0.09)',
    },
  },
  {
    id: 'graphite',
    name: '石墨黑',
    desc: '中性灰 + 银灰主色，克制耐看',
    mode: 'dark',
    swatch: ['#17181c', '#94a3b8', '#f59e0b'],
    vars: {
      bg: '#17181c',
      panel: '#212228',
      panelAlt: '#1b1c21',
      ink: '#f1f2f4',
      ink2: '#a8acb6',
      ink3: '#72767f',
      line: '#2e3037',
      lineBrand: '#3a3d46',
      brand: '#94a3b8',
      brandDark: '#cbd5e1',
      brandSoft: '#2b2e36',
      onBrand: '#14161a',
      accent: '#f59e0b',
      glow1: 'rgba(148,163,184,0.10)',
      glow2: 'rgba(245,158,11,0.06)',
    },
  },
  {
    id: 'oled',
    name: '纯黑 OLED',
    desc: '真黑省电，夜里最暗',
    mode: 'dark',
    swatch: ['#000000', '#22d3ee', '#a3e635'],
    vars: {
      bg: '#000000',
      panel: '#0b0b0e',
      panelAlt: '#08080a',
      ink: '#fafafa',
      ink2: '#a1a1aa',
      ink3: '#71717a',
      line: '#1f1f24',
      lineBrand: '#2a2a32',
      brand: '#22d3ee',
      brandDark: '#67e8f9',
      brandSoft: '#102a30',
      onBrand: '#04191d',
      accent: '#a3e635',
      glow1: 'rgba(34,211,238,0.12)',
      glow2: 'rgba(163,230,53,0.06)',
    },
  },
  {
    id: 'cyber',
    name: '赛博霓虹',
    desc: '紫底品红霓虹，最张扬的一套',
    mode: 'dark',
    swatch: ['#0a0520', '#d946ef', '#22d3ee'],
    vars: {
      bg: '#0a0520',
      panel: '#150b33',
      panelAlt: '#0f0727',
      ink: '#f3e8ff',
      ink2: '#bfa8e8',
      ink3: '#8a72b8',
      line: '#2e1b57',
      lineBrand: '#442a7a',
      brand: '#d946ef',
      brandDark: '#f0abfc',
      brandSoft: '#26124a',
      onBrand: '#ffffff',
      accent: '#22d3ee',
      glow1: 'rgba(217,70,239,0.20)',
      glow2: 'rgba(34,211,238,0.14)',
    },
  },
  {
    id: 'aurora',
    name: '极光',
    desc: '深青底 + 荧光绿，冷得很安静',
    mode: 'dark',
    swatch: ['#04201c', '#34d399', '#a78bfa'],
    vars: {
      bg: '#04201c',
      panel: '#0a2f28',
      panelAlt: '#06261f',
      ink: '#e3fbf4',
      ink2: '#94c9bb',
      ink3: '#5f968a',
      line: '#16453b',
      lineBrand: '#1f5c4d',
      brand: '#34d399',
      brandDark: '#6ee7b7',
      brandSoft: '#0f3a31',
      onBrand: '#03251d',
      accent: '#a78bfa',
      glow1: 'rgba(52,211,153,0.14)',
      glow2: 'rgba(167,139,250,0.10)',
    },
  },
]

export const THEME_BY_ID: Record<string, ThemeDef> = Object.fromEntries(
  THEMES.map((t) => [t.id, t]),
)

export const DEFAULT_THEME_ID = 'daylight'

/** CSS 变量名映射：加 token 只改这里 */
export const VAR_MAP: Record<keyof ThemeVars, string> = {
  bg: '--t-bg',
  panel: '--t-panel',
  panelAlt: '--t-panel-alt',
  ink: '--t-ink',
  ink2: '--t-ink-2',
  ink3: '--t-ink-3',
  line: '--t-line',
  lineBrand: '--t-line-brand',
  brand: '--t-brand',
  brandDark: '--t-brand-dark',
  brandSoft: '--t-brand-soft',
  onBrand: '--t-on-brand',
  accent: '--t-accent',
  glow1: '--t-glow-1',
  glow2: '--t-glow-2',
}
