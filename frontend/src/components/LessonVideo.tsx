import { useEffect, useRef, useState } from 'react'
import type { BiliSeries, BiliVideo } from '../types'

/**
 * 课程视频区：直接嵌 B站 官方外链播放器，播真实讲师的分P。
 *
 * 几个必须知道的约束（2026-11-06 实测）：
 * 1. **必须带 `isOutside=true`**：不带的话外站嵌入会提示「该视频无法播放」。
 *    链接由后端拼（见 learn.py 的 _bili），前端不重复拼参数。
 * 2. **点击后才挂 iframe**：B站 播放器一次要拉 64 个请求 / 212 KB，
 *    直接渲染会把课程页首屏拖慢；用户点了才加载，顺带绕开移动端自动播放限制。
 * 3. **画质锁 480P**：未登录只能到 480P，播放器右侧有个删不掉的
 *    「进入哔哩哔哩，观看更高清」浮层 —— 这是 B站 的引流，改不了。
 * 4. **视频会下架**：UP 删稿或改分P 后 iframe 里就是一片黑，跨域又读不到它的
 *    DOM，检测不出来。所以「在 B 站打开」始终可见，加载超过 8 秒再补一句提示。
 *
 * 旧的「自制动图 + TTS 旁白」版本已下线（2026-11-06 用户要求全换真视频）。
 * 需要回滚看 git：`git show 8f6c4b4:frontend/src/components/LessonVideo.tsx`。
 */

const SLOW_MS = 8000

export default function LessonVideo({
  bili,
  series,
  title,
}: {
  bili?: BiliVideo | null
  series?: BiliSeries | null
  title: string
}) {
  const [open, setOpen] = useState(true)
  const [playing, setPlaying] = useState(false)
  const [slow, setSlow] = useState(false)
  const timer = useRef<number | null>(null)

  // 换课要复位：否则上一课的「已播放」状态会让新一课直接挂 iframe
  useEffect(() => {
    setPlaying(false)
    setSlow(false)
    if (timer.current) window.clearTimeout(timer.current)
  }, [bili?.bvid, bili?.page])

  useEffect(() => {
    if (!playing) return undefined
    timer.current = window.setTimeout(() => setSlow(true), SLOW_MS)
    return () => {
      if (timer.current) window.clearTimeout(timer.current)
    }
  }, [playing])

  useEffect(() => () => {
    if (timer.current) window.clearTimeout(timer.current)
  }, [])

  // 没有精确映射的课：给「暂无」+ 该科目的推荐系列，不拿不相干的视频凑数。
  // 连推荐系列都没有（RAG / 后端 / 多模态 / AI 工程这四科）就整块不渲染，
  // 免得每节课都挂一条「暂无」，反而像坏了。
  if (!bili) {
    if (!series) return null
    return (
      <div className="mt-4 overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <div className="flex items-center gap-2 border-b border-slate-100 bg-slate-50/70 px-4 py-2">
          <span className="shrink-0 whitespace-nowrap text-sm font-medium text-slate-600">
            🎬 视频讲解
          </span>
          <span className="min-w-0 truncate text-[11px] text-slate-400">
            本节暂无逐点对应的视频
          </span>
        </div>
        <div className="px-4 py-4">
          <div className="text-[13px] leading-relaxed text-slate-600">
            这一节是课程自编的工程内容，B 站 上没有讲同一件事的视频，
            就不拿别的视频凑数了 —— 讲错的知识点比没有更坑。
          </div>
          <a
            href={series.url}
            target="_blank"
            rel="noreferrer noopener"
            className="mt-3 flex items-center gap-2 rounded-xl border border-indigo-200 bg-indigo-50/60 px-3 py-2.5 transition hover:border-indigo-300"
          >
            <span className="text-base">📺</span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-[12.5px] font-medium text-indigo-700">
                {series.series}
              </span>
              <span className="block truncate text-[11px] text-slate-500">
                {series.up} · 整系列目录
              </span>
            </span>
            <span className="shrink-0 text-[11px] text-indigo-600">去 B 站 ↗</span>
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="mt-4 overflow-hidden rounded-2xl border border-indigo-200 bg-white">
      <div className="flex items-center gap-2 border-b border-indigo-100 bg-indigo-50/60 px-4 py-2">
        <span className="shrink-0 whitespace-nowrap text-sm font-medium text-indigo-700">
          🎬 视频讲解
        </span>
        <span className="min-w-0 truncate text-[11px] text-slate-500">
          {bili.up} · {bili.series} · 第 {bili.page} 讲
        </span>
        <button
          onClick={() => setOpen((o) => !o)}
          className="ml-auto shrink-0 whitespace-nowrap rounded px-2 py-0.5 text-[11px] text-indigo-600 hover:bg-indigo-100"
        >
          {open ? '收起' : '展开'}
        </button>
      </div>

      {open && (
        <>
          {playing ? (
            <div className="relative aspect-[16/10] w-full bg-black">
              <iframe
                src={bili.embed}
                title={`${title} · 视频讲解`}
                data-bili-frame="1"
                className="absolute inset-0 h-full w-full"
                style={{ border: 0 }}
                scrolling="no"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                allowFullScreen
                referrerPolicy="no-referrer-when-downgrade"
              />
            </div>
          ) : (
            <button
              onClick={() => setPlaying(true)}
              data-bili-play="1"
              className="relative block aspect-[16/10] w-full overflow-hidden bg-slate-900 text-left"
            >
              <span className="absolute inset-0 flex flex-col items-center justify-center px-8">
                <span className="flex h-16 w-16 items-center justify-center rounded-full bg-white/95 text-indigo-600 shadow-lg transition-transform duration-200 hover:scale-105">
                  <span className="ml-1 text-2xl">▶</span>
                </span>
                <span className="mt-4 line-clamp-2 max-w-[560px] text-center text-[14px] font-medium leading-relaxed text-white">
                  {bili.part}
                </span>
                <span className="mt-1.5 text-center text-[11.5px] text-white/60">
                  {bili.up} · 点击播放（画质 480P，高清请到 B 站）
                </span>
              </span>
            </button>
          )}

          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 px-4 py-2.5">
            <span className="min-w-0 flex-1 truncate text-[11.5px] text-slate-500">
              第 {bili.page} 讲 · {bili.part}
            </span>
            {slow && (
              <span className="shrink-0 text-[11px] text-amber-600">
                加载慢？网络到 B 站 可能不通
              </span>
            )}
            <a
              href={bili.url}
              target="_blank"
              rel="noreferrer noopener"
              className="shrink-0 whitespace-nowrap rounded px-2 py-0.5 text-[11px] text-indigo-600 hover:bg-indigo-50"
            >
              在 B 站 打开 ↗
            </a>
          </div>
        </>
      )}
    </div>
  )
}
