/**
 * 首页海报（Hero）。
 *
 * 纯 SVG + CSS 绘制，不依赖任何外部图片：
 * - 渐变夜空 + 网格 + 光斑 + 远山剪影，做出「冒险」的氛围
 * - 右侧圆环显示当前等级的经验进度
 * - 底部加一层暗色 scrim，保证白字在任何屏幕上都能读清
 *
 * 之所以不用位图：手机端要清晰、要能跟随主题变色，也不想给静态资源加几百 KB。
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

  return (
    <div className="relative overflow-hidden rounded-2xl min-h-[164px] md:min-h-[176px] shadow-[0_12px_32px_-14px_rgba(79,70,229,0.6)]">
      {/* ---------- 背景插画 ---------- */}
      <svg
        viewBox="0 0 680 300"
        preserveAspectRatio="xMidYMid slice"
        className="absolute inset-0 w-full h-full"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="hp-sky" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#4338ca" />
            <stop offset="48%" stopColor="#6d28d9" />
            <stop offset="100%" stopColor="#0e7490" />
          </linearGradient>
          <radialGradient id="hp-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#a5b4fc" stopOpacity="0.75" />
            <stop offset="100%" stopColor="#a5b4fc" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="hp-glow2" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#f0abfc" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#f0abfc" stopOpacity="0" />
          </radialGradient>
          <pattern id="hp-grid" width="34" height="34" patternUnits="userSpaceOnUse">
            <path d="M34 0H0V34" fill="none" stroke="#ffffff" strokeOpacity="0.09" strokeWidth="1" />
          </pattern>
          <linearGradient id="hp-scrim" x1="0" y1="0" x2="0" y2="1">
            <stop offset="45%" stopColor="#1e1b4b" stopOpacity="0" />
            <stop offset="100%" stopColor="#1e1b4b" stopOpacity="0.55" />
          </linearGradient>
          <linearGradient id="hp-m1" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#312e81" stopOpacity="0.55" />
            <stop offset="100%" stopColor="#1e1b4b" stopOpacity="0.9" />
          </linearGradient>
          <linearGradient id="hp-m2" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#1e1b4b" stopOpacity="0.7" />
            <stop offset="100%" stopColor="#171544" stopOpacity="0.98" />
          </linearGradient>
        </defs>

        {/* 夜空 + 网格 + 光斑 */}
        <rect width="680" height="300" fill="url(#hp-sky)" />
        <rect width="680" height="300" fill="url(#hp-grid)" />
        <ellipse cx="150" cy="30" rx="170" ry="120" fill="url(#hp-glow)" />
        <ellipse cx="620" cy="250" rx="190" ry="130" fill="url(#hp-glow2)" />

        {/* 星点：只铺在上半部，避开文字 */}
        {[
          [78, 34], [186, 26], [274, 48], [356, 22], [448, 44], [536, 24], [622, 52],
          [126, 76], [246, 88], [404, 70], [588, 84],
        ].map(([x, y], i) => (
          <circle key={i} cx={x} cy={y} r={i % 3 === 0 ? 1.7 : 1.1} fill="#e0e7ff" opacity={0.85} />
        ))}

        {/* 远山剪影：压到最底部，留出中部给文字 */}
        <path d="M0 258 L96 196 L172 240 L258 186 L344 252 L428 200 L516 254 L598 208 L680 256 L680 300 L0 300 Z"
              fill="url(#hp-m1)" />
        <path d="M0 282 L84 246 L178 282 L272 242 L362 286 L456 248 L552 288 L644 252 L680 278 L680 300 L0 300 Z"
              fill="url(#hp-m2)" />

        {/* 漂浮的代码符号：只放在右半边，避免压住姓名 */}
        <g fill="#c7d2fe" fontFamily="Consolas, monospace" opacity="0.42">
          <text x="470" y="128" fontSize="20">{'{ }'}</text>
          <text x="586" y="150" fontSize="16">{'</>'}</text>
          <text x="524" y="192" fontSize="12">01</text>
          <text x="636" y="196" fontSize="12">λ</text>
        </g>

        {/* 顶部流光 */}
        <path d="M-40 44 L210 -34 L318 -34 L-40 104 Z" fill="#ffffff" opacity="0.05" />
        {/* 底部压暗，保证文字可读 */}
        <rect y="150" width="680" height="150" fill="url(#hp-scrim)" />
      </svg>

      {/* ---------- 前景 ---------- */}
      <div className="relative flex items-center gap-3 p-3.5">
        <div className="min-w-0 flex-1">
          <div className="text-[9px] tracking-[0.2em] text-indigo-200/80 uppercase">
            Code Adventurer
          </div>
          <div className="mt-1 flex items-baseline gap-1.5 flex-wrap">
            <span className="text-[19px] font-bold text-white leading-tight drop-shadow">
              你好，{name}
            </span>
            <span className="text-[10px] px-1.5 py-[1px] rounded-full bg-white/20 text-white/95 backdrop-blur-sm">
              Lv.{level} {title}
            </span>
          </div>
          <div className="text-[11px] text-indigo-100/85 mt-1 truncate">{subtitle}</div>

          <div className="mt-2.5 flex items-center gap-2">
            <div className="h-1.5 w-28 rounded-full bg-white/20 overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-amber-300 to-yellow-200 transition-all"
                style={{ width: `${Math.max(pct, 4)}%` }}
              />
            </div>
            <span className="text-[10px] text-indigo-100/80 shrink-0">
              {exp}/{expNext} EXP
            </span>
          </div>

          <div className="mt-2 text-[10px] text-indigo-100/60">软件工程 · 游戏化 AI 学习</div>
        </div>

        {/* 宽屏装饰：半透明终端窗口（手机上隐藏，避免挤文字） */}
        <div className="hidden md:block shrink-0 w-[210px] rounded-xl bg-white/10 border border-white/20 backdrop-blur-sm p-2">
          <div className="flex items-center gap-1 mb-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-300/90" />
            <span className="w-1.5 h-1.5 rounded-full bg-amber-300/90" />
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-300/90" />
            <span className="ml-auto text-[8px] text-indigo-100/60 font-mono">main.py</span>
          </div>
          <div className="space-y-1 font-mono text-[8px] leading-none">
            <div className="flex gap-1">
              <span className="text-fuchsia-200/90">def</span>
              <span className="text-indigo-50/90">learn(topic):</span>
            </div>
            <div className="pl-2 text-emerald-200/90">for lesson in topic:</div>
            <div className="pl-4 text-indigo-100/70">run(lesson)  <span className="text-white/40"># 亲自跑一遍</span></div>
            <div className="pl-2 text-amber-200/80">return growth</div>
            <div className="pt-1 flex items-center gap-1 text-indigo-100/50">
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
              stroke="#fbbf24"
              strokeWidth="4.5"
              strokeLinecap="round"
              strokeDasharray={`${(C * pct) / 100} ${C}`}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-[15px] font-bold text-white leading-none">{level}</span>
            <span className="text-[7px] text-indigo-100/80 mt-0.5 tracking-wide">LEVEL</span>
          </div>
        </div>
      </div>
    </div>
  )
}
