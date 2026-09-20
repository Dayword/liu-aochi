// 类型定义（与后端 schema 对齐）

export interface Character {
  name: string
  identity: string
  class_key: string
  class_name: string
  level: number
  exp: number
  exp_to_next: number
  coins: number
  hp: number
  max_hp: number
  title: string
  weekly_exp: number
  total_exp: number
  total_quests: number
  total_correct: number
  total_wrong: number
  total_chats: number
  total_bugs: number
  total_interviews: number
  streak_days: number
  onboarding_done: boolean
}

export interface ClassInfo {
  key: string
  name: string
  emoji: string
  desc: string
  stack: string[]
  mentors: string[]
}

export interface LevelItem {
  code: string
  name: string
  scene: string
  description: string
  difficulty: number
  order_no: number
  unlock_prev: string
  subject: string
  tags: string[]
  recommended_class: string
  base_exp: number
  base_coins: number
  hp: number
  icon: string
  status: 'locked' | 'unlocked' | 'completed'
  best_score: number
  attempts: number
  completed: boolean
}

export interface Scene {
  name: string
  icon: string
  level_count: number
  completed_count: number
}

export interface QuestQuestion {
  question_id: number
  type: 'choice' | 'blank' | 'short' | 'code'
  stem: string
  options: string[]
  difficulty: number
  subject: string
  index: number
  is_code: boolean
  starter_code: string
}

export interface AnswerResult {
  correct: boolean
  explanation: string
  knowledge_point: string
  user_answer: unknown
  expected_answer: unknown
  ai_analysis: string
  hp_left: number
  coins_gained: number
  exp_gained: number
  difficulty_now: number
  finished: boolean
  level_failed: boolean
}

export interface Settlement {
  run_id: string
  level_code: string
  correct_count: number
  wrong_count: number
  accuracy: number
  total_exp: number
  total_coins: number
  level_completed: boolean
  unlocked_next: string | null
  new_achievements: { code: string; name: string; icon: string; description: string }[]
  score: number
}

export interface QuizItem {
  stem: string
  options: string[]
  answer_index: number
  explanation: string
}

export interface InterviewStart {
  session_id: number
  round_no: number
  total_rounds: number
  interviewer_name: string
  question: string
  category: string
}

export interface InterviewReport {
  overall: number
  grade: string
  dimensions: Record<string, number>
  strong_point: string
  weak_point: string
  advice: string
  offer: string
}

export interface InterviewAnswer {
  session_id: number
  round_no: number
  next_question: string
  next_category: string
  round_finished: boolean
  round_scores: Record<string, number | string>
  interview_finished: boolean
  report: InterviewReport
}

export interface BugChallenge {
  code: string
  title: string
  description: string
  bug_type: string
  difficulty: number
  hint: string
  language: string
  done?: boolean
  buggy_code?: string
  test_cases_preview?: { input: string; expected: string }[]
}

export interface BugSubmit {
  score: number
  accuracy: number
  speed_ms: number
  quality: number
  tests_passed: number
  tests_total: number
  passed: boolean
  results: { input: string; expected: string; got: string; passed: boolean; time_ms: number }[]
  explanation: string
  exp_gained: number
  coins_gained: number
  new_achievements: { code: string; name: string; icon: string }[]
}

export interface Achievement {
  code: string
  name: string
  description: string
  icon: string
  category: string
  unlocked: boolean
  unlocked_at?: string
  exp_reward?: number
  coin_reward?: number
}

export interface DailyTask {
  code: string
  name: string
  description: string
  progress: number
  target: number
  done: boolean
  claimed: boolean
  exp_reward: number
  coin_reward: number
}

export interface WrongItem {
  id: number
  question_id: number
  stem: string
  subject: string
  difficulty: number
  user_answer: unknown
  correct_answer: unknown
  explanation: string
  knowledge_point: string
  reason: string
  resolved: boolean
  created_at: string
}

export interface LeaderEntry {
  rank: number
  nickname: string
  character_name: string
  class_name: string
  level: number
  total_exp: number
  weekly_exp: number
}

export interface Profile {
  character: Character
  achievements: Achievement[]
  daily_tasks: DailyTask[]
  wrong_count: number
  radar: { subjects: string[]; scores: number[] }
  recent_levels: { code: string; name: string; icon: string; best_score: number }[]
}

/** /api/code/run 的返回：沙箱执行结果 */
export interface CodeRunResult {
  stdout: string
  stderr: string
  exit_code: number
  time_ms: number
}

// ---------- 引导式学习 ----------
export interface LearnPointBrief {
  code: string
  order_no: number
  title: string
  summary: string
  stage: string
  subject: string
  runner: 'python' | 'sql' | 'none'
  status: 'locked' | 'unlocked' | 'completed'
}

export type QuizType = 'choice' | 'judge' | 'blank' | 'short' | 'applied'

export interface LearnQuizItem {
  index: number
  type: QuizType
  stem: string
  options: string[]
  hint: string
}

export interface LearnPointDetail extends LearnPointBrief {
  definition: string
  plain: string
  example: string
  example_output: string
  pitfalls: string[]
  task: string
  setup: string
  starter: string
  hint: string
  last_code: string
  has_task: boolean
  code_passed: boolean
  quizzes: LearnQuizItem[]
  quiz_state: Record<string, { correct?: boolean; seen?: boolean }>
  next_code: string | null
}

export interface LearnCheckResult {
  passed: boolean
  output: string
  error: string
  reason: string
  solved: number
  total: number
  lesson_completed: boolean
  next_code: string | null
}

export interface LearnQuizResult {
  correct: boolean | null
  correct_answer: string
  explanation: string
  coverage: number | null
  missing: string[]
  reference: string
  lesson_completed: boolean
  next_code: string | null
}

// ---------- 消消乐闯关 ----------
export interface Match3Start {
  level_code: string
  name: string
  subject: string
  difficulty: number
  rows: number
  cols: number
  gem_types: number
  moves: number
  target_score: number
}

export interface Match3Question {
  question_id: number
  stem: string
  options: string[]
  subject: string
  source: string
}

export interface Match3AnswerResult {
  correct: boolean
  correct_index: number
  explanation: string
}

export interface Match3CompleteResult {
  completed: boolean
  exp_gained: number
  coins_gained: number
  unlocked_next: string | null
}
