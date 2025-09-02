# app.py
import streamlit as st
import sqlite3
from datetime import date

# データベース接続
conn = sqlite3.connect("tasks.db", check_same_thread=False)
c = conn.cursor()

# テーブル作成（存在しない場合のみ）
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

# --- ヘルパー関数 ---
def get_tasks(selected_category):
    if selected_category == "全て":
        c.execute("SELECT id, category, title, content, priority, deadline FROM tasks WHERE completed=0 ORDER BY deadline, priority DESC, title")
    else:
        c.execute("SELECT id, category, title, content, priority, deadline FROM tasks WHERE completed=0 AND category=? ORDER BY deadline, priority DESC, title", (selected_category,))
    return c.fetchall()

def add_task(category, title, content, priority, deadline):
    c.execute("INSERT INTO tasks (category, title, content, priority, deadline) VALUES (?, ?, ?, ?, ?)", (category, title, content, priority, deadline))
    conn.commit()

def update_task(task_id, category, title, content, priority, deadline, completed):
    c.execute("UPDATE tasks SET category=?, title=?, content=?, priority=?, deadline=?, completed=? WHERE id=?",
              (category, title, content, priority, deadline, completed, task_id))
    conn.commit()

def delete_task(task_id):
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()

# --- UI ---
st.title("タスク管理アプリ")

# 上段：カテゴリ選択
categories = ["全て", "仕事", "個人開発", "その他"]
selected_category = st.selectbox("カテゴリ選択", categories)

# 中段：タスク一覧
st.subheader("タスク一覧")
tasks = get_tasks(selected_category)
task_display = [f"{t[1]} | {t[2]} | {t[3]} | {t[4]} | {t[5]}" for t in tasks]
selected_index = st.selectbox("編集／削除するタスクを選択", range(len(task_display)), format_func=lambda x: task_display[x] if tasks else "")

# 下段：追加／編集フォーム
st.subheader("タスク追加／編集")
with st.form("task_form"):
    if tasks:
        selected_task = tasks[selected_index]
        task_id = selected_task[0]
        category_val = selected_task[1]
        title_val = selected_task[2]
        content_val = selected_task[3]
        priority_val = selected_task[4]
        deadline_val = selected_task[5]
        completed_val = 0
    else:
        task_id = None
        category_val = "仕事"
        title_val = ""
        content_val = ""
        priority_val = "中"
        deadline_val = str(date.today())
        completed_val = 0

    # 入力項目順序
    category_input = st.selectbox("カテゴリ", categories, index=categories.index(category_val))
    title_input = st.text_input("タイトル", title_val)
    content_input = st.text_area("内容", content_val)
    priority_input = st.selectbox("重要度", ["高", "中", "低"], index=["高","中","低"].index(priority_val))
    deadline_input = st.date_input("締切日", value=date.fromisoformat(deadline_val))
    completed_input = st.checkbox("完了", value=completed_val)

    submitted = st.form_submit_button("保存")
    if submitted:
        if task_id:  # 編集
            update_task(task_id, category_input, title_input, content_input, priority_input, str(deadline_input), int(completed_input))
            st.success("タスクを更新しました")
        else:  # 新規追加
            add_task(category_input, title_input, content_input, priority_input, str(deadline_input))
            st.success("タスクを追加しました")
        st.experimental_rerun()

# 編集／削除操作ボタン
if tasks:
    if st.button("削除"):
        delete_task(tasks[selected_index][0])
        st.success("タスクを削除しました")
        st.experimental_rerun()
