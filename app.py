# app.py
import streamlit as st
import sqlite3
from datetime import datetime

# --- DB初期化（UI確認用、毎回新規作成） ---
conn = sqlite3.connect("tasks.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    title TEXT,
    content TEXT,
    priority INTEGER,
    deadline TEXT,
    completed INTEGER DEFAULT 0
)
""")
conn.commit()

# --- 上段：カテゴリ選択 ---
categories = ["全て", "仕事", "個人開発", "その他"]
selected_category = st.selectbox("カテゴリ選択", categories)

# --- 中段：タスク一覧 ---
def get_tasks(cat):
    if cat == "全て":
        c.execute("SELECT id, category, title, content, priority, deadline FROM tasks WHERE completed=0 ORDER BY deadline, priority DESC, title")
    else:
        c.execute("SELECT id, category, title, content, priority, deadline FROM tasks WHERE completed=0 AND category=? ORDER BY deadline, priority DESC, title", (cat,))
    return c.fetchall()

tasks = get_tasks(selected_category)

st.write("### タスク一覧")
if tasks:
    st.dataframe(
        data=[[t[1], t[5], t[2]] for t in tasks],  # カテゴリ、締切日、タイトル
        columns=["カテゴリ", "締切日", "タイトル"],
        use_container_width=True
    )
else:
    st.write("タスクはありません")

# --- 下段：タスク追加／編集フォーム ---
st.write("### タスク追加／編集")
with st.form("task_form"):
    form_category = st.selectbox("カテゴリ", ["仕事", "個人開発", "その他"])
    form_title = st.text_input("タイトル")
    form_content = st.text_area("内容")
    form_priority = st.number_input("重要度", min_value=1, max_value=5, value=3)
    form_deadline = st.date_input("締切日", datetime.today())
    form_completed = st.checkbox("完了")

    submitted = st.form_submit_button("保存")
    if submitted:
        # 新規追加
        c.execute("INSERT INTO tasks (category, title, content, priority, deadline, completed) VALUES (?, ?, ?, ?, ?, ?)",
                  (form_category, form_title, form_content, form_priority, form_deadline.strftime("%Y-%m-%d"), int(form_completed)))
        conn.commit()
        st.experimental_rerun()

# --- 下段：選択タスク編集／削除 ---
st.write("### タスク編集／削除")
task_ids = [t[0] for t in tasks]
selected_task_id = st.selectbox("編集するタスクを選択", ["未選択"] + task_ids)

if selected_task_id != "未選択":
    task_data = next(t for t in tasks if t[0] == selected_task_id)
    with st.form("edit_form"):
        edit_category = st.selectbox("カテゴリ", ["仕事", "個人開発", "その他"], index=["仕事", "個人開発", "その他"].index(task_data[1]))
        edit_title = st.text_input("タイトル", value=task_data[2])
        edit_content = st.text_area("内容", value=task_data[3])
        edit_priority = st.number_input("重要度", min_value=1, max_value=5, value=task_data[4])
        edit_deadline = st.date_input("締切日", datetime.strptime(task_data[5], "%Y-%m-%d"))
        edit_completed = st.checkbox("完了", value=False)

        save_btn = st.form_submit_button("保存")
        delete_btn = st.form_submit_button("削除")

        if save_btn:
            c.execute("""UPDATE tasks SET category=?, title=?, content=?, priority=?, deadline=?, completed=?
                         WHERE id=?""",
                      (edit_category, edit_title, edit_content, edit_priority,
                       edit_deadline.strftime("%Y-%m-%d"), int(edit_completed), selected_task_id))
            conn.commit()
            st.experimental_rerun()
        if delete_btn:
            c.execute("DELETE FROM tasks WHERE id=?", (selected_task_id,))
            conn.commit()
            st.experimental_rerun()
