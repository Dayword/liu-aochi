import ReactMarkdown from 'react-markdown'

/** 支持 `反引号` 和代码块的轻量 Markdown 渲染（与引导式学习页同一套排版） */
export default function Md({ children }: { children: string }) {
  return (
    <ReactMarkdown
      components={{
        p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
        pre: ({ children }) => (
          <pre className="bg-[#f4f6fa] border border-slate-200 p-3 rounded-lg overflow-x-auto text-xs my-2 leading-relaxed">
            {children}
          </pre>
        ),
        code: ({ children, className }) =>
          className?.includes('language') ? (
            <code className={className}>{children}</code>
          ) : (
            <code className="bg-indigo-50 text-indigo-700 px-1 py-0.5 rounded text-[0.9em]">
              {children}
            </code>
          ),
        strong: ({ children }) => <strong className="text-indigo-700">{children}</strong>,
        ul: ({ children }) => <ul className="list-disc pl-5 space-y-1 my-2">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal pl-5 space-y-1 my-2">{children}</ol>,
      }}
    >
      {children}
    </ReactMarkdown>
  )
}
