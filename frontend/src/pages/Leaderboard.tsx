import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Empty, Segmented, Select, Skeleton } from 'antd'
import { LeftOutlined, TrophyOutlined } from '@ant-design/icons'
import { api } from '../api/client'
import type { LeaderboardData, LeaderEntry } from '../types'

/**
 * 排行榜（独立页）。
 *
 * 分组规则：学号前 4 位=年级，5~9 位=班级。
 * 组内排序：已完成课时数降序 → 学号后两位（座号）升序。
 */
export default function Leaderboard() {
  const navigate = useNavigate()
  const [scope, setScope] = useState<'class' | 'grade'>('class')
  const [grade, setGrade] = useState('')
  const [cls, setCls] = useState('')
  const [data, setData] = useState<LeaderboardData | null>(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const qs = new URLSearchParams({ scope })
      if (grade) qs.set('grade', grade)
      if (cls) qs.set('class_code', cls)
      setData(await api.get<LeaderboardData>(`/api/growth/leaderboard?${qs.toString()}`))
    } catch {
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scope, grade, cls])

  const me = (data?.me ?? {}) as Record<string, number | string>
  const gradeOptions = useMemo(
    () => (data?.groups ?? []).map((g) => ({ value: g.grade, label: `${g.grade} 级` })),
    [data],
  )
  const classOptions = useMemo(() => {
    const want = grade || data?.grade
    const g = (data?.groups ?? []).find((x) => x.grade === want)
    return (g?.classes ?? []).map((c) => ({
      value: c.code,
      label: `${c.code} 班（${c.count} 人）`,
    }))
  }, [data, grade])

  return (
    <div className="space-y-3">
      {/* 顶部：标题 + 返回（底部 Tab 已经常驻，这里只做页内导航） */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => navigate(-1)}
          className="w-8 h-8 rounded-lg bg-white border border-indigo-100 flex items-center justify-center text-slate-500 active:bg-slate-50"
          aria-label="返回"
        >
          <LeftOutlined className="text-xs" />
        </button>
        <div className="flex items-center gap-1.5">
          <TrophyOutlined className="text-amber-500" />
          <h1 className="text-base font-bold text-indigo-700">排行榜</h1>
        </div>
        <span className="ml-auto text-[11px] text-slate-400">
          共 {data?.items.length ?? 0} 人 · 满课 {data?.total_lessons ?? 135}
        </span>
      </div>

      {/* 我的排名 */}
      {me.class_rank ? (
        <div className="game-panel p-3 bg-gradient-to-br from-indigo-50 to-violet-50">
          <div className="flex items-center gap-3">
            <div className="text-center shrink-0">
              <div className="text-2xl font-bold text-indigo-600">{me.class_rank}</div>
              <div className="text-[10px] text-slate-500">班级排名</div>
            </div>
            <div className="w-px h-8 bg-indigo-200 shrink-0" />
            <div className="text-center shrink-0">
              <div className="text-lg font-semibold text-violet-600">{me.grade_rank}</div>
              <div className="text-[10px] text-slate-500">年级排名</div>
            </div>
            <div className="min-w-0 flex-1 text-right">
              <div className="text-[12px] font-medium truncate">
                {me.name} · 座号 {me.seat_no}
              </div>
              <div className="text-[11px] text-slate-500">
                已完成 {me.completed}/{me.total} 课时
                <span className="ml-1 text-slate-400">
                  （班 {me.class_size} 人 / 级 {me.grade_size} 人）
                </span>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="game-panel p-3 text-[12px] text-amber-600">
          当前账号还没有绑定 11 位学号，暂不参与排名。
        </div>
      )}

      {/* 视图切换 + 年级/班级筛选 */}
      <div className="flex items-center gap-2 flex-wrap">
        <Segmented
          size="small"
          value={scope}
          onChange={(v) => {
            setScope(v as 'class' | 'grade')
            setCls('')
          }}
          options={[
            { label: '本班榜', value: 'class' },
            { label: '年级榜', value: 'grade' },
          ]}
        />
        <Select
          size="small"
          className="min-w-[92px]"
          value={grade || data?.grade || undefined}
          onChange={(v) => {
            setGrade(v)
            setCls('')
          }}
          options={gradeOptions}
          placeholder="年级"
        />
        {scope === 'class' && (
          <Select
            size="small"
            className="min-w-[130px]"
            value={cls || data?.class_code || undefined}
            onChange={setCls}
            options={classOptions}
            placeholder="班级"
          />
        )}
      </div>

      {/* 榜单 */}
      {loading ? (
        <div className="game-panel p-3">
          <Skeleton active paragraph={{ rows: 6 }} />
        </div>
      ) : !data || data.items.length === 0 ? (
        <div className="game-panel p-6">
          <Empty description="这个分组还没有人" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        </div>
      ) : (
        <div className="game-panel divide-y divide-slate-100 overflow-hidden">
          {data.items.map((it) => (
            <Row key={it.student_id} it={it} total={data.total_lessons} />
          ))}
        </div>
      )}
    </div>
  )
}

function Row({ it, total }: { it: LeaderEntry; total: number }) {
  const pct = total ? Math.round((it.completed / total) * 100) : 0
  const medal = it.rank === 1 ? '🥇' : it.rank === 2 ? '🥈' : it.rank === 3 ? '🥉' : ''
  return (
    <div
      className={`flex items-center gap-2.5 px-3 py-2 ${
        it.is_me ? 'bg-indigo-50/70' : ''
      }`}
    >
      <div className="w-6 text-center shrink-0">
        {medal ? (
          <span className="text-base leading-none">{medal}</span>
        ) : (
          <span className="text-[12px] text-slate-400 font-medium">{it.rank}</span>
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <span className={`text-[13px] truncate ${it.is_me ? 'font-semibold text-indigo-700' : ''}`}>
            {it.name}
          </span>
          {it.is_me && (
            <span className="text-[9px] px-1 rounded bg-indigo-600 text-white shrink-0">我</span>
          )}
          <span className="text-[10px] text-slate-400 shrink-0">座号 {it.seat_no}</span>
        </div>
        <div className="flex items-center gap-1.5 mt-0.5">
          <div className="h-1 flex-1 rounded-full bg-slate-100 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-indigo-400 to-violet-500"
              style={{ width: `${Math.max(pct, 2)}%` }}
            />
          </div>
          <span className="text-[10px] text-slate-400 shrink-0">
            {it.completed}/{total}
          </span>
        </div>
      </div>
      {it.grade && (
        <span className="text-[10px] text-slate-300 shrink-0">
          {it.class_code}
        </span>
      )}
    </div>
  )
}
