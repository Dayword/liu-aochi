/**
 * 一个极小的全局事件总线。
 *
 * 用途：判题发生在 Learn / LearnPractice / Game 三个互不相识的页面里，
 * 而「撒星星」「机器人表情」「连击数字」都在另一个角落。用一个 20 行的
 * 订阅表，比为了三个消费者把状态提到 Context 再层层传下去便宜得多。
 */
export type BusEvent =
  /** 提交了一道题；correct 是对错 */
  | { type: 'answer'; correct: boolean }
  /** 升级 */
  | { type: 'levelup'; level: number }
  /** 番茄钟开始 / 结束 */
  | { type: 'focus'; running: boolean }
  /** 通关（闯关全对、课程完成） */
  | { type: 'clear' }

type Handler = (e: BusEvent) => void

const subs = new Set<Handler>()

export function onBus(fn: Handler): () => void {
  subs.add(fn)
  return () => {
    subs.delete(fn)
  }
}

export function emit(e: BusEvent) {
  // 复制一份再遍历：订阅者在处理时取消订阅不会打断本轮派发
  for (const fn of [...subs]) {
    try {
      fn(e)
    } catch {
      /* 单个订阅者报错不能影响其它订阅者（比如特效挂了不该拦住判题） */
    }
  }
}


// 开发期调试口子：控制台里 __caEmit({type:'clear'}) 可以手动触发特效，
// 验收「画布真的画了东西」时用得上。生产构建里这段不会执行。
if (import.meta.env.DEV) {
  ;(window as unknown as { __caEmit?: typeof emit }).__caEmit = emit
}
