import json
import time
import urllib.request

BASE = 'http://127.0.0.1:8000'
USERNAME = 'tester' + str(int(time.time()))


def req(method, path, body=None, token=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header('Content-Type', 'application/json')
    if token:
        r.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def sse_chat(token, mentor, message):
    """调用流式对话接口，返回 (回复正文, 题目列表, 知识点总结)。"""
    body = json.dumps({'mentor': mentor, 'message': message}).encode()
    r = urllib.request.Request(BASE + '/api/chat/stream', data=body, method='POST')
    r.add_header('Content-Type', 'application/json')
    r.add_header('Authorization', 'Bearer ' + token)
    reply, quiz, summary = [], [], ''
    with urllib.request.urlopen(r, timeout=90) as resp:
        for raw in resp:
            line = raw.decode('utf-8', 'ignore').strip()
            if not line.startswith('data:'):
                continue
            ev = json.loads(line[5:].strip())
            if ev['type'] == 'reply':
                reply.append(ev['text'])
            elif ev['type'] == 'done':
                quiz, summary = ev['quiz'], ev['summary']
    return ''.join(reply), quiz, summary


def main():
    s, d = req('POST', '/api/auth/register',
               {'username': USERNAME, 'password': 'pass123456', 'nickname': '测试勇者'})
    print('1 register:', s, d.get('access_token', '')[:20])
    token = d['access_token']

    s, d = req('POST', '/api/user/onboard',
               {'name': '阿测', 'identity': '求职中', 'class_key': 'backend', 'answers': [0, 1, 0]}, token)
    print('2 onboard:', s, d.get('class_name'), 'Lv', d.get('level'), 'title', d.get('title'))

    s, d = req('GET', '/api/levels/map', token=token)
    print('3 level map:', s, 'levels:', len(d['levels']), 'scenes:', len(d['scenes']),
          'first:', d['levels'][0]['code'], d['levels'][0]['status'])

    s, d = req('POST', '/api/quests/start', {'level_code': 'nvillage-1', 'mode': 'normal'}, token)
    run_id = d.get('run_id')
    print('4 quest start:', s, 'run', run_id, 'total', d.get('total'), 'hp', d.get('hp'))

    for i in range(3):
        s, q = req('GET', f'/api/quests/question/{run_id}', token=token)
        if s != 200:
            print('   question err:', s, q)
            break
        ans = 0 if q['type'] == 'choice' else 'x'
        s, a = req('POST', '/api/quests/answer',
                   {'run_id': run_id, 'question_id': q['question_id'], 'answer': ans}, token)
        print(f"   Q{q['index']}: type={q['type']} correct={a.get('correct')} hp={a.get('hp_left')}")

    reply, quiz, summary = sse_chat(token, '老架构师', '什么是闭包？举例子')
    print('6 chat(stream):', reply[:40], '| 配套题目', len(quiz), '| 总结', summary[:20])

    s, d = req('POST', '/api/interview/start', {'class_key': 'backend', 'company': '字节跳动', 'difficulty': 2}, token)
    sid = d.get('session_id')
    print('7 interview:', s, 'sid', sid, 'Q:', d.get('question', '')[:30])

    s, d = req('GET', '/api/bugs/challenges', token=token)
    print('8 bugs:', s, 'count', len(d))

    s, d = req('POST', '/api/code/run', {'language': 'python', 'code': 'print(1+1)'}, token)
    print('9 code run:', s, d.get('stdout'))

    s, d = req('GET', '/api/growth/leaderboard?board=total', token=token)
    print('10 leaderboard:', s, len(d))

    # Bug submit full round
    s, d = req('POST', '/api/bugs/submit',
               {'bug_code': 'bug-01',
                'code': "def greet(name):\n    return 'Hello, ' + name\n\nprint(greet('Code'))"}, token)
    print('11 bug submit:', s, 'score', d.get('score'), 'passed', d.get('passed'),
          'acc', d.get('accuracy'))

    # Interview full flow (round 1 answer)
    s, d = req('POST', '/api/interview/answer',
               {'session_id': sid, 'answer': '我来自某大学计算机专业，技术栈是 Java 和 Spring，做过一个电商项目，负责订单模块的开发，实现了分布式锁防止超卖，最终接口性能提升了 50%。'}, token)
    print('12 interview answer:', s, 'round_finished', d.get('round_finished'),
          'next:', d.get('next_question', '')[:25])

    # Complete interview loop
    turns = 0
    while turns < 20:
        s, d = req('POST', '/api/interview/answer',
                   {'session_id': sid, 'answer': '这个问题我从背景、任务、行动和结果四个方面回答。我负责核心模块开发，使用合理的技术方案解决了问题，最终取得了可量化的成果。'}, token)
        turns += 1
        if s != 200:
            print('   interview loop err:', s, d)
            break
        if d.get('interview_finished'):
            print('   interview FINISHED round', d.get('round_no'), 'grade', d.get('report', {}).get('grade'),
                  'overall', d.get('report', {}).get('overall'))
            break
        if d.get('round_finished'):
            print(f"   round {d.get('round_no')} finished, scores:", d.get('round_scores', {}).get('平均分'))
    print('12b interview loop turns:', turns)

    # Profile
    s, d = req('GET', '/api/user/profile', token=token)
    print('13 profile:', s, 'char', d.get('character', {}).get('class_name'),
          'achievements', len(d.get('achievements', [])),
          'radar', d.get('radar', {}).get('subjects'))


if __name__ == '__main__':
    main()
