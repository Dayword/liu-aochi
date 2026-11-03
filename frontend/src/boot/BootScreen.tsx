import { useEffect, useRef } from 'react'
import { themeOf } from '../levelTheme'
import { BOOT_EASE, BOOT_STARS, BOOT_TIMING } from './bootTiming'
import './boot.css'

/**
 * 入场动画舞台（全屏）。
 *
 * 只做一件事：让「码境 CodeRealm」这个标从星场里长出来，然后把界面交还给你。
 * 不做终端打字、不做关卡路径、不做数据面板 —— 那些是页面里的内容，
 * 开场再演一遍只会让人觉得慢。
 *
 * 三条硬规则（踩过坑，别改）：
 *   1. 整块舞台 position:fixed 盖住全屏，结束时**整个卸载**，所以「露出的界面」
 *      就是真实 UI，不存在样式回退问题；
 *   2. 只动 transform / opacity / clip-path，外加 SVG 的 stroke-dashoffset；
 *   3. 任何异常都必须走到 finish()，绝不能把用户永久压在这一层下面。
 */
export default function BootScreen({ level, onDone }: { level: number; onDone: () => void }) {
  const theme = themeOf(level)
  const rootRef = useRef<HTMLDivElement>(null)
  const sceneRef = useRef<HTMLDivElement>(null)
  const centerRef = useRef<HTMLDivElement>(null)
  const markRef = useRef<SVGSVGElement>(null)
  const orbitRef = useRef<SVGEllipseElement>(null)
  const planetRef = useRef<SVGCircleElement>(null)
  const pulseRef = useRef<SVGCircleElement>(null)
  const dot1Ref = useRef<SVGCircleElement>(null)
  const dot2Ref = useRef<SVGCircleElement>(null)
  const wordRef = useRef<HTMLSpanElement>(null)
  const doneRef = useRef(false)

  useEffect(() => {
    const root = rootRef.current
    if (!root) return
    const mobile = window.matchMedia('(max-width: 767px)').matches
    const T = mobile ? BOOT_TIMING.mobile : BOOT_TIMING.desktop
    const anims: Animation[] = []
    const timers: number[] = []

    /** 页面里要让位的元素：一律先藏起来，等揭幕时再一环一环推上来 */
    const covered = Array.from(
      document.querySelectorAll<HTMLElement>('[data-boot-wave="bar"], [data-boot-wave="main"], [data-boot-wave="block"]'),
    )
    covered.forEach((el) => {
      el.style.opacity = '0'
    })

    const play = (
      el: Element | null | undefined,
      frames: Keyframe[],
      opt: KeyframeAnimationOptions,
    ) => {
      if (!el || typeof el.animate !== 'function') return
      try {
        anims.push(el.animate(frames, { fill: 'both', easing: BOOT_EASE.SOFT, ...opt }))
      } catch {
        /* 浏览器不支持就跳过这一段，不影响其它镜头 */
      }
    }

    const finish = () => {
      if (doneRef.current) return
      doneRef.current = true
      timers.forEach((t) => window.clearTimeout(t))
      anims.forEach((a) => {
        try {
          a.cancel()
        } catch {
          /* ignore */
        }
      })
      covered.forEach((el) => {
        el.style.opacity = ''
      })
      document.body.style.overflow = ''
      onDone()
    }

    // 任意操作都能跳过：用户不想看第二遍的时候不该被按住三秒
    const skip = () => finish()
    window.addEventListener('keydown', skip, { once: true })
    window.addEventListener('pointerdown', skip, { once: true })
    window.addEventListener('wheel', skip, { once: true, passive: true })

    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    // ---------- ① 星场浮出 ----------
    play(sceneRef.current, [{ opacity: 0 }, { opacity: 1 }], { duration: 320, easing: BOOT_EASE.SOFT })

    // ---------- ② 轨道先自己画一圈 ----------
    play(orbitRef.current, [{ strokeDashoffset: 1 }, { strokeDashoffset: 0 }], {
      duration: T.orbitDur,
      delay: T.orbit,
      easing: BOOT_EASE.ENTER,
    })

    // ---------- ③ 行星落位 ----------
    play(planetRef.current, [{ strokeDashoffset: 1 }, { strokeDashoffset: 0 }], {
      duration: T.planetDur,
      delay: T.planet,
      easing: BOOT_EASE.ENTER,
    })
    play(markRef.current, [{ transform: 'scale(.92)' }, { transform: 'scale(1)' }], {
      duration: T.planetDur + 220,
      delay: T.planet,
      easing: BOOT_EASE.ENTER,
    })

    // ---------- ④ 两颗小星点亮 ----------
    play(dot1Ref.current, [{ r: 0 }, { r: 1.8 }], {
      duration: T.dotsDur,
      delay: T.dots,
      easing: BOOT_EASE.ENTER,
    })
    play(dot2Ref.current, [{ r: 0 }, { r: 1.35 }], {
      duration: T.dotsDur,
      delay: T.dots + 90,
      easing: BOOT_EASE.ENTER,
    })

    // ---------- ⑤ 字标从左擦出 ----------
    play(wordRef.current, [{ clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0 0 0)' }], {
      duration: T.wordDur,
      delay: T.word,
      easing: BOOT_EASE.WIPE,
    })

    // ---------- ⑥ 字距收拢，像「合上」一样落定 ----------
    play(wordRef.current, [{ letterSpacing: '0.2em' }, { letterSpacing: '0.01em' }], {
      duration: T.trackDur,
      delay: T.track,
      easing: BOOT_EASE.WIPE,
    })
    play(centerRef.current, [{ transform: 'translate(-50%,-50%) scale(.985)' }, { transform: 'translate(-50%,-50%) scale(1)' }], {
      duration: T.trackDur,
      delay: T.track,
      easing: BOOT_EASE.ENTER,
    })

    // ---------- ⑦ 轨道向外扩一次（唯一一处「动势」收尾） ----------
    play(pulseRef.current, [{ r: 9, opacity: 0.5 }, { r: 17, opacity: 0 }], {
      duration: T.pulseDur,
      delay: T.pulse,
      easing: BOOT_EASE.SOFT,
    })

    // ---------- 调试：?bootAt=1200 定格到某一帧（仅开发环境） ----------
    const seek = import.meta.env.DEV ? new URLSearchParams(location.search).get('bootAt') : null
    if (seek) {
      const t = Number(seek) || 0
      anims.forEach((a) => {
        a.pause()
        a.currentTime = t
      })
      return () => {
        window.removeEventListener('keydown', skip)
        window.removeEventListener('pointerdown', skip)
        window.removeEventListener('wheel', skip)
        document.body.style.overflow = prevOverflow
      }
    }

    // ---------- ⑧ 揭幕：等页面就绪，最多等 readyTimeout ----------
    // 页面真正画出东西了没：主轴容器有高度就够（非首页没有 wave 区块）
    const appReady = () => {
      const mainEl = document.querySelector('[data-boot-wave="main"]')
      return !!mainEl && mainEl.getBoundingClientRect().height > 80
    }

    const reveal = () => {
      // 字标先走：否则淡出过程中一坨白字会正压在卡片上，很脏
      play(centerRef.current, [{ opacity: 1 }, { opacity: 0 }], {
        duration: 300,
        delay: 0,
        easing: BOOT_EASE.WIPE,
      })

      // 场景推进淡出（放大一点点，像镜头往前推）
      play(sceneRef.current, [
        { opacity: 1, transform: 'scale(1)' },
        { opacity: 0, transform: 'scale(1.05)' },
      ], { duration: T.outDur, easing: BOOT_EASE.WIPE })

      // 界面环环入场：侧栏/顶栏 → 主区 → 卡内区块
      document.querySelectorAll<HTMLElement>('[data-boot-wave="bar"]').forEach((el) => {
        play(el, [{ opacity: 0, transform: 'translateY(8px)' }, { opacity: 1, transform: 'translateY(0)' }], {
          duration: 380,
          delay: 20,
          easing: BOOT_EASE.ENTER,
        })
      })
      const mainEl = document.querySelector<HTMLElement>('[data-boot-wave="main"]')
      if (mainEl) {
        play(mainEl, [{ opacity: 0 }, { opacity: 1 }], { duration: 260, delay: 60, easing: BOOT_EASE.ENTER })
      }
      document.querySelectorAll<HTMLElement>('[data-boot-wave="block"]').forEach((el, i) => {
        play(el, [
          { opacity: 0, transform: 'translateY(14px)' },
          { opacity: 1, transform: 'translateY(0)' },
        ], { duration: 420, delay: 120 + i * 55, easing: BOOT_EASE.ENTER })
      })

      timers.push(window.setTimeout(finish, T.end - T.out))
    }

    const deadline = performance.now() + T.readyTimeout
    const waitReady = () => {
      if (doneRef.current) return
      if (appReady() || performance.now() > deadline) {
        reveal()
        return
      }
      timers.push(window.setTimeout(waitReady, 100))
    }
    timers.push(window.setTimeout(waitReady, T.out))

    return () => {
      window.removeEventListener('keydown', skip)
      window.removeEventListener('pointerdown', skip)
      window.removeEventListener('wheel', skip)
      document.body.style.overflow = prevOverflow
      timers.forEach((t) => window.clearTimeout(t))
      anims.forEach((a) => {
        try {
          a.cancel()
        } catch {
          /* ignore */
        }
      })
      covered.forEach((el) => {
        el.style.opacity = ''
      })
    }
    // 一次入场只跑一遍：level / onDone 变化不该重播
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div ref={rootRef} className="boot-stage" data-boot-stage aria-hidden="true">
      <div
        ref={sceneRef}
        className="boot-scene"
        style={{
          // 必须给一个不透明的底色：只写 radial-gradient 的话，中心那 40% 透明度
          // 会让下面浅色的页面透上来，整个舞台变成一块发白的光斑（踩过）。
          backgroundColor: theme.sky[2],
          backgroundImage: `radial-gradient(ellipse 72% 58% at 50% 38%, ${theme.sky[1]}70 0%, transparent 64%), radial-gradient(ellipse 96% 76% at 50% 30%, ${theme.sky[0]}45 0%, transparent 74%)`,
        }}
      >
        <div className="boot-dots" />
        {BOOT_STARS.map(([x, y, r], i) => (
          <span
            key={i}
            className="boot-star"
            style={{
              left: `${x}%`,
              top: `${y}%`,
              width: r * 2.4,
              height: r * 2.4,
              background: theme.glow[0],
              animationDelay: `${i * 0.42}s`,
            }}
          />
        ))}
        <div className="boot-veil" />

        <div ref={centerRef} className="boot-center">
          <svg ref={markRef} className="boot-mark" viewBox="0 0 34 34" fill="none">
            <ellipse
              ref={orbitRef}
              className="boot-draw"
              cx="17"
              cy="17"
              rx="14"
              ry="5"
              pathLength={1}
              stroke={theme.glow[0]}
              strokeWidth="1.4"
              opacity="0.9"
              transform="rotate(-22 17 17)"
            />
            <circle
              ref={pulseRef}
              cx="17"
              cy="17"
              r="9"
              stroke={theme.accent}
              strokeWidth="1.2"
              opacity="0"
            />
            <circle
              ref={planetRef}
              className="boot-draw"
              cx="17"
              cy="17"
              r="7.5"
              pathLength={1}
              stroke="#ffffff"
              strokeWidth="2.2"
            />
            <circle ref={dot1Ref} cx="28.6" cy="9.4" r="0" fill="#ffffff" />
            <circle ref={dot2Ref} cx="5.4" cy="23.8" r="0" fill={theme.glow[0]} />
          </svg>

          <span ref={wordRef} className="boot-word">
            码境 CodeRealm
          </span>
        </div>
      </div>
    </div>
  )
}
