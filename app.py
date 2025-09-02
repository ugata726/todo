# app.py
import streamlit as st
import sqlite3
from datetime import date

DB_PATH = "tasks.db"

# DB 初期化（毎回新規作成してUI確認用）
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    deadline TEXT,
    priority TEXT,
    title TEXT,
    content TEXT,
    completed INTEGER DEFAULT 0
)
""")
conn.commit()

# 上段：カテゴリ選択
categories = ["全て", "仕事", "個人開発", "その他"]
selected_category = st.selectbox("カテゴリ選択", categories)

# 中段：タスク一覧取得
def get_tasks(category):
    query = "SELECT id, category, deadline, priority, title, content FROM tasks WHERE completed=0"
    if category != "全て":
        query += " AND category=?"
        c.execute(query + " ORDER BY deadline, priority DESC, title", (category,))
    else:
        c.execute(query + " ORDER BY deadline, priority DESC, title")
    return c.fetchall()

tasks = get_tasks(selected_category)

st.subheader("タスク一覧")
for t in tasks:
    st.write(f"[{t[3]}] {t[2]} {t[4]} - {t[5]} ({t[1]})")

# 下段：タスク追加／編集／削除フォーム
st.subheader("タスク追加／編集")
with st.form("task_form", clear_on_submit=True):
    form_category = st.selectbox("カテゴリ", categories[1:])  # 全ては選択不可
    form_deadline = st.date_input("締切日", date.today())
    form_priority = st.selectbox("重要度", ["高", "中", "低"])
    form_title = st.text_input("タイトル")
    form_content = st.text_area("内容")
    form_completed = st.checkbox("完了")
    
    submit_type = st.radio("操作", ["新規追加", "編集", "削除"])
    task_id = st.number_input("編集/削除用ID（新規追加時は無視）", min_value=0, step=1)
    
    submitted = st.form_submit_button("実行")
    
    if submitted:
        if submit_type == "新規追加":
            c.execute(
                "INSERT INTO tasks (category, deadline, priority, title, content, completed) VALUES (?, ?, ?, ?, ?, ?)",
                (form_category, form_deadline.isoformat(), form_priority, form_title, form_content, int(form_completed))
            )
            conn.commit()
            st.success("タスク追加完了")
        elif submit_type == "編集":
            c.execute(
                "UPDATE tasks SET category=?, deadline=?, priority=?, title=?, content=?, completed=? WHERE id=?",
                (form_category, form_deadline.isoformat(), form_priority, form_title, form_content, int(form_completed), task_id)
            )
            conn.commit()
            st.success("タスク編集完了")
        elif submit_type == "削除":
            c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            conn.commit()
            st.success("タスク削除完了")
        st.experimental_rerun()
