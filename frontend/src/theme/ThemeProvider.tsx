import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { App as AntApp, ConfigProvider, theme as antdTheme } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { MotionConfig } from 'framer-motion'
import { DEFAULT_THEME_ID, THEMES, THEME_BY_ID, VAR_MAP } from './themes'
import type { ThemeDef, ThemeVars } from './themes'
import { wallCss } from './wallpapers'
import { getWallpaper } from '../lib/idb'
import { armAmbient } from '../audio/ambient'
import './theme.css'

/* ============================================================
 * 设置项定义
 * ========================================================== */

export type UiScale = 1 | 1.08 | 1.16
export type Texture = 'none' | 'grid' | 'dots' | 'scan'
export type CodeFont = 'mono' | 'cascadia' | 'consolas' | 'fira'
/** 环境音：全部用 Web Audio 实时合成，不引音频文件 */
export type AmbientId = 'none' | 'rain' | 'cafe' | 'keys' | 'white'
/** AI 导师人格：只改提示词，不改模型 */
export type PersonaId = 'warm' | 'strict' | 'snarky'
export type RobotSize = 'sm' | 'md' | 'lg'
export type RobotCorner = 'br' | 'bl'

export interface Settings {
  /** 主题 id */
  themeId: string
  /** 界面缩放（整体 zoom） */
  scale: UiScale
  /** 入场动画开关 */
  boot: boolean
  /** 界面过渡动效（关掉后所有 transition/animation 立即完成） */
  motion: boolean
  /** 背景纹理 */
  texture: Texture
  /** 壁纸：none / 内置 id / custom */
  wallpaper: string
  /** 高对比：描边与次要文字加深 */
  contrast: 'normal' | 'high'
  /** 键盘焦点描边 */
  focusRing: boolean
  /** 代码字号 */
  codeFontSize: number
  /** 代码字体 */
  codeFont: CodeFont
  /** Tab 宽度 */
  tabWidth: 2 | 4
  /** 代码自动换行 */
  wrap: boolean
  /** 环境音 */
  ambient: AmbientId
  /** 环境音音量 0~1 */
  ambientVolume: number
  /** 点击 / 答对 / 升级特效 */
  effects: boolean
  /** 伴学小机器人 */
  robot: boolean
  robotSize: RobotSize
  robotCorner: RobotCorner
  /** AI 导师人格 */
  persona: PersonaId
  /** 番茄钟时长（分钟） */
  focusMinutes: 25 | 45 | 50
  /** 专注时自动开环境音 */
  focusSound: boolean
  /** 彩蛋模式（连点 logo 7 次解锁） */
  easter: boolean
}

export const DEFAULT_SETTINGS: Settings = {
  themeId: DEFAULT_THEME_ID,
  scale: 1,
  boot: true,
  motion: true,
  texture: 'none',
  wallpaper: 'none',
  contrast: 'normal',
  focusRing: true,
  codeFontSize: 13,
  codeFont: 'mono',
  tabWidth: 4,
  wrap: true,
  ambient: 'none',
  ambientVolume: 0.35,
  effects: true,
  robot: true,
  robotSize: 'md',
  robotCorner: 'br',
  persona: 'warm',
  focusMinutes: 25,
  focusSound: true,
  easter: false,
}

export const PERSONA_LABEL: Record<PersonaId, string> = {
  warm: '温柔学姐',
  strict: '严厉面试官',
  snarky: '毒舌同事',
}

export const CODE_FONT_STACK: Record<CodeFont, string> = {
  mono: "'JetBrains Mono','Cascadia Code',Consolas,'Courier New',monospace",
  cascadia: "'Cascadia Code','Cascadia Mono',Consolas,monospace",
  consolas: "Consolas,'Courier New',monospace",
  fira: "'Fira Code','JetBrains Mono',Consolas,monospace",
}

const KEY = 'ca_settings_v1'

/** 读取设置：任何字段坏了都回退默认值，不让一条脏数据把整站变白屏 */
export function loadSettings(): Settings {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return DEFAULT_SETTINGS
    const parsed = JSON.parse(raw) as Partial<Settings>
    const merged = { ...DEFAULT_SETTINGS, ...parsed }
    if (!THEME_BY_ID[merged.themeId]) merged.themeId = DEFAULT_THEME_ID
    return merged
  } catch {
    return DEFAULT_SETTINGS
  }
}

function saveSettings(s: Settings) {
  try {
    localStorage.setItem(KEY, JSON.stringify(s))
  } catch {
    /* 隐私模式下 localStorage 可能不可写，忽略即可 */
  }
}

/**
 * 把设置写进 DOM。
 *
 * 变量写在 `documentElement` 上而不是某个容器：AntD 的弹层、Popover、Drawer
 * 都是挂到 body 下的 portal，变量挂在容器里它们读不到，会变成默认白底。
 */
export function applySettings(s: Settings, customWallUrl?: string | null) {
  const theme = THEME_BY_ID[s.themeId] ?? THEMES[0]
  const root = document.documentElement

  root.dataset.theme = theme.id
  root.dataset.mode = theme.mode
  root.dataset.texture = s.texture
  root.dataset.contrast = s.contrast
  root.dataset.motion = s.motion ? 'on' : 'off'
  root.dataset.focus = s.focusRing ? 'on' : 'off'
  root.dataset.wall = s.wallpaper === 'none' ? 'off' : 'on'
  root.dataset.scale = String(s.scale)
  root.style.setProperty('--ui-scale', String(s.scale))
  root.style.setProperty('--wall-bg', wallCss(s.wallpaper, customWallUrl))

  for (const [k, cssVar] of Object.entries(VAR_MAP)) {
    root.style.setProperty(cssVar, theme.vars[k as keyof ThemeVars])
  }
  root.style.setProperty(
    '--code-font',
    CODE_FONT_STACK[s.codeFont] ?? CODE_FONT_STACK.mono,
  )
  root.style.setProperty('--code-size', `${s.codeFontSize}px`)
  root.style.setProperty('--code-line', `${Math.round(s.codeFontSize * 1.7)}px`)

  // 主题自带深浅，浏览器的滚动条/表单控件跟着变
  root.style.colorScheme = theme.mode
}

/* 自定义壁纸：Blob 存在 IndexedDB，读出来转 objectURL 缓存住，
   否则每次改设置都要重新解码一张 1600px 的图。 */
let CUSTOM_WALL_URL: string | null = null
let customWallPromise: Promise<string | null> | null = null

export function loadCustomWall(): Promise<string | null> {
  if (CUSTOM_WALL_URL) return Promise.resolve(CUSTOM_WALL_URL)
  if (!customWallPromise) {
    customWallPromise = getWallpaper()
      .then((blob) => {
        if (!blob) return null
        CUSTOM_WALL_URL = URL.createObjectURL(blob)
        return CUSTOM_WALL_URL
      })
      .catch(() => null)
  }
  return customWallPromise
}

/** 换了图 / 删了图之后调用，让下次读取拿到新的 Blob */
export function resetCustomWallCache() {
  if (CUSTOM_WALL_URL) URL.revokeObjectURL(CUSTOM_WALL_URL)
  CUSTOM_WALL_URL = null
  customWallPromise = null
}

/** 模块加载即应用一次：早于 React 渲染，避免「先白一帧再变深」 */
export const BOOT_SETTINGS = loadSettings()
applySettings(BOOT_SETTINGS)

/* ============================================================
 * Context
 * ========================================================== */

interface Ctx {
  settings: Settings
  theme: ThemeDef
  /** 改单个字段 */
  set: <K extends keyof Settings>(key: K, value: Settings[K]) => void
  /** 批量改（如「恢复默认」） */
  patch: (p: Partial<Settings>) => void
  reset: () => void
}

const SettingsCtx = createContext<Ctx | null>(null)

const SANS =
  "'Segoe UI','PingFang SC','Microsoft YaHei',system-ui,sans-serif"
const SERIF =
  "'Songti SC','STSong',Georgia,'Noto Serif SC','Source Han Serif SC',serif"

/** AntD 的 token 跟着主题走：不接这一层，深色下弹窗/下拉/日期选择器全是白块 */
function buildAntdTheme(theme: ThemeDef, highContrast: boolean) {
  const dark = theme.mode === 'dark'
  return {
    algorithm: dark ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
    token: {
      colorPrimary: theme.vars.brand,
      colorInfo: theme.vars.brand,
      colorLink: theme.vars.brandDark,
      colorSuccess: dark ? '#34d399' : '#059669',
      colorWarning: dark ? '#fbbf24' : '#d97706',
      colorError: dark ? '#fb7185' : '#e11d48',
      colorBgBase: theme.vars.bg,
      colorBgContainer: theme.vars.panel,
      colorBgElevated: theme.vars.panel,
      colorBgLayout: theme.vars.bg,
      colorText: theme.vars.ink,
      colorTextSecondary: theme.vars.ink2,
      colorTextTertiary: theme.vars.ink3,
      colorBorder: highContrast ? theme.vars.ink3 : theme.vars.line,
      colorBorderSecondary: theme.vars.line,
      borderRadius: 10,
      fontFamily: theme.serif ? SERIF : SANS,
    },
  }
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<Settings>(BOOT_SETTINGS)

  // 上次选了环境音：浏览器不允许无交互自动播放，
  // 这里只挂一个「首次点击就恢复」的监听，不硬启动、不报错。
  useEffect(() => {
    if (BOOT_SETTINGS.ambient !== 'none') {
      armAmbient(BOOT_SETTINGS.ambient, BOOT_SETTINGS.ambientVolume)
    }
  }, [])

  useEffect(() => {
    let alive = true
    // 自定义壁纸是异步读的（IndexedDB），其余设置同步生效
    const run = async () => {
      const url = settings.wallpaper === 'custom' ? await loadCustomWall() : null
      if (!alive) return
      applySettings(settings, url)
      saveSettings(settings)
    }
    void run()
    return () => {
      alive = false
    }
  }, [settings])

  const set = useCallback(
    <K extends keyof Settings>(key: K, value: Settings[K]) => {
      setSettings((s) => ({ ...s, [key]: value }))
    },
    [],
  )

  const patch = useCallback((p: Partial<Settings>) => {
    setSettings((s) => ({ ...s, ...p }))
  }, [])

  const reset = useCallback(() => setSettings(DEFAULT_SETTINGS), [])

  const theme = THEME_BY_ID[settings.themeId] ?? THEMES[0]
  const antd = useMemo(
    () => buildAntdTheme(theme, settings.contrast === 'high'),
    [theme, settings.contrast],
  )

  const value = useMemo<Ctx>(
    () => ({ settings, theme, set, patch, reset }),
    [settings, theme, set, patch, reset],
  )

  return (
    <SettingsCtx.Provider value={value}>
      <ConfigProvider locale={zhCN} theme={antd}>
        <AntApp>
          {/* framer-motion 的动画是 JS 驱动的，CSS 管不到：
              关掉动效时用 reducedMotion="always" 让它跳过位移/缩放。 */}
          <MotionConfig reducedMotion={settings.motion ? 'never' : 'always'}>
            {children}
          </MotionConfig>
        </AntApp>
      </ConfigProvider>
    </SettingsCtx.Provider>
  )
}

export function useSettings(): Ctx {
  const ctx = useContext(SettingsCtx)
  if (!ctx) {
    throw new Error('useSettings 必须在 ThemeProvider 内使用')
  }
  return ctx
}

/** 只要主题信息时的简写 */
export function useTheme(): ThemeDef {
  return useSettings().theme
}
