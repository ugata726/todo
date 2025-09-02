# app.py
import streamlit as st
import sqlite3
from datetime import date

DB_FILE = "tasks.db"

# --- DB 初期化 ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            deadline DATE NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            priority TEXT CHECK(priority IN ('低', '中', '高')) DEFAULT '中',
            completed INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# --- DB 操作 ---
def get_tasks(category):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if category == "全て":
        c.execute("SELECT id, category, deadline, title, content, priority FROM tasks WHERE completed=0 ORDER BY deadline, priority DESC, title")
    else:
        c.execute("SELECT id, category, deadline, title, content, priority FROM tasks WHERE completed=0 AND category=? ORDER BY deadline, priority DESC, title", (category,))
    tasks = c.fetchall()
    conn.close()
    return tasks

def add_task(category, deadline, title, content, priority):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO tasks (category, deadline, title, content, priority, completed) VALUES (?, ?, ?, ?, ?, 0)",
        (category, deadline, title, content, priority)
    )
    conn.commit()
    conn.close()

def update_task(task_id, category, deadline, title, content, priority, completed):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "UPDATE tasks SET category=?, deadline=?, title=?, content=?, priority=?, completed=? WHERE id=?",
        (category, deadline, title, content, priority, completed, task_id)
    )
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()

# --- 初期化 ---
init_db()
st.title("タスク管理アプリ")

# --- 上段：カテゴリ選択 ---
st.subheader("カテゴリ選択")
category_options = ["全て", "仕事", "個人開発", "その他"]
selected_category = st.radio("カテゴリを選択してください", category_options, horizontal=True)

# --- 中段：タスク一覧 ---
st.subheader("タスク一覧")
tasks = get_tasks(selected_category)

if tasks:
    selected_task = st.radio(
        "タスクを選択してください",
        options=tasks,
        format_func=lambda x: f"[{x[2]}] {x[3]}（{x[1]}・重要度:{x[5]}）",
        key="task_list"
    )
else:
    selected_task = None
    st.info("タスクがありません。")

# --- 下段：追加・編集フォーム ---
st.subheader("タスク追加 / 編集 / 削除")
with st.form("task_form"):
    if selected_task:
        task_id, category, deadline, title, content, priority = selected_task
        category_val = st.selectbox("カテゴリ", category_options[1:], index=category_options[1:].index(category))
        deadline_val = st.date_input("締切日", date.fromisoformat(deadline))
        title_val = st.text_input("タイトル", title)
        content_val = st.text_area("内容", content if content else "")
        priority_val = st.selectbox("重要度", ["低", "中", "高"], index=["低", "中", "高"].index(priority))
        completed_val = st.checkbox("完了", value=False)
    else:
        task_id = None
        category_val = st.selectbox("カテゴリ", category_options[1:])
        deadline_val = st.date_input("締切日", date.today())
        title_val = st.text_input("タイトル")
        content_val = st.text_area("内容")
        priority_val = st.selectbox("重要度", ["低", "中", "高"], index=1)
        completed_val = st.checkbox("完了", value=False)

    submitted = st.form_submit_button("保存")
    deleted = st.form_submit_button("削除")

    if submitted:
        if task_id:
            update_task(task_id, category_val, deadline_val.isoformat(), title_val, content_val, priority_val, int(completed_val))
            st.success("タスクを更新しました。")
        else:
            add_task(category_val, deadline_val.isoformat(), title_val, content_val, priority_val)
            st.success("タスクを追加しました。")
        st.rerun()

    if deleted and task_id:
        delete_task(task_id)
        st.success("タスクを削除しました。")
        st.rerun()
