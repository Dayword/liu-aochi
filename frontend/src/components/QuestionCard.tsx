import type { ReactNode } from 'react'
import FavStar from './FavStar'

const DIFF_LABELS = ['L1', 'L2', 'L3', 'L4', 'L5']

/**
 * 题目卡片：错题本与收藏夹共用。
 *
 * 布局特意把星标放在题干右上角 —— 手机上拇指够得到，
 * 也符合「题目旁边有个收藏按钮」的直觉。
 */
export default function QuestionCard({
  qid,
  favored,
  onToggleFav,
  subject,
  difficulty,
  stem,
  options = [],
  correctAnswer,
  explanation,
  knowledgePoint,
  badge,
  footer,
  dim = false,
}: {
  qid: number
  favored: boolean
  onToggleFav: (qid: number) => Promise<unknown> | void
  subject: string
  difficulty: number
  stem: string
  options?: string[]
  correctAnswer: unknown
  explanation?: string
  knowledgePoint?: string
  badge?: ReactNode
  footer?: ReactNode
  dim?: boolean
}) {
  const correctText =
    typeof correctAnswer === 'number' && options[correctAnswer] !== undefined
      ? `${'ABCD'[correctAnswer]}. ${options[correctAnswer]}`
      : String(correctAnswer ?? '')

  return (
    <div className={`game-panel p-3 ${dim ? 'opacity-60' : ''}`}>
      <div className="flex items-start gap-1">
        <div className="min-w-0 flex-1">
          <div className="mb-1 flex flex-wrap items-center gap-1.5 text-[10px]">
            <span className="rounded-full bg-indigo-100 px-1.5 py-0.5 text-indigo-600">
              {subject}
            </span>
            <span className="rounded-full bg-slate-100 px-1.5 py-0.5 text-slate-500">
              {DIFF_LABELS[Math.max(0, Math.min(4, difficulty - 1))]}
            </span>
            {badge}
          </div>
          <div className="text-[13px] leading-relaxed text-slate-800">{stem}</div>
        </div>
        <FavStar qid={qid} favored={favored} onToggle={onToggleFav} />
      </div>

      {options.length > 0 && (
        <div className="mt-2 space-y-1">
          {options.map((o, i) => (
            <div
              key={i}
              className={`rounded-lg px-2 py-1 text-[12px] ${
                i === correctAnswer
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'bg-slate-50 text-slate-500'
              }`}
            >
              <span className="mr-1 text-slate-400">{'ABCD'[i]}.</span>
              {o}
            </div>
          ))}
        </div>
      )}

      {options.length === 0 && correctText && (
        <div className="mt-2 rounded-lg bg-emerald-50 px-2 py-1 text-[12px] text-emerald-700">
          正确答案：{correctText}
        </div>
      )}

      {explanation && (
        <div className="mt-2 text-[11.5px] leading-relaxed text-slate-500">
          <span className="text-indigo-600">解析：</span>
          {explanation}
        </div>
      )}
      {knowledgePoint && (
        <div className="mt-1 text-[10.5px] text-slate-400">考点：{knowledgePoint}</div>
      )}

      {footer && <div className="mt-2 flex items-center justify-end gap-2">{footer}</div>}
    </div>
  )
}
