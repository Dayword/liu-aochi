import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { App, Button, Input, Modal, Progress, Segmented, Skeleton } from 'antd'
import {
  EditOutlined,
  RightOutlined,
  StarOutlined,
  TrophyOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import * as echarts from 'echarts'
import { api } from '../api/client'
import { useAuth } from '../store/auth'
import type { AchievementFamily, Profile } from '../types'

/** 能力雷达：尺寸压到 160px 以内，避免手机上占满一屏 */
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

/** 无名额限制的「铜/银/金」档位徽标 */
function TierDots({ fam }: { fam: AchievementFamily }) {
  return (
    <span className="tracking-tighter">
      {fam.tiers.map((t) => (
        <span
          key={t.code}
          className={t.unlocked ? '' : 'opacity-25 grayscale'}
          title={`${t.tier} · ${t.name}`}
          style={{ fontSize: 13 }}
        >
          {t.icon}
        </span>
      ))}
    </span>
  )
}

/** 「我的」页：个人信息 / 学习进度 / 排名 / 成就 / 收藏 / 错题 */
export default function Profile() {
  const { message, modal } = App.useApp()
  const { logout, user, refreshMe } = useAuth()
  const navigate = useNavigate()
  const [profile, setProfile] = useState<Profile | null>(null)
  const [loading, setLoading] = useState(true)
  // 资料编辑弹窗
  const [editOpen, setEditOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({ nickname: '', identity: '在校学生' })
  // 老账号首次绑定学号/姓名（绑定后同样不可改）
  const [bindOpen, setBindOpen] = useState(false)
  const [bindForm, setBindForm] = useState({ student_id: '', real_name: '' })
  // 成就弹窗
  const [achOpen, setAchOpen] = useState<AchievementFamily | null>(null)

  const load = async (silent = false) => {
    if (!silent) setLoading(true)
    try {
      setProfile(await api.get<Profile>('/api/user/profile'))
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

  const openEdit = () => {
    setForm({
      nickname: profile?.student?.nickname || user?.nickname || '',
      identity: profile?.character?.identity || '在校学生',
    })
    setEditOpen(true)
  }

  const saveProfile = async () => {
    setSaving(true)
    try {
      await api.patch('/api/user/profile', {
        nickname: form.nickname.trim(),
        identity: form.identity,
      })
      message.success('资料已更新')
      setEditOpen(false)
      await refreshMe()
      await load(true)
    } catch (e) {
      message.error((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  const bindIdentity = async () => {
    const sid = bindForm.student_id.trim()
    const name = bindForm.real_name.trim()
    if (!/^\d{11}$/.test(sid)) {
      message.warning('学号必须是 11 位数字')
      return
    }
    if (!/^[\u4e00-\u9fa5·]{2,10}$/.test(name)) {
      message.warning('姓名必须是中文（2~10 个汉字）')
      return
    }
    modal.confirm({
      title: '确认绑定学号与姓名？',
      content: (
        <div className="text-[13px] leading-relaxed">
          <div>
            学号：<b>{sid}</b>
          </div>
          <div>
            姓名：<b>{name}</b>
          </div>
          <div className="mt-2 text-rose-600">绑定后不可修改，请确认无误。</div>
        </div>
      ),
      okText: '确认绑定',
      cancelText: '再检查一下',
      onOk: async () => {
        await api.patch('/api/user/profile', { student_id: sid, real_name: name })
        message.success('已绑定')
        setBindOpen(false)
        await refreshMe()
        await load(true)
      },
    })
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

  const { character, student, learn, rank, radar, wrong_count } = profile
  const families = profile.achievement_families || []
  const favCount = profile.favorites_count || 0
  const studentId = student?.student_id || user?.student_id || ''
  const realName = student?.real_name || user?.real_name || character.name
  const expPct = Math.min(100, Math.round((character.exp / character.exp_to_next) * 100))
  const achTotal = families.reduce((a, f) => a + f.tiers.length, 0)
  const achGot = families.reduce((a, f) => a + f.unlocked_count, 0)

  return (
    <div className="space-y-3">
      {/* ===== 个人信息 ===== */}
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
        <div className="mt-1 flex items-center justify-between text-[10px] text-slate-400">
          <span>每完成 1 个课时 +10 经验 · 累计 {character.total_exp}</span>
          {!studentId && (
            <button
              onClick={() => {
                setBindForm({ student_id: '', real_name: realName || '' })
                setBindOpen(true)
              }}
              className="text-indigo-600"
            >
              绑定学号
            </button>
          )}
        </div>
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

      {/* ===== 成就墙：一个家族一张卡，点开看铜银金三档 ===== */}
      <div className="game-panel p-3">
        <div className="flex items-center justify-between mb-2">
          <div className="text-[13px] font-semibold text-slate-700">
            🏅 成就墙
            <span className="text-[11px] font-normal text-slate-400 ml-1">
              {achGot}/{achTotal}
            </span>
          </div>
          <span className="text-[10px] text-slate-400">点开看三档</span>
        </div>
        <div className="grid grid-cols-2 gap-1.5">
          {families.map((f) => {
            const next = f.tiers.find((t) => !t.unlocked)
            return (
              <button
                key={f.key}
                onClick={() => setAchOpen(f)}
                data-ach={f.key}
                className={`rounded-xl border p-2 text-left transition-colors active:bg-slate-50 ${
                  f.unlocked_count === 3
                    ? 'border-amber-300 bg-amber-50'
                    : f.unlocked_count > 0
                      ? 'border-indigo-200 bg-white'
                      : 'border-slate-100 bg-slate-50'
                }`}
              >
                <div className="flex items-center gap-1">
                  <span className="text-[15px] leading-none">{f.icon}</span>
                  <span className="min-w-0 flex-1 truncate text-[11.5px] text-slate-700">
                    {f.name}
                  </span>
                  <TierDots fam={f} />
                </div>
                <div className="mt-1 flex items-baseline gap-1 text-[10px] text-slate-400">
                  <span>
                    {f.metric_label} {f.current}
                    {next ? `/${next.target}` : ' · 满级'}
                  </span>
                </div>
                <Progress
                  percent={
                    next ? Math.min(100, Math.round((f.current / next.target) * 100)) : 100
                  }
                  size="small"
                  showInfo={false}
                  strokeColor={f.unlocked_count === 3 ? '#f59e0b' : '#6366f1'}
                  trailColor="#e2e8f0"
                />
              </button>
            )
          })}
        </div>
      </div>

      {/* ===== 收藏 / 错题：两个入口按钮 ===== */}
      <div className="grid grid-cols-2 gap-2">
        <button
          onClick={() => navigate('/favorites')}
          className="game-panel flex items-center gap-2 p-3 text-left active:bg-slate-50"
        >
          <StarOutlined className="text-[18px] text-amber-500" />
          <div className="min-w-0 flex-1">
            <div className="text-[12.5px] font-medium text-slate-700">我的收藏</div>
            <div className="text-[10px] text-slate-400">{favCount} 道题</div>
          </div>
          <RightOutlined className="text-[9px] text-slate-300" />
        </button>
        <button
          onClick={() => navigate('/wrong')}
          className="game-panel flex items-center gap-2 p-3 text-left active:bg-slate-50"
        >
          <span className="text-[18px] leading-none">📕</span>
          <div className="min-w-0 flex-1">
            <div className="text-[12.5px] font-medium text-slate-700">错题记录</div>
            <div className="text-[10px] text-slate-400">{wrong_count} 道题</div>
          </div>
          <RightOutlined className="text-[9px] text-slate-300" />
        </button>
      </div>

      {/* ===== 资料编辑弹窗：只让改昵称和身份 ===== */}
      <Modal
        open={editOpen}
        title="编辑个人资料"
        okText="保存"
        cancelText="取消"
        confirmLoading={saving}
        onOk={saveProfile}
        onCancel={() => setEditOpen(false)}
        width={400}
      >
        <div className="space-y-3 pt-1">
          <div className="rounded-xl bg-slate-50 p-2.5">
            <div className="flex items-center gap-1 text-[11px] text-slate-400">
              <WarningOutlined />
              学号与姓名注册后不可修改
            </div>
            <div className="mt-1 grid grid-cols-2 gap-2 text-[12px]">
              <div>
                <div className="text-[10px] text-slate-400">学号</div>
                <div className="font-medium text-slate-700">{studentId || '未绑定'}</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-400">姓名</div>
                <div className="font-medium text-slate-700">{student?.real_name || realName}</div>
              </div>
            </div>
            {studentId && student?.grade && (
              <div className="mt-1 text-[10px] text-slate-400">
                {student.grade} 级 · 班级 {student.class_code} · {student.seat_no} 号
              </div>
            )}
          </div>
          <div>
            <div className="text-[12px] text-slate-500 mb-1">昵称</div>
            <Input
              maxLength={20}
              value={form.nickname}
              placeholder="显示在角色卡上的昵称"
              onChange={(e) => setForm({ ...form, nickname: e.target.value })}
            />
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

      {/* ===== 老账号首次绑定学号姓名 ===== */}
      <Modal
        open={bindOpen}
        title="绑定学号与姓名"
        okText="确认绑定"
        cancelText="取消"
        onOk={bindIdentity}
        onCancel={() => setBindOpen(false)}
        width={400}
      >
        <div className="space-y-3 pt-1">
          <div className="rounded-xl bg-amber-50 p-2.5 text-[11.5px] leading-relaxed text-amber-700">
            绑定后学号与姓名不可再修改，也会按学号进年级 / 班级排行榜。
          </div>
          <div>
            <div className="text-[12px] text-slate-500 mb-1">学号</div>
            <Input
              maxLength={11}
              inputMode="numeric"
              value={bindForm.student_id}
              placeholder="11 位学号"
              onChange={(e) =>
                setBindForm({
                  ...bindForm,
                  student_id: e.target.value.replace(/\D/g, '').slice(0, 11),
                })
              }
            />
          </div>
          <div>
            <div className="text-[12px] text-slate-500 mb-1">姓名</div>
            <Input
              maxLength={10}
              value={bindForm.real_name}
              placeholder="中文姓名"
              onChange={(e) => setBindForm({ ...bindForm, real_name: e.target.value })}
            />
          </div>
        </div>
      </Modal>

      {/* ===== 成就详情弹窗：铜 → 银 → 金 ===== */}
      <Modal
        open={!!achOpen}
        title={
          achOpen ? (
            <span className="text-[15px]">
              {achOpen.icon} {achOpen.name}
            </span>
          ) : (
            ''
          )
        }
        onCancel={() => setAchOpen(null)}
        footer={null}
        width={400}
      >
        {achOpen && (
          <div className="space-y-2 pt-1">
            <div className="text-[11.5px] text-slate-500">
              当前{achOpen.metric_label}：
              <b className="text-indigo-600">{achOpen.current}</b>
              {achOpen.next_target ? ` · 距下一档还差 ${Math.max(0, achOpen.next_target - achOpen.current)}` : ' · 已全部解锁'}
            </div>
            {achOpen.tiers.map((t) => (
              <div
                key={t.code}
                className={`rounded-xl border p-2.5 ${
                  t.unlocked ? 'border-amber-200 bg-amber-50' : 'border-slate-100 bg-slate-50'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className={`text-[16px] ${t.unlocked ? '' : 'opacity-30 grayscale'}`}>
                    {t.icon}
                  </span>
                  <span className="text-[12.5px] font-medium text-slate-700">
                    {t.tier} · {t.name}
                  </span>
                  <span className="ml-auto text-[11px] text-slate-400">
                    {t.unlocked ? '已解锁' : `目标 ${t.target}`}
                  </span>
                </div>
                <div className="mt-0.5 text-[11px] leading-relaxed text-slate-500">
                  {t.description}
                </div>
                <Progress
                  percent={Math.min(100, Math.round((achOpen.current / t.target) * 100))}
                  size="small"
                  showInfo={false}
                  strokeColor={t.unlocked ? '#f59e0b' : '#cbd5e1'}
                  trailColor="#e2e8f0"
                />
              </div>
            ))}
            <div className="text-center text-[10px] text-slate-400">
              三档按同一指标递进：铜 → 银 → 金
            </div>
          </div>
        )}
      </Modal>

      {/* ===== 退出登录 ===== */}
      <Button block danger onClick={askLogout} className="mb-2">
        退出登录
      </Button>
    </div>
  )
}
