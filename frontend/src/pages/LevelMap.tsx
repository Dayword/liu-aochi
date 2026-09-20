import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { App, Button, Progress } from 'antd'
import { motion } from 'framer-motion'
import { api } from '../api/client'
import { MAX_LIVES, formatCountdown, useLives } from '../game/lives'
import type { LevelItem, Scene } from '../types'

const DIFF_COLORS = ['#34d399', '#a3e635', '#d97706', '#ea580c', '#dc2626']
const DIFF_LABELS = ['L1 入门', 'L2 基础', 'L3 进阶', 'L4 困难', 'L5 专家']

export default function LevelMap() {
  const { message } = App.useApp()
  const [levels, setLevels] = useState<LevelItem[]>([])
  const [scenes, setScenes] = useState<Scene[]>([])
  const [refreshing, setRefreshing] = useState(false)
  const { lives, nextInMs } = useLives()

  const loadMap = useCallback(async () => {
    const d = await api.get<{ scenes: Scene[]; levels: LevelItem[] }>('/api/levels/map')
    setScenes(d.scenes)
    setLevels(d.levels)
  }, [])

  useEffect(() => {
    loadMap().catch((e) => message.error((e as Error).message))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadMap])

  const refresh = async () => {
    setRefreshing(true)
    try {
      await loadMap()
      message.success('已刷新')
    } catch (e) {
      message.error((e as Error).message)
    } finally {
      setRefreshing(false)
    }
  }

  const grouped = useMemo(() => {
    const map = new Map<string, LevelItem[]>()
    for (const lv of levels) {
      if (!map.has(lv.scene)) map.set(lv.scene, [])
      map.get(lv.scene)!.push(lv)
    }
    return map
  }, [levels])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-indigo-700">🗺️ 冒险大陆</h1>
          <p className="text-slate-500 text-sm mt-1">
            从新手村出发，穿越数据森林、算法峡谷，最终拿下大厂 Offer
          </p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          <div className="text-[11px] text-slate-500">
            <span className="mr-1">生命值</span>
            <span className="font-mono">
              {lives}/{MAX_LIVES}
            </span>
            {lives < MAX_LIVES && (
              <span className="ml-2 text-amber-600/80">
                下一颗 {formatCountdown(nextInMs)}
              </span>
            )}
          </div>
          <div className="flex gap-2 text-[11px]">
            {DIFF_LABELS.map((l, i) => (
              <span key={l} className="px-2 py-1 rounded-full" style={{ background: `${DIFF_COLORS[i]}22`, color: DIFF_COLORS[i] }}>
                {l}
              </span>
            ))}
          </div>
        </div>
      </div>

      {[...grouped.entries()].map(([scene, items], si) => {
        const sceneInfo = scenes.find((s) => s.name === scene)
        const completed = items.filter((i) => i.completed).length
        return (
          <div key={scene} className="game-panel p-5">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-3xl">{sceneInfo?.icon || items[0]?.icon}</span>
              <div className="flex-1">
                <h2 className="font-semibold text-indigo-800">{scene}</h2>
                <Progress
                  percent={Math.round((completed / items.length) * 100)}
                  size="small"
                  strokeColor="#34d399"
                  trailColor="#e2e8f0"
                  format={() => `${completed}/${items.length} 关`}
                  style={{ maxWidth: 300 }}
                />
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {items.map((lv, i) => {
                const locked = lv.status === 'locked'
                const done = lv.completed
                return (
                  <motion.div
                    key={lv.code}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.03 }}
                    whileHover={locked ? undefined : { y: -3 }}
                  >
                    <Link to={locked ? '/levels' : `/match3/${lv.code}`}>
                      <div
                        className={`p-4 rounded-2xl border h-full transition-all ${
                          locked
                            ? 'border-slate-300 bg-slate-100 opacity-60'
                            : done
                              ? 'border-emerald-300 bg-emerald-50'
                              : 'border-indigo-300 bg-indigo-50 hover:border-indigo-400/70'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <span className="text-3xl">{locked ? '🔒' : lv.icon}</span>
                          <span
                            className="px-2 py-0.5 rounded-full text-[10px] font-medium"
                            style={{
                              background: `${DIFF_COLORS[lv.difficulty - 1]}22`,
                              color: DIFF_COLORS[lv.difficulty - 1],
                            }}
                          >
                            {DIFF_LABELS[lv.difficulty - 1]}
                          </span>
                        </div>
                        <div className="mt-2 font-medium text-slate-800">{lv.name}</div>
                        <div className="text-[11px] text-slate-500 mt-1 line-clamp-2 min-h-[30px]">
                          {lv.description}
                        </div>
                        <div className="mt-2 flex items-center justify-between text-[11px]">
                          <span className="text-slate-500">{lv.subject}</span>
                          {done ? (
                            <span className="text-emerald-600">
                              ✓ 最佳 {lv.best_score}/10
                            </span>
                          ) : (
                            <span className="text-amber-600">
                              +{lv.base_exp} EXP · +{lv.base_coins}🪙
                            </span>
                          )}
                        </div>
                      </div>
                    </Link>
                  </motion.div>
                )
              })}
            </div>
          </div>
        )
      })}

      {levels.length === 0 && (
        <div className="game-panel p-10 text-center text-slate-500">关卡加载中…</div>
      )}

      <div className="text-center pb-4">
        <Button loading={refreshing} onClick={refresh}>
          🔄 刷新地图
        </Button>
      </div>
    </div>
  )
}
