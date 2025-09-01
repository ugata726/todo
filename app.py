# app.py
import streamlit as st
import sqlite3
from datetime import datetime

# ----- DBセットアップ -----
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
    done INTEGER DEFAULT 0
)
""")
conn.commit()

# ----- UI設定 -----
st.set_page_config(page_title="TODOアプリ（UI固め版）", layout="centered")

# ----- メニュー固定 -----
CATEGORIES = ["仕事", "個人開発", "その他"]

st.markdown("## タスク追加 / 編集フォーム")

with st.form("task_form", clear_on_submit=True):
    col1, col2 = st.columns([1, 2])
    with col1:
        category = st.selectbox("カテゴリ", CATEGORIES)
    with col2:
        title = st.text_input("タイトル")
    content = st.text_area("内容")
    importance = st.radio("重要度", ["最優先", "優先", "通常"])
    due_date = st.date_input("締切日")
    submitted = st.form_submit_button("追加 / 更新")

    if submitted:
        c.execute("""
        INSERT INTO tasks (category, title, content, importance, due_date)
        VALUES (?, ?, ?, ?, ?)
        """, (category, title, content, importance, due_date.strftime("%Y-%m-%d")))
        conn.commit()
        st.success(f"タスク『{title}』を追加しました！")
        st.experimental_rerun()

# ----- タスク一覧 -----
st.markdown("## タスク一覧")
c.execute("""
SELECT id, category, title, due_date
FROM tasks
ORDER BY due_date ASC, title ASC
""")
rows = c.fetchall()

if rows:
    for row in rows:
        st.write(f"{row[1]} | {row[3]} | {row[2]}")
else:
    st.info("タスクは存在しません。")

# ----- 選択タスク詳細表示 -----
st.markdown("## タスク詳細（編集 / 削除）")
task_ids = [row[0] for row in rows]
selected_id = st.selectbox("編集・削除対象タスクを選択", ["未選択"] + task_ids)

if selected_id != "未選択":
    c.execute("SELECT category, title, content, importance, due_date FROM tasks WHERE id=?", (selected_id,))
    t = c.fetchone()
    if t:
        with st.form("edit_form"):
            category_edit = st.selectbox("カテゴリ", CATEGORIES, index=CATEGORIES.index(t[0]))
            title_edit = st.text_input("タイトル", t[1])
            content_edit = st.text_area("内容", t[2])
            importance_edit = st.radio("重要度", ["最優先", "優先", "通常"], index=["最優先","優先","通常"].index(t[3]))
            due_date_edit = st.date_input("締切日", datetime.strptime(t[4], "%Y-%m-%d"))
            update_btn = st.form_submit_button("更新")
            delete_btn = st.form_submit_button("削除")

            if update_btn:
                c.execute("""
                UPDATE tasks
                SET category=?, title=?, content=?, importance=?, due_date=?
                WHERE id=?
                """, (category_edit, title_edit, content_edit, importance_edit, due_date_edit.strftime("%Y-%m-%d"), selected_id))
                conn.commit()
                st.success("タスクを更新しました！")
                st.experimental_rerun()
            if delete_btn:
                c.execute("DELETE FROM tasks WHERE id=?", (selected_id,))
                conn.commit()
                st.success("タスクを削除しました！")
                st.experimental_rerun()
