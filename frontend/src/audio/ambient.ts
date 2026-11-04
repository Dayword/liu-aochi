import type { AmbientId } from '../theme/ThemeProvider'

/**
 * 环境音：全部由 Web Audio 实时合成，没有一个音频文件。
 *
 * 雨声 = 白噪声过高通 + 带通；咖啡馆 = 棕噪声低通 + 慢速音量起伏；
 * 键盘 = 随机短促的滤波脉冲；白噪音 = 白噪声直接低通。
 * 好处：零请求、零版权问题、体积 0；坏处：不可能像录音那样逼真，
 * 所以定位是「背景底噪」，不是「听雨入睡」。
 */
let ctx: AudioContext | null = null
let master: GainNode | null = null
let live: { stop: () => void } | null = null
let armed = false
let wanted: { id: AmbientId; volume: number } | null = null

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

/** 生成噪声缓冲；brown 是白噪声的积分，低频更重，像人群/远处的车流 */
function noiseBuffer(ac: AudioContext, seconds = 4, kind: 'white' | 'brown' = 'white') {
  const len = Math.floor(ac.sampleRate * seconds)
  const buf = ac.createBuffer(1, len, ac.sampleRate)
  const data = buf.getChannelData(0)
  let last = 0
  for (let i = 0; i < len; i++) {
    const w = Math.random() * 2 - 1
    if (kind === 'white') {
      data[i] = w * 0.5
    } else {
      last = (last + 0.02 * w) / 1.02
      data[i] = last * 3.2
    }
  }
  return buf
}

function loopSource(ac: AudioContext, buf: AudioBuffer) {
  const src = ac.createBufferSource()
  src.buffer = buf
  src.loop = true
  src.start()
  return src
}

function build(id: AmbientId, ac: AudioContext): { stop: () => void } | null {
  const nodes: AudioScheduledSourceNode[] = []
  const gains: GainNode[] = []

  if (id === 'rain' || id === 'white' || id === 'cafe') {
    const brown = id === 'cafe'
    const src = loopSource(ac, noiseBuffer(ac, 4, brown ? 'brown' : 'white'))
    const filter = ac.createBiquadFilter()
    if (id === 'rain') {
      filter.type = 'highpass'
      filter.frequency.value = 900
      const band = ac.createBiquadFilter()
      band.type = 'peaking'
      band.frequency.value = 2400
      band.gain.value = 4
      const g = ac.createGain()
      g.gain.value = 0.5
      src.connect(filter).connect(band).connect(g).connect(master!)
      gains.push(g)
    } else if (id === 'cafe') {
      filter.type = 'lowpass'
      filter.frequency.value = 620
      filter.Q.value = 0.4
      const g = ac.createGain()
      g.gain.value = 0.85
      // 慢速起伏：人声忽远忽近的感觉，2 个不同周期叠加更自然
      const lfo1 = ac.createOscillator()
      lfo1.frequency.value = 0.07
      const lfo2 = ac.createOscillator()
      lfo2.frequency.value = 0.13
      const depth = ac.createGain()
      depth.gain.value = 0.18
      lfo1.connect(depth)
      lfo2.connect(depth)
      depth.connect(g.gain)
      lfo1.start()
      lfo2.start()
      nodes.push(lfo1, lfo2)
      src.connect(filter).connect(g).connect(master!)
      gains.push(g)
    } else {
      filter.type = 'lowpass'
      filter.frequency.value = 7200
      const g = ac.createGain()
      g.gain.value = 0.5
      src.connect(filter).connect(g).connect(master!)
      gains.push(g)
    }
    nodes.push(src)
  }

  if (id === 'keys') {
    // 随机间隔的短脉冲：过滤后的噪声 + 快速衰减，听起来像远处的键盘
    const tick = () => {
      if (!ctx || !master) return
      const src = ac.createBufferSource()
      src.buffer = noiseBuffer(ac, 0.02)
      const bp = ac.createBiquadFilter()
      bp.type = 'bandpass'
      bp.frequency.value = 1800 + Math.random() * 1400
      bp.Q.value = 6
      const g = ac.createGain()
      const now = ac.currentTime
      g.gain.setValueAtTime(0.0001, now)
      g.gain.exponentialRampToValueAtTime(0.5 + Math.random() * 0.4, now + 0.004)
      g.gain.exponentialRampToValueAtTime(0.0001, now + 0.06)
      src.connect(bp).connect(g).connect(master)
      src.start(now)
      src.stop(now + 0.08)
    }
    const timer = window.setInterval(() => {
      // 成串敲击：一下之后可能紧跟两下，比匀速更像打字
      tick()
      if (Math.random() > 0.55) window.setTimeout(tick, 70 + Math.random() * 90)
      if (Math.random() > 0.8) window.setTimeout(tick, 220 + Math.random() * 160)
    }, 260 + Math.random() * 120)
    return {
      stop: () => {
        window.clearInterval(timer)
        for (const g of gains) g.disconnect()
      },
    }
  }

  return {
    stop: () => {
      for (const n of nodes) {
        try {
          n.stop()
        } catch {
          /* 已停止 */
        }
        n.disconnect()
      }
      for (const g of gains) g.disconnect()
    },
  }
}

function fade(target: number, ms = 420) {
  if (!ctx || !master) return
  const now = ctx.currentTime
  master.gain.cancelScheduledValues(now)
  master.gain.setValueAtTime(Math.max(0.0001, master.gain.value), now)
  master.gain.linearRampToValueAtTime(Math.max(0.0001, target), now + ms / 1000)
}

export function playAmbient(id: AmbientId, volume: number) {
  wanted = { id, volume }
  if (id === 'none') {
    stopAmbient()
    return
  }
  const ac = ensure()
  if (!ac || !master) return

  // 换声音时先把旧的停掉，否则两个底噪叠在一起会变成噪音
  if (live) {
    live.stop()
    live = null
  }
  live = build(id, ac)

  const go = () => {
    fade(Math.min(1, Math.max(0, volume)))
  }
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
    live.stop()
    live = null
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
export function armAmbient(id: AmbientId, volume: number) {
  if (id === 'none' || armed) return
  armed = true
  wanted = { id, volume }
  const kick = () => {
    window.removeEventListener('pointerdown', kick)
    window.removeEventListener('keydown', kick)
    playAmbient(id, wanted?.volume ?? volume)
  }
  window.addEventListener('pointerdown', kick, { once: true })
  window.addEventListener('keydown', kick, { once: true })
}
