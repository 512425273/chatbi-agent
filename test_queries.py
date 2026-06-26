import requests, json, time

tests = [
    '男女各有多少人',
    '平均年龄多大',
    '各职级人数分布',
    '本科学历有多少人',
    '列出所有主管级以上的员工',
    '最近入职的5个人是谁',
    '按学历统计人数',
]

time.sleep(3)
for q in tests:
    try:
        r = requests.post('http://localhost:8080/api/query', json={'message': q, 'history': []}, timeout=30)
        result = r.json()
        if 'error' in result:
            print(f'FAIL [{q}]')
            print(f'  Error: {str(result.get("error",""))[:100]}')
        else:
            print(f'PASS [{q}]')
            print(f'  SQL: {result["sql"][:120]}')
            print(f'  Rows: {result["row_count"]}')
            if result.get('analysis'):
                print(f'  Analysis: {result["analysis"][:100]}')
    except Exception as e:
        print(f'CRASH [{q}]')
        print(f'  Exception: {str(e)[:80]}')
    print()
