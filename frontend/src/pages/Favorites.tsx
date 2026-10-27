import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { App, Empty, Input, Skeleton } from 'antd'
import { api } from '../api/client'
import QuestionCard from '../components/QuestionCard'
import { useFavorites } from '../store/favorites'
import type { FavoriteItem } from '../types'

/**
 * 我的收藏（独立页面）。
 *
 * 收藏入口在每道题的右上角星标；这里取消收藏会直接从列表里消失，
 * 不弹二次确认 —— 星标本身就是可撤销操作，再弹一次太啰嗦。
 */
export default function Favorites() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const { ids: favIds, toggle } = useFavorites()
  const [items, setItems] = useState<FavoriteItem[]>([])
  const [loading, setLoading] = useState(true)
  const [kw, setKw] = useState('')

  useEffect(() => {
    api
      .get<FavoriteItem[]>('/api/growth/favorites')
      .then(setItems)
      .catch((e) => message.error((e as Error).message))
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const list = useMemo(() => {
    const k = kw.trim()
    return k ? items.filter((i) => i.stem.includes(k) || i.subject.includes(k)) : items
  }, [items, kw])

  const unFav = async (qid: number) => {
    const favored = await toggle(qid)
    if (!favored) setItems((prev) => prev.filter((i) => i.question_id !== qid))
  }

  return (
    <div className="space-y-3">
      <div className="game-panel p-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate(-1)}
            className="shrink-0 text-[12px] text-slate-500 active:text-indigo-600"
          >
            ← 返回
          </button>
          <div className="min-w-0 flex-1">
            <h1 className="text-[16px] font-bold text-indigo-700">⭐ 我的收藏</h1>
            <p className="text-[11px] text-slate-400">共 {items.length} 道题</p>
          </div>
        </div>
        <Input
          allowClear
          className="mt-2"
          placeholder="搜题干或学科"
          value={kw}
          onChange={(e) => setKw(e.target.value)}
        />
      </div>

      {loading ? (
        <div className="game-panel p-4">
          <Skeleton active paragraph={{ rows: 6 }} />
        </div>
      ) : list.length === 0 ? (
        <div className="game-panel p-8">
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              items.length === 0 ? '还没有收藏的题，答题时点右上角 ☆ 就能收藏' : '没有匹配的题'
            }
          />
        </div>
      ) : (
        <div className="space-y-2">
          {list.map((f) => (
            <QuestionCard
              key={f.id}
              qid={f.question_id}
              favored={favIds.has(f.question_id)}
              onToggleFav={unFav}
              subject={f.subject}
              difficulty={f.difficulty}
              stem={f.stem}
              options={f.options}
              correctAnswer={f.correct_answer}
              explanation={f.explanation}
              knowledgePoint={f.knowledge_point}
            />
          ))}
        </div>
      )}
    </div>
  )
}
