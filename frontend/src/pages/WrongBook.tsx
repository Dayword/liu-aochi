import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { App, Button, Empty, Segmented, Skeleton } from 'antd'
import { api } from '../api/client'
import QuestionCard from '../components/QuestionCard'
import { useFavorites } from '../store/favorites'
import type { WrongItem } from '../types'

/**
 * 错题本（独立页面）。
 *
 * 数据来源：答题时答错自动入库（Quest 闯关 / 知识竞速 / Bug 之外的答题入口）。
 * 这里能做三件事：标记掌握、从本子移除、顺手收藏。
 */
export default function WrongBook() {
  const { message, modal } = App.useApp()
  const navigate = useNavigate()
  const { ids: favIds, toggle: toggleFav } = useFavorites()
  const [items, setItems] = useState<WrongItem[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'todo' | 'done'>('todo')

  const load = async () => {
    setLoading(true)
    try {
      setItems(await api.get<WrongItem[]>('/api/growth/wrong-book'))
    } catch (e) {
      message.error((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const todo = useMemo(() => items.filter((i) => !i.resolved), [items])
  const done = useMemo(() => items.filter((i) => i.resolved), [items])
  const list = tab === 'todo' ? todo : done

  const resolve = async (id: number) => {
    try {
      await api.post(`/api/growth/wrong-book/${id}/resolve`)
      setItems((prev) => prev.map((i) => (i.id === id ? { ...i, resolved: true } : i)))
      message.success('已标记为掌握')
    } catch (e) {
      message.error((e as Error).message)
    }
  }

  const remove = (id: number) => {
    modal.confirm({
      title: '从错题本移除？',
      content: '移除后不会再出现在列表里，但答题统计里的「答错」不会变。',
      okText: '移除',
      okButtonProps: { danger: true },
      cancelText: '取消',
      onOk: async () => {
        try {
          await api.del(`/api/growth/wrong-book/${id}`)
          setItems((prev) => prev.filter((i) => i.id !== id))
          message.success('已移除')
        } catch (e) {
          message.error((e as Error).message)
        }
      },
    })
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
            <h1 className="text-[16px] font-bold text-indigo-700">📕 错题本</h1>
            <p className="text-[11px] text-slate-400">
              答错的题会自动进来 · 待掌握 {todo.length} 题 · 已掌握 {done.length} 题
            </p>
          </div>
        </div>
        <Segmented
          block
          className="mt-2"
          value={tab}
          onChange={(v) => setTab(v as 'todo' | 'done')}
          options={[
            { label: `待掌握 ${todo.length}`, value: 'todo' },
            { label: `已掌握 ${done.length}`, value: 'done' },
          ]}
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
              tab === 'todo' ? '没有待掌握的错题，继续保持' : '还没有标记掌握的题'
            }
          />
        </div>
      ) : (
        <div className="space-y-2">
          {list.map((w) => (
            <QuestionCard
              key={w.id}
              qid={w.question_id}
              favored={favIds.has(w.question_id)}
              onToggleFav={toggleFav}
              subject={w.subject}
              difficulty={w.difficulty}
              stem={w.stem}
              options={w.options}
              correctAnswer={w.correct_answer}
              explanation={w.explanation}
              knowledgePoint={w.knowledge_point}
              dim={w.resolved}
              badge={
                w.resolved ? (
                  <span className="text-emerald-600">✓ 已掌握</span>
                ) : (
                  <span className="text-rose-500">{w.reason || '答错了'}</span>
                )
              }
              footer={
                <>
                  {!w.resolved && (
                    <>
                      <button
                        onClick={() => remove(w.id)}
                        className="text-[11px] text-slate-400 active:text-rose-500"
                      >
                        移除
                      </button>
                      <Button size="small" onClick={() => resolve(w.id)}>
                        标记掌握
                      </Button>
                    </>
                  )}
                  {w.resolved && (
                    <button
                      onClick={() => remove(w.id)}
                      className="text-[11px] text-slate-400 active:text-rose-500"
                    >
                      移除
                    </button>
                  )}
                </>
              }
            />
          ))}
        </div>
      )}
    </div>
  )
}
