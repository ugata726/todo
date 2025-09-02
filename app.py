# app.py
import streamlit as st
import sqlite3
from datetime import datetime

DB_FILE = "tasks.db"

# DB初期化（UI固め用、毎回初期化可能）
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            title TEXT,
            content TEXT,
            priority TEXT,
            deadline TEXT,
            completed INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# DB接続
def get_tasks(selected_category):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if selected_category == "全て":
        c.execute("SELECT id, category, title, content, priority, deadline FROM tasks WHERE completed=0 ORDER BY deadline, priority DESC, title")
    else:
        c.execute("SELECT id, category, title, content, priority, deadline FROM tasks WHERE completed=0 AND category=? ORDER BY deadline, priority DESC, title", (selected_category,))
    tasks = c.fetchall()
    conn.close()
    return tasks

# タスク追加
def add_task(category, title, content, priority, deadline):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO tasks (category, title, content, priority, deadline) VALUES (?, ?, ?, ?, ?)",
              (category, title, content, priority, deadline))
    conn.commit()
    conn.close()

# タスク更新
def update_task(task_id, category, title, content, priority, deadline, completed):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""UPDATE tasks SET category=?, title=?, content=?, priority=?, deadline=?, completed=?
                 WHERE id=?""",
              (category, title, content, priority, deadline, completed, task_id))
    conn.commit()
    conn.close()

# タスク削除
def delete_task(task_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()

# --- UI ---
st.title("タスク管理")

# 上段：カテゴリ選択
categories = ["全て", "仕事", "個人開発", "その他"]
selected_category = st.selectbox("カテゴリ選択", categories)

# 中段：タスク一覧
tasks = get_tasks(selected_category)
st.subheader("タスク一覧")
for t in tasks:
    task_id, category, title, content, priority, deadline = t
    st.write(f"**{title}** | {category} | {priority} | {deadline}")
    if st.button(f"編集: {title}", key=f"edit_{task_id}"):
        st.session_state["edit_task"] = t
    if st.button(f"削除: {title}", key=f"del_{task_id}"):
        delete_task(task_id)
        st.experimental_rerun()

# 下段：タスク追加・編集フォーム
st.subheader("タスク追加／編集")
if "edit_task" in st.session_state:
    task = st.session_state["edit_task"]
    task_id, category, title, content, priority, deadline = task
else:
    task_id, category, title, content, priority, deadline = None, "仕事", "", "", "中", datetime.today().strftime("%Y-%m-%d")

with st.form(key="task_form"):
    category = st.selectbox("カテゴリ", ["仕事", "個人開発", "その他"], index=["仕事", "個人開発", "その他"].index(category))
    title = st.text_input("タイトル", value=title)
    content = st.text_area("内容", value=content)
    priority = st.selectbox("重要度", ["高", "中", "低"], index=["高","中","低"].index(priority))
    deadline = st.date_input("締切日", value=datetime.strptime(deadline, "%Y-%m-%d"))
    completed = st.checkbox("完了", value=False)
    submit_btn = st.form_submit_button("保存")

if submit_btn:
    if task_id is None:
        add_task(category, title, content, priority, deadline.strftime("%Y-%m-%d"))
    else:
        update_task(task_id, category, title, content, priority, deadline.strftime("%Y-%m-%d"), int(completed))
        del st.session_state["edit_task"]
    st.experimental_rerun()
