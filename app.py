from flask import Flask, request, jsonify, render_template, Response
from openai import OpenAI
import pymysql
import pandas as pd
import traceback
import json
import os
from pathlib import Path

# 从 .env 文件加载配置
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

app = Flask(__name__)

# DeepSeek 配置（请填入你的 DeepSeek API Key）
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-your-key-here")
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# MySQL 配置（请修改为你自己的数据库连接）
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "your-password",
    "database": "my_ai",
    "charset": "utf8mb4"
}

# 表结构描述（供 LLM 生成 SQL 使用）
TABLE_SCHEMA = """
CREATE TABLE info_employee (
  工作地点 TEXT,
  工号 TEXT,
  姓名 TEXT,
  特长 TEXT,
  钉钉昵称 TEXT,
  入职日期 DATETIME,
  性别 TEXT,
  民族 TEXT,
  出生日期 DATETIME,
  招聘方式 TEXT,
  人员类别 TEXT,
  机构 TEXT,
  一级组织 TEXT,
  二级组织 TEXT,
  三级组织 TEXT,
  四级组织 TEXT,
  五级组织 TEXT,
  六级组织 TEXT,
  七级组织 TEXT,
  八级组织 TEXT,
  编码 BIGINT,
  部门 TEXT,
  岗位 TEXT,
  职位 TEXT,
  职级 TEXT,
  职等 TEXT,
  职务 TEXT,
  职务序列 TEXT,
  直接上级 TEXT,
  人员状态 TEXT,
  试用开始日期 DATETIME,
  试用期(月) DOUBLE,
  预计试用结束日期 DATETIME,
  实际试用结束日期 DATETIME,
  转正日期 DATETIME,
  最高学历 TEXT,
  毕业学校名称 TEXT,
  专业 TEXT,
  语种等级 TEXT,
  语种类别 TEXT,
  毕业时间 DATETIME,
  司龄 DOUBLE,
  工龄 DOUBLE,
  年龄 BIGINT
);
"""

SYSTEM_PROMPT_SQL = f"""你是一个 MySQL 数据分析专家。请根据用户的自然语言问题，生成对应的 SQL 查询语句。

数据库表结构：
{TABLE_SCHEMA}

【字段值参考】
- 性别: '男', '女'
- 职级: '职员层', '助理层', '专员层', '组长层', '主管层', '副经理层', '经理层', '总监层'
- 最高学历: '初中', '高中', '中技', '大专', '普通本科', '二本本科', '一本本科', '211本科', '985本科', '海外留学', '硕士研究生', '211硕士', '985硕士'
- 招聘方式: '社会招聘', '校园招聘', '内部竞聘', '内部推荐', '其他'
- 人员状态: '正式', '试用'
- 年龄范围: 2~47, 平均约28岁
- 用户说"部门"通常指"部门"字段，不要用 一级组织~八级组织 字段

【常见问题与对应 SQL 示例】
1. 问："男女各有多少人" → SELECT 性别, COUNT(*) AS 人数 FROM info_employee GROUP BY 性别 ORDER BY 人数 DESC
2. 问："各部门人数分布" → SELECT 部门, COUNT(*) AS 人数 FROM info_employee GROUP BY 部门 ORDER BY 人数 DESC
3. 问："平均年龄是多少" → SELECT AVG(年龄) AS 平均年龄 FROM info_employee
4. 问："30岁以上员工有哪些" → SELECT * FROM info_employee WHERE 年龄 > 30 ORDER BY 年龄
5. 问："各职级人数" → SELECT 职级, COUNT(*) AS 人数 FROM info_employee GROUP BY 职级 ORDER BY 人数 DESC
6. 问："本科学历的有多少人" → SELECT COUNT(*) AS 人数 FROM info_employee WHERE 最高学历 LIKE '%本科%'
7. 问："列出所有部门经理" → SELECT * FROM info_employee WHERE 岗位 LIKE '%经理%' OR 职位 LIKE '%经理%'
8. 问："最近入职的5个人" → SELECT 姓名, 部门, 岗位, 入职日期 FROM info_employee ORDER BY 入职日期 DESC LIMIT 5
9. 问："各学历层次人数" → SELECT 最高学历, COUNT(*) AS 人数 FROM info_employee GROUP BY 最高学历 ORDER BY 人数 DESC

规则：
1. 只返回纯 SQL 语句，不要任何解释、不要 markdown 代码块标记
2. SQL 必须以 SELECT 开头
3. 分组统计必须用 GROUP BY + ORDER BY
4. COUNT(*) 的别名用中文，如 AS 人数、AS 数量
5. 日期字段用 YEAR()、MONTH() 函数提取年份月份
6. 字符串模糊匹配用 LIKE
7. 涉及上下级关系用"直接上级"字段
8. 用户说"看所有""列全部"等用 SELECT *，不要限制 LIMIT
9. 年龄相关查询用"年龄"字段，司龄相关用"司龄"字段
10. 如果用户问得模糊，参照上面的示例做出合理推断
"""


def query_mysql(sql):
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
        return jsonify({"error": "请输入查询内容"}), 400

    history = data.get("history", [])

    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_SQL},
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
        sql = sql.replace("```sql", "").replace("```", "").strip()

        try:
            df = query_mysql(sql)
        except Exception as sql_err:
            fix_messages = messages.copy()
            fix_messages.append({"role": "assistant", "content": sql})
            fix_messages.append({"role": "user", "content": f"上面的 SQL 执行报错：{sql_err}\n请修正 SQL 语句，只返回修正后的 SQL。"})
            fix_resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=fix_messages,
                temperature=0.1,
                max_tokens=2000
            )
            sql = fix_resp.choices[0].message.content.strip()
            sql = sql.replace("```sql", "").replace("```", "").strip()
            df = query_mysql(sql)

        result_data = json.loads(df.to_json(orient="records", force_ascii=False))
        columns = list(df.columns)

        analysis_prompt = f"""用户的提问：{user_message}
生成的 SQL：{sql}
查询结果（前 50 行）：{df.head(50).to_string(index=False)}
总行数：{len(df)}"""

        analysis_resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个数据分析师。根据用户的提问、对应的SQL和数据结果，给出简洁的数据分析结论和建议。要求：用中文回答，指出关键数据特征，给出业务建议，控制在80字以内，直接说结论。"},
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
    app.run(host="0.0.0.0", port=8080, debug=True)
