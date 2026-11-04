import { useRef } from 'react'
import { useSettings } from '../theme/ThemeProvider'

/**
 * 行号 + 自动缩进的代码编辑区。
 *
 * 抽成组件的原因：引导式学习的「动手任务」页和 AI 导师的「代码沙箱」页
 * 用的是同一套编辑体验，之前这段逻辑埋在 Learn.tsx 里，复制一份必然走样。
 *
 * 关键点（都是新手真会踩的）：
 * - 回车继承上一行缩进，上一行以 `:` 结尾再多缩一级 —— Python 全靠缩进分块；
 * - Tab 插入 4 个空格而不是 `\t`，否则粘贴到别处会缩进乱掉；
 * - 行号用独立的 <pre> 画，靠 scrollTop 与 textarea 同步（不能跟着一起滚，
 *   否则行号会滚出视野）。
 */
export default function CodeEditor({
  value,
  onChange,
  placeholder,
  className = '',
}: {
  value: string
  onChange: (v: string) => void
  placeholder?: string
  className?: string
}) {
  const taRef = useRef<HTMLTextAreaElement>(null)
  const gutterRef = useRef<HTMLPreElement>(null)
  // 字号/字体/Tab 宽度/换行都来自「设置 → 编辑器」，改一处全站生效
  const { settings } = useSettings()
  const tab = ' '.repeat(settings.tabWidth)

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    const ta = e.currentTarget
    if (e.key === 'Tab') {
      e.preventDefault()
      const s = ta.selectionStart
      const end = ta.selectionEnd
      const next = value.slice(0, s) + tab + value.slice(end)
      onChange(next)
      requestAnimationFrame(() => {
        ta.selectionStart = ta.selectionEnd = s + tab.length
      })
      return
    }
    if (e.key === 'Enter') {
      e.preventDefault()
      const s = ta.selectionStart
      const end = ta.selectionEnd
      const lineStart = value.lastIndexOf('\n', s - 1) + 1
      const line = value.slice(lineStart, s)
      const indent = (line.match(/^[ \t]*/) || [''])[0]
      const extra = line.trimEnd().endsWith(':') ? tab : ''
      const insert = '\n' + indent + extra
      const next = value.slice(0, s) + insert + value.slice(end)
      onChange(next)
      const pos = s + insert.length
      requestAnimationFrame(() => {
        ta.selectionStart = ta.selectionEnd = pos
        if (gutterRef.current) gutterRef.current.scrollTop = ta.scrollTop
      })
    }
  }

  const lineCount = value.split('\n').length
  // 用 CSS 变量而不是写死 px：设置里改字号，这里不用重新渲染也不用传参
  const codeStyle = {
    fontFamily: 'var(--code-font)',
    fontSize: 'var(--code-size)',
    lineHeight: 'var(--code-line)',
  } as const

  return (
    <div
      className={`flex min-h-0 flex-1 overflow-hidden rounded-xl border border-indigo-200 bg-[#f8f9fd] focus-within:border-indigo-400 ${className}`}
    >
      <pre
        ref={gutterRef}
        aria-hidden
        className="select-none shrink-0 overflow-hidden whitespace-pre text-right pl-2 pr-1.5 py-2.5 bg-slate-100 font-mono text-slate-400"
        style={codeStyle}
      >
        {Array.from({ length: lineCount }, (_, i) => i + 1).join('\n')}
      </pre>
      <textarea
        ref={taRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKeyDown}
        onScroll={(e) => {
          if (gutterRef.current) gutterRef.current.scrollTop = e.currentTarget.scrollTop
        }}
        wrap={settings.wrap ? 'soft' : 'off'}
        spellCheck={false}
        className="flex-1 min-w-0 h-full bg-transparent px-2.5 py-2.5 font-mono text-slate-800 outline-none resize-none"
        style={{
          ...codeStyle,
          whiteSpace: settings.wrap ? 'pre-wrap' : 'pre',
        }}
        placeholder={placeholder}
      />
    </div>
  )
}
