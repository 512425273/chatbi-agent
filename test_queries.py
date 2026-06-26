import requests, json, time

tests = [
    '鐢峰コ鍚勬湁澶氬皯浜?,
    '骞冲潎骞撮緞澶氬ぇ',
    '鍚勮亴绾т汉鏁板垎甯?,
    '鏈瀛﹀巻鏈夊灏戜汉',
    '鍒楀嚭鎵€鏈変富绠＄骇浠ヤ笂鐨勫憳宸?,
    '鏈€杩戝叆鑱岀殑5涓汉鏄皝',
    '鎸夊鍘嗙粺璁′汉鏁?,
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
