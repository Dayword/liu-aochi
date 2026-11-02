import LevelCover from './LevelCover'
import { themeOf } from '../levelTheme'

/**
 * 首页海报（Hero）。
 *
 * 背景是 LevelCover：13 级一级一张封面（底色 + 装饰意象 + 强调色），
 * 换级不只是换个数字，整张卡片的调子都会变 —— 这是「升级」最直接的反馈。
 *
 * 纯 SVG + CSS 绘制，不依赖任何外部图片：手机端要清晰，也不想给静态资源加几百 KB。
 * 底部压一层暗色 scrim，保证白字在任何一级的封面上都能读清。
 */
export default function HomePoster({
  name,
  subtitle,
  level,
  title,
  pct,
  exp,
  expNext,
}: {
  name: string
  subtitle: string
  level: number
  title: string
  pct: number
  exp: number
  expNext: number
}) {
  const R = 22
  const C = 2 * Math.PI * R
  const theme = themeOf(level)
  // 服务端/旧数据可能给的 title 与本地主题表不一致（改名前的缓存），以本地表为准
  const label = theme.title || title

  return (
    <div className="relative overflow-hidden rounded-2xl min-h-[164px] md:min-h-[176px] shadow-[0_12px_32px_-14px_rgba(15,23,42,0.55)]">
      <LevelCover theme={theme} />

      {/* ---------- 前景 ---------- */}
      <div className="relative flex items-center gap-3 p-3.5">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5 text-[9px] tracking-[0.2em] text-white/55 uppercase">
            <span>CodeRealm</span>
            <span className="text-white/30">/</span>
            <span className="tracking-[0.12em]">Lv.{level} of 13</span>
          </div>
          <div className="mt-1 flex items-baseline gap-1.5 flex-wrap">
            <span className="text-[19px] font-bold text-white leading-tight drop-shadow">
              你好，{name}
            </span>
            <span
              data-level-chip
              className="text-[10px] px-1.5 py-[1px] rounded-full text-white/95 backdrop-blur-sm"
              style={{ background: 'rgba(255,255,255,0.18)' }}
            >
              Lv.{level} {theme.icon} {label}
            </span>
          </div>
          <div className="text-[11px] text-white/65 mt-1 truncate">{subtitle}</div>

          <div className="mt-2.5 flex items-center gap-2">
            <div className="h-1.5 w-28 rounded-full bg-white/20 overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${Math.max(pct, 4)}%`,
                  background: `linear-gradient(90deg, ${theme.accent}, #ffffff)`,
                }}
              />
            </div>
            <span className="text-[10px] text-white/70 shrink-0">
              {exp}/{expNext} EXP
            </span>
          </div>

          <div className="mt-2 text-[10px] text-white/50">{theme.note}</div>
        </div>

        {/* 宽屏装饰：半透明终端窗口（手机上隐藏，避免挤文字） */}
        <div className="hidden md:block shrink-0 w-[210px] rounded-xl bg-white/10 border border-white/20 backdrop-blur-sm p-2">
          <div className="flex items-center gap-1 mb-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-300/90" />
            <span className="w-1.5 h-1.5 rounded-full bg-amber-300/90" />
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-300/90" />
            <span className="ml-auto text-[8px] text-white/50 font-mono">main.py</span>
          </div>
          <div className="space-y-1 font-mono text-[8px] leading-none">
            <div className="flex gap-1">
              <span className="text-fuchsia-200/90">def</span>
              <span className="text-white/85">learn(topic):</span>
            </div>
            <div className="pl-2 text-emerald-200/90">for lesson in topic:</div>
            <div className="pl-4 text-white/60">run(lesson)  <span className="text-white/30"># 亲自跑一遍</span></div>
            <div className="pl-2 text-amber-200/80">return growth</div>
            <div className="pt-1 flex items-center gap-1 text-white/40">
              <span className="text-emerald-300/90">▌</span>
              <span>ready</span>
            </div>
          </div>
        </div>

        {/* 等级进度环 */}
        <div className="relative shrink-0 w-[58px] h-[58px]">
          <svg viewBox="0 0 58 58" className="w-[58px] h-[58px] -rotate-90">
            <circle cx="29" cy="29" r={R} fill="none" stroke="#ffffff" strokeOpacity="0.22" strokeWidth="4.5" />
            <circle
              cx="29"
              cy="29"
              r={R}
              fill="none"
              stroke={theme.accent}
              strokeWidth="4.5"
              strokeLinecap="round"
              strokeDasharray={`${(C * pct) / 100} ${C}`}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-[15px] font-bold text-white leading-none">{level}</span>
            <span className="text-[7px] text-white/60 mt-0.5 tracking-wide">LEVEL</span>
          </div>
        </div>
      </div>
    </div>
  )
}
