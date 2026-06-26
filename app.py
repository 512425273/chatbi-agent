from flask import Flask, request, jsonify, render_template, Response
from openai import OpenAI
import pymysql
import pandas as pd
import traceback
import json

app = Flask(__name__)

# DeepSeek 閰嶇疆锛堜粠鐜鍙橀噺璇诲彇锛屼笉涓婁紶鍒?GitHub锛?import os
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    raise ValueError("璇疯缃幆澧冨彉閲?DEEPSEEK_API_KEY锛屾垨鍦ㄤ唬鐮佷腑鐩存帴濉叆浣犵殑 Key")
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# MySQL 閰嶇疆
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "MyAi@2024!Secure",
    "database": "my_ai",
    "charset": "utf8mb4"
}

# 琛ㄧ粨鏋勬弿杩帮紙渚?LLM 鐢熸垚 SQL 浣跨敤锛?TABLE_SCHEMA = """
CREATE TABLE info_employee (
  宸ヤ綔鍦扮偣 TEXT,
  宸ュ彿 TEXT,
  濮撳悕 TEXT,
  鐗归暱 TEXT,
  閽夐拤鏄电О TEXT,
  鍏ヨ亴鏃ユ湡 DATETIME,
  鎬у埆 TEXT,
  姘戞棌 TEXT,
  鍑虹敓鏃ユ湡 DATETIME,
  鎷涜仒鏂瑰紡 TEXT,
  浜哄憳绫诲埆 TEXT,
  鏈烘瀯 TEXT,
  涓€绾х粍缁?TEXT,
  浜岀骇缁勭粐 TEXT,
  涓夌骇缁勭粐 TEXT,
  鍥涚骇缁勭粐 TEXT,
  浜旂骇缁勭粐 TEXT,
  鍏骇缁勭粐 TEXT,
  涓冪骇缁勭粐 TEXT,
  鍏骇缁勭粐 TEXT,
  缂栫爜 BIGINT,
  閮ㄩ棬 TEXT,
  宀椾綅 TEXT,
  鑱屼綅 TEXT,
  鑱岀骇 TEXT,
  鑱岀瓑 TEXT,
  鑱屽姟 TEXT,
  鑱屽姟搴忓垪 TEXT,
  鐩存帴涓婄骇 TEXT,
  浜哄憳鐘舵€?TEXT,
  璇曠敤寮€濮嬫棩鏈?DATETIME,
  璇曠敤鏈?鏈? DOUBLE,
  棰勮璇曠敤缁撴潫鏃ユ湡 DATETIME,
  瀹為檯璇曠敤缁撴潫鏃ユ湡 DATETIME,
  杞鏃ユ湡 DATETIME,
  鏈€楂樺鍘?TEXT,
  姣曚笟瀛︽牎鍚嶇О TEXT,
  涓撲笟 TEXT,
  璇绛夌骇 TEXT,
  璇绫诲埆 TEXT,
  姣曚笟鏃堕棿 DATETIME,
  鍙搁緞 DOUBLE,
  宸ラ緞 DOUBLE,
  骞撮緞 BIGINT
);
"""

SYSTEM_PROMPT_SQL = f"""浣犳槸涓€涓?MySQL 鏁版嵁鍒嗘瀽涓撳銆傝鏍规嵁鐢ㄦ埛鐨勮嚜鐒惰瑷€闂锛岀敓鎴愬搴旂殑 SQL 鏌ヨ璇彞銆?
鏁版嵁搴撹〃缁撴瀯锛?{TABLE_SCHEMA}

銆愬瓧娈靛€煎弬鑰冦€?- 鎬у埆: '鐢?, '濂?
- 鑱岀骇: '鑱屽憳灞?, '鍔╃悊灞?, '涓撳憳灞?, '缁勯暱灞?, '涓荤灞?, '鍓粡鐞嗗眰', '缁忕悊灞?, '鎬荤洃灞?
- 鏈€楂樺鍘? '鍒濅腑', '楂樹腑', '涓妧', '澶т笓', '鏅€氭湰绉?, '浜屾湰鏈', '涓€鏈湰绉?, '211鏈', '985鏈', '娴峰鐣欏', '纭曞＋鐮旂┒鐢?, '211纭曞＋', '985纭曞＋'
- 鎷涜仒鏂瑰紡: '绀句細鎷涜仒', '鏍″洯鎷涜仒', '鍐呴儴鎷涜仒', '鍐呴儴鎷涜仒', '鍐呴儴鎷涜仒', '鍏朵粬'
- 浜哄憳鐘舵€? '姝ｅ紡', '璇曠敤'
- 宀椾綅: 鍖呭惈 '杩愯惀', '涓撳憳', '璁捐甯?, '宸ョ▼甯?, '涓荤', '缁忕悊', '缁勯暱', '鍔╃悊', 'HRBP' 绛夊叧閿瘝
- 骞撮緞鑼冨洿: 2~47, 骞冲潎绾?8宀?- 浜哄憳绫诲埆: 澶ч儴鍒嗕负 NULL, 灏戞暟涓?'瑙佷範杩愯惀(鍚岃)'
- 鐢ㄦ埛璇?閮ㄩ棬"閫氬父鎸?閮ㄩ棬"瀛楁锛屼笉瑕佺敤 涓€绾х粍缁噡鍏骇缁勭粐 瀛楁

銆愬父瑙侀棶棰樹笌瀵瑰簲 SQL 绀轰緥銆?1. 闂細"鐢峰コ鍚勬湁澶氬皯浜? 鈫?SELECT 鎬у埆, COUNT(*) AS 浜烘暟 FROM info_employee GROUP BY 鎬у埆 ORDER BY 浜烘暟 DESC
2. 闂細"鍚勯儴闂ㄤ汉鏁板垎甯? 鈫?SELECT 閮ㄩ棬, COUNT(*) AS 浜烘暟 FROM info_employee GROUP BY 閮ㄩ棬 ORDER BY 浜烘暟 DESC
3. 闂細"骞冲潎骞撮緞鏄灏? 鈫?SELECT AVG(骞撮緞) AS 骞冲潎骞撮緞 FROM info_employee
4. 闂細"30宀佷互涓婂憳宸ユ湁鍝簺" 鈫?SELECT * FROM info_employee WHERE 骞撮緞 > 30 ORDER BY 骞撮緞
5. 闂細"鍚勮亴绾т汉鏁? 鈫?SELECT 鑱岀骇, COUNT(*) AS 浜烘暟 FROM info_employee GROUP BY 鑱岀骇 ORDER BY 浜烘暟 DESC
6. 闂細"鏈瀛﹀巻鐨勬湁澶氬皯浜? 鈫?SELECT COUNT(*) AS 浜烘暟 FROM info_employee WHERE 鏈€楂樺鍘?LIKE '%鏈%'
7. 闂細"鍒楀嚭鎵€鏈夐儴闂ㄧ粡鐞? 鈫?SELECT * FROM info_employee WHERE 宀椾綅 LIKE '%缁忕悊%' OR 鑱屼綅 LIKE '%缁忕悊%'
8. 闂細"鏈€杩戝叆鑱岀殑5涓汉" 鈫?SELECT 濮撳悕, 閮ㄩ棬, 宀椾綅, 鍏ヨ亴鏃ユ湡 FROM info_employee ORDER BY 鍏ヨ亴鏃ユ湡 DESC LIMIT 5
9. 闂細"鍚勫鍘嗗眰娆′汉鏁? 鈫?SELECT 鏈€楂樺鍘? COUNT(*) AS 浜烘暟 FROM info_employee GROUP BY 鏈€楂樺鍘?ORDER BY 浜烘暟 DESC

瑙勫垯锛?1. 鍙繑鍥炵函 SQL 璇彞锛屼笉瑕佷换浣曡В閲娿€佷笉瑕?markdown 浠ｇ爜鍧楁爣璁?2. SQL 蹇呴』浠?SELECT 寮€澶?3. 鍒嗙粍缁熻蹇呴』鐢?GROUP BY + ORDER BY
4. COUNT(*) 鐨勫埆鍚嶇敤涓枃锛屽 AS 浜烘暟銆丄S 鏁伴噺
5. 鏃ユ湡瀛楁鐢?YEAR()銆丮ONTH() 鍑芥暟鎻愬彇骞翠唤鏈堜唤
6. 瀛楃涓叉ā绯婂尮閰嶇敤 LIKE
7. 娑夊強涓婁笅绾у叧绯荤敤"鐩存帴涓婄骇"瀛楁
8. 鐢ㄦ埛璇?鐪嬫墍鏈?"鍒楀叏閮?绛夌敤 SELECT *锛屼笉瑕侀檺鍒?LIMIT
9. 骞撮緞鐩稿叧鏌ヨ鐢?骞撮緞"瀛楁锛屽徃榫勭浉鍏崇敤"鍙搁緞"瀛楁
10. 濡傛灉鐢ㄦ埛闂緱妯＄硦锛屽弬鐓т笂闈㈢殑绀轰緥鍋氬嚭鍚堢悊鎺ㄦ柇
"""

SYSTEM_PROMPT_ANALYSIS = """浣犳槸涓€涓暟鎹垎鏋愬笀銆傛牴鎹敤鎴风殑鎻愰棶銆佸搴旂殑SQL鍜屾暟鎹粨鏋滐紝缁欏嚭绠€娲佺殑鏁版嵁鍒嗘瀽缁撹鍜屽缓璁€?
瑕佹眰锛?- 鐢ㄤ腑鏂囧洖绛旓紝鑷劧鏄撴噦
- 鎸囧嚭鍏抽敭鏁版嵁鐗瑰緛锛堟渶澶у€笺€佹渶灏忓€笺€佸垎甯冭秼鍔跨瓑锛?- 缁欏嚭涓氬姟寤鸿锛堝浜哄憳缁撴瀯浼樺寲銆佹嫑鑱樻柟鍚戠瓑锛?- 鎺у埗鍦?80 瀛椾互鍐?- 涓嶈璇?鏍规嵁鏁版嵁""鏁版嵁鏄剧ず"杩欑搴熻瘽锛岀洿鎺ヨ缁撹"""


def query_mysql(sql):
    """鎵ц SQL 骞惰繑鍥?DataFrame"""
    conn = pymysql.connect(**DB_CONFIG)
    try:
        df = pd.read_sql(sql, conn)
        return df
    finally:
        conn.close()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/query", methods=["POST"])
def handle_query():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "璇疯緭鍏ユ煡璇㈠唴瀹?}), 400

    # 璁板綍瀵硅瘽涓婁笅鏂囷紙鏈€杩?3 杞級
    history = data.get("history", [])

    try:
        # ===== 绗?姝ワ細LLM 鐢熸垚 SQL =====
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_SQL + '\n\n娉ㄦ剰锛氬鏋滅敤鎴锋彁鍒?涓婁竴杞?"涔嬪墠""鍒氭墠"绛変笂涓嬫枃锛岃缁撳悎鍘嗗彶瀵硅瘽鐞嗚В銆?},
        ]
        for h in history[-3:]:
            messages.append({"role": "user" if h["role"] == "user" else "assistant", "content": h["content"]})
        messages.append({"role": "user", "content": user_message})

        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.1,
            max_tokens=2000
        )
        sql = resp.choices[0].message.content.strip()
        # 娓呯悊鍙兘鐨?markdown 鏍囪
        sql = sql.replace("```sql", "").replace("```", "").strip()

        # ===== 绗?姝ワ細鎵ц SQL锛堝け璐ユ椂閲嶈瘯涓€娆★級=====
        try:
            df = query_mysql(sql)
        except Exception as sql_err:
            # 璁?LLM 鏍规嵁鎶ラ敊閲嶆柊鐢熸垚 SQL
            fix_messages = messages.copy()
            fix_messages.append({"role": "assistant", "content": sql})
            fix_messages.append({"role": "user", "content": f"涓婇潰鐨?SQL 鎵ц鎶ラ敊锛歿sql_err}\n璇蜂慨姝?SQL 璇彞锛屽彧杩斿洖淇鍚庣殑 SQL銆?})
            fix_resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=fix_messages,
                temperature=0.1,
                max_tokens=2000
            )
            sql = fix_resp.choices[0].message.content.strip()
            sql = sql.replace("```sql", "").replace("```", "").strip()
            df = query_mysql(sql)
        # 澶勭悊 NaN/NaT 鍊硷紝纭繚 JSON 搴忓垪鍖栦笉鎶ラ敊
        result_data = json.loads(df.to_json(orient="records", force_ascii=False))
        columns = list(df.columns)

        # ===== 绗?姝ワ細LLM 鍒嗘瀽缁撴灉 =====
        analysis_prompt = f"""鐢ㄦ埛鐨勬彁闂細{user_message}
鐢熸垚鐨?SQL锛歿sql}
鏌ヨ缁撴灉锛堝墠 50 琛岋級锛歿df.head(50).to_string(index=False)}
鎬昏鏁帮細{len(df)}"""

        analysis_resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_ANALYSIS},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        analysis = analysis_resp.choices[0].message.content.strip()

        return jsonify({
            "sql": sql,
            "columns": columns,
            "data": result_data,
            "row_count": len(df),
            "analysis": analysis
        })

    except Exception as e:
        return jsonify({"error": str(e), "detail": traceback.format_exc()}), 500


if __name__ == "__main__":
    print("=" * 50)
    print("  鍛樺伐鏁版嵁 AI 鏌ヨ绯荤粺")
    print("  鍚姩鍦板潃: http://localhost:8080")
    print("  LAN 璁块棶: http://<浣犵殑IP>:8080")
    print("=" * 50)
    app.run(host="0.0.0.0", port=8080, debug=True)
