import { useState } from 'react'
import { StarFilled, StarOutlined } from '@ant-design/icons'

/**
 * 题目收藏星标：点一下收藏、再点取消。
 *
 * `favored` 由父组件从 useFavorites() 里取，保证同一页多处星标状态一致；
 * 这里只管点按动画和请求，不自己存状态。
 */
export default function FavStar({
  qid,
  favored,
  onToggle,
  size = 16,
  withLabel = false,
}: {
  qid: number
  favored: boolean
  onToggle: (qid: number) => Promise<unknown> | void
  size?: number
  withLabel?: boolean
}) {
  const [busy, setBusy] = useState(false)

  const click = async (e: React.MouseEvent) => {
    e.stopPropagation()
    e.preventDefault()
    if (busy) return
    setBusy(true)
    try {
      await onToggle(qid)
    } finally {
      setBusy(false)
    }
  }

  return (
    <button
      type="button"
      onClick={click}
      title={favored ? '取消收藏' : '收藏这道题'}
      aria-label={favored ? '取消收藏' : '收藏'}
      data-fav={favored ? '1' : '0'}
      className={`inline-flex shrink-0 items-center gap-1 rounded-full px-1.5 py-1 transition-colors ${
        favored ? 'text-amber-500' : 'text-slate-300 hover:text-amber-400'
      } ${busy ? 'opacity-50' : ''}`}
    >
      {favored ? <StarFilled style={{ fontSize: size }} /> : <StarOutlined style={{ fontSize: size }} />}
      {withLabel && (
        <span className="text-[11px]">{favored ? '已收藏' : '收藏'}</span>
      )}
    </button>
  )
}
