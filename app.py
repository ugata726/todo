import streamlit as st
import sqlite3
from datetime import date

# --- DB 初期化 ---
def init_db():
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            deadline DATE NOT NULL,
            completed INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_tasks(category=None):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    if category and category != "全て":
        c.execute("SELECT id, category, deadline, title FROM tasks WHERE category=? AND completed=0 ORDER BY deadline, title", (category,))
    else:
        c.execute("SELECT id, category, deadline, title FROM tasks WHERE completed=0 ORDER BY deadline, title")
    rows = c.fetchall()
    conn.close()
    return rows

def add_task(category, title, deadline):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute("INSERT INTO tasks (category, title, deadline) VALUES (?, ?, ?)", (category, title, deadline))
    conn.commit()
    conn.close()

def update_task(task_id, category, title, deadline):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute("UPDATE tasks SET category=?, title=?, deadline=? WHERE id=?", (category, title, deadline, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()

def complete_task(task_id):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute("UPDATE tasks SET completed=1 WHERE id=?", (task_id,))
    conn.commit()
    conn.close()

# --- アプリ本体 ---
init_db()
st.title("タスク管理 (ローカルSQLite版)")

# 上段：カテゴリ選択
categories = ["全て", "仕事", "個人開発", "その他"]
selected_category = st.selectbox("カテゴリを選択", categories)

# 中段：タスク一覧
tasks = get_tasks(selected_category)
st.subheader("未完了タスク一覧")
if tasks:
    selected_task = st.radio(
        "タスクを選択してください",
        tasks,
        format_func=lambda x: f"[{x[1]}] {x[2]} : {x[3]}"
    )
else:
    selected_task = None
    st.info("未完了タスクはありません")

# 下段：追加・編集フォーム
st.subheader("タスク追加 / 編集 / 完了 / 削除")

if selected_task:
    task_id, sel_category, sel_deadline, sel_title = selected_task
    mode = "edit"
else:
    task_id, sel_category, sel_deadline, sel_title = None, "仕事", date.today().isoformat(), ""
    mode = "new"

with st.form(key="task_form", clear_on_submit=False):
    category_input = st.selectbox("カテゴリ", categories[1:], index=(categories[1:].index(sel_category) if sel_category in categories[1:] else 0))
    title_input = st.text_input("タイトル", sel_title)
    deadline_input = st.date_input("締切日", value=date.fromisoformat(sel_deadline) if isinstance(sel_deadline, str) else date.today())

    submitted = st.form_submit_button("保存")
    if submitted:
        if not title_input.strip():
            st.error("タイトルは必須です")
        else:
            if mode == "new":
                add_task(category_input, title_input, deadline_input.isoformat())
                st.success("タスクを追加しました")
            else:
                update_task(task_id, category_input, title_input, deadline_input.isoformat())
                st.success("タスクを更新しました")
            st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        if mode == "edit" and st.form_submit_button("完了"):
            complete_task(task_id)
            st.success("タスクを完了にしました")
            st.rerun()
    with col2:
        if mode == "edit" and st.form_submit_button("削除"):
            delete_task(task_id)
            st.success("タスクを削除しました")
            st.rerun()
