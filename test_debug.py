import requests, json

r = requests.post('http://localhost:8080/api/query', json={'message': '列出所有主管级以上的员工', 'history': []}, timeout=30)
result = r.json()
if 'error' in result:
    print('Error:', result['error'])
    if 'detail' in result:
        print('Detail preview:', result['detail'][:300])
else:
    print('SQL:', result['sql'])
    print('Columns:', result['columns'])
    print('Rows:', result['row_count'])
    print('First row:', json.dumps(result['data'][0], ensure_ascii=False) if result['data'] else 'empty')
