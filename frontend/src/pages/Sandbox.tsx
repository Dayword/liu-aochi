import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { App, Button } from 'antd'
import { api } from '../api/client'
import CodeEditor from '../components/CodeEditor'
import SplitPane from '../components/SplitPane'
import type { CodeRunResult } from '../types'

const SAMPLE = `# 随便写点什么，点右上角「▶ 运行」
# 这段只是示例，直接改掉就行
def fib(n):
    a, b = 0, 1
    out = []
    for _ in range(n):
        out.append(a)
        a, b = b, a + b
    return out

print(fib(10))
`

/**
 * 独立的代码沙箱页（AI 导师侧入口）。
 *
 * 之前它挤在对话右侧只占 360px，手机上被压到下面几乎没法用；
 * 改成整页后，编辑区和输出区都能拿到全宽，配合可拖拽分屏自己分配比例。
 *
 * 代码来源两种：对话里点「▶ 运行」带过来的（location.state.code），
 * 或用户自己点进来从空白开始。
 */
export default function Sandbox() {
  const navigate = useNavigate()
  const location = useLocation()
  const { message } = App.useApp()
  const passed = (location.state as { code?: string } | null)?.code
  const [code, setCode] = useState(passed || SAMPLE)
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<CodeRunResult | null>(null)

  const run = async () => {
    if (!code.trim()) return
    setRunning(true)
    setResult(null)
    try {
      setResult(await api.post<CodeRunResult>('/api/code/run', { language: 'python', code }))
    } catch (e) {
      message.error((e as Error).message)
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="h-[100dvh] flex flex-col bg-[#f6f7fb]">
      {/* 顶部工具条：返回 / 标题 / 运行 */}
      <header className="shrink-0 flex items-center gap-2 px-2 h-12 bg-white/95 backdrop-blur border-b border-indigo-100">
        <button
          onClick={() => navigate(-1)}
          aria-label="返回"
          className="shrink-0 w-9 h-9 rounded-lg text-slate-500 active:bg-slate-100 text-lg"
        >
          ←
        </button>
        <div className="min-w-0">
          <div className="text-sm font-medium text-indigo-700 leading-tight">🧪 代码沙箱</div>
          <div className="text-[10px] text-slate-500 leading-tight">
            Python · 独立进程 · 5s 超时{passed ? ' · 已带入对话里的代码' : ''}
          </div>
        </div>
        <Button
          size="small"
          type="primary"
          loading={running}
          disabled={!code.trim()}
          onClick={run}
          className="ml-auto shrink-0"
        >
          ▶ 运行
        </Button>
      </header>

      <div className="flex-1 min-h-0 p-2">
        <SplitPane
          storageKey="ca_sandbox_ratio"
          initial={0.6}
          snaps={[0.4, 0.6, 0.8]}
          top={
            <CodeEditor
              value={code}
              onChange={setCode}
              placeholder="在这里写 Python…（回车自动缩进，Tab 缩进 4 格）"
            />
          }
          bottom={
            <div className="flex-1 min-h-0 overflow-auto rounded-xl border border-slate-200 bg-white p-2.5 text-xs">
              {running && <div className="text-amber-600 animate-pulse">⏳ 正在沙箱中运行…</div>}
              {!running && !result && (
                <div className="h-full flex items-center justify-center text-center px-4 text-slate-400">
                  运行结果会显示在这里 · 中间那条横杠可以上下拖，自己分配比例
                </div>
              )}
              {!running && result && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={result.exit_code === 0 ? 'text-emerald-600' : 'text-rose-600'}>
                      {result.exit_code === 0 ? '✅ 运行成功' : `❌ 退出码 ${result.exit_code}`}
                    </span>
                    <span className="text-slate-500">耗时 {result.time_ms} ms</span>
                  </div>
                  {result.stdout && (
                    <pre className="whitespace-pre-wrap font-mono text-slate-800">{result.stdout}</pre>
                  )}
                  {!result.stdout && result.exit_code === 0 && (
                    <div className="text-amber-700/90 leading-relaxed">
                      代码执行完毕但没有输出。定义好的函数需要被调用才会打印结果 ——
                      试试在末尾加一行 <code className="text-amber-600">print(...)</code>
                    </div>
                  )}
                  {result.stderr && (
                    <pre className="whitespace-pre-wrap font-mono text-rose-600">{result.stderr}</pre>
                  )}
                </div>
              )}
            </div>
          }
        />
      </div>
    </div>
  )
}
