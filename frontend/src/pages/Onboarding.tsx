import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, App, Steps, Segmented, Input } from 'antd'
import { motion } from 'framer-motion'
import { api } from '../api/client'
import { useAuth } from '../store/auth'
import type { ClassInfo, QuestQuestion } from '../types'

export default function Onboarding() {
  const [step, setStep] = useState(0)
  const [name, setName] = useState('')
  const [identity, setIdentity] = useState('在校学生')
  const [classes, setClasses] = useState<ClassInfo[]>([])
  const [classKey, setClassKey] = useState('backend')
  const [testQuestions, setTestQuestions] = useState<QuestQuestion[]>([])
  const [answers, setAnswers] = useState<number[]>([])
  const [submitting, setSubmitting] = useState(false)
  const { refreshMe } = useAuth()
  const { message } = App.useApp()
  const navigate = useNavigate()

  useEffect(() => {
    api.get<ClassInfo[]>('/api/user/classes').then((c) => {
      setClasses(c)
      if (c.length) setClassKey(c[1]?.key || c[0].key)
    })
    api
      .get<QuestQuestion[]>('/api/user/onboard-questions')
      .then((qs) => {
        setTestQuestions(qs)
        // 预填 -1：避免稀疏数组被序列化成 null 触发后端校验失败
        setAnswers(qs.map(() => -1))
      })
      .catch(() => message.warning('入门测试题加载失败，可直接跳过'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const next = () => {
    if (step === 0 && !name.trim()) {
      message.warning('给冒险者起个名字吧')
      return
    }
    setStep((s) => s + 1)
  }

  const finish = async () => {
    setSubmitting(true)
    try {
      await api.post('/api/user/onboard', {
        name: name.trim(),
        identity,
        class_key: classKey,
        answers,
      })
      await refreshMe()
      message.success('角色创建成功，冒险开始！')
      navigate('/')
    } catch (e) {
      message.error((e as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  const steps = [
    { title: '选择身份' },
    { title: '创建角色' },
    { title: '能力初测' },
  ]

  return (
    <div className="min-h-[80vh] flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="game-panel w-full max-w-2xl p-8"
      >
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-indigo-700">⚔️ 新手村 · 角色创建</h1>
          <p className="text-slate-500 text-sm mt-1">选择你的冒险之路，1 分钟完成引导</p>
        </div>
        <Steps current={step} items={steps} size="small" className="mb-8" />

        {step === 0 && (
          <div className="space-y-6">
            <div>
              <div className="text-sm text-slate-500 mb-2">你的身份是？</div>
              <Segmented
                block
                size="large"
                value={identity}
                onChange={(v) => setIdentity(v as string)}
                options={[
                  { label: '🎓 在校学生', value: '在校学生' },
                  { label: '💼 求职中', value: '求职中' },
                ]}
              />
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-2">冒险者昵称</div>
              <Input
                size="large"
                placeholder="例如：阿测、代码侠"
                value={name}
                onChange={(e) => setName(e.target.value)}
                maxLength={16}
              />
            </div>
          </div>
        )}

        {step === 1 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {classes.map((c) => (
              <button
                key={c.key}
                onClick={() => setClassKey(c.key)}
                className={`text-left p-4 rounded-2xl border transition-all ${
                  classKey === c.key
                    ? 'border-indigo-400 bg-indigo-50 shadow-lg'
                    : 'border-indigo-200 bg-slate-50 hover:border-indigo-400/60'
                }`}
              >
                <div className="text-2xl mb-1">{c.emoji}</div>
                <div className="font-medium text-indigo-700">{c.name}</div>
                <div className="text-[11px] text-slate-500 mt-1 leading-relaxed">{c.desc}</div>
                <div className="text-[11px] text-amber-600/80 mt-2">{c.stack.join(' · ')}</div>
              </button>
            ))}
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6">
            {testQuestions.map((q, i) => (
              <div key={q.question_id} className="p-4 rounded-2xl bg-slate-50 border border-indigo-100">
                <div className="text-xs text-slate-500 mb-1">入门测试 {i + 1}/3 · {q.subject}</div>
                <div className="text-sm text-slate-700 mb-3">{q.stem}</div>
                <div className="grid gap-2">
                  {q.options.map((opt, oi) => (
                    <button
                      key={oi}
                      onClick={() => {
                        const next = [...answers]
                        next[i] = oi
                        setAnswers(next)
                      }}
                      className={`text-left px-3 py-2 rounded-xl text-sm border transition-all ${
                        answers[i] === oi
                          ? 'border-indigo-400 bg-indigo-100 text-indigo-800'
                          : 'border-indigo-200 text-slate-600 hover:border-indigo-400/60'
                      }`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </div>
            ))}
            {testQuestions.length === 0 && (
              <div className="text-center text-slate-500 text-sm py-8">测试题加载中或不可用，可直接完成创建</div>
            )}
          </div>
        )}

        <div className="flex justify-between mt-8">
          {step > 0 ? (
            <Button onClick={() => setStep((s) => s - 1)}>上一步</Button>
          ) : (
            <span />
          )}
          {step < 2 ? (
            <Button type="primary" onClick={next}>下一步</Button>
          ) : (
            <Button type="primary" loading={submitting} onClick={finish}>
              完成创建 · 开始冒险
            </Button>
          )}
        </div>
      </motion.div>
    </div>
  )
}
