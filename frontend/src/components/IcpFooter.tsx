/**
 * ICP 备案号页脚。
 *
 * 管局要求：备案通过的网站必须在**首页底部**展示备案号，并链接到
 * https://beian.miit.gov.cn/ 可查询。抽查到没挂会被要求限期整改。
 *
 * 备案号通过构建期环境变量注入（deploy.sh 会写 frontend/.env.production），
 * 未配置时整块不渲染 —— 本地开发和 GitHub Pages 上不会出现空占位。
 */
export default function IcpFooter() {
  const beian = (import.meta.env.VITE_ICP_BEIAN ?? '').trim()
  if (!beian) return null

  return (
    <footer className="py-6 text-center text-[11px] text-slate-400 leading-relaxed">
      <a
        href="https://beian.miit.gov.cn/"
        target="_blank"
        rel="noreferrer noopener"
        className="hover:text-slate-600 transition-colors"
      >
        {beian}
      </a>
    </footer>
  )
}
