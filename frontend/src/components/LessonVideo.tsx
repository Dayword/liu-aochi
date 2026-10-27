import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { LearnVideo, LearnVideoScene } from '../types'

/**
 * 课程讲解视频播放器。
 *
 * 设计要点（2026-10-25 重做，修「讲一半就跳下一句」）：
 * 1. **旁白拆成短句逐条念**。浏览器（尤其 Chrome）对单条长语音会在约 15 秒处
 *    截断并触发 onend，播放器会误以为「念完了」而切镜。实测 528 个分镜里
 *    158 个（29.9%）旁白超过 15 秒，100/113 课中招，所以必须按句拆。
 * 2. **念完之前绝不切镜**。旧版把 onend 当成「可以提前切」的信号，一旦浏览器
 *    提前触发 onend 就直接跳镜 —— 这就是听感上「话没说完就换下一句」。
 *    现在改为：语音没结束就继续等，宁可让这一镜变长，也不切断。
 * 3. 语音全念完且已达到该镜的视觉最短时长，才进入下一镜；没有语音包时
 *    完全按视觉时长走，不会出现长时间静默。
 * 4. 进度条以「实时时长数组」为准：每镜念完后用真实耗时回填，所以总时长会
 *    随着播放略微变化，但读数始终是真实的。
 */

/** 优先挑中文女声；名字里带这些关键字的先试 */
const VOICE_HINTS = ['xiaoxiao', 'xiaoyi', 'huihui', 'yaoyao', 'female', 'natural']

/** 单条语音的最大字数：约 6 秒，远低于浏览器的截断阈值 */
const CHUNK_MAX = 28

function pickChineseVoice(): SpeechSynthesisVoice | null {
  if (typeof window === 'undefined' || !window.speechSynthesis) return null
  const all = window.speechSynthesis.getVoices() || []
  const zh = all.filter((v) => /^zh/i.test(v.lang))
  if (!zh.length) return null
  for (const hint of VOICE_HINTS) {
    const hit = zh.find((v) => v.name.toLowerCase().includes(hint))
    if (hit) return hit
  }
  return zh[0]
}

function fmt(ms: number) {
  const s = Math.max(0, Math.floor(ms / 1000))
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

/**
 * 单片超长时的断点选择：尽量别切在英文单词或数字中间。
 * 在 0.6~1.0 倍上限之间找最近的空格/标点，找不到就退到字母数字边界。
 */
function cutPoint(s: string): number {
  const lo = Math.max(1, Math.floor(CHUNK_MAX * 0.6))
  for (let i = CHUNK_MAX; i >= lo; i -= 1) {
    if (/[\s，、,：:；;]/.test(s[i - 1])) return i
  }
  let i = CHUNK_MAX
  while (i > lo && /[A-Za-z0-9_]/.test(s[i - 1]) && /[A-Za-z0-9_]/.test(s[i])) i -= 1
  return i > lo ? i : lo
}

/**
 * 把旁白切成短句。
 *
 * 不能只在句号处拆——课程文案里大量内容靠逗号/冒号推进，按句号拆会切出
 * 一堆超长片段，再被硬切就变成「两种完全 | 不同的东西」这种断法，听感很碎。
 * 所以：先按所有标点切成小片段（保留标点），再**贪心拼**到不超过上限；
 * 只有单片本身超长（比如没有标点的代码行）才按 cutPoint 切。
 */
function splitChunks(text: string): string[] {
  const raw = (text || '').replace(/\s+/g, ' ').trim()
  if (!raw) return []
  const pieces = raw.match(/[^，。！？；：、,.!?;:]+[，。！？；：、,.!?;:]?/g) ?? [raw]
  const out: string[] = []
  let buf = ''
  const flush = () => {
    if (buf) {
      out.push(buf)
      buf = ''
    }
  }
  for (const piece of pieces) {
    let p = piece.trim()
    if (!p) continue
    while (p.length > CHUNK_MAX) {
      flush()
      const cut = cutPoint(p)
      out.push(p.slice(0, cut).trim())
      p = p.slice(cut).trim()
    }
    if (!p) continue
    if (buf.length + p.length > CHUNK_MAX) flush()
    buf += p
    // 句末标点处断句，读起来更自然
    if (/[。！？；!?;]$/.test(p)) flush()
  }
  flush()
  return out.length ? out : [raw]
}

/** 估算配音时长：中文约 4.5 字/秒，另加段间停顿 */
function estimateMs(text: string): number {
  return splitChunks(text).reduce((acc, c) => acc + c.length * 220 + 180, 0)
}

/** 该镜的视觉最短时长：内容没演完也不能切 */
function visualMs(s: LearnVideoScene): number {
  return Math.max(1200, s.dur || 3000)
}

/** 初始时长：视觉时长与配音估算取大者（配音念完会回填真实值） */
function initialMs(s: LearnVideoScene): number {
  return Math.max(visualMs(s), estimateMs(s.say || ''))
}

function SceneTitle({ s }: { s: LearnVideoScene }) {
  return (
    <div className="absolute inset-0 flex flex-col justify-center px-10">
      <div className="text-[11px] tracking-wider text-slate-400">{s.eyebrow}</div>
      <div className="mt-2 text-2xl font-bold text-indigo-800">{s.title}</div>
      <div className="mt-2 text-sm text-slate-500">{s.sub}</div>
      <div className="mt-5 h-[3px] w-14 rounded bg-indigo-500" />
    </div>
  )
}

function SceneLines({ s, t, budget }: { s: LearnVideoScene; t: number; budget: number }) {
  const items = s.items || []
  const per = budget / Math.max(1, items.length)
  return (
    <div className="absolute inset-0 px-9 py-7">
      <div className="text-xs font-medium text-slate-500">{s.heading}</div>
      <div className="mt-4 space-y-3">
        {items.map((it, i) => {
          const shown = t >= i * per * 0.85
          return (
            <div
              key={i}
              className="flex gap-3 transition-all duration-500"
              style={{ opacity: shown ? 1 : 0, transform: shown ? 'none' : 'translateY(8px)' }}
            >
              <span className="mt-1 h-5 w-5 shrink-0 rounded-full bg-indigo-100 text-center text-[11px] font-medium leading-5 text-indigo-700">
                {i + 1}
              </span>
              <div className="text-[13.5px] leading-relaxed text-slate-700">{it}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function SceneCode({ s, t, budget }: { s: LearnVideoScene; t: number; budget: number }) {
  const lines = s.lines || []
  const steps = s.steps || []

  // 当前高亮到第几步：按时间在镜头内均分
  const shownSteps = Math.max(0, Math.min(steps.length, Math.floor((t / budget) * steps.length) + 1))
  const cur = steps[shownSteps - 1]
  const prev = steps[shownSteps - 2]

  // 没有 trace 到（示例跑不通）就退化成按行推进
  const fallbackLine = Math.floor((t / budget) * lines.length)
  const activeLine = steps.length ? cur?.line ?? -1 : fallbackLine

  const vars = cur?.vars || {}
  const prevVars = prev?.vars || {}

  const outSoFar = useMemo(() => {
    if (!steps.length) return ''
    return steps.slice(0, shownSteps).map((x) => x.out || '').join('')
  }, [steps, shownSteps])

  return (
    <div className="absolute inset-0 flex gap-4 px-4 py-4">
      <div className="min-w-0 flex-[1.45]">
        <div className="mb-2 text-[11px] text-slate-400">{s.caption || '示例代码'}</div>
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white py-2">
          {lines.map((ln, i) => (
            <div
              key={i}
              className={`whitespace-pre px-2 font-mono text-[12px] leading-[1.85] transition-colors ${
                i === activeLine
                  ? 'border-l-[3px] border-indigo-500 bg-indigo-50 text-indigo-900'
                  : 'border-l-[3px] border-transparent text-slate-600'
              }`}
            >
              <span className="mr-2 inline-block w-4 select-none text-right text-[10px] text-slate-300">
                {i + 1}
              </span>
              {ln.replace(/\t/g, '    ')}
            </div>
          ))}
        </div>
      </div>

      <div className="flex min-w-0 flex-1 flex-col gap-3">
        <div>
          <div className="mb-1.5 text-[11px] text-slate-400">变量区</div>
          <div className="space-y-1">
            {Object.keys(vars).length === 0 && (
              <div className="text-[11px] text-slate-300">（还没赋值）</div>
            )}
            {Object.entries(vars).map(([k, v]) => {
              const changed = prevVars[k] !== undefined && prevVars[k] !== v
              return (
                <div
                  key={k}
                  className={`flex items-center justify-between gap-2 rounded-md border px-2 py-1 text-[11.5px] transition-colors ${
                    changed ? 'border-indigo-300 bg-indigo-50' : 'border-slate-200 bg-white'
                  }`}
                >
                  <span className="font-mono text-sky-700">{k}</span>
                  <span className="truncate font-mono font-medium text-indigo-900">{v}</span>
                </div>
              )
            })}
          </div>
        </div>
        <div>
          <div className="mb-1.5 text-[11px] text-slate-400">输出</div>
          <pre className="min-h-[56px] whitespace-pre-wrap rounded-lg border border-slate-200 bg-white px-2 py-1.5 font-mono text-[11.5px] leading-relaxed text-emerald-700">
            {outSoFar}
          </pre>
        </div>
      </div>
    </div>
  )
}

function SceneCommands({ s, t, budget }: { s: LearnVideoScene; t: number; budget: number }) {
  const lines = s.lines || []
  const shown = Math.max(1, Math.min(lines.length, Math.floor((t / budget) * lines.length) + 1))
  const done = shown >= lines.length
  return (
    <div className="absolute inset-0 px-6 py-4">
      <div className="mb-2 text-[11px] text-slate-400">{s.caption}</div>
      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white py-2">
        {lines.map((ln, i) => {
          const isOut = ln.trimStart().startsWith('→')
          const visible = i < shown
          return (
            <div
              key={i}
              className={`whitespace-pre px-3 font-mono text-[12px] leading-[1.8] transition-opacity duration-300 ${
                isOut ? 'pl-6 text-emerald-700' : 'text-slate-700'
              }`}
              style={{ opacity: visible ? 1 : 0.08 }}
            >
              {ln}
            </div>
          )
        })}
      </div>
      {s.output && (
        <div className="mt-3 transition-opacity duration-500" style={{ opacity: done ? 1 : 0 }}>
          <div className="mb-1 text-[11px] text-slate-400">运行结果</div>
          <pre className="max-h-[86px] overflow-auto whitespace-pre-wrap rounded-lg border border-emerald-200 bg-emerald-50 px-2.5 py-1.5 font-mono text-[11.5px] leading-relaxed text-emerald-800">
            {s.output}
          </pre>
        </div>
      )}
    </div>
  )
}

function ScenePitfalls({ s, t, budget }: { s: LearnVideoScene; t: number; budget: number }) {
  const items = s.items || []
  const per = budget / Math.max(1, items.length)
  return (
    <div className="absolute inset-0 px-8 py-6">
      <div className="text-xs font-medium text-slate-500">{s.heading}</div>
      <div className="mt-3 space-y-2">
        {items.map((it, i) => {
          const shown = t >= i * per * 0.8
          return (
            <div
              key={i}
              className="flex gap-2.5 text-[12.5px] leading-relaxed text-slate-700 transition-all duration-400"
              style={{ opacity: shown ? 1 : 0, transform: shown ? 'none' : 'translateX(-6px)' }}
            >
              <span className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-sm border border-rose-300 bg-rose-100" />
              <span>{it}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function SceneTask({ s }: { s: LearnVideoScene }) {
  return (
    <div className="absolute inset-0 flex flex-col justify-center px-9">
      <div className="text-[11px] tracking-wider text-slate-400">{s.heading}</div>
      <div className="mt-2 text-lg font-bold text-indigo-800">{s.text}</div>
      <div className="mt-3 flex flex-wrap gap-2">
        {(s.bullets || []).map((b, i) => (
          <span
            key={i}
            className="rounded-md border border-slate-200 bg-white px-2 py-1 font-mono text-[11px] text-sky-700"
          >
            {b}
          </span>
        ))}
      </div>
    </div>
  )
}

export default function LessonVideo({ video, code }: { video: LearnVideo; code: string }) {
  const scenes = video.scenes

  const [open, setOpen] = useState(true)
  const [playing, setPlaying] = useState(false)
  const [sceneIdx, setSceneIdx] = useState(0)
  const [t, setT] = useState(0)
  const [voiceOn, setVoiceOn] = useState(true)
  const [speed, setSpeed] = useState(1)
  const [voiceName, setVoiceName] = useState('')
  const [speaking, setSpeaking] = useState(false)
  const [voiceError, setVoiceError] = useState('')
  // 是否已经用一次真实手势「解锁」过语音。iOS Safari 要求第一次 speak()
  // 必须发生在用户点击里，之后由定时器驱动的后续句子才能念出来。
  const [unlocked, setUnlocked] = useState(false)

  const tRef = useRef(0)
  const sceneRef = useRef(0)
  const voiceRef = useRef<SpeechSynthesisVoice | null>(null)
  // cancel() 也会给上一句触发 onend，用递增 token 把「自己取消的」过滤掉
  const speakToken = useRef(0)
  // 该镜旁白是否还在念：念着就不许切镜
  const speakingRef = useRef(false)
  // 当前念到第几段，暂停后从这里接着念
  const chunkRef = useRef(0)
  // 语音比预计还久时已经多等了多久（浏览器吞掉 onend 时的兜底）
  const overrunRef = useRef(0)
  // 哪些镜的旁白已经念完：暂停后继续时不要重念最后一句
  const spokenDone = useRef<Set<number>>(new Set())

  // 每镜的实时时长：初始按估算，念完后用真实耗时回填
  const initial = useMemo(() => scenes.map(initialMs), [scenes])
  const durRef = useRef<number[]>(initial)
  useEffect(() => {
    durRef.current = initial
  }, [initial])

  // 语音列表是异步加载的，某些浏览器首次 getVoices() 返回空
  useEffect(() => {
    if (typeof window === 'undefined' || !window.speechSynthesis) return
    const sync = () => {
      const v = pickChineseVoice()
      voiceRef.current = v
      setVoiceName(v ? v.name : '')
    }
    sync()
    window.speechSynthesis.addEventListener('voiceschanged', sync)
    return () => window.speechSynthesis.removeEventListener('voiceschanged', sync)
  }, [])

  // 手机浏览器切到后台会把语音挂起，回来要手动 resume
  useEffect(() => {
    const onVis = () => {
      if (document.visibilityState === 'visible' && playing) {
        window.speechSynthesis?.resume()
      }
    }
    document.addEventListener('visibilitychange', onVis)
    return () => document.removeEventListener('visibilitychange', onVis)
  }, [playing])

  /**
   * ⚠️ 关键修复（2026-10-27，手机端「开不了声音」）：
   * 旧实现要求 `voiceName` 有值才允许念，而**移动端 getVoices() 经常返回空数组**
   * （Android Chrome 首次必然为空，iOS 要等 voiceschanged），于是 speechOk 恒为 false，
   * 按钮永远显示「配音关」，点也点不亮。
   * 实际上没有 voice 对象也能 speak —— 浏览器会用默认语音，只要 lang 给对。
   * 所以这里只判断 API 是否存在，音色只用来优先挑中文。
   */
  const speechOk = typeof window !== 'undefined' && !!window.speechSynthesis
  const canSpeak = speechOk && voiceOn

  /** 主动停止：先推进 token，让被 cancel 的旧句子稍后到达的 onend 失效 */
  const stopSpeech = useCallback(() => {
    speakToken.current += 1
    speakingRef.current = false
    setSpeaking(false)
    window.speechSynthesis?.cancel()
  }, [])

  /**
   * 念某一镜的旁白：**拆成短句逐条念**，全部念完才算结束。
   * from 用于暂停后接着念。
   */
  const speakScene = useCallback(
    (i: number, from = 0) => {
      const chunks = splitChunks(scenes[i]?.say || '')
      if (!canSpeak || !chunks.length) {
        speakingRef.current = false
        setSpeaking(false)
        return
      }
      const my = speakToken.current + 1
      speakToken.current = my
      const synth = window.speechSynthesis
      // iOS 上 cancel() 紧跟着 speak() 会把新句子一起丢掉，所以只有在真的在念时才 cancel，
      // 且 cancel 之后等一帧再开口。
      if (synth.speaking || synth.pending) synth.cancel()
      speakingRef.current = true
      chunkRef.current = from
      setSpeaking(true)

      const finish = () => {
        speakingRef.current = false
        setSpeaking(false)
        spokenDone.current.add(i)
        // 用真实耗时回填这一镜时长，但绝不低于视觉最短时长
        durRef.current[i] = Math.max(visualMs(scenes[i]), tRef.current)
      }

      const speakAt = (k: number) => {
        if (my !== speakToken.current) return
        if (k >= chunks.length) {
          finish()
          return
        }
        chunkRef.current = k
        const u = new SpeechSynthesisUtterance(chunks[k])
        u.lang = 'zh-CN'
        if (voiceRef.current) u.voice = voiceRef.current
        u.rate = 1.02 * speed
        u.pitch = 1.05
        u.onend = () => speakAt(k + 1)
        u.onerror = (ev) => {
          // not-allowed / audio-busy 在移动端很常见：多半是还没拿到手势授权，
          // 或者系统音频被别的 App 占着。给出可操作的提示，别静默失败。
          const err = (ev as SpeechSynthesisErrorEvent)?.error || ''
          if (err === 'not-allowed' || err === 'audio-busy') {
            setVoiceError('浏览器拦住了语音，点一下「🔊 声音」按钮再试')
          } else if (err && err !== 'interrupted' && err !== 'canceled') {
            setVoiceError(`语音出错：${err}`)
          }
          if (my === speakToken.current) finish()
        }
        synth.resume() // 有的浏览器会自己挂起
        synth.speak(u)
      }

      // 等一帧：给 cancel 一个落地的机会，iOS 才不会吞掉第一句
      window.setTimeout(() => speakAt(Math.min(from, chunks.length - 1)), 60)
    },
    [scenes, speed, canSpeak],
  )

  /**
   * 解锁语音：必须在用户点击里同步调一次 speak()，否则 iOS / Android Chrome
   * 会拒掉后续所有由定时器触发的语音 —— 表现就是「点了播放没声音」。
   * 这里念一句几乎无声的「。」，唯一作用是拿到音频焦点。
   */
  const unlockAudio = useCallback(() => {
    if (speechOk !== true) return
    try {
      const synth = window.speechSynthesis
      synth.resume()
      const u = new SpeechSynthesisUtterance('。')
      u.lang = 'zh-CN'
      u.volume = 0.01
      u.rate = 2
      synth.speak(u)
      setUnlocked(true)
      setVoiceError('')
    } catch {
      setVoiceError('这个浏览器不支持语音朗读，只能看字幕')
    }
  }, [speechOk])

  // 换课就重置
  useEffect(() => {
    speakToken.current += 1
    speakingRef.current = false
    setSpeaking(false)
    window.speechSynthesis?.cancel()
    setPlaying(false)
    setSceneIdx(0)
    setT(0)
    tRef.current = 0
    sceneRef.current = 0
    chunkRef.current = 0
    overrunRef.current = 0
    spokenDone.current.clear()
  }, [code])

  useEffect(() => () => stopSpeech(), [stopSpeech])

  // 时间轴：100ms 一跳
  useEffect(() => {
    if (!playing) return
    const id = window.setInterval(() => {
      const i = sceneRef.current
      const durs = durRef.current

      // 旁白还没念完但已到预计时长 → 把这一镜拉长，绝不切断
      if (speakingRef.current && tRef.current >= durs[i]) {
        if (overrunRef.current > 30000) {
          // 兜底：浏览器吞了 onend，不能永远卡住
          stopSpeech()
        } else {
          overrunRef.current += 100
          durs[i] += 100 * speed
        }
      }

      tRef.current += 100 * speed

      const target = canSpeak ? durs[i] : visualMs(scenes[i])
      if (!speakingRef.current && tRef.current >= target) {
        if (sceneRef.current + 1 < scenes.length) {
          sceneRef.current += 1
          tRef.current = 0
          overrunRef.current = 0
          setSceneIdx(sceneRef.current)
          speakScene(sceneRef.current)
        } else {
          tRef.current = target
          setPlaying(false)
          stopSpeech()
        }
      }
      setT(tRef.current)
    }, 100)
    return () => window.clearInterval(id)
  }, [playing, speed, scenes, canSpeak, speakScene, stopSpeech])

  /** 该镜当前时长：有配音按回填/估算，没配音只按视觉时长 */
  const durAt = (i: number) => (canSpeak ? durRef.current[i] ?? initial[i] : visualMs(scenes[i]))

  const total = useMemo(
    () => scenes.reduce((acc, _, i) => acc + durAt(i), 0) || 1,
    // durRef 会在播放中被回填/拉长，靠 t 的变化触发重算
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [scenes, canSpeak, t, initial],
  )

  const toggle = () => {
    if (!playing) {
      // iOS：第一次必须在点击里开口，不然之后定时器念的都会被拦
      if (!unlocked) unlockAudio()
      // 已经播到结尾：点击「重播」要从头开始，否则会卡在最后一帧
      const atEnd = sceneRef.current === scenes.length - 1 && tRef.current >= durAt(sceneRef.current) - 1
      if (atEnd) {
        sceneRef.current = 0
        tRef.current = 0
        chunkRef.current = 0
        overrunRef.current = 0
        spokenDone.current.clear()
        setSceneIdx(0)
        setT(0)
      }
      setPlaying(true)
      if (!spokenDone.current.has(sceneRef.current)) {
        speakScene(sceneRef.current, chunkRef.current)
      }
    } else {
      setPlaying(false)
      stopSpeech()
    }
  }

  const seek = (ratio: number) => {
    const durs = scenes.map((_, i) => durAt(i))
    const sum = durs.reduce((a, b) => a + b, 0) || 1
    const target = Math.max(0, Math.min(1, ratio)) * sum
    let acc = 0
    let idx = 0
    for (let i = 0; i < durs.length; i += 1) {
      if (target < acc + durs[i] || i === durs.length - 1) {
        idx = i
        break
      }
      acc += durs[i]
    }
    sceneRef.current = idx
    tRef.current = target - acc
    chunkRef.current = 0
    overrunRef.current = 0
    spokenDone.current.clear()
    setSceneIdx(idx)
    setT(tRef.current)
    if (playing) speakScene(idx, 0)
  }

  if (!scenes.length) return null

  // 手机端给一条「没声音怎么排查」的提示（桌面端不需要，占地方）
  const isTouch =
    typeof navigator !== 'undefined' && /iPhone|iPad|iPod|Android/i.test(navigator.userAgent)

  const elapsed = scenes.slice(0, sceneIdx).reduce((acc, _, i) => acc + durAt(i), 0) + t
  const scene = scenes[sceneIdx]
  const budget = Math.max(600, durAt(sceneIdx))
  const pct = Math.min(100, (elapsed / total) * 100)

  return (
    <div className="mt-4 overflow-hidden rounded-2xl border border-indigo-200 bg-white">
      <div className="flex items-center gap-2 border-b border-indigo-100 bg-indigo-50/60 px-4 py-2">
        <span className="shrink-0 whitespace-nowrap text-sm font-medium text-indigo-700">
          🎬 讲解视频
        </span>
        <span className="min-w-0 truncate text-[11px] text-slate-500">
          {fmt(total)} · {scenes.length} 个画面 · 内容取自本课原文
        </span>
        {speaking && (
          <span
            className="flex shrink-0 items-center gap-1 whitespace-nowrap text-[11px] text-emerald-600"
            title="正在朗读本镜旁白"
          >
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
            朗读中
          </span>
        )}
        <button
          onClick={() => setOpen((o) => !o)}
          className="ml-auto shrink-0 whitespace-nowrap rounded px-2 py-0.5 text-[11px] text-indigo-600 hover:bg-indigo-100"
        >
          {open ? '收起' : '展开'}
        </button>
      </div>

      {open && (
        <>
          <div className="relative h-[330px] overflow-hidden bg-[#f8f9fd]">
            {scenes.map((s, i) => (
              <div
                key={i}
                className="absolute inset-0 transition-opacity duration-500"
                style={{ opacity: i === sceneIdx ? 1 : 0, pointerEvents: 'none' }}
              >
                {s.kind === 'title' && <SceneTitle s={s} />}
                {s.kind === 'lines' && <SceneLines s={s} t={t} budget={budget} />}
                {s.kind === 'code' && <SceneCode s={s} t={t} budget={budget} />}
                {s.kind === 'commands' && <SceneCommands s={s} t={t} budget={budget} />}
                {s.kind === 'pitfalls' && <ScenePitfalls s={s} t={t} budget={budget} />}
                {s.kind === 'task' && <SceneTask s={s} />}
              </div>
            ))}

            {/* 字幕条 */}
            <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-[#f8f9fd] via-[#f8f9fd]/95 to-transparent px-5 pb-2.5 pt-8">
              <div className="text-[12.5px] leading-relaxed text-slate-700">{scene.say || ''}</div>
            </div>

            {!playing && (
              <button
                onClick={toggle}
                className="absolute inset-0 flex items-center justify-center bg-slate-900/5 backdrop-blur-[1px]"
              >
                <span className="flex h-14 w-14 items-center justify-center rounded-full bg-indigo-600 text-white shadow-lg transition-transform hover:scale-105">
                  <span className="ml-1 text-xl">▶</span>
                </span>
              </button>
            )}
          </div>

          <div className="flex items-center gap-3 px-4 py-2.5">
            <button
              onClick={toggle}
              className="rounded-lg border border-indigo-300 px-3 py-1 text-xs text-indigo-700 hover:bg-indigo-50"
            >
              {playing ? '暂停' : elapsed >= total ? '重播' : '播放'}
            </button>
            <button
              onClick={() => seek(0)}
              className="rounded-lg border border-slate-200 px-2 py-1 text-xs text-slate-500 hover:bg-slate-50"
              title="回到开头"
            >
              ↺
            </button>
            <div
              onClick={(e) => {
                const r = e.currentTarget.getBoundingClientRect()
                seek((e.clientX - r.left) / r.width)
              }}
              className="group relative h-1 flex-1 cursor-pointer rounded bg-slate-200"
            >
              <div
                className="absolute inset-y-0 left-0 rounded bg-indigo-500"
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="text-[11px] tabular-nums text-slate-400">
              {fmt(elapsed)} / {fmt(total)}
            </span>
            <button
              onClick={() => {
                const next = !voiceOn
                setVoiceOn(next)
                if (!next) {
                  stopSpeech()
                } else {
                  // 打开声音也要算一次手势：先解锁，再接着念
                  unlockAudio()
                  if (playing && !spokenDone.current.has(sceneRef.current)) {
                    speakScene(sceneRef.current, chunkRef.current)
                  }
                }
              }}
              disabled={!speechOk}
              className={`rounded-lg border px-2 py-1 text-[11px] ${
                voiceOn && speechOk
                  ? 'border-emerald-300 bg-emerald-50 text-emerald-700'
                  : 'border-slate-200 text-slate-400'
              }`}
              title={
                speechOk
                  ? voiceName
                    ? `当前音色：${voiceName}`
                    : '系统未提供中文音色，仍会用默认语音朗读'
                  : '这个浏览器不支持语音朗读，只能看字幕'
              }
            >
              {!speechOk ? '🔇 无语音' : voiceOn ? '🔊 声音开' : '🔇 开声音'}
            </button>
            <button
              onClick={() => setSpeed((s) => (s === 1 ? 1.25 : s === 1.25 ? 1.5 : 1))}
              className="rounded-lg border border-slate-200 px-2 py-1 text-[11px] text-slate-500 hover:bg-slate-50"
            >
              {speed}x
            </button>
          </div>

          {(voiceError || isTouch) && (
            <div className="px-4 pb-1 text-[10.5px] leading-relaxed text-amber-600">
              {voiceError ||
                '手机听不到声音？先点一下「🔊 声音开」，iPhone 还要确认侧边静音开关没有打开'}
            </div>
          )}

          <div className="flex items-center gap-1.5 px-4 pb-3">
            {scenes.map((_, i) => {
              const before = scenes.slice(0, i).reduce((acc, __, j) => acc + durAt(j), 0)
              return (
                <button
                  key={i}
                  onClick={() => seek(before / total)}
                  className={`h-1.5 flex-1 rounded transition-colors ${
                    i === sceneIdx ? 'bg-indigo-500' : i < sceneIdx ? 'bg-indigo-200' : 'bg-slate-200'
                  }`}
                  title={`第 ${i + 1} 个画面`}
                />
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
