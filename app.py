import streamlit as st
import sqlite3
from datetime import date

# -----------------------------
# DB 初期化（UI確認用:毎回新規作成）
# -----------------------------
conn = sqlite3.connect("tasks.db")
c = conn.cursor()

# tasks テーブル作成（既存があれば削除して新規作成）
c.execute("DROP TABLE IF EXISTS tasks")
c.execute("""
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    deadline TEXT,
    priority TEXT,
    title TEXT,
    content TEXT,
    completed INTEGER
)
""")
conn.commit()

# -----------------------------
# 上段：カテゴリ選択
# -----------------------------
st.title("タスク管理（UI固め版）")

categories = ["全て", "仕事", "個人開発", "その他"]
selected_category = st.selectbox("カテゴリ選択", categories)

# -----------------------------
# 中段：タスク一覧
# -----------------------------
def get_tasks(category):
    if category == "全て":
        c.execute("SELECT id, category, deadline, priority, title FROM tasks WHERE completed=0 ORDER BY deadline, priority DESC, title")
    else:
        c.execute(
            "SELECT id, category, deadline, priority, title FROM tasks WHERE completed=0 AND category=? ORDER BY deadline, priority DESC, title",
            (category,)
        )
    return c.fetchall()

tasks = get_tasks(selected_category)

st.subheader("タスク一覧")
selected_task_index = st.selectbox(
    "編集するタスクを選択",
    options=range(len(tasks)),
    format_func=lambda x: f"{tasks[x][1]} | {tasks[x][2]} | {tasks[x][3]} | {tasks[x][4]}" if tasks else ""
) if tasks else None

selected_task = tasks[selected_task_index] if selected_task_index is not None else None

# -----------------------------
# 下段：タスク追加／編集フォーム
# -----------------------------
st.subheader("タスク追加／編集")
with st.form(key="task_form"):
    category = st.selectbox("カテゴリ", ["仕事", "個人開発", "その他"], index=["仕事", "個人開発", "その他"].index(selected_task[1]) if selected_task else 0)
    deadline = st.date_input("締切日", value=date.fromisoformat(selected_task[2]) if selected_task else date.today())
    priority = st.selectbox("重要度", ["高", "中", "低"], index=["高", "中", "低"].index(selected_task[3]) if selected_task else 1)
    title = st.text_input("タイトル", value=selected_task[4] if selected_task else "")
    content = st.text_area("内容", value=selected_task[5] if selected_task else "")
    completed = st.checkbox("完了", value=selected_task[6] if selected_task else False)

    submit_add = st.form_submit_button("新規追加")
    submit_update = st.form_submit_button("保存")
    submit_delete = st.form_submit_button("削除")

# -----------------------------
# フォーム操作
# -----------------------------
if submit_add:
    c.execute(
        "INSERT INTO tasks (category, deadline, priority, title, content, completed) VALUES (?, ?, ?, ?, ?, ?)",
        (category, deadline.isoformat(), priority, title, content, int(completed))
    )
    conn.commit()
    st.experimental_rerun()

if submit_update and selected_task:
    c.execute(
        "UPDATE tasks SET category=?, deadline=?, priority=?, title=?, content=?, completed=? WHERE id=?",
        (category, deadline.isoformat(), priority, title, content, int(completed), selected_task[0])
    )
    conn.commit()
    st.experimental_rerun()

if submit_delete and selected_task:
    c.execute("DELETE FROM tasks WHERE id=?", (selected_task[0],))
    conn.commit()
    st.experimental_rerun()
