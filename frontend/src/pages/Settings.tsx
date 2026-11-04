import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { App as AntApp, Button, Input, Slider, Switch } from 'antd'
import {
  BgColorsOutlined,
  CheckCircleFilled,
  CodeOutlined,
  CommentOutlined,
  DownOutlined,
  InfoCircleOutlined,
  LockOutlined,
  LogoutOutlined,
  PictureOutlined,
  SafetyOutlined,
  SettingOutlined,
  SmileOutlined,
} from '@ant-design/icons'
import { useAuth } from '../store/auth'
import { api } from '../api/client'
import { pwdProblems, ruleChips } from '../lib/password'
import {
  CODE_FONT_STACK,
  PERSONA_LABEL,
  loadCustomWall,
  resetCustomWallCache,
  useSettings,
} from '../theme/ThemeProvider'
import type {
  AmbientId,
  CodeFont,
  PersonaId,
  RobotCorner,
  RobotSize,
  Texture,
  UiScale,
} from '../theme/ThemeProvider'
import { THEMES } from '../theme/themes'
import type { ThemeDef } from '../theme/themes'
import { WALLPAPERS } from '../theme/wallpapers'
import type { Wallpaper } from '../theme/wallpapers'
import { delWallpaper, putWallpaper, shrinkImage } from '../lib/idb'
import { playAmbient, setAmbientVolume, stopAmbient } from '../audio/ambient'
import { focusTimeText, startFocus, useFocus } from '../focus/store'

/* ============================================================
 * 小部件
 * ========================================================== */

/**
 * 折叠抽屉。默认全部收起 —— 六个板块全展开是一屏半的滚动，
 * 手机上要划四下才能看到「修改密码」。
 *
 * 只允许同时开一个（手风琴）：展开状态存的是「哪一个是开的」，
 * 点当前那个就收起来，点别的就把上一个替换掉。
 */
function Section({
  icon,
  title,
  summary,
  open,
  onToggle,
  children,
}: {
  icon: ReactNode
  title: string
  summary?: string
  open: boolean
  onToggle: () => void
  children: ReactNode
}) {
  const inner = useRef<HTMLDivElement>(null)

  // 收起来时把内容设为 inert：否则键盘 Tab 会跳进看不见的输入框，
  // 屏幕阅读器也会把整段设置念出来（视觉上却是折叠的）。
  useEffect(() => {
    const el = inner.current
    if (!el) return
    if (open) el.removeAttribute('inert')
    else el.setAttribute('inert', '')
  }, [open])

  return (
    <section className="game-panel overflow-hidden">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        className="w-full flex items-center gap-2.5 px-3.5 py-3 text-left hover:bg-slate-50/60 transition-colors"
      >
        <span className="w-7 h-7 shrink-0 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center text-[14px]">
          {icon}
        </span>
        <span className="text-[13.5px] font-semibold text-slate-800 leading-tight shrink-0">
          {title}
        </span>
        {summary && (
          <span className="ml-auto min-w-0 truncate text-[11px] text-slate-400 text-right">
            {summary}
          </span>
        )}
        <DownOutlined
          className={`shrink-0 text-[11px] text-slate-400 transition-transform duration-300 ${
            open ? 'rotate-180' : ''
          } ${summary ? '' : 'ml-auto'}`}
        />
      </button>

      <div
        className={`grid transition-[grid-template-rows] duration-300 ease-out ${
          open ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'
        }`}
      >
        <div ref={inner} className="overflow-hidden" aria-hidden={!open}>
          <div className="px-3.5 pb-3.5">{children}</div>
        </div>
      </div>
    </section>
  )
}

function Row({
  label,
  hint,
  children,
  stack,
}: {
  label: string
  hint?: string
  children: ReactNode
  /** 控件换行放到下一行（选项多的时候用） */
  stack?: boolean
}) {
  return (
    <div
      className={`py-2.5 border-t border-slate-100 first:border-t-0 ${
        stack ? '' : 'flex items-center justify-between gap-3'
      }`}
    >
      <div className="min-w-0">
        <div className="text-[13px] text-slate-700 leading-tight">{label}</div>
        {hint && <div className="text-[11px] text-slate-400 leading-tight mt-1">{hint}</div>}
      </div>
      <div className={stack ? 'mt-2' : 'shrink-0'}>{children}</div>
    </div>
  )
}

/** 胶囊分段控件：移动端自动换行，比 Segmented 更抗窄屏 */
function Seg<T extends string | number>({
  value,
  options,
  onChange,
}: {
  value: T
  options: { label: string; value: T }[]
  onChange: (v: T) => void
}) {
  return (
    <div className="inline-flex flex-wrap gap-1 rounded-xl bg-slate-100 p-0.5">
      {options.map((o) => (
        <button
          key={String(o.value)}
          onClick={() => onChange(o.value)}
          className={`px-2.5 py-1 rounded-[9px] text-[12px] transition-colors ${
            value === o.value
              ? 'bg-white text-indigo-700 font-medium shadow-sm'
              : 'text-slate-500'
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}

/** 主题预览卡：用**那套主题**的真实颜色画，不是模糊的色块 */
function ThemeCard({
  theme,
  active,
  onClick,
}: {
  theme: ThemeDef
  active: boolean
  onClick: () => void
}) {
  const v = theme.vars
  return (
    <button
      onClick={onClick}
      data-theme-card={theme.id}
      title={theme.desc}
      className="relative rounded-xl overflow-hidden border-2 text-left transition-transform active:scale-[0.97]"
      style={{ background: v.bg, borderColor: active ? v.brand : v.line }}
    >
      <div className="p-1.5">
        <div className="rounded-lg p-1.5 space-y-1" style={{ background: v.panel }}>
          <div className="h-[3px] w-8 rounded-full" style={{ background: v.brand }} />
          <div
            className="h-[3px] w-11 rounded-full"
            style={{ background: v.ink3, opacity: 0.75 }}
          />
          <div className="flex items-center gap-1 pt-0.5">
            <span className="h-2 w-2 rounded-full" style={{ background: v.accent }} />
            <span className="h-2 w-2 rounded-full" style={{ background: v.brandSoft }} />
            <span
              className="ml-auto h-[3px] w-4 rounded-full"
              style={{ background: v.ink2, opacity: 0.5 }}
            />
          </div>
        </div>
      </div>
      <div className="px-2 pb-1.5 flex items-center justify-between">
        <span className="text-[11.5px] font-medium" style={{ color: v.ink }}>
          {theme.name}
        </span>
        <span className="text-[9px]" style={{ color: v.ink3 }}>
          {theme.mode === 'dark' ? '深色' : '浅色'}
        </span>
      </div>
      {active && (
        <CheckCircleFilled
          className="absolute top-1 right-1 text-[12px]"
          style={{ color: v.brand }}
        />
      )}
    </button>
  )
}

/** 壁纸卡：内置的用 CSS 渐变缩略，自定义的用真实图 */
function WallCard({
  wall,
  active,
  customUrl,
  onClick,
}: {
  wall: Wallpaper
  active: boolean
  customUrl?: string | null
  onClick: () => void
}) {
  const bg =
    wall.id === 'custom'
      ? customUrl
        ? `url("${customUrl}")`
        : 'repeating-linear-gradient(45deg, var(--t-line) 0 6px, transparent 6px 12px)'
      : wall.thumb || 'var(--t-panel-alt)'
  return (
    <button
      onClick={onClick}
      title={wall.name}
      className={`relative shrink-0 w-[62px] rounded-lg overflow-hidden border-2 transition-transform active:scale-95 ${
        active ? 'border-indigo-500' : 'border-transparent'
      }`}
    >
      <div
        className="h-[42px] w-full"
        style={{ backgroundImage: bg, backgroundSize: 'cover', backgroundPosition: 'center' }}
      />
      <div className="text-[10px] py-0.5 text-center text-slate-500 bg-white/70">{wall.name}</div>
    </button>
  )
}

const AMBIENTS: { id: AmbientId; label: string; desc: string }[] = [
  { id: 'none', label: '无', desc: '关掉' },
  { id: 'rain', label: '雨声', desc: '白噪声滤出来的雨' },
  { id: 'cafe', label: '咖啡馆', desc: '低频人声底噪' },
  { id: 'keys', label: '键盘', desc: '随机敲击声' },
  { id: 'white', label: '白噪音', desc: '最朴素的底噪' },
]

const PERSONAS: { id: PersonaId; desc: string }[] = [
  { id: 'warm', desc: '先肯定再讲清楚，卡住时给台阶，适合刚开始学' },
  { id: 'strict', desc: '追问细节、指出含糊表述，按面试标准要求你' },
  { id: 'snarky', desc: '嘴上不留情，但答案照样给全，适合脸皮厚的时候' },
]

/* ============================================================
 * 页面
 * ========================================================== */

export default function Settings() {
  const { settings, theme, set, reset } = useSettings()
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { message, modal } = AntApp.useApp()
  const focus = useFocus()

  // 手风琴：默认一个都不开
  const [open, setOpen] = useState<string | null>(null)
  const toggle = (id: string) => setOpen((cur) => (cur === id ? null : id))

  // ---- 改密码 ----
  const [oldPwd, setOldPwd] = useState('')
  const [newPwd, setNewPwd] = useState('')
  const [newPwd2, setNewPwd2] = useState('')
  const [pwdBusy, setPwdBusy] = useState(false)

  // ---- 自定义壁纸 ----
  const fileRef = useRef<HTMLInputElement>(null)
  const [customUrl, setCustomUrl] = useState<string | null>(null)
  const [wallBusy, setWallBusy] = useState(false)

  useEffect(() => {
    void loadCustomWall().then(setCustomUrl)
  }, [])

  const onPickWall = async (file?: File | null) => {
    if (!file) return
    setWallBusy(true)
    try {
      const blob = await shrinkImage(file)
      await putWallpaper(blob)
      resetCustomWallCache()
      setCustomUrl(await loadCustomWall())
      set('wallpaper', 'custom')
      message.success('壁纸已保存（只存在这台设备）')
    } catch (e) {
      message.error(e instanceof Error ? e.message : '图片处理失败')
    } finally {
      setWallBusy(false)
    }
  }

  const removeWall = async () => {
    await delWallpaper()
    resetCustomWallCache()
    setCustomUrl(null)
    set('wallpaper', 'none')
  }

  // ---- 环境音 ----
  const chooseAmbient = (id: AmbientId) => {
    set('ambient', id)
    if (id === 'none') stopAmbient()
    else playAmbient(id, settings.ambientVolume)
  }

  // ---- 改密码 ----
  const submitPassword = async () => {
    if (!oldPwd || !newPwd) {
      message.warning('请填写当前密码和新密码')
      return
    }
    // 规则与注册页、后端 schemas.py 三处一致（见 src/lib/password.ts）
    const bad = pwdProblems(newPwd)
    if (bad.length) {
      message.warning(`新密码还缺：${bad.map((b) => b.label).join('、')}`)
      return
    }
    if (newPwd !== newPwd2) {
      message.warning('两次输入的新密码不一致')
      return
    }
    if (newPwd === oldPwd) {
      message.warning('新密码不能和当前密码一样')
      return
    }
    setPwdBusy(true)
    try {
      await api.post('/api/auth/change-password', {
        old_password: oldPwd,
        new_password: newPwd,
      })
      setOldPwd('')
      setNewPwd('')
      setNewPwd2('')
      message.success('密码已修改，下次登录用新密码')
    } catch (e) {
      message.error(e instanceof Error ? e.message : '修改失败，请重试')
    } finally {
      setPwdBusy(false)
    }
  }

  // ---- 清缓存 ----
  const clearCache = () => {
    modal.confirm({
      title: '清除本地缓存？',
      content:
        '会清掉这台设备上的界面设置、收藏缓存与临时标记，登录状态保留。学习进度存在服务器，不受影响。',
      okText: '清除并刷新',
      okButtonProps: { danger: true },
      cancelText: '取消',
      onOk: () => {
        const token = localStorage.getItem('ca_token')
        Object.keys(localStorage)
          .filter((k) => k.startsWith('ca_') && k !== 'ca_token')
          .forEach((k) => localStorage.removeItem(k))
        sessionStorage.clear()
        if (token) localStorage.setItem('ca_token', token)
        location.reload()
      },
    })
  }

  const askLogout = () => {
    modal.confirm({
      title: '确认退出登录？',
      content: '退出后需要重新用学号和密码登录，学习进度不会丢失。',
      okText: '退出登录',
      okButtonProps: { danger: true },
      cancelText: '再想想',
      onOk: () => {
        logout()
        navigate('/login', { replace: true })
      },
    })
  }

  const lookSummary = [
    theme.name,
    settings.wallpaper !== 'none' ? '壁纸' : '',
    settings.scale > 1 ? `${Math.round(settings.scale * 100)}%` : '',
  ]
    .filter(Boolean)
    .join(' · ')

  const funSummary = [
    settings.robot ? '机器人' : '无机器人',
    settings.effects ? '特效' : '',
    settings.ambient !== 'none'
      ? AMBIENTS.find((a) => a.id === settings.ambient)?.label
      : '',
  ]
    .filter(Boolean)
    .join(' · ')

  return (
    <div className="max-w-3xl mx-auto space-y-2.5">
      <header className="px-1">
        <h1 className="text-[19px] font-bold text-slate-800 flex items-center gap-2 leading-tight">
          <SettingOutlined className="text-indigo-600" />
          设置
        </h1>
        <p className="text-[11.5px] text-slate-500 mt-1 leading-relaxed">
          外观与偏好只保存在这台设备上，换设备需要重新设置；学习进度、收藏、错题、专注记录存在服务器。
        </p>
      </header>

      {/* ==================== 外观 ==================== */}
      <Section
        icon={<BgColorsOutlined />}
        title="外观"
        summary={lookSummary}
        open={open === 'look'}
        onToggle={() => toggle('look')}
      >
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
          {THEMES.map((t) => (
            <ThemeCard
              key={t.id}
              theme={t}
              active={settings.themeId === t.id}
              onClick={() => set('themeId', t.id)}
            />
          ))}
        </div>
        <div className="mt-2 text-[11px] text-slate-400 leading-relaxed">
          当前：<span className="text-indigo-600 font-medium">{theme.name}</span> · {theme.desc}
        </div>

        <Row label="壁纸" hint="铺在页面底层，所有卡片不透明，不会影响阅读" stack>
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            {WALLPAPERS.map((w) => (
              <WallCard
                key={w.id}
                wall={w}
                active={settings.wallpaper === w.id}
                customUrl={customUrl}
                onClick={() => {
                  if (w.id === 'custom' && !customUrl) fileRef.current?.click()
                  else set('wallpaper', w.id)
                }}
              />
            ))}
          </div>
          <div className="flex items-center gap-2 mt-1.5">
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => {
                void onPickWall(e.target.files?.[0])
                e.currentTarget.value = ''
              }}
            />
            <Button size="small" icon={<PictureOutlined />} loading={wallBusy} onClick={() => fileRef.current?.click()}>
              {customUrl ? '换一张' : '上传图片'}
            </Button>
            {customUrl && (
              <Button size="small" type="text" danger onClick={() => void removeWall()}>
                移除
              </Button>
            )}
            <span className="text-[10px] text-slate-400">压缩到 1600px，只存本机</span>
          </div>
        </Row>

        <Row label="界面缩放" hint="整体放大字号与控件，手机上一屏会少显示一点">
          <Seg<UiScale>
            value={settings.scale}
            onChange={(v) => set('scale', v)}
            options={[
              { label: '标准', value: 1 },
              { label: '大', value: 1.08 },
              { label: '特大', value: 1.16 },
            ]}
          />
        </Row>
        <Row label="背景纹理" hint="只在页面空白处显示，不压卡片">
          <Seg<Texture>
            value={settings.texture}
            onChange={(v) => set('texture', v)}
            options={[
              { label: '无', value: 'none' },
              { label: '网格', value: 'grid' },
              { label: '点阵', value: 'dots' },
              { label: '扫描线', value: 'scan' },
            ]}
          />
        </Row>
        <Row label="入场动画" hint="每次打开网站播的那段星空动画，约 3 秒">
          <Switch checked={settings.boot} onChange={(v) => set('boot', v)} size="small" />
        </Row>
        <Row label="界面动效" hint="页面切换、卡片悬浮的过渡；关掉后更省电">
          <Switch checked={settings.motion} onChange={(v) => set('motion', v)} size="small" />
        </Row>
      </Section>

      {/* ==================== 编辑器 ==================== */}
      <Section
        icon={<CodeOutlined />}
        title="编辑器"
        summary={`${settings.codeFontSize}px · ${settings.tabWidth} 空格`}
        open={open === 'editor'}
        onToggle={() => toggle('editor')}
      >
        <Row label="代码字号">
          <Seg<number>
            value={settings.codeFontSize}
            onChange={(v) => set('codeFontSize', v)}
            options={[
              { label: '12', value: 12 },
              { label: '13', value: 13 },
              { label: '15', value: 15 },
              { label: '17', value: 17 },
            ]}
          />
        </Row>
        <Row label="等宽字体" stack>
          <Seg<CodeFont>
            value={settings.codeFont}
            onChange={(v) => set('codeFont', v)}
            options={[
              { label: '系统等宽', value: 'mono' },
              { label: 'Cascadia', value: 'cascadia' },
              { label: 'Consolas', value: 'consolas' },
              { label: 'Fira Code', value: 'fira' },
            ]}
          />
        </Row>
        <Row label="Tab 宽度" hint="缩进用几个空格，Python 建议 4">
          <Seg<2 | 4>
            value={settings.tabWidth}
            onChange={(v) => set('tabWidth', v)}
            options={[
              { label: '2 空格', value: 2 },
              { label: '4 空格', value: 4 },
            ]}
          />
        </Row>
        <Row label="自动换行" hint="关掉后长行横向滚动，不折行">
          <Switch checked={settings.wrap} onChange={(v) => set('wrap', v)} size="small" />
        </Row>

        {/* 实时预览：改字号/字体立刻能看到，不用跳去答题页试 */}
        <div className="mt-1 rounded-xl border border-slate-200 overflow-hidden">
          <div className="px-2.5 py-1 text-[10px] text-slate-400 border-b border-slate-200 bg-slate-50">
            预览
          </div>
          <pre
            className="m-0 px-2.5 py-2 bg-[#f8f9fd] text-slate-800"
            style={{
              fontFamily: CODE_FONT_STACK[settings.codeFont],
              fontSize: `${settings.codeFontSize}px`,
              lineHeight: `${Math.round(settings.codeFontSize * 1.7)}px`,
              whiteSpace: settings.wrap ? 'pre-wrap' : 'pre',
              overflowX: 'auto',
            }}
          >{`def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i`}</pre>
        </div>
      </Section>

      {/* ==================== 氛围与互动 ==================== */}
      <Section
        icon={<SmileOutlined />}
        title="氛围与互动"
        summary={funSummary}
        open={open === 'fun'}
        onToggle={() => toggle('fun')}
      >
        <Row label="伴学小机器人" hint="右下角的小家伙；随等级变形，答题时有反应">
          <Switch checked={settings.robot} onChange={(v) => set('robot', v)} size="small" />
        </Row>
        {settings.robot && (
          <>
            <Row label="大小">
              <Seg<RobotSize>
                value={settings.robotSize}
                onChange={(v) => set('robotSize', v)}
                options={[
                  { label: '小', value: 'sm' },
                  { label: '中', value: 'md' },
                  { label: '大', value: 'lg' },
                ]}
              />
            </Row>
            <Row label="位置">
              <Seg<RobotCorner>
                value={settings.robotCorner}
                onChange={(v) => set('robotCorner', v)}
                options={[
                  { label: '右下', value: 'br' },
                  { label: '左下', value: 'bl' },
                ]}
              />
            </Row>
          </>
        )}

        <Row label="点击与通关特效" hint="答对撒星星、连击计数、升级彩带；关掉后完全停掉动画">
          <Switch checked={settings.effects} onChange={(v) => set('effects', v)} size="small" />
        </Row>

        <Row label="环境音" hint="全部实时合成，没有音频文件，不耗流量" stack>
          <div className="flex flex-wrap gap-1.5">
            {AMBIENTS.map((a) => (
              <button
                key={a.id}
                onClick={() => chooseAmbient(a.id)}
                title={a.desc}
                className={`px-2.5 py-1 rounded-lg text-[12px] border transition-colors ${
                  settings.ambient === a.id
                    ? 'border-indigo-400 bg-indigo-50 text-indigo-700 font-medium'
                    : 'border-slate-200 text-slate-500'
                }`}
              >
                {a.label}
              </button>
            ))}
          </div>
          {settings.ambient !== 'none' && (
            <div className="flex items-center gap-2 mt-2">
              <span className="text-[11px] text-slate-400">音量</span>
              <Slider
                className="!flex-1"
                min={0}
                max={100}
                value={Math.round(settings.ambientVolume * 100)}
                onChange={(v) => {
                  set('ambientVolume', v / 100)
                  setAmbientVolume(v / 100)
                }}
                tooltip={{ formatter: (v) => `${v}%` }}
              />
            </div>
          )}
        </Row>

        <Row label="专注时长" hint="番茄钟一轮多长；不发经验，只记录专注时间">
          <Seg<25 | 45 | 50>
            value={settings.focusMinutes}
            onChange={(v) => set('focusMinutes', v)}
            options={[
              { label: '25 分钟', value: 25 },
              { label: '45 分钟', value: 45 },
              { label: '50 分钟', value: 50 },
            ]}
          />
        </Row>
        <Row label="专注时自动开环境音" hint="开始专注时如果环境音是关的，自动切到雨声">
          <Switch
            checked={settings.focusSound}
            onChange={(v) => set('focusSound', v)}
            size="small"
          />
        </Row>
        <Row label="开始一轮专注" hint={focus.running ? `进行中 ${focusTimeText(focus.remain)}` : '开始后顶部会出现倒计时'}>
          <Button
            size="small"
            type="primary"
            disabled={focus.running}
            onClick={() => {
              if (settings.focusSound && settings.ambient === 'none') {
                set('ambient', 'rain')
                playAmbient('rain', settings.ambientVolume)
              }
              // 不再弹「已开始」的 toast：顶部的倒计时胶囊本身就是反馈，
              // 而 AntD message 默认出现在顶部正中，正好把胶囊盖住。
              startFocus(settings.focusMinutes)
            }}
          >
            {focus.running ? '进行中' : '开始专注'}
          </Button>
        </Row>

        {settings.easter && (
          <Row label="彩蛋模式" hint="机器人偶尔说些不该说的话，首页会混进几句秘密格言">
            <Switch checked={settings.easter} onChange={(v) => set('easter', v)} size="small" />
          </Row>
        )}
      </Section>

      {/* ==================== AI 导师 ==================== */}
      <Section
        icon={<CommentOutlined />}
        title="AI 导师"
        summary={PERSONA_LABEL[settings.persona]}
        open={open === 'ai'}
        onToggle={() => toggle('ai')}
      >
        <div className="space-y-1.5">
          {PERSONAS.map((p) => (
            <button
              key={p.id}
              onClick={() => set('persona', p.id)}
              className={`w-full text-left rounded-xl border px-3 py-2 transition-colors ${
                settings.persona === p.id
                  ? 'border-indigo-400 bg-indigo-50/60'
                  : 'border-slate-200 hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center gap-1.5">
                <span className="text-[12.5px] font-semibold text-slate-800">
                  {PERSONA_LABEL[p.id]}
                </span>
                {settings.persona === p.id && (
                  <CheckCircleFilled className="text-[11px] text-indigo-500" />
                )}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">{p.desc}</div>
            </button>
          ))}
        </div>
        <div className="mt-2 text-[11px] text-slate-400 leading-relaxed">
          人格只改变说话方式，讲的内容仍是同一套课程口径；换人格不会丢对话历史。
        </div>
      </Section>

      {/* ==================== 账号与安全 ==================== */}
      <Section
        icon={<SafetyOutlined />}
        title="账号与安全"
        summary={user?.student_id ? `学号 ${user.student_id}` : ''}
        open={open === 'account'}
        onToggle={() => toggle('account')}
      >
        <div className="rounded-xl border border-slate-200 p-2.5 mt-1.5">
          <div className="flex items-center gap-1.5 text-[12.5px] font-medium text-slate-700">
            <LockOutlined className="text-indigo-600" />
            修改密码
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5 mb-2">
            学号 {user?.student_id || user?.username || '—'}
            {user?.real_name ? ` · ${user.real_name}` : ''}
          </div>
          <div className="space-y-2">
            <Input.Password
              placeholder="当前密码"
              value={oldPwd}
              onChange={(e) => setOldPwd(e.target.value)}
              autoComplete="current-password"
            />
            <Input.Password
              placeholder="新密码（大写+小写+数字+特殊符号）"
              value={newPwd}
              onChange={(e) => setNewPwd(e.target.value)}
              autoComplete="new-password"
            />
            {newPwd && (
              <div className="flex flex-wrap gap-1">
                {ruleChips(newPwd).map((r) => (
                  <span
                    key={r.key}
                    className={`text-[10px] px-1.5 py-0.5 rounded border ${
                      r.ok
                        ? 'border-emerald-300 bg-emerald-50 text-emerald-600'
                        : 'border-slate-200 bg-slate-50 text-slate-400'
                    }`}
                  >
                    {r.ok ? '✓' : '·'} {r.label}
                  </span>
                ))}
              </div>
            )}
            <Input.Password
              placeholder="再输一次新密码"
              value={newPwd2}
              onChange={(e) => setNewPwd2(e.target.value)}
              autoComplete="new-password"
              onPressEnter={submitPassword}
            />
          </div>
          <Button type="primary" block loading={pwdBusy} onClick={submitPassword} className="!mt-2">
            保存新密码
          </Button>
        </div>

        <Row label="清除本地缓存" hint="界面设置、收藏缓存、临时标记；不影响学习进度">
          <Button size="small" danger onClick={clearCache}>
            清除
          </Button>
        </Row>
        <Row label="退出登录">
          <Button size="small" icon={<LogoutOutlined />} onClick={askLogout}>
            退出
          </Button>
        </Row>
      </Section>

      {/* ==================== 关于与无障碍 ==================== */}
      <Section
        icon={<InfoCircleOutlined />}
        title="关于与无障碍"
        summary={`v${__APP_VERSION__}`}
        open={open === 'about'}
        onToggle={() => toggle('about')}
      >
        <Row label="高对比" hint="加深次要文字与描边，光线强时更清楚">
          <Switch
            size="small"
            checked={settings.contrast === 'high'}
            onChange={(v) => set('contrast', v ? 'high' : 'normal')}
          />
        </Row>
        <Row label="键盘焦点描边" hint="用 Tab 键操作时高亮当前焦点，键盘党必备">
          <Switch size="small" checked={settings.focusRing} onChange={(v) => set('focusRing', v)} />
        </Row>
        <Row label="恢复默认设置" hint="只重置外观与偏好，不动学习数据">
          <Button
            size="small"
            onClick={() => {
              reset()
              message.success('已恢复默认设置')
            }}
          >
            恢复默认
          </Button>
        </Row>

        <div className="mt-2 pt-2.5 border-t border-slate-100 text-[11px] text-slate-400 space-y-1 leading-relaxed">
          <div className="flex justify-between">
            <span>版本</span>
            <span className="font-mono text-slate-500">{__APP_VERSION__}</span>
          </div>
          <div className="flex justify-between">
            <span>构建时间</span>
            <span className="font-mono text-slate-500">
              {new Date(__BUILD_TIME__).toLocaleString('zh-CN', { hour12: false })}
            </span>
          </div>
          <div className="flex justify-between">
            <span>主题</span>
            <span className="text-slate-500">
              {theme.name}（{theme.id}）
            </span>
          </div>
          <div className="pt-1">
            发现问题或有建议，直接找课代表反馈，或在
            <a
              className="text-indigo-600 underline decoration-dotted ml-0.5"
              href="https://github.com/Dayword/liu-aochi/issues"
              target="_blank"
              rel="noreferrer"
            >
              GitHub Issues
            </a>
            提一条。
          </div>
        </div>
      </Section>
    </div>
  )
}
