import { useEffect } from 'react'
import BrandMark from '../boot/BrandMark'
import { useLocation, useNavigate } from 'react-router-dom'
import { Progress } from 'antd'
import { CloseOutlined, LogoutOutlined, RightOutlined, SettingOutlined } from '@ant-design/icons'
import { AnimatePresence, motion } from 'framer-motion'
import { useAuth } from '../store/auth'
import { NAV_GROUPS } from '../nav'

/** 当前路径是否命中某个入口（首页要精确匹配，否则所有页面都高亮首页） */
function isActive(path: string, to: string) {
  if (to === '/') return path === '/'
  return path === to || path.startsWith(`${to}/`)
}

/**
 * 手机端左侧抽屉：**全站入口都在这里**。
 *
 * 之前手机只有底部 4 个 Tab，知识地图 / 面试闯关 / Bug 猎人 / 错题本
 * 全部没有入口，学生只能靠记住 URL——所以做了这个抽屉。
 *
 * 打开方式有两种：
 * 1. 顶部品牌条左侧的 ☰（最可靠，谁都能发现）
 * 2. 从屏幕左边缘往右滑（iOS/Android 的通用习惯）
 */
export default function MobileDrawer({
  open,
  onClose,
  onLogout,
}: {
  open: boolean
  onClose: () => void
  onLogout: () => void
}) {
  const { character, user } = useAuth()
  const navigate = useNavigate()
  const { pathname } = useLocation()

  // 抽屉打开时锁住背景滚动，否则手指在遮罩上划会把下面的页面拖走
  useEffect(() => {
    if (!open) return
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = prev
    }
  }, [open])

  // 抽屉内再往左滑 → 关掉（和打开手势对称，符合直觉）
  useEffect(() => {
    if (!open) return
    let sx = 0
    let sy = 0
    let tracking = false
    const start = (e: TouchEvent) => {
      if (e.touches.length !== 1) return
      sx = e.touches[0].clientX
      sy = e.touches[0].clientY
      tracking = true
    }
    const move = (e: TouchEvent) => {
      if (!tracking) return
      const dx = e.touches[0].clientX - sx
      const dy = e.touches[0].clientY - sy
      if (dx < -46 && Math.abs(dx) > Math.abs(dy) * 1.4) {
        tracking = false
        onClose()
      }
    }
    const end = () => {
      tracking = false
    }
    window.addEventListener('touchstart', start, { passive: true })
    window.addEventListener('touchmove', move, { passive: true })
    window.addEventListener('touchend', end, { passive: true })
    return () => {
      window.removeEventListener('touchstart', start)
      window.removeEventListener('touchmove', move)
      window.removeEventListener('touchend', end)
    }
  }, [open, onClose])

  const expPct = character
    ? Math.min(100, Math.round((character.exp / character.exp_to_next) * 100))
    : 0

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            key="mm-mask"
            data-drawer-mask="1"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
            onClick={onClose}
            className="md:hidden fixed inset-0 z-[60] bg-slate-900/40 backdrop-blur-[1px]"
          />
          <motion.aside
            key="mm-panel"
            data-drawer="1"
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'tween', duration: 0.24, ease: [0.32, 0.72, 0, 1] }}
            className="md:hidden fixed left-0 top-0 bottom-0 z-[61] w-[80vw] max-w-[306px] bg-white shadow-2xl flex flex-col"
          >
            {/* 品牌 + 关闭 */}
            <div className="flex items-center gap-2 px-3.5 h-12 border-b border-indigo-100 shrink-0">
              <BrandMark size={22} tone="dark" />
              <div className="min-w-0 flex-1">
                <div className="font-bold text-[14px] text-indigo-700 leading-tight truncate">
                  码境 CodeRealm
                </div>
                <div className="text-[10px] text-slate-400 leading-tight">全部功能</div>
              </div>
              <button
                onClick={onClose}
                aria-label="关闭菜单"
                className="w-8 h-8 rounded-lg text-slate-400 active:bg-slate-100 flex items-center justify-center shrink-0"
              >
                <CloseOutlined className="text-[13px]" />
              </button>
            </div>

            {/* 用户卡：等级 + 经验 */}
            {character && (
              <div className="px-3.5 py-2.5 border-b border-indigo-100 t-brand-fade shrink-0">
                <div className="text-[13px] font-semibold text-slate-700 truncate">
                  {user?.real_name || character.name}
                </div>
                <div className="text-[10px] text-slate-400 truncate">
                  {user?.student_id ? `学号 ${user.student_id}` : character.identity}
                  {' · '}Lv.{character.level} {character.title}
                </div>
                <Progress
                  className="!mt-1 !mb-0"
                  percent={expPct}
                  size="small"
                  showInfo={false}
                  strokeColor="var(--t-brand)"
                  trailColor="var(--t-line)"
                />
              </div>
            )}

            {/* 全部入口 */}
            <nav className="flex-1 overflow-y-auto overscroll-contain px-2 py-2 space-y-2.5">
              {NAV_GROUPS.map((g, gi) => (
                <div key={gi} className="space-y-0.5">
                  {g.title && (
                    <div className="px-2.5 pt-1 pb-0.5 text-[10px] font-medium text-slate-400 tracking-wide">
                      {g.title}
                    </div>
                  )}
                  {g.items.map((item) => {
                    const active = isActive(pathname, item.to)
                    return (
                      <button
                        key={item.to}
                        data-nav={item.to}
                        onClick={() => {
                          onClose()
                          navigate(item.to)
                        }}
                        className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-left transition-colors ${
                          active
                            ? 'bg-indigo-100 text-indigo-700 font-medium'
                            : 'text-slate-600 active:bg-slate-100'
                        }`}
                      >
                        <span className="text-[16px] leading-none w-5 text-center shrink-0 opacity-80">
                          {item.icon}
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className="block text-[13.5px] leading-tight truncate">
                            {item.label}
                          </span>
                          <span className="block text-[10px] text-slate-400 leading-tight truncate mt-0.5">
                            {item.desc}
                          </span>
                        </span>
                        <RightOutlined className="text-[8px] text-slate-300 shrink-0" />
                      </button>
                    )
                  })}
                </div>
              ))}
            </nav>

            {/* 设置 + 退出登录：设置放前面，它是高频操作（换主题、调字号） */}
            <div className="shrink-0 border-t border-indigo-100 p-2 pb-[max(0.5rem,env(safe-area-inset-bottom))]">
              <div className="flex items-center gap-1">
                <button
                  data-nav="/settings"
                  onClick={() => {
                    onClose()
                    navigate('/settings')
                  }}
                  className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-[12px] text-slate-500 active:bg-slate-100"
                >
                  <SettingOutlined className="text-[12px]" />
                  设置
                </button>
                <button
                  onClick={() => {
                    onClose()
                    onLogout()
                  }}
                  className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-[12px] text-slate-500 active:bg-slate-100"
                >
                  <LogoutOutlined className="text-[12px]" />
                  退出登录
                </button>
              </div>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}

/**
 * 屏幕左边缘往右滑 → 打开抽屉。
 *
 * 只在最左 28px 内起手才认：否则会和知识地图的画布拖拽、图表的横向滑动打架。
 * 位移超过 52px 且明显是横向动作才触发；判定成纵向滚动就立刻放弃，
 * 不能让用户想上下滑页面的时候突然弹出抽屉。
 */
export function useEdgeSwipe(onOpen: () => void) {
  useEffect(() => {
    let sx = 0
    let sy = 0
    let tracking = false

    const start = (e: TouchEvent) => {
      if (e.touches.length !== 1) return
      if (window.innerWidth >= 768) return
      const t = e.touches[0]
      if (t.clientX > 28) return
      sx = t.clientX
      sy = t.clientY
      tracking = true
    }
    const move = (e: TouchEvent) => {
      if (!tracking) return
      const t = e.touches[0]
      const dx = t.clientX - sx
      const dy = t.clientY - sy
      if (dx > 52 && Math.abs(dx) > Math.abs(dy) * 1.5) {
        tracking = false
        // cancelable=false 说明浏览器已经在滚动了，此时 preventDefault 会被忽略
        // 并打一条 console 警告；判一下再调，控制台保持干净。
        if (e.cancelable) e.preventDefault()
        onOpen()
      } else if (Math.abs(dy) > 36 && Math.abs(dy) > Math.abs(dx)) {
        tracking = false
      }
    }
    const end = () => {
      tracking = false
    }

    window.addEventListener('touchstart', start, { passive: true })
    window.addEventListener('touchmove', move, { passive: false })
    window.addEventListener('touchend', end, { passive: true })
    window.addEventListener('touchcancel', end, { passive: true })
    return () => {
      window.removeEventListener('touchstart', start)
      window.removeEventListener('touchmove', move)
      window.removeEventListener('touchend', end)
      window.removeEventListener('touchcancel', end)
    }
  }, [onOpen])
}

