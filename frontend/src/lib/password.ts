/**
 * 密码规则 —— 前端唯一来源。
 *
 * 必须与后端 `app/schemas.py::password_problems()` 保持一致：
 * 前端放宽只是让用户在提交后被后端打回一次，前端收紧则是自己造规则。
 * 注册页与「设置 → 修改密码」共用这一份，别各写一份。
 */
export interface PwdRule {
  key: string
  label: string
  test: (p: string) => boolean
}

export const PWD_RULES: PwdRule[] = [
  { key: 'len', label: '8~64 位', test: (p) => p.length >= 8 && p.length <= 64 },
  { key: 'upper', label: '大写字母', test: (p) => /[A-Z]/.test(p) },
  { key: 'lower', label: '小写字母', test: (p) => /[a-z]/.test(p) },
  { key: 'digit', label: '数字', test: (p) => /\d/.test(p) },
  { key: 'special', label: '特殊符号', test: (p) => /[^A-Za-z0-9\s]/.test(p) },
]

export const PWD_RULE_TEXT = '密码需 8~64 位，且同时含大写字母、小写字母、数字、特殊符号'

/** 返回未满足的规则（空数组 = 合规） */
export function pwdProblems(p: string): PwdRule[] {
  return PWD_RULES.filter((r) => !r.test(p))
}

/** 规则胶囊：满足变绿、未满足变灰，注册页与改密码共用 */
export function ruleChips(p: string) {
  return PWD_RULES.map((r) => ({ ...r, ok: r.test(p) }))
}
