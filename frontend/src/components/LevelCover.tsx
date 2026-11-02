import { useId } from 'react'
import type { LevelTheme } from '../levelTheme'

/**
 * 等级封面（纯 SVG，无位图）。
 *
 * 13 级各一套「底色 + 装饰图层」：底色来自 levelTheme.ts 的三停渐变，
 * 装饰图层按 motif 画几笔意象（碎石 / 铁轨 / 桥拱 / 烛火 / 月与塔 /
 * 拓扑网 / 罗盘 / 裂壁 / 脚手架 / 灯笼 / 星座 / 星系）。
 *
 * 画法上刻意都很「省」：每层只用一个色相、透明度压在 .15~.5，
 * 因为封面上要压姓名和白字，装饰一浓就读不清。所有渐变 id 用 useId 加前缀，
 * 同一页渲染 13 张封面时不会互相抢 id。
 */
export default function LevelCover({ theme }: { theme: LevelTheme }) {
  const uid = useId().replace(/[^a-zA-Z0-9]/g, '')
  const gid = (n: string) => `${uid}-${n}`
  const u = (n: string) => `url(#${gid(n)})`
  const [c1, c2, c3] = theme.sky
  const [g1, g2] = theme.glow

  return (
    <svg
      viewBox="0 0 680 300"
      preserveAspectRatio="xMidYMid slice"
      className="absolute inset-0 w-full h-full"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id={gid('sky')} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor={c1} />
          <stop offset="50%" stopColor={c2} />
          <stop offset="100%" stopColor={c3} />
        </linearGradient>
        <radialGradient id={gid('glow1')} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={g1} stopOpacity="0.55" />
          <stop offset="100%" stopColor={g1} stopOpacity="0" />
        </radialGradient>
        <radialGradient id={gid('glow2')} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={g2} stopOpacity="0.45" />
          <stop offset="100%" stopColor={g2} stopOpacity="0" />
        </radialGradient>
        <pattern id={gid('tex-grid')} width="34" height="34" patternUnits="userSpaceOnUse">
          <path d="M34 0H0V34" fill="none" stroke="#ffffff" strokeOpacity="0.08" strokeWidth="1" />
        </pattern>
        <pattern id={gid('tex-dots')} width="22" height="22" patternUnits="userSpaceOnUse">
          <circle cx="11" cy="11" r="1.3" fill="#ffffff" fillOpacity="0.14" />
        </pattern>
        <pattern id={gid('tex-stripes')} width="16" height="16" patternUnits="userSpaceOnUse">
          <path d="M-4 4 L4 -4 M0 16 L16 0 M12 20 L20 12" stroke="#ffffff" strokeOpacity="0.07" strokeWidth="3" />
        </pattern>
        <pattern id={gid('tex-weave')} width="26" height="26" patternUnits="userSpaceOnUse">
          <path d="M-6 6 L6 -6 M20 32 L32 20 M-6 26 L6 38 M20 -6 L32 -18" stroke="#ffffff" strokeOpacity="0.1" strokeWidth="1.5" />
          <path d="M-6 -6 L6 6 M20 20 L32 32 M-6 20 L6 32 M20 -14 L32 -2" stroke="#ffffff" strokeOpacity="0.06" strokeWidth="1.5" />
        </pattern>
        <pattern id={gid('tex-scan')} width="8" height="8" patternUnits="userSpaceOnUse">
          <path d="M0 4H8" stroke="#ffffff" strokeOpacity="0.06" strokeWidth="1" />
        </pattern>
        <linearGradient id={gid('hscrim')} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#0b1020" stopOpacity="0.5" />
          <stop offset="55%" stopColor="#0b1020" stopOpacity="0.12" />
          <stop offset="100%" stopColor="#0b1020" stopOpacity="0" />
        </linearGradient>
        <linearGradient id={gid('scrim')} x1="0" y1="0" x2="0" y2="1">
          <stop offset="28%" stopColor="#0b1020" stopOpacity="0" />
          <stop offset="100%" stopColor="#0b1020" stopOpacity="0.7" />
        </linearGradient>
      </defs>

      <rect width="680" height="300" fill={u('sky')} />
      {theme.texture !== 'none' && (
        <rect width="680" height="300" fill={u(`tex-${theme.texture}`)} />
      )}
      <ellipse cx="120" cy="20" rx="180" ry="120" fill={u('glow1')} />
      <ellipse cx="610" cy="250" rx="200" ry="140" fill={u('glow2')} />

      {theme.motif === 'rubble' && (
        <g>
          <g fill="#e4e4e7" opacity="0.16">
            <path d="M430 232 l24 -16 l26 10 l-4 18 l-30 6 z" />
            <path d="M520 258 l16 -12 l20 8 l-2 14 l-24 2 z" />
            <path d="M604 226 l14 -10 l16 7 l-2 13 l-20 2 z" />
          </g>
          <g fill="#e4e4e7" opacity="0.3">
            <circle cx="486" cy="196" r="2.4" />
            <circle cx="562" cy="212" r="1.8" />
            <circle cx="640" cy="256" r="2" />
            <circle cx="404" cy="270" r="1.6" />
          </g>
        </g>
      )}

      {theme.motif === 'clearing' && (
        <g stroke="#bef264" fill="none" opacity="0.28">
          <path d="M392 262 q40 -26 78 -6 q34 18 70 -4 q30 -18 62 2" strokeWidth="2.5" />
          <path d="M470 200 l34 -46 M512 206 l30 -40 M558 210 l26 -34" strokeWidth="3" strokeLinecap="round" />
          <path d="M404 226 l22 -28 M600 236 l20 -26" strokeWidth="2" strokeLinecap="round" opacity="0.6" />
        </g>
      )}

      {theme.motif === 'rail' && (
        <g stroke="#fcd34d" strokeLinecap="round">
          <g opacity="0.3">
            {[0, 1, 2, 3, 4, 5, 6].map((i) => {
              const t = i / 6
              const y = 300 - t * 150
              const halfW = 120 - t * 78
              const cx = 470 + t * 60
              return <line key={i} x1={cx - halfW / 2} y1={y} x2={cx + halfW / 2} y2={y} strokeWidth={2.5 - t} />
            })}
          </g>
          <g opacity="0.45" strokeWidth="3">
            <line x1="400" y1="300" x2="510" y2="150" />
            <line x1="540" y1="300" x2="530" y2="150" />
          </g>
        </g>
      )}

      {theme.motif === 'bridge' && (
        <g>
          <path d="M356 268 Q520 122 684 268" fill="none" stroke="#7dd3fc" strokeWidth="7" opacity="0.35" />
          <path d="M356 268 Q520 122 684 268" fill="none" stroke="#bae6fd" strokeWidth="2" opacity="0.5" />
          <g stroke="#7dd3fc" strokeWidth="4" opacity="0.28">
            <line x1="380" y1="268" x2="380" y2="300" />
            <line x1="520" y1="196" x2="520" y2="300" />
            <line x1="660" y1="268" x2="660" y2="300" />
          </g>
        </g>
      )}

      {theme.motif === 'lamp' && (
        <g>
          <ellipse cx="588" cy="150" rx="86" ry="86" fill={u('glow2')} />
          <line x1="588" y1="152" x2="588" y2="284" stroke="#fdba74" strokeWidth="4" opacity="0.35" />
          <circle cx="588" cy="148" r="11" fill="#fdba74" opacity="0.85" />
          <circle cx="588" cy="148" r="24" fill="none" stroke="#fdba74" strokeWidth="1.5" opacity="0.4" />
          <path d="M566 300 q22 -16 44 0" stroke="#fdba74" strokeWidth="3" fill="none" opacity="0.22" />
        </g>
      )}

      {theme.motif === 'night' && (
        <g>
          <path d="M612 62 a34 34 0 1 0 34 42 a27 27 0 1 1 -34 -42 z" fill="#e2e8f0" opacity="0.55" />
          <g fill="#0b1026" opacity="0.55">
            <path d="M404 300 v-78 h22 v78 z" />
            <path d="M440 300 v-52 h18 v52 z" />
            <path d="M470 300 v-96 h24 v96 z" />
            <path d="M506 300 v-40 h16 v40 z" />
          </g>
          <g fill="#c7d2fe" opacity="0.45">
            <circle cx="560" cy="70" r="1.6" />
            <circle cx="636" cy="130" r="1.4" />
            <circle cx="500" cy="96" r="1.2" />
          </g>
        </g>
      )}

      {theme.motif === 'web' && (
        <g>
          <g stroke="#5eead4" opacity="0.32" strokeWidth="1.6">
            <line x1="430" y1="112" x2="524" y2="164" />
            <line x1="524" y1="164" x2="470" y2="248" />
            <line x1="524" y1="164" x2="626" y2="120" />
            <line x1="524" y1="164" x2="612" y2="228" />
            <line x1="470" y1="248" x2="612" y2="228" />
            <line x1="626" y1="120" x2="612" y2="228" />
          </g>
          <g fill="#5eead4" opacity="0.6">
            <circle cx="524" cy="164" r="5" />
            <circle cx="430" cy="112" r="3.4" />
            <circle cx="470" cy="248" r="3.4" />
            <circle cx="626" cy="120" r="3.4" />
            <circle cx="612" cy="228" r="3.4" />
          </g>
        </g>
      )}

      {theme.motif === 'compass' && (
        <g transform="translate(566 158)">
          <g fill="none" stroke="#67e8f9">
            <circle r="96" strokeWidth="1" opacity="0.22" />
            <circle r="74" strokeWidth="1.5" opacity="0.32" strokeDasharray="2 8" />
            <circle r="40" strokeWidth="1" opacity="0.25" />
          </g>
          <path d="M0 -60 L14 0 L0 60 L-14 0 Z" fill="#67e8f9" opacity="0.4" />
          <g stroke="#67e8f9" strokeWidth="2" opacity="0.5">
            <line x1="0" y1="-96" x2="0" y2="-84" />
            <line x1="0" y1="96" x2="0" y2="84" />
            <line x1="-96" y1="0" x2="-84" y2="0" />
            <line x1="96" y1="0" x2="84" y2="0" />
          </g>
        </g>
      )}

      {theme.motif === 'crack' && (
        <g stroke="#fca5a5" fill="none" strokeLinecap="round">
          <g opacity="0.45" strokeWidth="2.4">
            <path d="M500 148 l58 -44 M500 148 l62 14 M500 148 l-14 62 M500 148 l44 50" />
            <path d="M558 104 l22 -16 M562 162 l34 8 M486 210 l-8 44 M544 198 l18 34" strokeWidth="1.4" />
          </g>
          <circle cx="500" cy="148" r="4" fill="#fca5a5" opacity="0.6" stroke="none" />
        </g>
      )}

      {theme.motif === 'build' && (
        <g>
          <g fill="#c4b5fd" opacity="0.2">
            <rect x="404" y="238" width="56" height="62" rx="3" />
            <rect x="470" y="206" width="56" height="94" rx="3" />
            <rect x="536" y="172" width="56" height="128" rx="3" />
            <rect x="602" y="228" width="52" height="72" rx="3" />
          </g>
          <g stroke="#c4b5fd" opacity="0.35" strokeWidth="1.5">
            <line x1="396" y1="238" x2="662" y2="238" />
            <line x1="440" y1="176" x2="440" y2="100" strokeDasharray="4 6" />
            <line x1="440" y1="176" x2="566" y2="176" strokeDasharray="4 6" />
            <circle cx="440" cy="176" r="4" fill="#c4b5fd" />
          </g>
        </g>
      )}

      {theme.motif === 'lanterns' && (
        <g>
          <path d="M380 46 H680" stroke="#fde047" strokeWidth="1.5" opacity="0.25" />
          {[
            { x: 440, y: 46, len: 46, r: 16 },
            { x: 530, y: 46, len: 78, r: 20 },
            { x: 620, y: 46, len: 58, r: 17 },
          ].map((l) => (
            <g key={l.x}>
              <line x1={l.x} y1={l.y} x2={l.x} y2={l.y + l.len} stroke="#fde047" strokeWidth="1.4" opacity="0.35" />
              <circle cx={l.x} cy={l.y + l.len + l.r} r={l.r * 1.9} fill={u('glow2')} />
              <ellipse cx={l.x} cy={l.y + l.len + l.r} rx={l.r} ry={l.r * 1.15} fill="#fde047" opacity="0.5" />
              <line x1={l.x} y1={l.y + l.len + l.r * 2.15} x2={l.x} y2={l.y + l.len + l.r * 2.15 + 12} stroke="#fde047" strokeWidth="2" opacity="0.4" />
            </g>
          ))}
        </g>
      )}

      {theme.motif === 'constellation' && (
        <g>
          <g stroke="#93c5fd" opacity="0.3" strokeWidth="1.4">
            <path d="M420 220 L486 164 L556 190 L620 116 L664 168" fill="none" />
            <path d="M486 164 L508 96" fill="none" />
            <path d="M556 190 L548 262" fill="none" />
          </g>
          <g fill="#e0eaff" opacity="0.8">
            {[
              [420, 220, 2.6], [486, 164, 3.6], [556, 190, 2.8], [620, 116, 4.2],
              [664, 168, 2.4], [508, 96, 2.2], [548, 262, 2.2],
            ].map(([x, y, r], i) => (
              <circle key={i} cx={x} cy={y} r={r} />
            ))}
          </g>
        </g>
      )}

      {theme.motif === 'cosmos' && (
        <g>
          <ellipse cx="520" cy="140" rx="150" ry="40" fill="none" stroke="#f0abfc" strokeWidth="2" opacity="0.34" transform="rotate(-16 520 140)" />
          <ellipse cx="520" cy="140" rx="104" ry="26" fill="none" stroke="#f0abfc" strokeWidth="1.6" opacity="0.28" transform="rotate(-16 520 140)" />
          <ellipse cx="520" cy="140" rx="58" ry="14" fill="none" stroke="#fbcfe8" strokeWidth="1.4" opacity="0.3" transform="rotate(-16 520 140)" />
          <circle cx="520" cy="140" r="42" fill={u('glow2')} />
          <circle cx="520" cy="140" r="11" fill="#fbcfe8" opacity="0.75" />
          <g fill="#f5d0fe" opacity="0.6">
            {[[410, 76], [628, 90], [470, 216], [600, 232], [348, 150], [664, 176]].map(([x, y], i) => (
              <circle key={i} cx={x} cy={y} r={i % 2 ? 1.4 : 2.2} />
            ))}
          </g>
        </g>
      )}

      <path d="M-40 44 L210 -34 L318 -34 L-40 104 Z" fill="#ffffff" opacity="0.05" />
      {/* 左侧横向柔光：底色调浅之后靠它保住白字的对比度，比整体压暗好看 */}
      <rect width="680" height="300" fill={u('hscrim')} />
      <rect y="120" width="680" height="180" fill={u('scrim')} />
    </svg>
  )
}
