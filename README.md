# ChatBI - 自然语言员工数据查询 Agent

一个 AI Agent 作品：输入自然语言，自动查询员工数据并给出分析。

## 功能

- 自然语言 → SQL：用中文问问题，自动生成 SQL 查询员工表
- 图表展示：自动判断数据类型生成柱状图
- AI 分析：每次查询附带数据解读和建议
- 手机/电脑自适应：浏览器打开即用

## 技术栈

- **后端**: Python Flask + DeepSeek API
- **数据库**: MySQL (PyMySQL + pandas)
- **前端**: 纯 HTML/CSS/JS + Chart.js
- **Prompt Engineering**: Few-shot + 字段枚举 + 错误自愈

## 快速开始

1. 在 pp.py 中配置你的 MySQL 连接信息
2. 配置 DeepSeek API Key
3. 运行: python app.py
4. 浏览器打开 http://localhost:8080