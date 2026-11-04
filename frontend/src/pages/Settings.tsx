import { useState } from 'react'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { App as AntApp, Button, Input, Switch } from 'antd'
import {
  BgColorsOutlined,
  CheckCircleFilled,
  CodeOutlined,
  InfoCircleOutlined,
  LockOutlined,
  LogoutOutlined,
  SafetyOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useAuth } from '../store/auth'
import { api } from '../api/client'
import { pwdProblems, ruleChips } from '../lib/password'
import { CODE_FONT_STACK, useSettings } from '../theme/ThemeProvider'
import type { CodeFont, Texture, UiScale } from '../theme/ThemeProvider'
import { THEMES } from '../theme/themes'
import type { ThemeDef } from '../theme/themes'

/* ============================================================
 * 小部件
 * ========================================================== */

function Section({
  icon,
  title,
  desc,
  children,
}: {
  icon: ReactNode
  title: string
  desc?: string
  children: ReactNode
}) {
  return (
    <section className="game-panel p-3.5 md:p-4">
      <div className="flex items-center gap-2 mb-1">
        <span className="w-7 h-7 shrink-0 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center text-[14px]">
          {icon}
        </span>
        <div className="min-w-0">
          <div className="text-[13.5px] font-semibold text-slate-800 leading-tight">{title}</div>
          {desc && <div className="text-[11px] text-slate-400 leading-tight mt-0.5">{desc}</div>}
        </div>
      </div>
      <div>{children}</div>
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

/* ============================================================
 * 页面
 * ========================================================== */

export default function Settings() {
  const { settings, theme, set, reset } = useSettings()
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { message, modal } = AntApp.useApp()

  // ---- 改密码 ----
  const [oldPwd, setOldPwd] = useState('')
  const [newPwd, setNewPwd] = useState('')
  const [newPwd2, setNewPwd2] = useState('')
  const [pwdBusy, setPwdBusy] = useState(false)

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

  return (
    <div className="max-w-3xl mx-auto space-y-3">
      <header className="px-1">
        <h1 className="text-[19px] font-bold text-slate-800 flex items-center gap-2 leading-tight">
          <SettingOutlined className="text-indigo-600" />
          设置
        </h1>
        <p className="text-[11.5px] text-slate-500 mt-1 leading-relaxed">
          外观与偏好只保存在这台设备上，换设备需要重新设置；学习进度、收藏、错题存在服务器，不受影响。
        </p>
      </header>

      {/* ==================== 外观 ==================== */}
      <Section
        icon={<BgColorsOutlined />}
        title="外观"
        desc="10 套主题 · 深浅各 5 套，立即生效"
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

        <div className="mt-1">
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
            <Switch
              checked={settings.boot}
              onChange={(v) => set('boot', v)}
              size="small"
            />
          </Row>
          <Row label="界面动效" hint="页面切换、卡片悬浮的过渡；关掉后更省电">
            <Switch
              checked={settings.motion}
              onChange={(v) => set('motion', v)}
              size="small"
            />
          </Row>
        </div>
      </Section>

      {/* ==================== 编辑器 ==================== */}
      <Section icon={<CodeOutlined />} title="编辑器" desc="影响动手任务与代码沙箱">
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

      {/* ==================== 账号与安全 ==================== */}
      <Section icon={<SafetyOutlined />} title="账号与安全">
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
          <Button
            type="primary"
            block
            loading={pwdBusy}
            onClick={submitPassword}
            className="!mt-2"
          >
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
      <Section icon={<InfoCircleOutlined />} title="关于与无障碍">
        <Row label="高对比" hint="加深次要文字与描边，光线强时更清楚">
          <Switch
            size="small"
            checked={settings.contrast === 'high'}
            onChange={(v) => set('contrast', v ? 'high' : 'normal')}
          />
        </Row>
        <Row label="键盘焦点描边" hint="用 Tab 键操作时高亮当前焦点，键盘党必备">
          <Switch
            size="small"
            checked={settings.focusRing}
            onChange={(v) => set('focusRing', v)}
          />
        </Row>
        <Row label="恢复默认设置" hint="只重置外观与偏好，不动主题之外的数据">
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
