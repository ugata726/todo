import streamlit as st
import sqlite3
from datetime import date

DB_PATH = "tasks.db"

# -------------------
# DB 初期化
# -------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 既存テーブルを削除
    c.execute("DROP TABLE IF EXISTS tasks")
    # 新規作成
    c.execute("""
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            deadline DATE NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            priority TEXT DEFAULT '中',
            completed INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# -------------------
# タスク取得
# -------------------
def get_tasks(selected_category):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
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
    tasks = c.fetchall()
    conn.close()
    return tasks

# -------------------
# タスク追加
# -------------------
def add_task(category, deadline, title, content, priority):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO tasks (category, deadline, title, content, priority)
        VALUES (?, ?, ?, ?, ?)
    """, (category, deadline, title, content, priority))
    conn.commit()
    conn.close()

# -------------------
# タスク更新
# -------------------
def update_task(task_id, category, deadline, title, content, priority, completed):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE tasks 
        SET category=?, deadline=?, title=?, content=?, priority=?, completed=? 
        WHERE id=?
    """, (category, deadline, title, content, priority, completed, task_id))
    conn.commit()
    conn.close()

# -------------------
# タスク削除
# -------------------
def delete_task(task_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()

# -------------------
# 初期化実行
# -------------------
init_db()

# -------------------
# Streamlit UI
# -------------------
st.title("タスク管理（UI確認用）")

# 上段：カテゴリ選択
categories = ["全て", "仕事", "個人開発", "その他"]
selected_category = st.selectbox("カテゴリ選択", categories)

# 中段：タスク一覧
st.subheader("タスク一覧")
tasks = get_tasks(selected_category)
if tasks:
    for t in tasks:
        st.write(f"{t[2]} | {t[3]} ({t[5]})")  # 締切日 | タイトル (優先度)
else:
    st.write("タスクはありません。")

# 下段：タスク追加・編集フォーム
st.subheader("タスク追加 / 編集")

# 新規タスク入力
with st.form("task_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        new_category = st.selectbox("カテゴリ", ["仕事", "個人開発", "その他"])
        new_deadline = st.date_input("締切日", date.today())
        new_priority = st.selectbox("重要度", ["高", "中", "低"])
    with col2:
        new_title = st.text_input("タイトル")
        new_content = st.text_area("内容")
    submitted = st.form_submit_button("追加")
    if submitted:
        add_task(new_category, new_deadline, new_title, new_content, new_priority)
        st.experimental_rerun()

# 選択タスクの編集・削除
if tasks:
    task_titles = [f"{t[2]} | {t[3]} ({t[5]})" for t in tasks]
    selected_index = st.selectbox("編集するタスクを選択", range(len(tasks)), format_func=lambda x: task_titles[x])
    selected_task = tasks[selected_index]

    with st.form("edit_form"):
        edit_category = st.selectbox("カテゴリ", ["仕事", "個人開発", "その他"], index=categories.index(selected_task[1]) - 1)
        edit_deadline = st.date_input("締切日", selected_task[2])
        edit_priority = st.selectbox("重要度", ["高", "中", "低"], index=["高","中","低"].index(selected_task[5]))
        edit_title = st.text_input("タイトル", selected_task[3])
        edit_content = st.text_area("内容", selected_task[4])
        edit_completed = st.checkbox("完了済み", value=False)
        save_btn = st.form_submit_button("保存")
        delete_btn = st.form_submit_button("削除")

        if save_btn:
            update_task(selected_task[0], edit_category, edit_deadline, edit_title, edit_content, edit_priority, int(edit_completed))
            st.experimental_rerun()
        if delete_btn:
            delete_task(selected_task[0])
            st.experimental_rerun()
