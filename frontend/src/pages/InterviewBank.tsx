import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Input, Spin } from 'antd'
import { DownOutlined } from '@ant-design/icons'
import { api } from '../api/client'
import type { QBankItem, QBankSubject } from '../types'

/**
 * 面试考题：按「科目 → 模块（课程阶段）→ 课程 → 题目」组织，和引导式学习同一套结构。
 *
 * 为什么不是一张大列表：学生查题时脑子里是「我现在学 MySQL 索引，这一块会怎么问」，
 * 按课程阶段分组正好对上他正在学的位置；看完题还能顺手点进那门课补。
 *
 * 答案默认折叠：先自己想一遍再看，比直接读答案有用。同一时刻只展开一道，
 * 手机上不会一口气拉出几百行。
 */

/** 极简 Markdown：只处理 `行内代码`，答案里到处是 `dict`、`O(1)` 这种，不排一下很难读 */
function Rich({ text }: { text: string }) {
  const parts = text.split(/(`[^`]+`)/g)
  return (
    <>
      {parts.map((p, i) =>
        p.length > 1 && p.startsWith('`') && p.endsWith('`') ? (
          <code key={i} className="bg-indigo-50 text-indigo-700 px-1 py-[1px] rounded text-[0.92em]">
            {p.slice(1, -1)}
          </code>
        ) : (
          <span key={i}>{p}</span>
        ),
      )}
    </>
  )
}

const HOT: Record<number, { t: string; c: string; dot: string }> = {
  3: { t: '必问', c: 'bg-rose-50 text-rose-600', dot: '#ef4444' },
  2: { t: '常问', c: 'bg-amber-50 text-amber-600', dot: '#f59e0b' },
  1: { t: '纵深', c: 'bg-slate-100 text-slate-500', dot: '#cbd5e1' },
}

const STATUS: Record<string, { t: string; c: string }> = {
  completed: { t: '已学完', c: 'text-emerald-600 bg-emerald-50' },
  unlocked: { t: '可学', c: 'text-indigo-600 bg-indigo-50' },
  locked: { t: '未解锁', c: 'text-slate-400 bg-slate-100' },
}

export default function InterviewBank() {
  const navigate = useNavigate()
  const [data, setData] = useState<QBankSubject[]>([])
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState('')
  const [active, setActive] = useState(0)
  const [openModules, setOpenModules] = useState<Set<string>>(new Set())
  /** 当前展开的那一道题，key = 模块名|课程code|序号；同时只开一道 */
  const [openKey, setOpenKey] = useState('')
  const [q, setQ] = useState('')

  useEffect(() => {
    let alive = true
    api
      .get<QBankSubject[]>('/api/learn/interview-bank')
      .then((d) => {
        if (!alive) return
        setData(d)
        const first = d[0]
        if (first?.modules.length) setOpenModules(new Set([first.modules[0].name]))
      })
      .catch((e) => {
        if (alive) setErr((e as Error).message || '加载失败')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [])

  const subject = data[active]

  // 切科目：展开第一个模块，收起已打开的答案
  useEffect(() => {
    if (!subject) return
    setOpenModules(new Set(subject.modules.length ? [subject.modules[0].name] : []))
    setOpenKey('')
    setQ('')
  }, [subject])

  const hit = (it: QBankItem, t: string) =>
    it.q.toLowerCase().includes(t) ||
    it.kp.toLowerCase().includes(t) ||
    it.answer.toLowerCase().includes(t)

  const modules = useMemo(() => {
    if (!subject) return []
    const t = q.trim().toLowerCase()
    if (!t) return subject.modules
    return subject.modules
      .map((m) => ({
        ...m,
        lessons: m.lessons
          .map((l) => ({ ...l, items: l.items.filter((it) => hit(it, t)) }))
          .filter((l) => l.items.length),
        items: m.items.filter((it) => hit(it, t)),
      }))
      .filter((m) => m.lessons.length || m.items.length)
  }, [subject, q])

  const searching = q.trim().length > 0
  const shown = modules.reduce(
    (n, m) => n + m.items.length + m.lessons.reduce((k, l) => k + l.items.length, 0),
    0,
  )

  const toggleModule = (name: string) =>
    setOpenModules((prev) => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })

  const openLesson = (code: string) => {
    sessionStorage.setItem('ca_learn_code', code)
    navigate('/learn')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Spin size="large" />
      </div>
    )
  }
  if (err || !subject) {
    return <div className="py-24 text-center text-sm text-slate-400">{err || '暂无考题'}</div>
  }

  return (
    <div className="space-y-3">
      {/* 科目切换 */}
      <div className="flex gap-1.5 overflow-x-auto pb-0.5 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {data.map((s, i) => (
          <button
            key={s.subject}
            onClick={() => setActive(i)}
            className={`shrink-0 px-3 py-1.5 rounded-lg text-[13px] transition-colors ${
              i === active
                ? 'bg-indigo-600 text-white font-medium shadow-sm'
                : 'bg-white text-slate-600 border border-slate-200 hover:border-indigo-300 hover:text-indigo-600'
            }`}
          >
            {s.subject}
            <span className={`ml-1 text-[11px] ${i === active ? 'text-indigo-200' : 'text-slate-400'}`}>
              {s.total}
            </span>
          </button>
        ))}
      </div>

      {/* 这科怎么考 + 工具条 */}
      <div className="game-panel p-3">
        <p className="text-[12px] leading-relaxed text-slate-500">{subject.intro}</p>
        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-slate-400">
          <span>
            共 <b className="text-slate-600">{subject.total}</b> 题
          </span>
          <span>
            必问 <b className="text-rose-500">{subject.hot_total}</b>
          </span>
          <span>
            覆盖课程 {subject.lesson_covered}/{subject.lesson_total}
          </span>
          <span className="hidden sm:inline">题目按课程阶段分组，点题看标准答案</span>
        </div>
        <div className="mt-2.5 flex items-center gap-1.5">
          <Input
            allowClear
            size="small"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="搜题目、知识点或答案，如 索引"
            className="flex-1 max-w-[260px]"
          />
          <button
            onClick={() => setOpenModules(new Set(modules.map((m) => m.name)))}
            className="px-2 py-1 rounded-md text-[12px] text-slate-600 border border-slate-200 bg-white hover:border-indigo-300"
          >
            展开全部
          </button>
          <button
            onClick={() => setOpenModules(new Set())}
            className="px-2 py-1 rounded-md text-[12px] text-slate-600 border border-slate-200 bg-white hover:border-indigo-300"
          >
            收起
          </button>
        </div>
        {searching && (
          <div className="mt-2 text-[11px] text-indigo-500">命中 {shown} 题</div>
        )}
      </div>

      {/* 模块 → 课程 → 题 */}
      {modules.length === 0 && (
        <div className="game-panel py-12 text-center text-[13px] text-slate-400">
          没有匹配的题目，换个关键词试试
        </div>
      )}

      {modules.map((m) => {
        const count =
          m.items.length + m.lessons.reduce((k, l) => k + l.items.length, 0)
        // 搜索时强制展开，否则命中结果藏在折叠块里等于没搜
        const open = searching || openModules.has(m.name)
        return (
          <div key={m.name} className="game-panel overflow-hidden" data-module={m.name}>
            <button
              onClick={() => toggleModule(m.name)}
              className="w-full flex items-center gap-2 px-3 py-2.5 text-left hover:bg-slate-50/70"
            >
              <span className="w-1 h-4 rounded-full bg-indigo-400/70 shrink-0" />
              <span className="text-[13px] font-semibold text-slate-700">{m.name}</span>
              <span className="text-[11px] text-slate-400">{count} 题</span>
              <DownOutlined
                style={{ fontSize: 10, color: '#94a3b8' }}
                className={`ml-auto transition-transform ${open ? 'rotate-180' : ''}`}
              />
            </button>

            {open && (
              <div className="px-3 pb-3 space-y-2">
                {m.lessons.map((les) => (
                  <div key={les.code} data-lesson={les.code}>
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <span className="text-[11px] text-slate-400">
                        第 {les.order_no} 课
                      </span>
                      <span className="text-[12px] font-medium text-slate-600">
                        {les.title}
                      </span>
                      <span
                        className={`text-[10px] px-1 py-[1px] rounded ${STATUS[les.status]?.c || ''}`}
                      >
                        {STATUS[les.status]?.t || les.status}
                      </span>
                      <button
                        onClick={() => openLesson(les.code)}
                        className="ml-auto text-[11px] text-indigo-500 hover:text-indigo-700 shrink-0"
                      >
                        去学这一课 ›
                      </button>
                    </div>
                    <div className="space-y-1">
                      {les.items.map((it, ii) => {
                        const key = `${m.name}|${les.code}|${ii}`
                        return (
                          <QuestionRow
                            key={key}
                            item={it}
                            open={openKey === key}
                            onToggle={() => setOpenKey(openKey === key ? '' : key)}
                          />
                        )
                      })}
                    </div>
                  </div>
                ))}

                {m.items.length > 0 && (
                  <div>
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <span className="text-[12px] font-medium text-slate-600">没有对应课程的题</span>
                      <span className="text-[10px] px-1 py-[1px] rounded bg-slate-100 text-slate-400">
                        待补课
                      </span>
                    </div>
                    <div className="space-y-1">
                      {m.items.map((it, ii) => {
                        const key = `${m.name}|none|${ii}`
                        return (
                          <QuestionRow
                            key={key}
                            item={it}
                            open={openKey === key}
                            onToggle={() => setOpenKey(openKey === key ? '' : key)}
                          />
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )
      })}

      <div className="text-center text-[11px] text-slate-400 py-2">
        想按知识点看全貌？去「思维导图」；想练开口说？去「面试闯关」
      </div>
    </div>
  )
}

function QuestionRow({
  item,
  open,
  onToggle,
}: {
  item: QBankItem
  open: boolean
  onToggle: () => void
}) {
  const h = HOT[item.hot] || HOT[2]
  return (
    <div
      className={`rounded-lg border transition-colors ${
        open ? 'border-indigo-200 bg-indigo-50/40' : 'border-slate-200/80 bg-white hover:border-indigo-200'
      }`}
    >
      <button onClick={onToggle} className="w-full flex items-start gap-2 px-2.5 py-2 text-left">
        <span
          className="mt-[6px] w-1.5 h-1.5 rounded-full shrink-0"
          style={{ background: h.dot }}
        />
        <span className="min-w-0 flex-1">
          <span className="block text-[13px] leading-snug text-slate-700">{item.q}</span>
          <span className="mt-0.5 flex items-center gap-1.5">
            <span className={`text-[10px] px-1 py-[1px] rounded ${h.c}`}>{h.t}</span>
            {item.kp && <span className="text-[10.5px] text-slate-400">{item.kp}</span>}
          </span>
        </span>
        <DownOutlined
          style={{ fontSize: 9, color: '#94a3b8' }}
          className={`mt-[6px] shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}
        />
      </button>
      {open && (
        <div className="px-2.5 pb-2.5">
          <div className="rounded-md bg-white border border-indigo-100 px-2.5 py-2">
            <div className="text-[10px] text-indigo-500 mb-1">标准答案</div>
            <p className="text-[12.5px] leading-relaxed text-slate-600">
              <Rich text={item.answer} />
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
