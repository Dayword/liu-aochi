import type { AmbientId } from '../theme/ThemeProvider'

/**
 * 环境音：全部由 Web Audio 实时合成，没有一个音频文件。
 *
 * 和第一版的区别：第一版基本就是「一段噪声过个滤波器」，听感是电风扇不是雨。
 * 现在每一种声音都是**多层叠加 + 随机事件**：
 *   底噪层（噪声 → 滤波器）给「场」，事件层（随机调度的短音）给「事」。
 * 雨声靠雨点、咖啡馆靠断续人声、键盘靠真实敲击节奏、篝火靠爆裂声，
 * 只有事件层随机起来，才不会听出循环。
 */

export type NoiseKind = 'white' | 'pink' | 'brown'

/** 雨的四档强度 */
export const RAIN_LEVELS = ['细雨', '小雨', '中雨', '大雨'] as const
export const RAIN_DEFAULT = 1

export interface AmbientOpts {
  /** 0~3，对应 RAIN_LEVELS */
  rainLevel: number
}

const DEFAULT_OPTS: AmbientOpts = { rainLevel: RAIN_DEFAULT }

interface Voice {
  /** 已构建的参数指纹，同指纹不重建（避免调音量也重开一遍） */
  key: string
  out: GainNode
  stop: () => void
}

let ctx: AudioContext | null = null
let master: GainNode | null = null
let live: Voice | null = null
let armed = false
let wanted: { id: AmbientId; volume: number; opts: AmbientOpts } | null = null
/** 只用于验收：切一次声音算一次，用来证明「只调音量不会重建」 */
let buildCount = 0

function ensure(): AudioContext | null {
  if (ctx) return ctx
  const AC = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
  if (!AC) return null
  try {
    ctx = new AC()
  } catch {
    // 无音频设备的机器（部分 Linux 服务器、无头浏览器）会在这里抛，
    // 环境音是纯装饰，不能因为它把设置页搞崩
    return null
  }
  master = ctx.createGain()
  master.gain.value = 0
  master.connect(ctx.destination)
  return ctx
}

/* ============================================================
 * 噪声素材
 * ========================================================== */

const bufCache = new Map<string, AudioBuffer>()

/**
 * 生成噪声缓冲。双声道**各自独立**生成——左右完全相同会听起来「挤在头中间」，
 * 立体声去相关是这个合成器里性价比最高的一步。
 * pink 用 Paul Kellet 的经典滤波器，比白噪声柔和得多，接近雨/风/人群的能量分布。
 */
function noiseBuf(ac: AudioContext, kind: NoiseKind, seconds = 3): AudioBuffer {
  const key = `${kind}:${seconds}:${ac.sampleRate}`
  const hit = bufCache.get(key)
  if (hit) return hit
  const len = Math.floor(ac.sampleRate * seconds)
  const buf = ac.createBuffer(2, len, ac.sampleRate)
  for (let ch = 0; ch < 2; ch++) {
    const d = buf.getChannelData(ch)
    let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0, last = 0
    for (let i = 0; i < len; i++) {
      const w = Math.random() * 2 - 1
      if (kind === 'white') {
        d[i] = w * 0.45
      } else if (kind === 'brown') {
        last = (last + 0.02 * w) / 1.02
        d[i] = last * 3.2
      } else {
        b0 = 0.99886 * b0 + w * 0.0555179
        b1 = 0.99332 * b1 + w * 0.0750759
        b2 = 0.969 * b2 + w * 0.153852
        b3 = 0.8665 * b3 + w * 0.3104856
        b4 = 0.55 * b4 + w * 0.5329522
        b5 = -0.7616 * b5 - w * 0.016898
        d[i] = (b0 + b1 + b2 + b3 + b4 + b5 + b6 + w * 0.5362) * 0.09
        b6 = w * 0.115926
      }
    }
  }
  bufCache.set(key, buf)
  return buf
}

function loop(ac: AudioContext, buf: AudioBuffer, dest: AudioNode, offset = 0) {
  const s = ac.createBufferSource()
  s.buffer = buf
  s.loop = true
  s.connect(dest)
  s.start(0, offset)
  return s
}

/* ============================================================
 * 小工具
 * ========================================================== */

const rnd = (a: number, b: number) => a + Math.random() * (b - a)
/** 指数分布间隔：事件不会像节拍器一样均匀，这一点决定了「像不像现场」 */
const gap = (perSecond: number) => -Math.log(1 - Math.random()) / Math.max(0.1, perSecond)

function env(p: AudioParam, t: number, peak: number, attack: number, decay: number) {
  p.setValueAtTime(0.0001, t)
  p.exponentialRampToValueAtTime(Math.max(0.0002, peak), t + attack)
  p.exponentialRampToValueAtTime(0.0001, t + attack + decay)
}

/** 会自己收尾的随机事件调度器：每 200ms 补齐未来 0.9s 内的事件，切后台被节流也不会断 */
function pump(ac: AudioContext, perSecond: number, fire: (t: number) => void) {
  let next = ac.currentTime + 0.04
  let dead = false
  const tick = () => {
    if (dead) return
    const until = ac.currentTime + 0.9
    if (next < ac.currentTime) next = ac.currentTime + 0.02
    let guard = 0
    while (next < until && guard++ < 500) {
      fire(next)
      next += gap(perSecond)
    }
  }
  tick()
  const timer = window.setInterval(tick, 200)
  return () => {
    dead = true
    window.clearInterval(timer)
  }
}

/* ============================================================
 * 雨
 * ========================================================== */

/**
 * 四档参数。听感的差别不只是「响度」，主要是三层比例：
 * hiss（高频沙沙）→ body（中低频的连成一片）→ rumble（脚下那种低鸣）。
 * 细雨只有稀疏的高频雨点；大雨是 body 与 rumble 撑起来的轰鸣。
 */
const RAIN = [
  { hiss: 0.16, hp: 2800, peak: 5200, body: 0.06, bodyLp: 1100, rumble: 0.0, drops: 4, dropGain: 0.36, drip: 0.4, swell: 0.35 },
  { hiss: 0.24, hp: 2000, peak: 4200, body: 0.15, bodyLp: 760, rumble: 0.02, drops: 13, dropGain: 0.26, drip: 0.24, swell: 0.28 },
  { hiss: 0.38, hp: 1300, peak: 3200, body: 0.28, bodyLp: 560, rumble: 0.055, drops: 28, dropGain: 0.19, drip: 0.13, swell: 0.2 },
  { hiss: 0.54, hp: 760, peak: 2400, body: 0.48, bodyLp: 430, rumble: 0.13, drops: 52, dropGain: 0.13, drip: 0.05, swell: 0.14 },
]

function buildRain(ac: AudioContext, dest: AudioNode, level: number) {
  const p = RAIN[Math.max(0, Math.min(3, Math.round(level)))]
  const stops: (() => void)[] = []

  // —— 底噪：高频沙沙 ——
  const hissHp = ac.createBiquadFilter()
  hissHp.type = 'highpass'
  hissHp.frequency.value = p.hp
  hissHp.Q.value = 0.6
  const hissPeak = ac.createBiquadFilter()
  hissPeak.type = 'peaking'
  hissPeak.frequency.value = p.peak
  hissPeak.Q.value = 0.8
  hissPeak.gain.value = 3.5
  const hissGain = ac.createGain()
  hissGain.gain.value = p.hiss
  const hissSrc = loop(ac, noiseBuf(ac, 'pink'), hissHp)
  hissHp.connect(hissPeak).connect(hissGain).connect(dest)

  // 慢速起伏：一阵一阵的，不是一条直线（两个周期错开，避免听出循环）
  const swellA = ac.createOscillator()
  swellA.frequency.value = 0.061
  const swellB = ac.createOscillator()
  swellB.frequency.value = 0.097
  const swellDepth = ac.createGain()
  swellDepth.gain.value = p.hiss * p.swell
  swellA.connect(swellDepth)
  swellB.connect(swellDepth)
  swellDepth.connect(hissGain.gain)
  swellA.start()
  swellB.start()
  stops.push(() => { swellA.stop(); swellB.stop() })

  // —— 雨幕：雨点砸下来的中低频成片感 ——
  const bodyLp = ac.createBiquadFilter()
  bodyLp.type = 'lowpass'
  bodyLp.frequency.value = p.bodyLp
  bodyLp.Q.value = 0.7
  const bodyGain = ac.createGain()
  bodyGain.gain.value = p.body
  const bodySrc = loop(ac, noiseBuf(ac, 'pink'), bodyLp, 1.1)
  bodyLp.connect(bodyGain).connect(dest)

  // —— 低频轰鸣：只有中雨以上才有 ——
  if (p.rumble > 0) {
    const rl = ac.createBiquadFilter()
    rl.type = 'lowpass'
    rl.frequency.value = 130
    const rg = ac.createGain()
    rg.gain.value = p.rumble
    const rsrc = loop(ac, noiseBuf(ac, 'brown'), rl, 0.7)
    rl.connect(rg).connect(dest)
  }

  // —— 雨点：随机高频短音，这一层才是「雨」而不是「噪声」 ——
  const dropBuf = noiseBuf(ac, 'white', 1)
  const dropAt = (t: number) => {
    const pan = ac.createStereoPanner()
    pan.pan.value = rnd(-0.85, 0.85)
    pan.connect(dest)

    const src = ac.createBufferSource()
    src.buffer = dropBuf
    const bp = ac.createBiquadFilter()
    bp.type = 'bandpass'
    // 偏向高频：雨点落在窗台/叶子上是「嗒」，不是「咚」
    bp.frequency.value = 900 + Math.pow(Math.random(), 1.7) * 5600
    bp.Q.value = rnd(1.4, 4.2)
    const g = ac.createGain()
    env(g.gain, t, p.dropGain * rnd(0.35, 1), 0.0015, rnd(0.014, 0.05))
    src.connect(bp).connect(g).connect(pan)
    src.start(t, Math.random() * 0.9, 0.12)
    src.stop(t + 0.14)

    // 「滴」——气泡共振，音高往上滑。细雨里偶尔冒一声非常抓耳，
    // 但不能多、不能响：密了就像电子合成器的 pew，反而不像雨
    if (Math.random() < p.drip) {
      const o = ac.createOscillator()
      o.type = 'sine'
      const f0 = rnd(680, 1250)
      o.frequency.setValueAtTime(f0, t)
      o.frequency.exponentialRampToValueAtTime(f0 * rnd(1.8, 2.6), t + 0.05)
      const og = ac.createGain()
      env(og.gain, t, p.dropGain * rnd(0.14, 0.34), 0.004, 0.07)
      o.connect(og).connect(pan)
      o.start(t)
      o.stop(t + 0.12)
    }
  }
  stops.push(pump(ac, p.drops, dropAt))

  return {
    stop: () => {
      for (const s of stops) s()
      hissSrc.stop()
      bodySrc.stop()
    },
  }
}

/* ============================================================
 * 咖啡馆
 * ========================================================== */

function buildCafe(ac: AudioContext, dest: AudioNode) {
  const stops: (() => void)[] = []

  // 房间底噪：低频的嗡嗡声，远低于人声，只负责「空间感」
  const roomLp = ac.createBiquadFilter()
  roomLp.type = 'lowpass'
  roomLp.frequency.value = 380
  const roomGain = ac.createGain()
  roomGain.gain.value = 0.085
  // 80Hz 以下全是「轰」，切掉之后低频占比立刻正常，人声才浮得出来
  const roomHp = ac.createBiquadFilter()
  roomHp.type = 'highpass'
  roomHp.frequency.value = 80
  const roomSrc = loop(ac, noiseBuf(ac, 'brown'), roomHp)
  roomHp.connect(roomLp).connect(roomGain).connect(dest)

  // 人声：一段一段的「音节」，音节连成词、词之间换人。
  // 不用共振峰那么复杂，带通 + 低通 + 随机包络已经很像隔着桌子听人说话。
  // f1 落在 450~900Hz：这是人声「有元音味道」的区间，
  // 压低到 300 以下就只剩嗡嗡声，跟空调外机没区别（第一版就是这么翻的车）。
  const voiceBuf = noiseBuf(ac, 'pink', 2)
  const syllable = (t: number, panNode: StereoPannerNode, base: number, amp: number) => {
    const src = ac.createBufferSource()
    src.buffer = voiceBuf
    const f1 = ac.createBiquadFilter()
    f1.type = 'bandpass'
    f1.frequency.value = base * rnd(0.8, 1.25) // 元音不同，音色不同
    f1.Q.value = rnd(1.2, 2.2)
    const f2 = ac.createBiquadFilter()
    f2.type = 'lowpass'
    f2.frequency.value = rnd(1800, 3200)
    const g = ac.createGain()
    const dur = rnd(0.07, 0.19)
    env(g.gain, t, amp * rnd(0.5, 1), 0.02, dur)
    src.connect(f1).connect(f2).connect(g).connect(panNode)
    src.start(t, Math.random() * 1.8, dur + 0.1)
    src.stop(t + dur + 0.12)
  }
  const utterance = (t: number) => {
    const pan = ac.createStereoPanner()
    pan.pan.value = rnd(-0.9, 0.9)
    pan.connect(dest)
    const base = rnd(450, 900) // 男声偏低、女声偏高
    const amp = rnd(0.16, 0.3) * (1 - Math.abs(pan.pan.value) * 0.35) // 两边的人更远
    const n = Math.round(rnd(2, 7))
    let cursor = t
    for (let i = 0; i < n; i++) {
      // 每个音节之间可能连着说，也可能换气停一下
      if (i > 0) cursor += Math.random() < 0.14 ? rnd(0.16, 0.4) : rnd(0.09, 0.16)
      syllable(cursor, pan, base, amp)
    }
  }
  stops.push(pump(ac, 2.8, utterance))

  // 杯碟碰撞：细小的三角波 + 两个泛音，偶尔一声，位置随机
  stops.push(
    pump(ac, 0.14, (t) => {
      const pan = ac.createStereoPanner()
      pan.pan.value = rnd(-0.95, 0.95)
      pan.connect(dest)
      const f = rnd(1900, 4200)
      for (const [mul, amp] of [
        [1, 0.055],
        [2.71, 0.022],
        [5.3, 0.012],
      ]) {
        const o = ac.createOscillator()
        o.type = 'triangle'
        o.frequency.value = f * mul
        const g = ac.createGain()
        env(g.gain, t, amp, 0.002, mul > 2 ? 0.06 : 0.28)
        o.connect(g).connect(pan)
        o.start(t)
        o.stop(t + 0.4)
      }
    }),
  )

  return {
    stop: () => {
      for (const s of stops) s()
      roomSrc.stop()
    },
  }
}

/* ============================================================
 * 键盘
 * ========================================================== */

function buildKeys(ac: AudioContext, dest: AudioNode) {
  const stops: (() => void)[] = []
  const buf = noiseBuf(ac, 'white', 1)

  const click = (t: number, deep: number) => {
    const pan = ac.createStereoPanner()
    pan.pan.value = rnd(-0.35, 0.35)
    pan.connect(dest)

    // 键帽的「嗒」：极短的高频噪声
    const src = ac.createBufferSource()
    src.buffer = buf
    const bp = ac.createBiquadFilter()
    bp.type = 'bandpass'
    bp.frequency.value = rnd(1600, 4200) - deep * 400
    bp.Q.value = rnd(2, 4)
    const g = ac.createGain()
    env(g.gain, t, rnd(0.28, 0.44), 0.001, rnd(0.01, 0.025))
    src.connect(bp).connect(g).connect(pan)
    src.start(t, Math.random() * 0.9, 0.05)
    src.stop(t + 0.06)

    // 键程到底的「咚」：低频短正弦，没有它就只剩塑料声
    const o = ac.createOscillator()
    o.type = 'sine'
    o.frequency.setValueAtTime(rnd(150, 210) - deep * 40, t)
    o.frequency.exponentialRampToValueAtTime(rnd(70, 95), t + 0.05)
    const og = ac.createGain()
    env(og.gain, t, rnd(0.045, 0.085), 0.002, 0.05 + deep * 0.03)
    o.connect(og).connect(pan)
    o.start(t)
    o.stop(t + 0.1)
  }

  // 真实打字是成串的：敲 3~14 下一停，停 0.5~2.4 秒再来一串
  let dead = false
  let timer = 0
  const burst = () => {
    if (dead) return
    const n = Math.round(rnd(3, 14))
    let t = ac.currentTime + 0.02
    for (let i = 0; i < n; i++) {
      const space = Math.random() < 0.06
      click(t, space ? 1 : 0)
      t += space ? rnd(0.11, 0.18) : rnd(0.055, 0.16)
    }
    const wait = rnd(120, 700) + (n > 10 ? rnd(200, 900) : 0)
    timer = window.setTimeout(burst, wait)
  }
  // 立刻敲第一串：点了半天没动静，会以为功能坏了
  burst()
  stops.push(() => {
    dead = true
    window.clearTimeout(timer)
  })

  return {
    stop: () => {
      for (const s of stops) s()
    },
  }
}

/* ============================================================
 * 海浪
 * ========================================================== */

function buildWaves(ac: AudioContext, dest: AudioNode) {
  // 一个 0.085Hz 的 LFO = 11.7 秒一个浪，正好是海边的节奏
  const lfo = ac.createOscillator()
  lfo.frequency.value = 0.085
  const lfo2 = ac.createOscillator()
  lfo2.frequency.value = 0.052

  const washLp = ac.createBiquadFilter()
  washLp.type = 'lowpass'
  washLp.frequency.value = 780
  const washGain = ac.createGain()
  washGain.gain.value = 0.26
  const washSrc = loop(ac, noiseBuf(ac, 'pink'), washLp)
  washLp.connect(washGain).connect(dest)

  const washDepth = ac.createGain()
  washDepth.gain.value = 0.17
  lfo.connect(washDepth)
  lfo2.connect(washDepth)
  washDepth.connect(washGain.gain)

  // 浪花：只有浪头才有，所以把 LFO 延迟 1.6 秒（= 浪推上来之后再碎）
  const delay = ac.createDelay(3)
  delay.delayTime.value = 1.6
  const foamHp = ac.createBiquadFilter()
  foamHp.type = 'highpass'
  foamHp.frequency.value = 2200
  const foamGain = ac.createGain()
  // 底值必须大于 LFO 深度，否则增益会跑到负数（反相，不报错但很怪）
  foamGain.gain.value = 0.09
  const foamSrc = loop(ac, noiseBuf(ac, 'white'), foamHp, 1.3)
  foamHp.connect(foamGain).connect(dest)
  const foamDepth = ac.createGain()
  foamDepth.gain.value = 0.08
  lfo.connect(delay)
  delay.connect(foamDepth)
  foamDepth.connect(foamGain.gain)

  const rumbleLp = ac.createBiquadFilter()
  rumbleLp.type = 'lowpass'
  rumbleLp.frequency.value = 140
  const rumbleGain = ac.createGain()
  rumbleGain.gain.value = 0.09
  const rumbleSrc = loop(ac, noiseBuf(ac, 'brown'), rumbleLp, 0.4)
  rumbleLp.connect(rumbleGain).connect(dest)

  lfo.start()
  lfo2.start()

  return {
    stop: () => {
      lfo.stop()
      lfo2.stop()
      washSrc.stop()
      foamSrc.stop()
      rumbleSrc.stop()
    },
  }
}

/* ============================================================
 * 篝火
 * ========================================================== */

function buildFire(ac: AudioContext, dest: AudioNode) {
  const stops: (() => void)[] = []

  // 火焰本身：低频噪声 + 随机增益抖动（不用正弦 LFO，会听出规律）
  const baseLp = ac.createBiquadFilter()
  baseLp.type = 'lowpass'
  baseLp.frequency.value = 480
  baseLp.Q.value = 0.8
  const baseGain = ac.createGain()
  baseGain.gain.value = 0.12
  const baseSrc = loop(ac, noiseBuf(ac, 'brown'), baseLp)
  baseLp.connect(baseGain).connect(dest)

  // 中间那层「呼呼」：只有低频会像鼓风机，加上这段才像火在烧
  const midBp = ac.createBiquadFilter()
  midBp.type = 'bandpass'
  midBp.frequency.value = 1100
  midBp.Q.value = 0.6
  const midGain = ac.createGain()
  midGain.gain.value = 0.05
  const midSrc = loop(ac, noiseBuf(ac, 'pink'), midBp, 0.9)
  midBp.connect(midGain).connect(dest)

  let dead = false
  const flicker = () => {
    if (dead) return
    const t = ac.currentTime
    const v = baseGain.gain.value
    baseGain.gain.cancelScheduledValues(t)
    baseGain.gain.setValueAtTime(v, t)
    baseGain.gain.linearRampToValueAtTime(v * rnd(0.55, 1.5), t + rnd(0.07, 0.3))
    timer = window.setTimeout(flicker, rnd(90, 320))
  }
  let timer = window.setTimeout(flicker, 100)

  // 爆裂：极短的噪声脉冲，密的时候连成「噼啪」
  const crackBuf = noiseBuf(ac, 'white', 1)
  stops.push(
    pump(ac, 8, (t) => {
      const pan = ac.createStereoPanner()
      pan.pan.value = rnd(-0.8, 0.8)
      pan.connect(dest)
      const src = ac.createBufferSource()
      src.buffer = crackBuf
      const hp = ac.createBiquadFilter()
      hp.type = 'highpass'
      hp.frequency.value = rnd(1200, 4200)
      const g = ac.createGain()
      env(g.gain, t, rnd(0.06, 0.3), 0.0008, rnd(0.008, 0.05))
      src.connect(hp).connect(g).connect(pan)
      src.start(t, Math.random() * 0.9, 0.06)
      src.stop(t + 0.08)
    }),
  )

  return {
    stop: () => {
      dead = true
      window.clearTimeout(timer)
      for (const s of stops) s()
      baseSrc.stop()
      midSrc.stop()
    },
  }
}

/* ============================================================
 * 白噪音
 * ========================================================== */

function buildWhite(ac: AudioContext, dest: AudioNode) {
  const lp = ac.createBiquadFilter()
  lp.type = 'lowpass'
  lp.frequency.value = 7500
  const g = ac.createGain()
  g.gain.value = 0.3
  const src = loop(ac, noiseBuf(ac, 'pink'), lp)
  lp.connect(g).connect(dest)
  return { stop: () => src.stop() }
}

/* ============================================================
 * 组装
 * ========================================================== */

/**
 * 各声音的响度配平。
 * 合成出来的原始电平差得很远：键盘是一串很稀的瞬态（RMS 只有雨声的 1/14），
 * 直接摆在一起，用户从「大雨」切到「键盘」会以为坏了。
 * 这里按离线渲染实测的 RMS 反推系数，目标是把六种声音拉到同一档，
 * 雨的四档**内部差异保留**（那是雨势本身的强弱，不该被配平掉）。
 */
const TRIM: Record<string, number> = {
  rain: 1,
  cafe: 1.7,
  keys: 2.8,
  waves: 0.85,
  fire: 1.9,
  white: 0.75,
}

function build(
  id: AmbientId,
  ac: AudioContext,
  opts: AmbientOpts,
  dest: AudioNode,
): { out: GainNode; stop: () => void; trim: number } | null {
  if (id === 'none') return null
  const out = ac.createGain()
  out.gain.value = 0
  out.connect(dest)
  const p = { ...DEFAULT_OPTS, ...opts }
  const rain = Math.max(0, Math.min(3, Math.round(p.rainLevel)))

  const body =
    id === 'rain'
      ? buildRain(ac, out, rain)
      : id === 'cafe'
        ? buildCafe(ac, out)
        : id === 'keys'
          ? buildKeys(ac, out)
          : id === 'waves'
            ? buildWaves(ac, out)
            : id === 'fire'
              ? buildFire(ac, out)
              : buildWhite(ac, out)

  return {
    out,
    trim: TRIM[id] ?? 1,
    stop: () => {
      body.stop()
      out.disconnect()
    },
  }
}

function fade(target: number, ms = 420) {
  if (!ctx || !master) return
  const now = ctx.currentTime
  const g = master.gain
  g.cancelScheduledValues(now)
  g.setValueAtTime(Math.max(0.0001, g.value), now)
  g.linearRampToValueAtTime(Math.max(0.0001, target), now + ms / 1000)
}

/**
 * 播放某个环境音。
 * 切换声音或切换雨的强度时**交叉淡入淡出**：旧的 0.45s 内淡到 0 再销毁，
 * 新的从 0 淡上来。硬切会在切换瞬间「啪」一下，非常明显。
 */
export function playAmbient(id: AmbientId, volume: number, opts: AmbientOpts = DEFAULT_OPTS) {
  const rain = Math.max(0, Math.min(3, Math.round(opts.rainLevel)))
  const merged: AmbientOpts = { ...DEFAULT_OPTS, ...opts, rainLevel: rain }
  wanted = { id, volume, opts: merged }
  if (id === 'none') {
    stopAmbient()
    return
  }
  const ac = ensure()
  if (!ac || !master) return

  const key = `${id}:${id === 'rain' ? rain : ''}`
  if (live && live.key === key) {
    // 只是调音量或重复点同一个，不重建
    const go = () => fade(Math.min(1, Math.max(0, volume)))
    if (ac.state === 'suspended') void ac.resume().then(go).catch(() => undefined)
    else go()
    return
  }

  const next = build(id, ac, merged, master)
  if (!next) return
  buildCount++
  const old = live
  live = { key, out: next.out, stop: next.stop }

  const now = ac.currentTime
  next.out.gain.setValueAtTime(0.0001, now)
  next.out.gain.linearRampToValueAtTime(next.trim, now + 0.45)
  if (old) {
    old.out.gain.cancelScheduledValues(now)
    old.out.gain.setValueAtTime(Math.max(0.0001, old.out.gain.value), now)
    old.out.gain.linearRampToValueAtTime(0.0001, now + 0.45)
    window.setTimeout(() => old.stop(), 700)
  }

  const go = () => fade(Math.min(1, Math.max(0, volume)))
  if (ac.state === 'suspended') {
    void ac.resume().then(go).catch(() => {
      /* 用户还没交互，等 armAmbient 的那次点击 */
    })
  } else {
    go()
  }
}

export function setAmbientVolume(volume: number) {
  if (wanted) wanted.volume = volume
  if (ctx && master) fade(Math.min(1, Math.max(0, volume)))
}

export function stopAmbient() {
  if (live) {
    const old = live
    live = null
    if (ctx) {
      const now = ctx.currentTime
      old.out.gain.cancelScheduledValues(now)
      old.out.gain.setValueAtTime(Math.max(0.0001, old.out.gain.value), now)
      old.out.gain.linearRampToValueAtTime(0.0001, now + 0.35)
      window.setTimeout(() => old.stop(), 500)
    } else {
      old.stop()
    }
  }
  if (ctx && master) fade(0.0001, 260)
}

export function ambientRunning(): boolean {
  return !!live
}

/**
 * 页面加载时如果上次选了环境音，浏览器会拦住自动播放。
 * 这里不硬启动，而是等第一次点击/触摸再恢复 —— 用户不会看到报错，
 * 也不会出现「设置里选了雨声但什么都没有」的困惑。
 */
export function armAmbient(id: AmbientId, volume: number, opts: AmbientOpts = DEFAULT_OPTS) {
  if (id === 'none' || armed) return
  armed = true
  wanted = { id, volume, opts }
  const kick = () => {
    window.removeEventListener('pointerdown', kick)
    window.removeEventListener('keydown', kick)
    const w = wanted
    playAmbient(id, w?.volume ?? volume, w?.opts ?? opts)
  }
  window.addEventListener('pointerdown', kick, { once: true })
  window.addEventListener('keydown', kick, { once: true })
}

// 调试钩子（仅开发环境）：验收脚本需要把分析器挂到 master 上量响度/频谱，
// 还要能把同一个 build 跑在 OfflineAudioContext 上离线渲染 —— 无头浏览器的
// 音频时钟只按 2% 的速度走，实时取样根本量不出东西。
if (import.meta.env.DEV) {
  ;(window as unknown as Record<string, unknown>).__caAudio = {
    ctx: () => ctx,
    master: () => master,
    running: () => !!live,
    key: () => live?.key ?? '',
    builds: () => buildCount,
    buildOffline: (ac: BaseAudioContext, id: AmbientId, opts: AmbientOpts) => {
      const v = build(id, ac as unknown as AudioContext, { ...DEFAULT_OPTS, ...opts }, ac.destination)
      // 线上是淡入到 trim 的，离线没有那段斜坡，这里直接给满
      if (v) v.out.gain.value = v.trim
      return v
    },
  }
}
