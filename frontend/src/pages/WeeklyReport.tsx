import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { App as AntApp, Button, Spin } from 'antd'
import { ArrowLeftOutlined, DownloadOutlined, ReloadOutlined } from '@ant-design/icons'
import { api } from '../api/client'
import { useSettings } from '../theme/ThemeProvider'

/**
 * 每周学习报告。
 *
 * 数据全部由后端聚合（/api/growth/weekly-report），页面只负责画。
 * 「下载图片」走 SVG → Canvas → PNG：不引 html2canvas（多 200KB，
 * 而且会把整个 DOM 的样式一起搬，主题变量经常丢），卡片本身按
 * 固定 1080×1350 排版，导出的图和屏幕上看到的是同一份数据。
 */
interface DayStat {
  date: string
  label: string
  count: number
}

interface Report {
  start: string
  end: string
  days: DayStat[]
  completed: number
  completed_total: number
  total_lessons: number
  subjects: { subject: string; count: number }[]
  wrong_new: number
  wrong_total: number
  wrong_open: number
  focus_minutes: number
  focus_days: number
  streak: number
  level: number
  title: string
  weekly_exp: number
  total_exp: number
}

const esc = (s: string) =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

export default function WeeklyReport() {
  const navigate = useNavigate()
  const { theme } = useSettings()
  const { message } = AntApp.useApp()
  const [data, setData] = useState<Report | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)

  const load = () => {
    setLoading(true)
    api
      .get<Report>('/api/growth/weekly-report')
      .then(setData)
      .catch((e) => message.error(e instanceof Error ? e.message : '加载失败'))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const maxDay = useMemo(
    () => Math.max(1, ...(data?.days.map((d) => d.count) ?? [0])),
    [data],
  )

  /** 生成一张 1080×1350 的 SVG 海报（深底、主题色点缀），再转 PNG 下载 */
  const download = async () => {
    if (!data) return
    setBusy(true)
    try {
      const v = theme.vars
      const W = 1080
      const H = 1350
      const pad = 72
      const allZero = data.days.every((d) => d.count === 0)
      // 柱状图的基线固定在 1030：卡片第二行到 770，留 60px 才不挤在一起
      const BASE = 1030
      const bars = data.days
        .map((d, i) => {
          const bw = 78
          const gap = 42
          const x = pad + 24 + i * (bw + gap)
          const h = Math.round((d.count / maxDay) * 170)
          const y = BASE - h
          return `<g>
            <rect x="${x}" y="${BASE}" width="${bw}" height="8" rx="4" fill="${v.line}" opacity="0.5"/>
            <rect x="${x}" y="${y}" width="${bw}" height="${Math.max(6, h)}" rx="10" fill="${v.brand}"/>
            <text x="${x + bw / 2}" y="${y - 16}" font-size="26" fill="${v.ink}" text-anchor="middle" font-weight="700">${d.count}</text>
            <text x="${x + bw / 2}" y="${BASE + 46}" font-size="24" fill="${v.ink3}" text-anchor="middle">${esc(d.label)}</text>
          </g>`
        })
        .join('')
      const subjects = data.subjects
        .slice(0, 4)
        .map((s, i) => `${esc(s.subject)} ${s.count} 课${i === Math.min(3, data.subjects.length - 1) ? '' : ' · '}`)
        .join('')
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
        <defs>
          <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="${v.bg}"/>
            <stop offset="100%" stop-color="${v.panel}"/>
          </linearGradient>
        </defs>
        <rect width="${W}" height="${H}" fill="url(#bg)"/>
        <rect x="${pad}" y="${pad}" width="${W - pad * 2}" height="4" rx="2" fill="${v.brand}" opacity="0.5"/>

        <text x="${pad}" y="210" font-size="34" fill="${v.brandDark}" font-weight="700">码境 CodeRealm · 本周学习报告</text>
        <text x="${pad}" y="286" font-size="72" fill="${v.ink}" font-weight="800">Lv.${data.level} ${esc(data.title)}</text>
        <text x="${pad}" y="342" font-size="28" fill="${v.ink3}">${esc(data.start)} ~ ${esc(data.end)} · 累计 ${data.total_exp} 经验</text>

        <g>
          <rect x="${pad}" y="400" width="440" height="190" rx="28" fill="${v.panel}" stroke="${v.line}"/>
          <text x="${pad + 36}" y="470" font-size="26" fill="${v.ink3}">本周完成课程</text>
          <text x="${pad + 36}" y="548" font-size="64" fill="${v.ink}" font-weight="800">${data.completed}</text>
          <text x="${pad + 36 + 70}" y="548" font-size="28" fill="${v.ink3}">/ 累计 ${data.completed_total} 课</text>

          <rect x="${pad + 464}" y="400" width="440" height="190" rx="28" fill="${v.panel}" stroke="${v.line}"/>
          <text x="${pad + 500}" y="470" font-size="26" fill="${v.ink3}">专注时长</text>
          <text x="${pad + 500}" y="548" font-size="64" fill="${v.ink}" font-weight="800">${data.focus_minutes}</text>
          <text x="${pad + 500 + 96}" y="548" font-size="28" fill="${v.ink3}">分钟 · ${data.focus_days} 天</text>
        </g>

        <g>
          <rect x="${pad}" y="620" width="440" height="150" rx="28" fill="${v.panel}" stroke="${v.line}"/>
          <text x="${pad + 36}" y="682" font-size="26" fill="${v.ink3}">连续学习</text>
          <text x="${pad + 36}" y="744" font-size="52" fill="${v.ink}" font-weight="800">${data.streak} 天</text>

          <rect x="${pad + 464}" y="620" width="440" height="150" rx="28" fill="${v.panel}" stroke="${v.line}"/>
          <text x="${pad + 500}" y="682" font-size="26" fill="${v.ink3}">待处理错题</text>
          <text x="${pad + 500}" y="744" font-size="52" fill="${v.ink}" font-weight="800">${data.wrong_open} 道</text>
        </g>

        ${allZero
          ? `<rect x="${pad}" y="846" width="${W - pad * 2}" height="150" rx="28" fill="none" stroke="${v.line}" stroke-dasharray="10 10"/>
             <text x="${W / 2}" y="932" font-size="28" fill="${v.ink3}" text-anchor="middle">本周还没有完成记录</text>`
          : bars}

        <text x="${pad}" y="1150" font-size="26" fill="${v.ink3}">本周学了</text>
        <text x="${pad}" y="1204" font-size="32" fill="${v.ink}" font-weight="600">${esc(subjects || '还没有完成的课程')}</text>

        <text x="${pad}" y="1256" font-size="23" fill="${v.ink3}">学习进度 ${data.completed_total}/${data.total_lessons} 课 · 新增错题 ${data.wrong_new} 道</text>
        <text x="${pad}" y="1296" font-size="21" fill="${v.ink3}">经验只来自完成课程：每完成一课 +10</text>

        <text x="${W - pad}" y="${H - 32}" font-size="21" fill="${v.ink3}" text-anchor="end">${esc(data.end)} · 由码境生成</text>
      </svg>`

      const url = URL.createObjectURL(new Blob([svg], { type: 'image/svg+xml;charset=utf-8' }))
      const img = await new Promise<HTMLImageElement>((resolve, reject) => {
        const im = new Image()
        im.onload = () => resolve(im)
        im.onerror = () => reject(new Error('海报渲染失败'))
        im.src = url
      })
      const canvas = document.createElement('canvas')
      canvas.width = W
      canvas.height = H
      const ctx = canvas.getContext('2d')
      if (!ctx) throw new Error('浏览器不支持 Canvas')
      ctx.drawImage(img, 0, 0, W, H)
      URL.revokeObjectURL(url)
      const blob = await new Promise<Blob>((resolve, reject) =>
        canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('导出失败'))), 'image/png'),
      )
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `码境周报-${data.end}.png`
      a.click()
      window.setTimeout(() => URL.revokeObjectURL(a.href), 4000)
      message.success('已保存到下载目录')
    } catch (e) {
      message.error(e instanceof Error ? e.message : '导出失败')
    } finally {
      setBusy(false)
    }
  }

  if (loading) {
    return (
      <div className="py-20 flex justify-center">
        <Spin />
      </div>
    )
  }

  if (!data) return null

  const pct = Math.round((data.completed_total / data.total_lessons) * 100)

  return (
    <div className="max-w-3xl mx-auto space-y-3">
      <div className="flex items-center gap-2">
        <Button size="small" type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>
          返回
        </Button>
        <h1 className="text-[17px] font-bold text-slate-800">本周学习报告</h1>
        <span className="text-[11px] text-slate-400">
          {data.start} ~ {data.end}
        </span>
        <div className="ml-auto flex gap-1.5">
          <Button size="small" icon={<ReloadOutlined />} onClick={load} />
          <Button size="small" type="primary" icon={<DownloadOutlined />} loading={busy} onClick={() => void download()}>
            存为图片
          </Button>
        </div>
      </div>

      {/* 海报卡：屏幕上看到的排版和导出的图一致 */}
      <div className="game-panel p-4 md:p-6">
        <div className="text-[11px] text-indigo-600 font-medium">码境 CodeRealm · 本周学习报告</div>
        <div className="text-[24px] font-bold text-slate-800 leading-tight mt-1">
          Lv.{data.level} {data.title}
        </div>
        <div className="text-[11.5px] text-slate-400 mt-1">
          累计 {data.total_exp} 经验 · 本周 +{data.weekly_exp}
        </div>

        <div className="grid grid-cols-2 gap-2 mt-3">
          <div className="rounded-xl border border-slate-200 p-3">
            <div className="text-[11px] text-slate-400">本周完成课程</div>
            <div className="text-[22px] font-bold text-slate-800 leading-tight">
              {data.completed}
              <span className="text-[11px] font-normal text-slate-400 ml-1">/ 累计 {data.completed_total}</span>
            </div>
          </div>
          <div className="rounded-xl border border-slate-200 p-3">
            <div className="text-[11px] text-slate-400">专注时长</div>
            <div className="text-[22px] font-bold text-slate-800 leading-tight">
              {data.focus_minutes}
              <span className="text-[11px] font-normal text-slate-400 ml-1">分钟 · {data.focus_days} 天</span>
            </div>
          </div>
          <div className="rounded-xl border border-slate-200 p-3">
            <div className="text-[11px] text-slate-400">连续学习</div>
            <div className="text-[22px] font-bold text-slate-800 leading-tight">{data.streak} 天</div>
          </div>
          <div className="rounded-xl border border-slate-200 p-3">
            <div className="text-[11px] text-slate-400">待处理错题</div>
            <div className="text-[22px] font-bold text-slate-800 leading-tight">
              {data.wrong_open}
              <span className="text-[11px] font-normal text-slate-400 ml-1">本周新增 {data.wrong_new}</span>
            </div>
          </div>
        </div>

        {/* 七天柱状图：纯 div，不引图表库。一条记录都没有时不画七个短横线，
            那看起来像表格坏了，直接给一句话更清楚。 */}
        {data.days.every((d) => d.count === 0) ? (
          <div className="mt-4 h-[92px] rounded-xl border border-dashed border-slate-200 flex items-center justify-center text-[11.5px] text-slate-400">
            本周还没有完成记录，学完一课后这里会显示每天的进度
          </div>
        ) : (
        <div className="mt-4 flex items-end gap-2 h-[132px]">
          {data.days.map((d) => (
            <div key={d.date} className="flex-1 flex flex-col items-center justify-end h-full gap-1">
              <span className="text-[10px] text-slate-500">{d.count || ''}</span>
              <div
                className="w-full rounded-t-md bg-indigo-500/80 transition-[height] duration-500"
                style={{ height: `${Math.max(4, (d.count / maxDay) * 92)}px` }}
                title={`${d.label} 完成 ${d.count} 课`}
              />
              <span className="text-[10px] text-slate-400">{d.label.replace('周', '')}</span>
            </div>
          ))}
        </div>
        )}

        <div className="mt-4 pt-3 border-t border-slate-100 text-[11.5px] text-slate-500 leading-relaxed">
          {data.subjects.length ? (
            <>
              本周学了：
              {data.subjects.map((s, i) => (
                <span key={s.subject}>
                  {s.subject} {s.count} 课
                  {i < data.subjects.length - 1 ? ' · ' : ''}
                </span>
              ))}
            </>
          ) : (
            '本周还没有完成的课程，随便挑一课开始吧。'
          )}
        </div>

        <div className="mt-3">
          <div className="flex justify-between text-[10px] text-slate-400 mb-1">
            <span>主线进度</span>
            <span>
              {data.completed_total}/{data.total_lessons} 课 · {pct}%
            </span>
          </div>
          <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
            <div className="h-full rounded-full bg-indigo-500" style={{ width: `${pct}%` }} />
          </div>
        </div>
      </div>

      <p className="text-[11px] text-slate-400 px-1 leading-relaxed">
        统计口径：完成课程 = 该课动手题与客观题都通过；专注时长来自番茄钟记录；连续学习按「完成课程或专注」计。
        经验只来自完成课程，每课 +10。
      </p>
    </div>
  )
}
