import { useFocus, pauseFocus, resumeFocus, stopFocus, focusTimeText } from '../focus/store'
import { PauseOutlined, PlayCircleOutlined, CloseOutlined } from '@ant-design/icons'

/**
 * 专注中的悬浮条。
 *
 * 位置固定在顶部中间：桌面不会被左侧栏压住，手机落在标题栏下方；
 * 不用 AntD 的 Notification，因为它会抢焦点、还会在窄屏上盖住内容。
 */
export default function FocusHud() {
  const f = useFocus()
  if (!f.running) return null

  const pct = Math.min(100, Math.max(0, ((f.minutes * 60 - f.remain) / (f.minutes * 60)) * 100))

  return (
    // 手机：标题栏下方居中；桌面：右上角。
    // 桌面居中会压住设置页/周报页的标题与右上角按钮，靠右是唯一不挡东西的位置。
    <div className="fixed left-1/2 -translate-x-1/2 top-[52px] z-[58] pointer-events-none md:left-auto md:right-4 md:top-3 md:translate-x-0">
      <div className="pointer-events-auto flex items-center gap-2 rounded-full border border-[var(--t-line)] bg-[var(--t-panel)] pr-1.5 pl-3 py-1.5 shadow-lg">
        <span className="relative flex h-2 w-2">
          <span
            className={`absolute inline-flex h-full w-full rounded-full bg-[var(--t-accent)] ${
              f.paused ? '' : 'animate-ping opacity-60'
            }`}
          />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-[var(--t-accent)]" />
        </span>
        <span className="text-[12px] text-[var(--t-ink-2)] hidden sm:inline">
          {f.paused ? '已暂停' : '专注中'}
        </span>
        <span className="font-mono text-[14px] font-semibold tabular-nums text-[var(--t-ink)]">
          {focusTimeText(f.remain)}
        </span>
        <div className="hidden sm:block h-1 w-16 rounded-full bg-[var(--t-line)] overflow-hidden">
          <div
            className="h-full rounded-full bg-[var(--t-brand)] transition-[width] duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
        <button
          onClick={() => (f.paused ? resumeFocus() : pauseFocus())}
          aria-label={f.paused ? '继续专注' : '暂停'}
          className="w-6 h-6 rounded-full flex items-center justify-center text-[var(--t-ink-2)] hover:bg-[var(--t-panel-alt)]"
        >
          {f.paused ? <PlayCircleOutlined /> : <PauseOutlined />}
        </button>
        <button
          onClick={() => stopFocus()}
          aria-label="结束专注"
          className="w-6 h-6 rounded-full flex items-center justify-center text-[var(--t-ink-3)] hover:text-[var(--t-ink)] hover:bg-[var(--t-panel-alt)]"
        >
          <CloseOutlined className="text-[11px]" />
        </button>
      </div>
    </div>
  )
}
