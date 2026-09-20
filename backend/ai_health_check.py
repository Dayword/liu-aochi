"""AI 功能自检：逐个验证走大模型的功能到底是「真模型」还是「静默降级」。

背景：这些功能都写了兜底，模型不可用时会**悄无声息**地退回内置规则，
界面上看不出区别（曾经因此漏掉了 TokenHub 402 额度耗尽的问题）。
所以这里用「兜底文案指纹」来反推真实状态。

用法：
    cd backend && python ai_health_check.py
    API_BASE=http://127.0.0.1:8001 python ai_health_check.py
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get('API_BASE', 'http://127.0.0.1:8001')
USERNAME = 'aicheck' + str(int(time.time()))
BUDGET = float(os.environ.get('AI_CHECK_BUDGET', 300))  # 总预算秒数，超了直接汇报

# 兜底文案指纹：命中任一条 = 这次是降级，不是真模型
FALLBACK_MARKERS = {
    'mentor': ['这个问题我先帮你拆解一下思路', '你好呀，我是你的 AI 导师',
               '**核心考点**：', '给你一份分阶段学习路径',
               '流程拆解如下', '给你一段可直接运行的示例代码', '想深入了解，可以追问'],
    'analysis': ['错因分析：这题更偏向', '错因分析：可能是'],
    'interview': ['回答偏简短，建议补充关键术语和具体例子。',
                  '覆盖了部分要点，但关键术语缺失。',
                  '回答结构完整，关键点覆盖良好。'],
}

RESULTS: list[tuple[str, str, float, str]] = []  # (功能, 结论, 耗时, 证据)
START = time.time()


def _left() -> float:
    return BUDGET - (time.time() - START)


def req(method, path, body=None, token=None, timeout=120):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header('Content-Type', 'application/json')
    if token:
        r.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())
    except Exception as e:
        return 0, {'detail': f'{type(e).__name__}: {e}'}


def sse_chat(token, mentor, message, timeout=120):
    body = json.dumps({'mentor': mentor, 'message': message}).encode()
    r = urllib.request.Request(BASE + '/api/chat/stream', data=body, method='POST')
    r.add_header('Content-Type', 'application/json')
    r.add_header('Authorization', 'Bearer ' + token)
    reply = []
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        for raw in resp:
            line = raw.decode('utf-8', 'ignore').strip()
            if not line.startswith('data:'):
                continue
            ev = json.loads(line[5:].strip())
            if ev.get('type') == 'reply':
                reply.append(ev['text'])
            elif ev.get('type') == 'error':
                raise RuntimeError(ev.get('message', 'SSE error'))
    return ''.join(reply)


def judge(kind: str, text: str) -> str:
    """按兜底指纹判定：命中 = 降级。"""
    for m in FALLBACK_MARKERS.get(kind, []):
        if m in text:
            return m
    return ''


def record(name: str, ok: bool | None, dt: float, evidence: str):
    verdict = '未完成(超预算)' if ok is None else ('真模型 OK' if ok else '降级/失败')
    RESULTS.append((name, verdict, dt, evidence))
    mark = '✅' if ok else ('⏰' if ok is None else '⚠️')
    print(f'{mark} {name:14s} {verdict:14s} {dt:6.1f}s  {evidence[:70]}')


def main():
    s, d = req('POST', '/api/auth/register',
               {'username': USERNAME, 'password': 'pass123456', 'nickname': 'AI自检'})
    if s != 200:
        print('注册失败，后端没起来？', s, d)
        return 2
    token = d['access_token']
    req('POST', '/api/user/onboard',
        {'name': '自检', 'identity': '求职中', 'class_key': 'backend', 'answers': [0, 1, 0]}, token)

    s, h = req('GET', '/api/health')
    model = '未知'
    try:  # 直接读 .env，报告里带上真实模型 ID（402 是按模型计的，这行很关键）
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from app.config import settings
        model = settings.AI_MODEL or '(空=离线模式)'
    except Exception:
        pass
    print(f'后端 ai_enabled={h.get("ai_enabled")}  AI_MODEL={model}\n')

    # 1 AI 导师对话（流式）
    t = time.time()
    try:
        reply = sse_chat(token, '老架构师', '什么是闭包？举一个实际用到的例子。')
        hit = judge('mentor', reply)
        record('AI导师对话', not hit, time.time() - t,
               ('降级指纹: ' + hit) if hit else ('正文 %d 字: %s' % (len(reply), reply[:40])))
    except Exception as e:
        record('AI导师对话', False, time.time() - t, f'{type(e).__name__}: {e}')

    # 2 AI 实时出题（Match3，注意前缀是 /api/games/match3）
    t = time.time()
    try:
        s, d = req('GET', '/api/games/match3/question?level_code=nvillage-1', token=token)
        src = d.get('source', '?')
        record('AI实时出题', s == 200 and src == 'ai', time.time() - t,
               f'HTTP{s} source={src} stem={str(d.get("stem"))[:34]}')
    except Exception as e:
        record('AI实时出题', False, time.time() - t, f'{type(e).__name__}: {e}')

    # 3 错题 AI 解析（故意答错）
    t = time.time()
    try:
        s, d = req('POST', '/api/quests/start', {'level_code': 'nvillage-1', 'mode': 'normal'}, token)
        run_id = d.get('run_id')
        s, q = req('GET', f'/api/quests/question/{run_id}', token=token)
        ans = -1 if q.get('type') == 'choice' else '肯定不对的答案'
        s, a = req('POST', '/api/quests/answer',
                   {'run_id': run_id, 'question_id': q['question_id'], 'answer': ans}, token)
        analysis = a.get('ai_analysis') or ''
        hit = judge('analysis', analysis)
        record('错题AI解析', bool(analysis) and not hit, time.time() - t,
               ('降级指纹: ' + hit) if hit else (analysis[:40] or '无 ai_analysis 字段'))
    except Exception as e:
        record('错题AI解析', False, time.time() - t, f'{type(e).__name__}: {e}')

    # 4 面试四维评分（一轮 3 题，答满才结算出分数与点评）
    t = time.time()
    try:
        s, d = req('POST', '/api/interview/start',
                   {'class_key': 'backend', 'company': '字节跳动', 'difficulty': 2}, token)
        sid = d.get('session_id')
        answer = ('我在实习中负责订单模块，用 Redis 分布式锁解决超卖：'
                  '先加锁再校验库存，QPS 从 200 提升到 1200，超卖归零。')
        sc = {}
        for _ in range(3):
            s, a = req('POST', '/api/interview/answer',
                       {'session_id': sid, 'answer': answer}, token)
            if a.get('round_finished'):
                sc = a.get('round_scores') or {}
                break
        comment = str(sc.get('点评', '')) + str(sc.get('建议', ''))
        hit = judge('interview', comment)
        record('面试四维评分', bool(sc) and not hit, time.time() - t,
               ('降级指纹: ' + hit) if hit else
               f'四维={ {k: v for k, v in sc.items() if k in ("技术准确性", "逻辑清晰度")} }')
    except Exception as e:
        record('面试四维评分', False, time.time() - t, f'{type(e).__name__}: {e}')

    # 5 课程「要点提示」
    t = time.time()
    try:
        s, pt = req('GET', '/api/learn/points/mysql-01', token=token)
        builtin = pt.get('hint') or ''
        s, d = req('POST', '/api/learn/hint',
                   {'code': 'mysql-01', 'user_code': 'SELECT 1;', 'reason': '结果不符合要求'}, token)
        hint = d.get('hint', '')
        is_builtin = bool(hint) and hint.strip() == builtin.strip()
        record('课程要点提示', bool(hint) and not is_builtin, time.time() - t,
               '与课程内置 hint 完全相同 → 降级' if is_builtin else hint[:50])
    except Exception as e:
        record('课程要点提示', False, time.time() - t, f'{type(e).__name__}: {e}')

    # 汇总
    print('\n' + '=' * 74)
    ok = sum(1 for _, v, _, _ in RESULTS if v == '真模型 OK')
    total = len(RESULTS)
    print(f'AI 功能自检：{ok}/{total} 走真模型   （总耗时 {time.time() - START:.1f}s / 预算 {BUDGET:.0f}s）')
    for name, verdict, dt, ev in RESULTS:
        if verdict != '真模型 OK':
            print(f'  ⚠️ {name} → {verdict}：{ev[:90]}')
    if ok != total:
        print('\n排查建议：')
        print('  1) 打印当前 .env 的 AI_MODEL，逐模型试 —— 402 是**按模型**计的，')
        print('     某些模型额度耗尽但其它模型仍是免费额度（本项目就遇到过）。')
        print('  2) 命令：python -c "from app.config import settings; print(settings.AI_MODEL)"')
    print('=' * 74)
    return 0 if ok == total else 1


if __name__ == '__main__':
    sys.exit(main())
