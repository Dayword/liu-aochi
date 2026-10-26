import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { App, Button, Empty, Input, Modal, Progress, Segmented, Skeleton } from 'antd'
import {
  EditOutlined,
  RightOutlined,
  StarOutlined,
  TrophyOutlined,
} from '@ant-design/icons'
import * as echarts from 'echarts'
import { api } from '../api/client'
import { useAuth } from '../store/auth'
import type { Profile, WrongItem } from '../types'

const DIFF_LABELS = ['L1', 'L2', 'L3', 'L4', 'L5']

/** 能力雷达：维持原样式，尺寸压到 160px 以内，避免手机上占满一屏 */
function RadarChart({ subjects, scores }: { subjects: string[]; scores: number[] }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!ref.current) return
    const chart = echarts.init(ref.current)
    // 上限按数据取，避免后端万一给出超过 100 的值时多边形飞出画布糊成一片
    const max = Math.max(100, ...scores.map((v) => Math.ceil(v / 10) * 10))
    chart.setOption({
      backgroundColor: 'transparent',
      radar: {
        indicator: subjects.map((s) => ({ name: s, max })),
        radius: '70%',
        axisName: { color: '#64748b', fontSize: 9 },
        splitLine: { lineStyle: { color: 'rgba(99,102,241,0.25)' } },
        splitArea: { areaStyle: { color: ['rgba(99,102,241,0.03)', 'rgba(99,102,241,0.08)'] } },
        axisLine: { lineStyle: { color: 'rgba(99,102,241,0.3)' } },
      },
      series: [
        {
          type: 'radar',
          data: [
            {
              value: scores,
              areaStyle: { color: 'rgba(129,140,248,0.3)' },
              lineStyle: { color: '#818cf8', width: 2 },
              itemStyle: { color: '#a78bfa' },
            },
          ],
        },
      ],
    })
    const onResize = () => chart.resize()
    window.addEventListener('resize', onResize)
    return () => {
      window.removeEventListener('resize', onResize)
      chart.dispose()
    }
  }, [subjects, scores])
  return <div ref={ref} className="h-40 md:h-48 w-full" />
}

/** 「我的」页：个人信息 / 学习进度 / 排名 / 成就 / 收藏 / 错题 */
export default function Profile() {
  const { message, modal } = App.useApp()
  const { logout, user, refreshMe } = useAuth()
  const navigate = useNavigate()
  const [profile, setProfile] = useState<Profile | null>(null)
  const [wrongBook, setWrongBook] = useState<WrongItem[]>([])
  const [loading, setLoading] = useState(true)
  const [showAllAch, setShowAllAch] = useState(false)
  const [showAllWrong, setShowAllWrong] = useState(false)
  // 资料编辑弹窗
  const [editOpen, setEditOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({
    real_name: '',
    nickname: '',
    student_id: '',
    identity: '在校学生',
  })

  const load = async (silent = false) => {
    if (!silent) setLoading(true)
    try {
      const [p, w] = await Promise.all([
        api.get<Profile>('/api/user/profile'),
        api.get<WrongItem[]>('/api/growth/wrong-book'),
      ])
      setProfile(p)
      setWrongBook(w)
    } catch (e) {
      message.error((e as Error).message)
    } finally {
      if (!silent) setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const resolveWrong = async (id: number) => {
    await api.post(`/api/growth/wrong-book/${id}/resolve`)
    message.success('已标记为掌握')
    load()
  }

  /** 打开编辑弹窗：用当前资料预填 */
  const openEdit = () => {
    setForm({
      real_name: profile?.student?.real_name || user?.real_name || '',
      nickname: profile?.student?.nickname || user?.nickname || '',
      student_id: profile?.student?.student_id || user?.student_id || '',
      identity: profile?.character?.identity || '在校学生',
    })
    setEditOpen(true)
  }

  /** 保存资料：姓名必填，学号必须 11 位数字（后端还会查重） */
  const saveProfile = async () => {
    const name = form.real_name.trim()
    if (!name) {
      message.warning('请填写姓名')
      return
    }
    if (!/^\d{11}$/.test(form.student_id)) {
      message.warning('学号必须是 11 位数字')
      return
    }
    setSaving(true)
    try {
      await api.patch('/api/user/profile', {
        real_name: name,
        nickname: form.nickname.trim(),
        student_id: form.student_id,
        identity: form.identity,
      })
      message.success('资料已更新')
      setEditOpen(false)
      await refreshMe()          // 同步顶部品牌条 / 侧栏里的姓名
      await load(true)           // 静默刷新，不闪骨架屏
    } catch (e) {
      message.error((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  const askLogout = () => {
    modal.confirm({
      title: '确认退出登录？',
      content: '退出后需要重新用学号和密码登录，学习进度不会丢失。',
      okText: '退出登录',
      okButtonProps: { danger: true },
      cancelText: '再想想',
      onOk: () => {
        logout()
        navigate('/login', { replace: true })
      },
    })
  }

  if (loading) {
    return (
      <div className="game-panel p-4">
        <Skeleton active paragraph={{ rows: 8 }} />
      </div>
    )
  }
  if (!profile) {
    return <div className="game-panel p-6 text-center text-slate-500">加载失败，请刷新重试</div>
  }

  const { character, student, learn, rank, achievements, radar, wrong_count } = profile
  const studentId = student?.student_id || user?.student_id || ''
  const realName = student?.real_name || user?.real_name || character.name
  const expPct = Math.min(100, Math.round((character.exp / character.exp_to_next) * 100))
  const unlocked = achievements.filter((a) => a.unlocked)
  const achList = showAllAch ? achievements : achievements.slice(0, 8)
  const wrongList = showAllWrong ? wrongBook : wrongBook.slice(0, 3)

  return (
    <div className="space-y-3">
      {/* ===== 个人信息（可查看 + 点「编辑」修改） ===== */}
      <div className="game-panel relative p-3">
        <button
          onClick={openEdit}
          className="absolute right-2.5 top-2.5 z-10 flex items-center gap-0.5 rounded-full bg-indigo-50 px-2 py-0.5 text-[11px] text-indigo-600 active:bg-indigo-100"
        >
          <EditOutlined className="text-[10px]" />
          编辑
        </button>
        <div className="flex items-center gap-3 pr-14">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-500 text-white flex items-center justify-center text-xl shrink-0">
            {realName.slice(0, 1)}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-baseline gap-1.5">
              <span className="font-bold text-[15px] truncate">{realName}</span>
              <span className="text-[11px] text-amber-600 shrink-0">
                Lv.{character.level} {character.title}
              </span>
            </div>
            <div className="text-[11px] text-slate-500 truncate">
              {studentId ? `学号 ${studentId}` : '未绑定学号'}
              {student?.grade && ` · ${student.grade} 级 · 班级 ${student.class_code}`}
            </div>
            <div className="text-[11px] text-slate-400 truncate">
              {character.identity}
              {student?.seat_no && ` · ${student.seat_no} 号`}
              {student?.nickname && student.nickname !== realName && ` · @${student.nickname}`}
            </div>
          </div>
        </div>
        <Progress
          className="mt-2"
          percent={expPct}
          size="small"
          strokeColor={{ from: '#6366f1', to: '#a855f7' }}
          trailColor="#e2e8f0"
          format={() => (
            <span className="text-[10px] text-slate-500">
              {character.exp}/{character.exp_to_next}
            </span>
          )}
        />
      </div>

      {/* ===== 学习进度 + 我的排名 ===== */}
      <div className="grid grid-cols-2 gap-2">
        <button
          onClick={() => navigate('/learn')}
          className="game-panel p-3 text-left active:bg-slate-50"
        >
          <div className="text-[11px] text-slate-500">学习进度</div>
          <div className="text-lg font-bold text-indigo-600 leading-tight">
            {learn?.completed ?? 0}
            <span className="text-[11px] font-normal text-slate-400"> / {learn?.total ?? 135} 课时</span>
          </div>
          <Progress
            percent={learn?.pct ?? 0}
            size="small"
            showInfo={false}
            strokeColor="#6366f1"
            trailColor="#e2e8f0"
          />
          <div className="text-[10px] text-slate-400 mt-0.5 flex items-center">
            继续学习 <RightOutlined className="text-[8px] ml-0.5" />
          </div>
        </button>

        <button
          onClick={() => navigate('/leaderboard')}
          className="game-panel p-3 text-left active:bg-slate-50"
        >
          <div className="text-[11px] text-slate-500 flex items-center gap-1">
            <TrophyOutlined className="text-amber-500" /> 我的排名
          </div>
          {rank?.class_rank ? (
            <>
              <div className="text-lg font-bold text-violet-600 leading-tight">
                {rank.class_rank}
                <span className="text-[11px] font-normal text-slate-400">
                  {' '}/ {rank.class_size} 人（班）
                </span>
              </div>
              <div className="text-[11px] text-slate-500">
                年级 {rank.grade_rank} / {rank.grade_size} 人
              </div>
            </>
          ) : (
            <div className="text-[12px] text-slate-400 mt-2">暂无排名</div>
          )}
          <div className="text-[10px] text-slate-400 mt-0.5 flex items-center">
            查看排行榜 <RightOutlined className="text-[8px] ml-0.5" />
          </div>
        </button>
      </div>

      {/* ===== 答题统计 + 能力雷达 ===== */}
      <div className="game-panel p-3">
        <div className="text-[13px] font-semibold text-slate-700 mb-1.5">📊 答题统计 · 能力雷达</div>
        <div className="md:flex md:items-center md:justify-center md:gap-8">
          <div className="flex items-center gap-3 text-[11px] text-slate-500 mb-1 md:mb-0 md:w-36 md:shrink-0 md:flex-col md:items-stretch md:gap-2.5">
            <span className="md:flex md:items-center md:justify-between">
              <span>答对</span>{' '}
              <b className="text-emerald-600">{character.total_correct} 题</b>
            </span>
            <span className="md:flex md:items-center md:justify-between">
              <span>答错</span>{' '}
              <b className="text-rose-600">{character.total_wrong} 题</b>
            </span>
            <span className="md:flex md:items-center md:justify-between">
              <span>正确率</span>{' '}
              <b className="text-indigo-600">
                {Math.round(
                  (character.total_correct /
                    Math.max(1, character.total_correct + character.total_wrong)) *
                    100,
                )}
                %
              </b>
            </span>
          </div>
          <div className="md:w-80 md:shrink-0">
            <RadarChart subjects={radar.subjects} scores={radar.scores} />
          </div>
        </div>
      </div>

      {/* ===== 成就墙 ===== */}
      <div className="game-panel p-3">
        <div className="flex items-center justify-between mb-2">
          <div className="text-[13px] font-semibold text-slate-700">
            🏅 成就墙
            <span className="text-[11px] font-normal text-slate-400 ml-1">
              {unlocked.length}/{achievements.length}
            </span>
          </div>
          {achievements.length > 8 && (
            <button
              onClick={() => setShowAllAch(!showAllAch)}
              className="text-[11px] text-indigo-600"
            >
              {showAllAch ? '收起' : '全部'}
            </button>
          )}
        </div>
        <div className="grid grid-cols-4 md:grid-cols-6 gap-1.5">
          {achList.map((a) => (
            <div
              key={a.code}
              title={`${a.name}：${a.description}`}
              className={`rounded-xl border p-1.5 text-center ${
                a.unlocked
                  ? 'border-amber-200 bg-amber-50'
                  : 'border-slate-100 bg-slate-50 opacity-55'
              }`}
            >
              <div className="text-lg leading-none">{a.icon}</div>
              <div className="text-[9px] mt-0.5 truncate text-slate-600">{a.name}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ===== 收藏（占位） ===== */}
      <div className="game-panel p-3">
        <div className="text-[13px] font-semibold text-slate-700 mb-1.5 flex items-center gap-1">
          <StarOutlined className="text-amber-500" /> 我的收藏
        </div>
        <div className="rounded-xl border border-dashed border-slate-200 py-4 text-center">
          <div className="text-[12px] text-slate-400">还没有收藏内容</div>
          <div className="text-[10px] text-slate-300 mt-0.5">
            课时 / 面试题的收藏功能正在开发中
          </div>
        </div>
      </div>

      {/* ===== 错题记录 ===== */}
      <div className="game-panel p-3">
        <div className="flex items-center justify-between mb-2">
          <div className="text-[13px] font-semibold text-slate-700">
            📕 错题记录
            <span className="text-[11px] font-normal text-slate-400 ml-1">
              {wrong_count} 题
            </span>
          </div>
          {wrongBook.length > 3 && (
            <button
              onClick={() => setShowAllWrong(!showAllWrong)}
              className="text-[11px] text-indigo-600"
            >
              {showAllWrong ? '收起' : '全部'}
            </button>
          )}
        </div>
        {wrongBook.length === 0 ? (
          <Empty
            description="错题本是空的，答题错误会自动收录"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <div className="space-y-2">
            {wrongList.map((w) => (
              <div
                key={w.id}
                className={`rounded-xl border border-slate-100 p-2.5 ${w.resolved ? 'opacity-50' : ''}`}
              >
                <div className="flex items-center gap-1.5 text-[10px] mb-1">
                  <span className="px-1.5 py-0.5 rounded-full bg-indigo-100 text-indigo-600">
                    {w.subject}
                  </span>
                  <span className="px-1.5 py-0.5 rounded-full bg-slate-100 text-slate-500">
                    {DIFF_LABELS[w.difficulty - 1]}
                  </span>
                  {w.resolved && <span className="text-emerald-600">✓ 已掌握</span>}
                </div>
                <div className="text-[12px] text-slate-700 leading-snug line-clamp-2">
                  {w.stem}
                </div>
                <div className="flex items-center justify-between mt-1">
                  <div className="text-[10px] text-slate-400">
                    你的答案 <span className="text-rose-500">{String(w.user_answer) || '（空）'}</span>
                    {' · '}正确 <span className="text-emerald-600">{String(w.correct_answer)}</span>
                  </div>
                  {!w.resolved && (
                    <button
                      onClick={() => resolveWrong(w.id)}
                      className="text-[10px] text-indigo-600 shrink-0"
                    >
                      标记掌握
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ===== 资料编辑弹窗 ===== */}
      <Modal
        open={editOpen}
        title="编辑个人资料"
        okText="保存"
        cancelText="取消"
        confirmLoading={saving}
        onOk={saveProfile}
        onCancel={() => setEditOpen(false)}
        width={420}
      >
        <div className="space-y-3 pt-1">
          <div>
            <div className="text-[12px] text-slate-500 mb-1">
              姓名 <span className="text-rose-500">*</span>
            </div>
            <Input
              maxLength={20}
              value={form.real_name}
              placeholder="真实姓名，排行榜展示用"
              onChange={(e) => setForm({ ...form, real_name: e.target.value })}
            />
          </div>
          <div>
            <div className="text-[12px] text-slate-500 mb-1">昵称</div>
            <Input
              maxLength={20}
              value={form.nickname}
              placeholder="冒险者昵称，例如 阿测"
              onChange={(e) => setForm({ ...form, nickname: e.target.value })}
            />
          </div>
          <div>
            <div className="text-[12px] text-slate-500 mb-1">学号</div>
            <Input
              maxLength={11}
              inputMode="numeric"
              value={form.student_id}
              placeholder="11 位学号"
              onChange={(e) =>
                setForm({
                  ...form,
                  student_id: e.target.value.replace(/\D/g, '').slice(0, 11),
                })
              }
            />
            <div className="mt-1 text-[10px] leading-relaxed text-slate-400">
              {form.student_id.length === 11
                ? `${form.student_id.slice(0, 4)} 级 · 班级 ${form.student_id.slice(4, 9)} · 座号 ${form.student_id.slice(9)}`
                : '11 位数字 = 前 4 位年级 + 中间 5 位班级 + 后 2 位座号'}
              <br />
              改学号会同步改变年级 / 班级 / 座号，并影响排行榜分组
            </div>
          </div>
          <div>
            <div className="text-[12px] text-slate-500 mb-1">身份</div>
            <Segmented
              block
              value={form.identity}
              onChange={(v) => setForm({ ...form, identity: v as string })}
              options={[
                { label: '🎓 在校学生', value: '在校学生' },
                { label: '💼 求职中', value: '求职中' },
              ]}
            />
          </div>
        </div>
      </Modal>

      {/* ===== 退出登录（手机上唯一的入口） ===== */}
      <Button block danger onClick={askLogout} className="mb-2">
        退出登录
      </Button>
    </div>
  )
}
