# app.py
import streamlit as st
import sqlite3
from datetime import date

# ---------------------------
# データベース設定
# ---------------------------
conn = sqlite3.connect("tasks.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    title TEXT,
    content TEXT,
    importance TEXT,
    due_date TEXT,
    done INTEGER
)
""")
conn.commit()

# ---------------------------
# 上段メニュー
# ---------------------------
MENU_OPTIONS = ["すべて", "仕事", "個人開発", "その他"]
selected_menu = st.selectbox("カテゴリを選択", MENU_OPTIONS)

# ---------------------------
# 中段：タスク一覧
# ---------------------------
st.subheader("タスク一覧")

# 選択メニューに応じて取得
if selected_menu == "すべて":
    c.execute("""
        SELECT id, category, due_date, title FROM tasks
        ORDER BY due_date ASC,
        CASE importance WHEN '最優先' THEN 3 WHEN '優先' THEN 2 ELSE 1 END DESC
    """)
else:
    c.execute("""
        SELECT id, category, due_date, title FROM tasks
        WHERE category=?
        ORDER BY due_date ASC,
        CASE importance WHEN '最優先' THEN 3 WHEN '優先' THEN 2 ELSE 1 END DESC
    """, (selected_menu,))
tasks = c.fetchall()

task_ids = [t[0] for t in tasks]
task_display = [f"{t[1]} | {t[2]} | {t[3]}" for t in tasks]

selected_task_index = st.selectbox("編集するタスクを選択", [""] + task_display)
selected_task_id = task_ids[selected_task_index-1] if selected_task_index != "" else None

# ---------------------------
# 下段：タスク追加／編集フォーム
# ---------------------------
st.subheader("タスク追加／編集")
with st.form("task_form"):
    if selected_task_id:
        c.execute("SELECT category, title, content, importance, due_date, done FROM tasks WHERE id=?", (selected_task_id,))
        task_data = c.fetchone()
        category_val, title_val, content_val, importance_val, due_date_val, done_val = task_data
        due_date_val = date.fromisoformat(due_date_val)
    else:
        category_val, title_val, content_val, importance_val, due_date_val, done_val = "仕事", "", "", "通常", date.today(), False

    category = st.radio("カテゴリ", ["仕事", "個人開発", "その他"], index=["仕事","個人開発","その他"].index(category_val))
    title = st.text_input("タイトル", value=title_val)
    content = st.text_area("内容", value=content_val)
    importance = st.radio("重要度", ["最優先", "優先", "通常"], index=["最優先","優先","通常"].index(importance_val))
    due_date = st.date_input("締切日", value=due_date_val)
    done = st.checkbox("完了", value=bool(done_val))

    submitted_add = st.form_submit_button("追加")
    submitted_update = st.form_submit_button("更新")
    submitted_delete = st.form_submit_button("削除")

    if submitted_add and title.strip() != "":
        c.execute("""
            INSERT INTO tasks (category, title, content, importance, due_date, done)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (category, title, content, importance, due_date.isoformat(), int(done)))
        conn.commit()
        st.success(f"タスク '{title}' を追加しました！")
        st.experimental_rerun()

    if submitted_update and selected_task_id:
        c.execute("""
            UPDATE tasks
            SET category=?, title=?, content=?, importance=?, due_date=?, done=?
            WHERE id=?
        """, (category, title, content, importance, due_date.isoformat(), int(done), selected_task_id))
        conn.commit()
        st.success(f"タスク '{title}' を更新しました！")
        st.experimental_rerun()

    if submitted_delete and selected_task_id:
        c.execute("DELETE FROM tasks WHERE id=?", (selected_task_id,))
        conn.commit()
        st.success(f"タスク '{title}' を削除しました！")
        st.experimental_rerun()
