# app.py
import streamlit as st
import sqlite3
from datetime import date

DB_FILE = "tasks.db"

# --- DB初期化 ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            deadline TEXT,
            priority TEXT,
            title TEXT,
            content TEXT,
            completed INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- タスク取得 ---
def get_tasks(selected_category):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if selected_category == "全て":
        c.execute("SELECT id, category, deadline, priority, title, content FROM tasks WHERE completed=0 ORDER BY deadline, priority DESC, title")
    else:
        c.execute("SELECT id, category, deadline, priority, title, content FROM tasks WHERE completed=0 AND category=? ORDER BY deadline, priority DESC, title", (selected_category,))
    rows = c.fetchall()
    conn.close()
    return rows

# --- タスク追加 ---
def add_task(category, deadline, priority, title, content, completed):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO tasks (category, deadline, priority, title, content, completed) VALUES (?, ?, ?, ?, ?, ?)",
              (category, deadline, priority, title, content, completed))
    conn.commit()
    conn.close()

# --- タスク更新 ---
def update_task(task_id, category, deadline, priority, title, content, completed):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE tasks SET category=?, deadline=?, priority=?, title=?, content=?, completed=? WHERE id=?",
              (category, deadline, priority, title, content, completed, task_id))
    conn.commit()
    conn.close()

# --- タスク削除 ---
def delete_task(task_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()

# --- UI ---
st.title("タスク管理アプリ (UI固め完全版)")

# 上段：カテゴリ選択
categories = ["全て", "仕事", "個人開発", "その他"]
selected_category = st.selectbox("カテゴリ選択", categories)

# 中段：タスク一覧
tasks = get_tasks(selected_category)
st.subheader("タスク一覧（完了済み非表示）")
task_table = []
for t in tasks:
    task_table.append(f"{t[1]} | {t[3]} | {t[2]} | {t[4]}")  # カテゴリ | 重要度 | 締切 | タイトル
st.text_area("一覧表示", value="\n".join(task_table), height=200, disabled=True)

# 下段：タスク追加・編集・削除フォーム
st.subheader("タスク追加／編集／削除")
with st.form("task_form"):
    task_id = st.number_input("編集・削除する場合はIDを入力（新規追加は空白）", min_value=0, step=1)
    category = st.selectbox("カテゴリ", ["仕事", "個人開発", "その他"])
    deadline = st.date_input("締切日", value=date.today())
    priority = st.selectbox("重要度", ["高", "中", "低"])
    title = st.text_input("タイトル")
    content = st.text_area("内容")
    completed = st.checkbox("完了")
    submit = st.form_submit_button("保存")

if submit:
    if task_id > 0:
        update_task(task_id, category, deadline.isoformat(), priority, title, content, int(completed))
        st.success("タスクを更新しました。")
    else:
        add_task(category, deadline.isoformat(), priority, title, content, int(completed))
        st.success("新規タスクを追加しました。")

# --- タスク削除 ---
with st.form("delete_form"):
    del_id = st.number_input("削除するタスクIDを入力", min_value=0, step=1)
    del_submit = st.form_submit_button("削除")
if del_submit and del_id > 0:
    delete_task(del_id)
    st.success("タスクを削除しました。")
