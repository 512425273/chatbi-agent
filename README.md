# ChatBI - Natural Language Employee Query Agent

An AI Agent project: input natural language, automatically query employee data and generate analysis.

## Features
- Natural Language to SQL: Ask questions in Chinese, auto-generate SQL queries
- Chart visualization: auto-detect data types and render bar charts
- AI analysis: data insights with each query
- Mobile/Desktop responsive: open in browser, no login required

## Tech Stack
- **Backend**: Python Flask + DeepSeek API
- **Database**: MySQL (via PyMySQL + pandas)
- **Frontend**: Pure HTML/CSS/JS + Chart.js
- **Prompt Engineering**: Few-shot + field enumeration + error self-healing

## Quick Start
1. Edit app.py with your MySQL connection and DeepSeek API Key
2. Run: python app.py
3. Open http://localhost:8080
