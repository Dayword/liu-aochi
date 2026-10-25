import { useState } from 'react'
import Md from './Md'
import type { LearnProjectQuiz, LearnProjectRef } from '../types'

/**
 * 「项目实地」区块：把本课知识点对照到鸭先知 RAG 项目里的真实代码。
 *
 * 两种形态：
 * - used   → 直接给出 文件:行号 + 代码摘录，让学生看到它在生产代码里长什么样；
 * - absent → 说明项目里为什么没用它、实际用了什么替代方案，避免「学的都用得上」的错觉。
 *
 * 练习题走本地判分（点击即出对错 + 解析），不调用 /api/learn/quiz，
 * 所以既不会写库、也不会影响课程解锁和你已完成的进度。
 */
export default function ProjectField({ data }: { data: LearnProjectRef }) {
  const [picked, setPicked] = useState<Record<number, number>>({})
  const isUsed = data.kind === 'used'

  return (
    <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
      {/* 标题条：kind 决定颜色与文案 */}
      <div
        className={`flex items-center gap-2 flex-wrap px-3 py-2 border-b ${
          isUsed
            ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
            : 'bg-amber-50 border-amber-200 text-amber-800'
        }`}
      >
        <span className="text-xs font-medium">
          {isUsed ? '✅ 项目里就是这么写的' : '⚪ 项目里没有用它'}
        </span>
        {data.file && (
          <code className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-white/70 border border-black/5">
            {data.file}
            {data.lines ? `:${data.lines}` : ''}
          </code>
        )}
        <span className="ml-auto text-[10px] text-slate-500">鸭先知 · 游乐园智能体</span>
      </div>

      <div className="p-3 space-y-3">
        {data.snippet && (
          <div>
            <div className="text-[11px] text-slate-500 mb-1">
              {isUsed ? '真实代码' : '项目实际做法'}
            </div>
            <pre className="bg-[#f4f6fa] border border-slate-200 rounded-lg p-2.5 overflow-x-auto text-[11px] leading-relaxed">
              <code className="font-mono">{data.snippet}</code>
            </pre>
          </div>
        )}

        <div>
          <div className="text-[11px] text-slate-500 mb-1">这段代码在做什么</div>
          <div className="text-sm text-slate-700">
            <Md>{data.where}</Md>
          </div>
        </div>

        <div className="rounded-lg bg-indigo-50/60 border border-indigo-100 p-2.5">
          <div className="text-[11px] text-indigo-700 mb-1 font-medium">
            {isUsed ? '和本课的关系' : '项目为什么没用它'}
          </div>
          <div className="text-sm text-slate-700">
            <Md>{data.why}</Md>
          </div>
        </div>

        {data.quiz.length > 0 && (
          <div className="space-y-2">
            <div className="text-[11px] text-slate-500">练一练（点选项立即判对错）</div>
            {data.quiz.map((q, i) => (
              <QuizCard
                key={i}
                index={i}
                q={q}
                picked={picked[i]}
                onPick={(v) => setPicked((prev) => (i in prev ? prev : { ...prev, [i]: v }))}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function QuizCard({
  index,
  q,
  picked,
  onPick,
}: {
  index: number
  q: LearnProjectQuiz
  picked: number | undefined
  onPick: (v: number) => void
}) {
  const done = picked !== undefined
  const right = done && picked === q.answer
  const letters = 'ABCDEFGH'

  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5 space-y-1.5">
      <div className="flex items-start gap-1.5 text-sm text-slate-700">
        <span className="shrink-0 text-[10px] px-1 py-0.5 rounded bg-slate-200 text-slate-600 mt-0.5">
          {q.type === 'choice' ? `单选 ${index + 1}` : `判断 ${index + 1}`}
        </span>
        <span className="leading-relaxed">{q.stem}</span>
      </div>

      {q.type === 'choice' && q.options && (
        <div className="grid gap-1">
          {q.options.map((opt, i) => {
            let cls = 'border-slate-200 text-slate-600 hover:border-indigo-300'
            if (done) {
              if (i === q.answer) cls = 'border-emerald-400 bg-emerald-50 text-emerald-700'
              else if (i === picked) cls = 'border-rose-400 bg-rose-50 text-rose-700'
              else cls = 'border-slate-200 text-slate-400'
            }
            return (
              <button
                key={i}
                disabled={done}
                onClick={() => onPick(i)}
                className={`text-left px-2.5 py-1.5 rounded border text-xs transition-all ${cls}`}
              >
                <span className="text-slate-400 mr-1">{letters[i]}.</span>
                {opt}
              </button>
            )
          })}
        </div>
      )}

      {q.type === 'judge' && (
        <div className="flex gap-2">
          {[
            { v: 1, label: '对' },
            { v: 0, label: '错' },
          ].map((o) => {
            let cls = 'border-slate-200 text-slate-600 hover:border-indigo-300'
            if (done) {
              if (o.v === q.answer) cls = 'border-emerald-400 bg-emerald-50 text-emerald-700'
              else if (o.v === picked) cls = 'border-rose-400 bg-rose-50 text-rose-700'
              else cls = 'border-slate-200 text-slate-400'
            }
            return (
              <button
                key={o.v}
                disabled={done}
                onClick={() => onPick(o.v)}
                className={`px-4 py-1 rounded border text-xs transition-all ${cls}`}
              >
                {o.label}
              </button>
            )
          })}
        </div>
      )}

      {done && (
        <div
          className={`text-xs rounded px-2 py-1.5 leading-relaxed ${
            right ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'
          }`}
        >
          <span className="font-medium mr-1">{right ? '✓ 对了' : '✗ 不对'}</span>
          <Md>{q.explain}</Md>
        </div>
      )}
    </div>
  )
}
