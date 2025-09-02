# app.py
import streamlit as st
import sqlite3
from datetime import date

# -----------------------------
# DB初期化（UI固め用なので毎回リセット）
# -----------------------------
conn = sqlite3.connect("tasks.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    title TEXT,
    content TEXT,
    priority TEXT,
    deadline DATE,
    completed INTEGER DEFAULT 0
)
""")
conn.commit()

# -----------------------------
# ユーティリティ関数
# -----------------------------
def get_tasks(selected_category="全て"):
    if selected_category == "全て":
        c.execute("""
            SELECT id, category, deadline, title, content, priority 
            FROM tasks 
            WHERE completed=0 
            ORDER BY deadline, priority DESC, title
        """)
    else:
        c.execute("""
            SELECT id, category, deadline, title, content, priority 
            FROM tasks 
            WHERE completed=0 AND category=? 
            ORDER BY deadline, priority DESC, title
        """, (selected_category,))
    return c.fetchall()

def add_task(category, title, content, priority, deadline):
    c.execute("""
        INSERT INTO tasks (category, title, content, priority, deadline)
        VALUES (?, ?, ?, ?, ?)
    """, (category, title, content, priority, deadline))
    conn.commit()

def update_task(task_id, category, title, content, priority, deadline, completed):
    c.execute("""
        UPDATE tasks
        SET category=?, title=?, content=?, priority=?, deadline=?, completed=?
        WHERE id=?
    """, (category, title, content, priority, deadline, completed, task_id))
    conn.commit()

def delete_task(task_id):
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()

# -----------------------------
# 上段：カテゴリ選択
# -----------------------------
st.title("タスク管理（UI固め版）")
categories = ["全て", "仕事", "個人開発", "その他"]
selected_category = st.selectbox("カテゴリを選択", categories)

# -----------------------------
# 中段：タスク一覧
# -----------------------------
st.subheader("タスク一覧")
tasks = get_tasks(selected_category)

if tasks:
    task_titles = [f"{t[1]} | {t[2]} | {t[3]}" for t in tasks]  # カテゴリ | 締切日 | タイトル
    selected_index = st.selectbox("編集・削除したいタスクを選択", range(len(task_titles)), format_func=lambda x: task_titles[x])
    selected_task = tasks[selected_index]
else:
    st.write("未完了のタスクはありません")
    selected_task = None

# -----------------------------
# 下段：タスク追加／編集フォーム
# -----------------------------
st.subheader("タスク追加／編集")

if selected_task:
    # 選択タスクをフォームにロード
    task_id = selected_task[0]
    category = selected_task[1]
    deadline = selected_task[2]
    title = selected_task[3]
    content = selected_task[4]
    priority = selected_task[5]
    completed = 0
else:
    task_id = None
    category = "仕事"
    deadline = date.today().isoformat()
    title = ""
    content = ""
    priority = "中"
    completed = 0

with st.form(key="task_form"):
    category = st.selectbox("カテゴリ", ["仕事", "個人開発", "その他"], index=["仕事", "個人開発", "その他"].index(category))
    deadline = st.date_input("締切日", value=date.fromisoformat(deadline))
    priority = st.selectbox("重要度", ["高", "中", "低"], index=["高", "中", "低"].index(priority))
    title = st.text_input("タイトル", value=title)
    content = st.text_area("内容", value=content)
    completed = st.checkbox("完了", value=completed)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        submit_add = st.form_submit_button("新規追加")
    with col2:
        submit_update = st.form_submit_button("保存")
    with col3:
        submit_delete = st.form_submit_button("削除")

# -----------------------------
# ボタン処理
# -----------------------------
if submit_add:
    add_task(category, title, content, priority, deadline.isoformat())
    st.experimental_rerun()

if submit_update and selected_task:
    update_task(task_id, category, title, content, priority, deadline.isoformat(), completed)
    st.experimental_rerun()

if submit_delete and selected_task:
    delete_task(task_id)
    st.experimental_rerun()
